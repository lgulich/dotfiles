"""
Main GitStackPush class for managing stacked MRs.
"""
# pylint: disable=too-many-lines

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from git_stack.change_id import (
    extract_change_id,
    extract_position,
    extract_stack_name,
    generate_change_id,
    get_branch_name,
    get_git_username,
    validate_stack_name,
)
from git_stack.hosting_client import GitHostingClient, GitLabClient

# Lock for thread-safe mapping file operations
_mapping_lock = threading.Lock()

# Backup ref name for rollback
BACKUP_REF = 'refs/git-stack/backup'


class GitStackError(Exception):
    """Base exception for git-stack errors."""


class DirtyWorkingTreeError(GitStackError):
    """Raised when working tree has uncommitted changes."""


class CherryPickError(GitStackError):
    """Raised when cherry-pick fails."""


def load_mapping(path: Path) -> dict[str, Any]:
    """
    Load the Change-Id to MR mapping from file (thread-safe).

    Args:
        path: Path to the mapping JSON file

    Returns:
        Dictionary containing the mapping, empty dict if file doesn't exist
    """
    with _mapping_lock:
        if not path.exists():
            return {}

        try:
            with open(path) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (OSError, json.JSONDecodeError):
            return {}


def save_mapping(path: Path, data: dict[str, Any]) -> None:
    """
    Save the Change-Id to MR mapping to file (thread-safe).

    Args:
        path: Path to the mapping JSON file
        data: Dictionary to save
    """
    with _mapping_lock:
        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


def add_change_id_to_message(message: str, change_id: str) -> str:
    """
    Add Change-Id to a commit message if not already present.

    Args:
        message: Original commit message
        change_id: Change-Id to add

    Returns:
        Updated message with Change-Id
    """
    # Check if Change-Id already exists
    if extract_change_id(message):
        return message

    # Add blank line before Change-Id if message doesn't end with newline
    if message and not message.endswith('\n'):
        message += '\n'

    # Add another newline to separate from body
    if message and not message.endswith('\n\n'):
        message += '\n'

    return f"{message}Change-Id: {change_id}"


def truncate_mr_title(title: str, max_length: int = 255) -> str:
    """
    Truncate MR title to fit GitLab's 255-character limit.

    Args:
        title: Original title
        max_length: Maximum length (default 255 for GitLab)

    Returns:
        Truncated title with ellipsis if needed
    """
    if len(title) <= max_length:
        return title
    return title[:max_length - 3] + '...'


def build_stack_chain_description(chain: list[dict[str,
                                                   Any]], current_index: int,
                                  mr_mapping: dict[str, Any]) -> str:
    """
    Build a markdown description section showing the stack chain.

    Args:
        chain: List of commits in the chain
        current_index: Index of the current commit in the chain
        mr_mapping: Mapping of change_id to MR info

    Returns:
        Markdown string with stack chain information
    """
    lines = [
        '<!-- git-stack-chain -->',
        '',
        '## Stacked MRs',
        '',
    ]

    for i, commit in enumerate(chain):
        change_id = commit['change_id']

        if change_id not in mr_mapping:
            continue

        mr_info = mr_mapping[change_id]
        mr_iid = mr_info['mr_iid']
        mr_url = mr_info['mr_url']

        # Add visual indicator for current MR
        if i == current_index:
            if i > 0:
                lines.append('')
            prefix = '  - **'
            suffix = '** (this MR)'
        else:
            prefix = '  - '
            suffix = ''

        lines.append(
            f"{prefix}[!{mr_iid}]({mr_url}) {commit['subject']}{suffix}")

        if i == current_index and i < len(chain) - 1:
            lines.append('')

    lines.extend(['', '---', ''])

    return '\n'.join(lines)


def build_mr_chain(commits: list[dict[str, Any]],
                   base_branch: str) -> list[dict[str, Any]]:
    """
    Build MR chain with target branches for each commit.

    Args:
        commits: List of commit dicts with 'sha', 'change_id', 'subject'
        base_branch: The base branch name (may include origin/ prefix)

    Returns:
        List of commits with added 'target_branch' and 'source_branch' fields
    """
    chain = []

    # Strip origin/ prefix for MR target branches
    target_base_branch = base_branch.replace('origin/', '')

    for i, commit in enumerate(commits):
        commit_copy = commit.copy()

        if i == 0:
            commit_copy['target_branch'] = target_base_branch
        else:
            prev_change_id = commits[i - 1]['change_id']
            commit_copy['target_branch'] = get_branch_name(prev_change_id)

        commit_copy['source_branch'] = get_branch_name(commit['change_id'])
        chain.append(commit_copy)

    return chain


class GitStackPush:
    """Main class for managing stacked MRs."""

    def __init__(
        self,
        dry_run: bool = False,
        mapping_path: Path | None = None,
        stack_name: str | None = None,
        client: GitHostingClient | None = None,
    ):
        """
        Initialize GitStackPush.

        Args:
            dry_run: If True, don't execute any commands
            mapping_path: Path to mapping file (defaults to .git/git-stack-mapping.json)
            stack_name: Optional stack name to use
            client: GitHostingClient instance (defaults to GitLabClient)
        """
        self.dry_run = dry_run
        self.stack_name_override = stack_name

        # Set up mapping path - default to .git/ directory (per-repo)
        if mapping_path is None:
            import os  # pylint: disable=import-outside-toplevel

            env_path = os.getenv('GIT_STACK_MAPPING_FILE')
            if env_path:
                self.mapping_path = Path(env_path)
            else:
                # Use .git directory for per-repo mapping
                try:
                    git_dir = self._run_git_command(['rev-parse', '--git-dir'])
                    self.mapping_path = Path(
                        git_dir) / 'git-stack-mapping.json'
                except subprocess.CalledProcessError:
                    # Fallback to home directory if not in a git repo
                    self.mapping_path = (Path.home() / '.config' /
                                         'git-stack-mapping.json')
        else:
            self.mapping_path = mapping_path

        self.mapping = load_mapping(self.mapping_path)

        # Set up client
        self.client: GitHostingClient
        if client is None:
            self.client = GitLabClient(dry_run=dry_run)
        else:
            self.client = client

    def _run_git_command(self, args: list[str], check: bool = True) -> str:
        """
        Run a git command and return output.

        Args:
            args: Git command arguments
            check: Whether to raise exception on error

        Returns:
            Command output as string
        """
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            check=False,
        )

        if check and result.returncode != 0:
            error_msg = (result.stderr.strip()
                         if result.stderr else result.stdout.strip())
            print(f"Error running git command: git {' '.join(args)}",
                  file=sys.stderr)
            print(f"Error output: {error_msg}", file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode,
                                                ['git'] + args, result.stdout,
                                                result.stderr)

        return result.stdout.strip()

    def _validate_environment(self) -> None:
        """Validate that required tools and environment are available."""
        try:
            self._run_git_command(['rev-parse', '--git-dir'])
        except subprocess.CalledProcessError:
            print('Error: Not in a git repository', file=sys.stderr)
            sys.exit(1)

    def _check_clean_working_tree(self) -> None:
        """
        Check that the working tree is clean.

        Raises:
            DirtyWorkingTreeError: If there are uncommitted changes
        """
        status = self._run_git_command(['status', '--porcelain'])
        if status:
            raise DirtyWorkingTreeError(
                'Working tree has uncommitted changes. '
                'Please commit or stash them before proceeding.\n'
                f"Changes:\n{status}")

    def _create_backup_ref(self) -> None:
        """Create a backup ref pointing to current HEAD for rollback."""
        if self.dry_run:
            print('[DRY-RUN] Would create backup ref')
            return

        self._run_git_command(['update-ref', BACKUP_REF, 'HEAD'], check=False)

    def _restore_from_backup(self) -> bool:
        """
        Restore HEAD from backup ref.

        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            backup_sha = self._run_git_command(['rev-parse', BACKUP_REF],
                                               check=False)
            if backup_sha:
                self._run_git_command(['reset', '--hard', backup_sha])
                return True
        except subprocess.CalledProcessError:
            pass
        return False

    def _cleanup_backup_ref(self) -> None:
        """Remove the backup ref after successful operation."""
        self._run_git_command(['update-ref', '-d', BACKUP_REF], check=False)

    def _get_commits(self, base_branch: str) -> list[dict[str, Any]]:
        """
        Get list of commits between base branch and HEAD.

        Args:
            base_branch: Base branch to compare against

        Returns:
            List of commit dictionaries
        """
        if not base_branch.startswith('origin/'):
            base_branch = f"origin/{base_branch}"

        try:
            output = self._run_git_command(
                ['rev-list', '--reverse', f"{base_branch}..HEAD"])
            commit_shas = output.split('\n') if output else []
        except subprocess.CalledProcessError:
            print(
                f"Error: Unable to get commits. Is '{base_branch}' a valid branch?",
                file=sys.stderr,
            )
            sys.exit(1)

        if not commit_shas or commit_shas == ['']:
            return []

        commits = []
        for sha in commit_shas:
            message = self._run_git_command(['log', '-1', '--format=%B', sha])
            subject = self._run_git_command(['log', '-1', '--format=%s', sha])
            change_id = extract_change_id(message)

            commits.append({
                'sha': sha,
                'change_id': change_id,
                'subject': subject,
                'message': message,
            })

        return commits

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def _add_change_ids_to_commits(
            self, commits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Add Change-Ids to commits that don't have them.

        This rewrites git history using cherry-pick. Creates a backup ref
        before starting and rolls back on failure.

        Args:
            commits: List of commit dictionaries

        Returns:
            Updated list with Change-Ids added

        Raises:
            DirtyWorkingTreeError: If working tree has uncommitted changes
            CherryPickError: If cherry-pick fails and rollback is performed
        """
        commits_needing_ids = [c for c in commits if c['change_id'] is None]

        if not commits_needing_ids:
            return commits

        # Check for uncommitted changes before rewriting history
        self._check_clean_working_tree()

        # Determine stack name
        stack_name = self._determine_stack_name(commits)

        # Determine starting position
        start_position = 1
        for commit in commits:
            if commit['change_id']:
                pos = extract_position(commit['change_id'])
                if pos and pos >= start_position:
                    start_position = pos + 1

        if self.dry_run:
            print(f"\n[DRY-RUN] Would add Change-Ids to "
                  f"{len(commits_needing_ids)} commit(s) "
                  f"with stack name '{stack_name}'")
            position = 1
            for commit in commits:
                if commit['change_id'] is None:
                    new_id = generate_change_id(stack_name, position)
                    commit['change_id'] = new_id
                    print(f"  {commit['sha'][:8]}: {commit['subject']} -> "
                          f"Change-Id: {new_id}")
                else:
                    pos = extract_position(commit['change_id'])
                    if pos:
                        position = pos
                position += 1
            return commits

        # Create backup before rewriting history
        self._create_backup_ref()

        print(f"\nAdding Change-Ids to {len(commits_needing_ids)} "
              f"commit(s) with stack name '{stack_name}'...")

        # Save current branch/ref
        original_ref = self._run_git_command(['symbolic-ref', '-q', 'HEAD'],
                                             check=False)
        if not original_ref:
            original_ref = self._run_git_command(['rev-parse', 'HEAD'])

        # Get the base commit (parent of first commit)
        base_sha = self._run_git_command(
            ['rev-parse', f'{commits[0]["sha"]}~1'])

        try:
            # Checkout the base
            self._run_git_command(['checkout', base_sha], check=False)

            # Cherry-pick each commit and amend with Change-Id
            position = 1
            for commit in commits:
                if commit['change_id'] is None:
                    new_change_id = generate_change_id(stack_name, position)
                    commit['change_id'] = new_change_id

                    # Cherry-pick the commit
                    result = subprocess.run(
                        ['git', 'cherry-pick', commit['sha']],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if result.returncode != 0:
                        # Cherry-pick failed - abort and rollback
                        self._run_git_command(['cherry-pick', '--abort'],
                                              check=False)
                        self._restore_from_backup()
                        raise CherryPickError(
                            f"Cherry-pick failed for commit {commit['sha'][:8]}: "
                            f"{commit['subject']}\n"
                            f"Error: {result.stderr or result.stdout}\n"
                            'Rolled back to original state.')

                    # Amend with new message including Change-Id
                    new_message = add_change_id_to_message(
                        commit['message'], new_change_id)
                    self._run_git_command(
                        ['commit', '--amend', '-m', new_message])

                    # Update commit info
                    new_sha = self._run_git_command(['rev-parse', 'HEAD'])
                    commit['sha'] = new_sha
                    commit['message'] = new_message

                    print(f"  {commit['sha'][:8]}: {commit['subject']} -> "
                          f"Change-Id: {new_change_id}")
                else:
                    # Commit already has Change-Id, just cherry-pick it
                    result = subprocess.run(
                        ['git', 'cherry-pick', commit['sha']],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if result.returncode != 0:
                        self._run_git_command(['cherry-pick', '--abort'],
                                              check=False)
                        self._restore_from_backup()
                        raise CherryPickError(
                            f"Cherry-pick failed for commit {commit['sha'][:8]}: "
                            f"{commit['subject']}\n"
                            f"Error: {result.stderr or result.stdout}\n"
                            'Rolled back to original state.')

                    new_sha = self._run_git_command(['rev-parse', 'HEAD'])
                    commit['sha'] = new_sha
                    pos = extract_position(commit['change_id'])
                    if pos:
                        position = pos

                position += 1

            # Return to original branch/ref
            if original_ref.startswith('refs/heads/'):
                branch_name = original_ref.replace('refs/heads/', '')
                self._run_git_command(['checkout', branch_name], check=False)
                self._run_git_command(['reset', '--hard', commits[-1]['sha']],
                                      check=False)
            else:
                self._run_git_command(['checkout', commits[-1]['sha']],
                                      check=False)

            # Clean up backup ref on success
            self._cleanup_backup_ref()

        except CherryPickError:
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Unexpected error - try to rollback
            self._restore_from_backup()
            raise CherryPickError(
                f"Unexpected error during history rewrite: {e}\n"
                'Rolled back to original state.') from e

        return commits

    def _determine_stack_name(self, commits: list[dict[str, Any]]) -> str:
        """
        Determine the stack name to use.

        Args:
            commits: List of commits

        Returns:
            Stack name string
        """
        # Check command line override
        if self.stack_name_override:
            if not validate_stack_name(self.stack_name_override):
                print(
                    f"Error: Invalid stack name '{self.stack_name_override}'. "
                    'Stack names must contain only lowercase letters, numbers, '
                    'and hyphens.',
                    file=sys.stderr,
                )
                sys.exit(1)
            print(
                f"\nUsing stack name '{self.stack_name_override}' from command line"
            )
            return self.stack_name_override

        # Try to get from existing commits
        for commit in commits:
            if commit['change_id']:
                stack_name = extract_stack_name(commit['change_id'])
                if stack_name:
                    print(
                        f"\nUsing stack name '{stack_name}' from existing commits"
                    )
                    return stack_name

        # Prompt for stack name
        if self.dry_run:
            return 'example'

        while True:
            stack_name = input(
                "\nEnter stack name (e.g., 'feature', 'bugfix-123'): ").strip(
                )
            if validate_stack_name(stack_name):
                return stack_name
            print('  Error: Stack name must contain only lowercase letters, '
                  'numbers, and hyphens, and cannot start/end with a hyphen.')

    def _rebase_downstream_commits(self, commits: list[dict[str, Any]],
                                   _base_branch: str) -> list[dict[str, Any]]:
        """
        Fetch and rebase any downstream commits that exist on remote.

        If the local stack has commits 1-3 but remote has 1-4, this will
        fetch commit 4 and rebase it onto the local commit 3.

        Args:
            commits: List of local commits (with Change-IDs)
            base_branch: Base branch name

        Returns:
            Updated list of commits including rebased downstream commits
        """
        if not commits or not commits[0].get('change_id'):
            return commits

        stack_name = extract_stack_name(commits[0]['change_id'])
        if not stack_name:
            return commits

        # Get positions of local commits
        local_positions = set()
        for commit in commits:
            pos = extract_position(commit['change_id'])
            if pos:
                local_positions.add(pos)

        if not local_positions:
            return commits

        max_local_pos = max(local_positions)

        # Find downstream MRs on remote
        remote_mrs = self.client.find_mrs_by_stack_name(stack_name)
        downstream_mrs = []
        for mr in remote_mrs:
            # Extract position from branch name
            branch = mr['source_branch']
            # Branch format: user/stackname@position
            if '@' in branch:
                try:
                    pos = int(branch.split('@')[-1])
                    if pos > max_local_pos and mr['state'] == 'opened':
                        downstream_mrs.append((pos, mr))
                except ValueError:
                    continue

        if not downstream_mrs:
            return commits

        # Sort by position
        downstream_mrs.sort(key=lambda x: x[0])

        print(
            f"\nFound {len(downstream_mrs)} downstream commit(s) to rebase...")

        if self.dry_run:
            for pos, mr in downstream_mrs:
                print(f"[DRY-RUN] Would rebase: {mr['source_branch']} "
                      f"(position {pos})")
            return commits

        # Fetch and rebase each downstream commit
        for pos, mr in downstream_mrs:
            branch = mr['source_branch']
            print(f"  Rebasing {branch}...")

            try:
                # Fetch the branch
                self._run_git_command(['fetch', 'origin', branch])

                # Cherry-pick the commit onto current HEAD
                self._run_git_command(['cherry-pick', f'origin/{branch}'],
                                      check=True)

                # Get the new commit info
                new_sha = self._run_git_command(['rev-parse', 'HEAD']).strip()
                message = self._run_git_command(
                    ['log', '-1', '--format=%B', new_sha]).strip()
                subject = self._run_git_command(
                    ['log', '-1', '--format=%s', new_sha]).strip()
                change_id = extract_change_id(message)

                commits.append({
                    'sha': new_sha,
                    'message': message,
                    'subject': subject,
                    'change_id': change_id,
                })

                print(f"    + Rebased to {new_sha[:8]}")

            except subprocess.CalledProcessError as e:
                # Cherry-pick failed - likely a conflict
                print(f"\n  Rebase conflict while rebasing {branch}!")
                print('  Please resolve the conflict and then run:')
                print('    git cherry-pick --continue')
                print('    git-stack push')
                print('\n  Or abort with:')
                print('    git cherry-pick --abort')
                raise CherryPickError(
                    f"Rebase conflict while rebasing {branch}. "
                    'Please resolve manually.') from e

        return commits

    def _create_or_update_branches(self, chain: list[dict[str, Any]]) -> None:
        """
        Create or update branches for each commit in the chain.
        """
        print('\nCreating/updating branches...')

        try:
            current_branch = self._run_git_command(
                ['symbolic-ref', '--short', 'HEAD'], check=False).strip()
        except subprocess.CalledProcessError:
            current_branch = None

        if self.dry_run:
            for commit in chain:
                branch_name = commit['source_branch']
                print(f"[DRY-RUN] Would create/update branch: "
                      f"{branch_name} at {commit['sha'][:8]}")
            refspecs = [
                f"{commit['sha']}:refs/heads/{commit['source_branch']}"
                for commit in chain
            ]
            print(
                f"[DRY-RUN] Would push: git push -f origin {' '.join(refspecs)}"
            )
        else:
            # Create/update all local branches first
            for commit in chain:
                branch_name = commit['source_branch']
                if current_branch != branch_name:
                    self._run_git_command(
                        ['branch', '-f', branch_name, commit['sha']])

            # Batch push all branches
            refspecs = [
                f"{commit['sha']}:refs/heads/{commit['source_branch']}"
                for commit in chain
            ]
            push_cmd = ['push', '-f', 'origin'] + refspecs
            self._run_git_command(push_cmd)

            for commit in chain:
                print(f"  + {commit['source_branch']} at {commit['sha'][:8]}")

    # pylint: disable=too-many-locals,too-many-branches
    def _create_or_update_mrs(self, chain: list[dict[str, Any]]) -> None:
        """
        Create or update MRs for each commit in the chain.
        """
        print('\nCreating/updating MRs...')

        if self.dry_run:
            for commit in chain:
                change_id = commit['change_id']
                source_branch = commit['source_branch']
                target_branch = commit['target_branch']
                existing_mr = self.mapping.get(change_id)

                if existing_mr:
                    print(
                        f"[DRY-RUN] Would update MR !{existing_mr['mr_iid']}")
                else:
                    print('[DRY-RUN] Would create new MR')
                print(f"           Title: {commit['subject']}")
                print(
                    f"           Source: {source_branch} -> Target: {target_branch}"
                )
            return

        def process_mr(
            commit: dict[str, Any], ) -> tuple[str, int, str, str, str | None]:
            change_id = commit['change_id']
            source_branch = commit['source_branch']
            target_branch = commit['target_branch']
            existing_mr = self.mapping.get(change_id)

            if existing_mr:
                mr_iid = existing_mr['mr_iid']
                title = truncate_mr_title(commit['subject'])
                # Always pass target_branch to ensure it's updated if stack changed
                self.client.update_mr(mr_iid, title, target_branch)
                return ('update', mr_iid, existing_mr['mr_url'],
                        commit['subject'], None)

            title = truncate_mr_title(commit['subject'])
            # Remove Change-Id line from description (it should only be in commit)
            description = '\n'.join(
                line for line in commit['message'].split('\n')
                if not line.strip().startswith('Change-Id:')).rstrip()
            result = self.client.create_mr(
                source_branch=source_branch,
                target_branch=target_branch,
                title=title,
                description=description,
            )
            return (
                'create',
                result['mr_iid'],
                result['mr_url'],
                commit['subject'],
                change_id,
            )

        # Process all MRs in parallel
        results: list[tuple[str, int, str, str, str | None]] = []
        errors: list[tuple[str, str]] = []

        with ThreadPoolExecutor(max_workers=min(len(chain), 4)) as executor:
            futures = {
                executor.submit(process_mr, commit): commit
                for commit in chain
            }

            for future in as_completed(futures):
                commit = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    errors.append((commit['subject'], str(e)))

        # Update mapping for all new MRs (thread-safe)
        new_mrs_created = False
        for action, mr_iid, mr_url, _subject, change_id in results:
            if action == 'create' and change_id:
                self.mapping[change_id] = {
                    'mr_iid': mr_iid,
                    'mr_url': mr_url,
                    'project_id': self._get_project_id(),
                }
                new_mrs_created = True

        if new_mrs_created:
            save_mapping(self.mapping_path, self.mapping)

        # Print results
        for action, mr_iid, mr_url, subject, _ in results:
            if action == 'create':
                print(f"  + Created MR !{mr_iid}: {subject}")
            else:
                print(f"  ~ Updated MR !{mr_iid}: {subject}")
            print(f"    {mr_url}")

        for subject, error in errors:
            print(f"  ! Failed to process MR for {subject}: {error}")

    def _set_mr_dependencies(self, chain: list[dict[str, Any]]) -> None:
        """Set MR dependencies so each MR depends on the previous one."""
        print('\nSetting MR dependencies...')

        if self.dry_run:
            for i, commit in enumerate(chain):
                if i == 0:
                    continue
                change_id = commit['change_id']
                if change_id not in self.mapping:
                    continue
                prev_change_id = chain[i - 1]['change_id']
                if prev_change_id not in self.mapping:
                    continue
                mr_iid = self.mapping[change_id]['mr_iid']
                prev_mr_iid = self.mapping[prev_change_id]['mr_iid']
                print(
                    f"[DRY-RUN] Would set MR !{mr_iid} to depend on !{prev_mr_iid}"
                )
            return

        def set_dependency(
                i: int, commit: dict[str,
                                     Any]) -> tuple[str, int, int, str] | None:
            if i == 0:
                return None

            change_id = commit['change_id']
            if change_id not in self.mapping:
                return None

            prev_change_id = chain[i - 1]['change_id']
            if prev_change_id not in self.mapping:
                return None

            mr_iid = self.mapping[change_id]['mr_iid']
            prev_mr_iid = self.mapping[prev_change_id]['mr_iid']

            try:
                self.client.set_mr_dependencies(mr_iid, [prev_mr_iid])
                return ('success', mr_iid, prev_mr_iid, '')
            except ValueError as e:
                return ('not_available', 0, 0, str(e))
            except Exception as e:  # pylint: disable=broad-exception-caught
                return ('error', mr_iid, prev_mr_iid, str(e))

        feature_not_available = False
        with ThreadPoolExecutor(max_workers=min(len(chain), 4)) as executor:
            futures = {
                executor.submit(set_dependency, i, commit): (i, commit)
                for i, commit in enumerate(chain)
            }

            for future in as_completed(futures):
                result = future.result()
                if result is None:
                    continue

                status, mr_iid, prev_mr_iid, error = result
                if status == 'success':
                    print(f"  + Set MR !{mr_iid} to depend on !{prev_mr_iid}")
                elif status == 'not_available':
                    if not feature_not_available:
                        feature_not_available = True
                        print(f"  ! Skipping MR dependencies: {error}")
                    break
                else:
                    print(f"  ! Failed to set dependency for "
                          f"MR !{mr_iid} on !{prev_mr_iid}: {error}")

    def _update_mr_stack_links(self, chain: list[dict[str, Any]]) -> None:
        """Update MR comments with stack chain links."""
        print('\nUpdating MR stack links...')

        if self.dry_run:
            for commit in chain:
                change_id = commit['change_id']
                if change_id not in self.mapping:
                    continue
                mr_iid = self.mapping[change_id]['mr_iid']
                print(
                    f"[DRY-RUN] Would update stack links comment for MR !{mr_iid}"
                )
            return

        def update_stack_link(
                i: int, commit: dict[str, Any]) -> tuple[str, int, str] | None:
            change_id = commit['change_id']
            if change_id not in self.mapping:
                return None

            mr_iid = self.mapping[change_id]['mr_iid']
            stack_description = build_stack_chain_description(
                chain, i, self.mapping)

            try:
                existing_notes = self.client.get_mr_notes(mr_iid)
                stack_note_id = None
                for note in existing_notes:
                    if '<!-- git-stack-chain -->' in note['body']:
                        stack_note_id = note['id']
                        break

                if stack_note_id:
                    self.client.update_mr_note(mr_iid, stack_note_id,
                                               stack_description)
                else:
                    self.client.add_mr_note(mr_iid, stack_description)

                return ('success', mr_iid, '')
            except Exception as e:  # pylint: disable=broad-exception-caught
                return ('error', mr_iid, str(e))

        with ThreadPoolExecutor(max_workers=min(len(chain), 4)) as executor:
            futures = {
                executor.submit(update_stack_link, i, commit): (i, commit)
                for i, commit in enumerate(chain)
            }

            for future in as_completed(futures):
                result = future.result()
                if result is None:
                    continue

                status, mr_iid, error = result
                if status == 'success':
                    print(f"  + Updated stack links comment for MR !{mr_iid}")
                else:
                    print(
                        f"  ! Failed to update stack links for MR !{mr_iid}: {error}"
                    )

    def _get_project_id(self) -> str:
        """Get the GitLab project ID from git remote."""
        try:
            remote_url = self._run_git_command(['remote', 'get-url', 'origin'])
            match = re.search(r'[:/]([^/]+/[^/]+?)(?:\.git)?$', remote_url)
            if match:
                return match.group(1)
        except subprocess.CalledProcessError:
            pass
        return 'unknown'

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def push(self, base_branch: str) -> dict[str, Any] | None:
        """
        Process commits and create/update stacked MRs.

        Args:
            base_branch: Base branch to stack on

        Returns:
            Dict with execution plan if dry_run, None otherwise
        """
        self._validate_environment()

        commits = self._get_commits(base_branch)

        if not commits:
            print(f"No commits found between {base_branch} and HEAD")
            return None

        print(f"\nFound {len(commits)} commit(s) to process")

        try:
            commits = self._add_change_ids_to_commits(commits)
            # Fetch and rebase any downstream commits from remote
            commits = self._rebase_downstream_commits(commits, base_branch)
        except DirtyWorkingTreeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except CherryPickError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        chain = build_mr_chain(commits, base_branch)

        if self.dry_run:
            print('\n' + '=' * 60)
            print('DRY-RUN: MR Chain Plan')
            print('=' * 60)
            for i, commit in enumerate(chain, 1):
                print(f"\n{i}. {commit['subject']}")
                print(f"   SHA: {commit['sha'][:8]}")
                print(f"   Change-Id: {commit['change_id']}")
                print(f"   Branch: {commit['source_branch']}")
                print(f"   Target: {commit['target_branch']}")
                existing = self.mapping.get(commit['change_id'])
                if existing:
                    print(
                        f"   Action: UPDATE existing MR !{existing['mr_iid']}")
                else:
                    print('   Action: CREATE new MR')
            print('\n' + '=' * 60)
            return {'commits': commits, 'chain': chain}

        self._create_or_update_branches(chain)
        self._create_or_update_mrs(chain)
        self._set_mr_dependencies(chain)
        self._update_mr_stack_links(chain)

        print('\n+ Stack processing complete!')
        return None

    def clean(self) -> None:
        """Remove stale branches and entries from mapping file."""
        # First, clean up stale local branches not in the mapping
        stale_branches = self._find_stale_branches()

        if stale_branches:
            print(f"\nFound {len(stale_branches)} stale branch(es)...")
            deleted_local = 0
            deleted_remote = 0

            for branch in stale_branches:
                if self.dry_run:
                    print(f"  [DRY-RUN] Would delete branch {branch}")
                else:
                    # Delete local branch
                    try:
                        self._run_git_command(['branch', '-D', branch],
                                              check=False)
                        deleted_local += 1
                    except subprocess.CalledProcessError:
                        pass

                    # Delete remote branch
                    try:
                        self._run_git_command(
                            ['push', 'origin', '--delete', branch],
                            check=False)
                        deleted_remote += 1
                    except subprocess.CalledProcessError:
                        pass

                    print(f"  Deleted branch {branch}")

            if not self.dry_run and (deleted_local > 0 or deleted_remote > 0):
                print(f"\n+ Deleted {deleted_local} local and "
                      f"{deleted_remote} remote stale branch(es)")
        else:
            print('\nNo stale branches found')

        # Then, clean up mapping entries for closed/merged MRs
        if not self.mapping:
            print('No MRs in mapping file')
            return

        print(f"\nChecking {len(self.mapping)} MR(s)...")

        closed_count = 0
        orphaned_count = 0
        to_remove = []

        for change_id, mr_info in self.mapping.items():
            mr_iid = mr_info['mr_iid']
            branch_name = get_branch_name(change_id)

            # Check if branch exists locally
            try:
                self._run_git_command(['rev-parse', '--verify', branch_name],
                                      check=True)
                branch_exists = True
            except subprocess.CalledProcessError:
                branch_exists = False

            if not branch_exists:
                print(
                    f"  MR !{mr_iid} branch '{branch_name}' not found locally, "
                    'removing from mapping')
                to_remove.append(change_id)
                orphaned_count += 1
                continue

            try:
                state = self.client.get_mr_state(mr_iid)

                if state in ['closed', 'merged']:
                    print(f"  MR !{mr_iid} is {state}, removing from mapping")
                    to_remove.append(change_id)
                    closed_count += 1
                elif state:
                    print(f"  MR !{mr_iid} is {state}, keeping in mapping")
                else:
                    print(
                        f"  Warning: Could not determine state for MR !{mr_iid}, "
                        'keeping in mapping')
            except (subprocess.CalledProcessError, ValueError):
                print(
                    f"  Warning: Could not check MR !{mr_iid}, keeping in mapping"
                )

        for change_id in to_remove:
            del self.mapping[change_id]

        total_removed = closed_count + orphaned_count
        if total_removed > 0:
            save_mapping(self.mapping_path, self.mapping)
            parts = []
            if closed_count > 0:
                parts.append(f"{closed_count} closed/merged")
            if orphaned_count > 0:
                parts.append(f"{orphaned_count} orphaned")
            print(f"\n+ Removed {' and '.join(parts)} MR(s) from mapping")
        else:
            print('\n+ No closed or orphaned MRs found')

    def _find_stale_branches(self) -> list[str]:
        """
        Find local stack branches that are not in the mapping and have no open MR.

        Returns:
            List of stale branch names safe to delete
        """
        user_name = get_git_username()
        prefix = f"{user_name}/stack-"

        # Get all local branches matching the stack pattern
        try:
            output = self._run_git_command([
                'branch', '--list', f'{prefix}*', '--format=%(refname:short)'
            ])
        except subprocess.CalledProcessError:
            return []

        if not output:
            return []

        local_branches = set(output.strip().split('\n'))

        # Get branches that are in the mapping
        mapped_branches = {
            get_branch_name(change_id)
            for change_id in self.mapping
        }

        # Find candidate stale branches (in local but not in mapping)
        candidates = local_branches - mapped_branches

        if not candidates:
            return []

        # Filter out branches that have open MRs on remote
        # This prevents accidentally orphaning MRs not in our mapping
        stale = []
        for branch in candidates:
            if self._branch_has_open_mr(branch):
                print(f"  Skipping {branch} - has open MR on remote")
            else:
                stale.append(branch)

        return sorted(stale)

    def _branch_has_open_mr(self, branch: str) -> bool:
        """
        Check if a branch has an open MR on the remote.

        Args:
            branch: Branch name to check

        Returns:
            True if there's an open MR for this branch
        """
        try:
            # Use glab to check for open MRs with this source branch
            output = self._run_git_command(['ls-remote', 'origin', branch],
                                           check=False)
            # If branch doesn't exist on remote, no MR possible
            if not output:
                return False

            # Check via GitLab API if there's an open MR
            # Extract stack name from branch to search
            if '@' in branch:
                parts = branch.split('@')
                if len(parts) >= 2:
                    stack_name = parts[1]
                    mrs = self.client.find_mrs_by_stack_name(stack_name)
                    for mr in mrs:
                        if mr['source_branch'] == branch and mr[
                                'state'] == 'opened':
                            return True
            return False
        except (subprocess.CalledProcessError, ValueError):
            # If we can't check, be conservative and assume there might be an MR
            return True

    def reindex(self, base_branch: str) -> None:
        """Remove all Change-Ids, close old MRs, and create new Change-Ids."""
        print('\nReindexing stack...')

        commits = self._get_commits(base_branch)

        if not commits:
            print(f"No commits found between {base_branch} and HEAD")
            return

        print(f"\nFound {len(commits)} commit(s) to reindex")

        # Close existing MRs
        closed_count = 0
        for commit in commits:
            if commit['change_id']:
                existing_mr = self.mapping.get(commit['change_id'])
                if existing_mr:
                    mr_iid = existing_mr['mr_iid']

                    if self.dry_run:
                        print(f"[DRY-RUN] Would close MR !{mr_iid} for "
                              f"Change-Id {commit['change_id']}")
                    else:
                        try:
                            self.client.close_mr(mr_iid)
                            print(f"  Closed MR !{mr_iid} for "
                                  f"Change-Id {commit['change_id']}")
                            del self.mapping[commit['change_id']]
                            closed_count += 1
                        except (subprocess.CalledProcessError, ValueError):
                            print(f"  Warning: Could not close MR !{mr_iid}")

        if closed_count > 0 and not self.dry_run:
            save_mapping(self.mapping_path, self.mapping)
            print(f"\n+ Closed {closed_count} MR(s)")

        # Remove Change-Ids from all commits
        print('\nRemoving old Change-Ids and creating new ones...')

        for commit in commits:
            commit['change_id'] = None
            lines = commit['message'].split('\n')
            new_lines = [
                line for line in lines
                if not line.strip().startswith('Change-Id:')
            ]
            commit['message'] = '\n'.join(new_lines).rstrip() + '\n'

        try:
            commits = self._add_change_ids_to_commits(commits)
        except (DirtyWorkingTreeError, CherryPickError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if not self.dry_run:
            print(
                "\n+ Reindexing complete! Run 'git-stack push' to create new MRs"
            )

    # pylint: disable=too-many-branches
    def list(self) -> None:
        """List all stacks with their branches and MRs."""
        if not self.mapping:
            print('No stacks found (mapping file is empty)')
            return

        stacks: dict[str, list[dict[str, Any]]] = {}
        for change_id, mr_info in self.mapping.items():
            stack_name = extract_stack_name(change_id) or 'unknown'

            if stack_name not in stacks:
                stacks[stack_name] = []

            position = extract_position(change_id) or 0

            stacks[stack_name].append({
                'change_id': change_id,
                'position': position,
                'mr_iid': mr_info['mr_iid'],
                'mr_url': mr_info['mr_url'],
                'branch': get_branch_name(change_id),
            })

        for stack_name in sorted(stacks.keys()):
            items = sorted(stacks[stack_name], key=lambda x: x['position'])

            print(f"\nStack: {stack_name}")
            print(f"   Commits: {len(items)}")

            last_item = items[-1]
            print(f"   Last branch: {last_item['branch']}")
            print(
                f"   Last MR: !{last_item['mr_iid']} ({last_item['mr_url']})")

            print('\n   MRs in stack:')
            for item in items:
                print(
                    f"     {item['position']}. !{item['mr_iid']} - {item['branch']}"
                )

        print(f"\n+ Found {len(stacks)} stack(s)")

    def checkout(self, stack_name: str) -> None:
        """Checkout the latest branch from a stack."""
        if not self.mapping:
            print('No stacks found (mapping file is empty)')
            return

        stack_items: list[dict[str, Any]] = []
        for change_id, _ in self.mapping.items():
            current_stack_name = extract_stack_name(change_id)
            if current_stack_name == stack_name:
                position = extract_position(change_id) or 0
                stack_items.append({
                    'change_id': change_id,
                    'position': position,
                    'branch': get_branch_name(change_id),
                })

        if not stack_items:
            print(f"Error: Stack '{stack_name}' not found")
            print('\nAvailable stacks:')
            available_stacks: set[str] = set()
            for cid in self.mapping:
                sn = extract_stack_name(cid)
                if sn:
                    available_stacks.add(sn)
            for sn in sorted(available_stacks):
                print(f"  - {sn}")
            return

        stack_items.sort(key=lambda x: x['position'])
        last_item = stack_items[-1]

        print(f"\nChecking out latest branch from stack '{stack_name}'...")
        print(
            f"  Branch: {last_item['branch']} (position {last_item['position']})"
        )

        if self.dry_run:
            print(f"[DRY-RUN] Would run: git checkout {last_item['branch']}")
        else:
            try:
                self._run_git_command(['checkout', last_item['branch']])
                print(f"\n+ Checked out {last_item['branch']}")
            except subprocess.CalledProcessError:
                print(
                    f"\nError: Could not checkout branch {last_item['branch']}",
                    file=sys.stderr,
                )
                print(
                    f"You may need to fetch it first: "
                    f"git fetch origin {last_item['branch']}",
                    file=sys.stderr,
                )

    def remove(self, stack_name: str) -> None:
        """Remove all branches and close all MRs for a stack."""
        if not self.mapping:
            print('No stacks found (mapping file is empty)')
            return

        stack_items: list[dict[str, Any]] = []
        for change_id, mr_info in self.mapping.items():
            current_stack_name = extract_stack_name(change_id)
            if current_stack_name == stack_name:
                position = extract_position(change_id) or 0
                stack_items.append({
                    'change_id': change_id,
                    'position': position,
                    'branch': get_branch_name(change_id),
                    'mr_iid': mr_info['mr_iid'],
                })

        if not stack_items:
            print(f"Error: Stack '{stack_name}' not found")
            print('\nAvailable stacks:')
            available_stacks: set[str] = set()
            for cid in self.mapping:
                sn = extract_stack_name(cid)
                if sn:
                    available_stacks.add(sn)
            for sn in sorted(available_stacks):
                print(f"  - {sn}")
            return

        stack_items.sort(key=lambda x: x['position'])

        print(
            f"\nRemoving stack '{stack_name}' ({len(stack_items)} commits)...")

        # Close MRs
        closed_count = 0
        for item in stack_items:
            if self.dry_run:
                print(f"[DRY-RUN] Would close MR !{item['mr_iid']}")
            else:
                try:
                    self.client.close_mr(item['mr_iid'])
                    print(f"  Closed MR !{item['mr_iid']}")
                    closed_count += 1
                except (subprocess.CalledProcessError, ValueError):
                    print(f"  Warning: Could not close MR !{item['mr_iid']}")

        # Delete branches
        deleted_count = 0
        for item in stack_items:
            if self.dry_run:
                print(f"[DRY-RUN] Would delete branch {item['branch']}")
            else:
                try:
                    self._run_git_command(['branch', '-D', item['branch']],
                                          check=False)
                    self._run_git_command(
                        ['push', 'origin', '--delete', item['branch']],
                        check=False)
                    print(f"  Deleted branch {item['branch']}")
                    deleted_count += 1
                except subprocess.CalledProcessError:
                    print(
                        f"  Warning: Could not delete branch {item['branch']}")

        # Remove from mapping
        if not self.dry_run:
            for item in stack_items:
                if item['change_id'] in self.mapping:
                    del self.mapping[item['change_id']]

            save_mapping(self.mapping_path, self.mapping)
            print(f"\n+ Removed stack '{stack_name}'")
            print(f"  Closed {closed_count} MR(s)")
            print(f"  Deleted {deleted_count} branch(es)")
        else:
            print(
                f"\n[DRY-RUN] Would remove {len(stack_items)} items from mapping"
            )

    def show(self) -> None:
        """Show information about the current commit's stack."""
        try:
            current_sha = self._run_git_command(['rev-parse', 'HEAD']).strip()
        except subprocess.CalledProcessError:
            print('Error: Could not get current commit', file=sys.stderr)
            return

        try:
            commit_message = self._run_git_command(
                ['log', '-1', '--format=%B', current_sha])
            commit_subject = self._run_git_command(
                ['log', '-1', '--format=%s', current_sha])
        except subprocess.CalledProcessError:
            print('Error: Could not get commit message', file=sys.stderr)
            return

        change_id = extract_change_id(commit_message)

        if not change_id:
            print('\nCurrent commit has no Change-ID')
            print(f"   Commit: {current_sha[:8]}")
            print(f"   Subject: {commit_subject}")
            print("\nRun 'git-stack push' to add a Change-ID and create an MR")
            return

        stack_name = extract_stack_name(change_id)
        position = extract_position(change_id)

        print('\nCurrent Commit')
        print(f"   SHA: {current_sha[:8]}")
        print(f"   Subject: {commit_subject}")
        print(f"   Change-ID: {change_id}")

        if stack_name:
            print(f"\nStack: {stack_name}")
            if position is not None:
                print(f"   Position: {position}")

        if change_id in self.mapping:
            mr_info = self.mapping[change_id]
            print('\nMerge Request')
            print(f"   MR: !{mr_info['mr_iid']}")
            print(f"   URL: {mr_info['mr_url']}")
            print(f"   Branch: {get_branch_name(change_id)}")
        else:
            print('\nNo MR found for this commit')
            print("   Run 'git-stack push' to create an MR")

        if stack_name and self.mapping:
            stack_commits = []
            for cid, mr_info in self.mapping.items():
                sn = extract_stack_name(cid)
                if sn == stack_name:
                    pos = extract_position(cid) or 0
                    stack_commits.append({
                        'change_id': cid,
                        'position': pos,
                        'mr_iid': mr_info['mr_iid'],
                        'is_current': cid == change_id,
                    })

            if len(stack_commits) > 1:
                stack_commits.sort(key=lambda x: x['position'])
                print(f"\nOther commits in '{stack_name}' stack:")
                for sc in stack_commits:
                    if not sc['is_current']:
                        print(f"     {sc['position']}. !{sc['mr_iid']}")

    # pylint: disable=too-many-branches
    def status(self, base_branch: str) -> None:
        """Show status of all commits in the current stack."""
        commits = self._get_commits(base_branch)

        if not commits:
            print(f"No commits found between {base_branch} and HEAD")
            return

        if not commits[0]['change_id']:
            print("No Change-IDs found. Run 'git-stack push' first.")
            return

        stack_name = extract_stack_name(commits[0]['change_id'])

        print(f"\nStack: {stack_name}")
        print(f"   Base: {base_branch}")
        print(f"   Commits: {len(commits)}")
        print()

        for i, commit in enumerate(commits, 1):
            change_id = commit['change_id']
            branch_name = get_branch_name(change_id)

            if change_id not in self.mapping:
                status_icon = 'x'
                status_text = 'No MR'
                detail_text = None
            else:
                try:
                    remote_sha = self._run_git_command(
                        ['rev-parse', f"origin/{branch_name}"],
                        check=False).strip()

                    if not remote_sha:
                        status_icon = '!'
                        status_text = 'Not pushed'
                        detail_text = None
                    elif remote_sha == commit['sha']:
                        status_icon = '+'
                        status_text = 'Up-to-date'
                        detail_text = None
                    else:
                        status_icon = '!'
                        status_text = 'Out of sync'
                        detail_text = (
                            f"Local: {commit['sha'][:8]}, Remote: {remote_sha[:8]}"
                        )
                except subprocess.CalledProcessError:
                    status_icon = '!'
                    status_text = 'Not pushed'
                    detail_text = None

            mr_text = (f"!{self.mapping[change_id]['mr_iid']}"
                       if change_id in self.mapping else 'no MR')
            print(f"  {status_icon} {i}. {commit['subject'][:60]}")
            print(
                f"      SHA: {commit['sha'][:8]}  MR: {mr_text}  Status: {status_text}"
            )
            if detail_text:
                print(f"      {detail_text}")
