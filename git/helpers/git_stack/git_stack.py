#!/usr/bin/env python3
# pylint: disable=too-many-lines,broad-exception-caught
"""
git-stack: Manage stacked GitLab MRs

This script helps manage stacked GitLab MRs where each MR targets the previous
commit's MR branch. It uses Change-Ids (similar to Gerrit) to track commits
across rebases.

Subcommands:
  push     - Create or update stacked MRs
  clean    - Remove closed/merged MRs from mapping file
  reindex  - Remove all Change-Ids, close old MRs, and create new ones
"""

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from git_hosting_client import GitHostingClient, GitLabClient

# Try to import argcomplete for shell completion
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


# pylint: disable=too-few-public-methods
class StackNameCompleter:
    """Custom completer for stack names."""

    def __call__(self, prefix, parsed_args, **kwargs):
        """Return list of stack names for completion."""
        try:
            # Get the mapping file path
            repo_root = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                       capture_output=True,
                                       text=True,
                                       check=True).stdout.strip()

            mapping_path = Path(repo_root) / '.git' / 'git-stack-mapping.json'

            if not mapping_path.exists():
                return []

            with open(mapping_path, 'r') as f:
                mapping = json.load(f)

            # Extract unique stack names
            stack_names = set()
            for change_id in mapping.keys():
                stack_name = extract_stack_name(change_id)
                if stack_name:
                    stack_names.add(stack_name)

            return sorted(stack_names)
        except Exception:
            return []


def extract_change_id(commit_message: str) -> str | None:
    """
    Extract Change-Id from a commit message.

    Args:
        commit_message: The commit message text

    Returns:
        The Change-Id string if found, None otherwise
    """
    if not commit_message:
        return None

    # Match format: uuid-stackname-N (e.g., a1b2c3d4-feature-1)
    match = re.search(r'Change-Id:\s+([a-f0-9]+-[a-z0-9-]+-\d+)',
                      commit_message)
    if match:
        return match.group(1)

    # Also support old format for backward compatibility
    match = re.search(r'Change-Id:\s+([a-f0-9-]+)', commit_message)
    if match:
        return match.group(1)

    return None


def extract_stack_name(change_id: str | None) -> str | None:
    """
    Extract stack name from a Change-Id.

    Args:
        change_id: The Change-Id string (format: uuid-stackname-N)

    Returns:
        The stack name if found, None otherwise
    """
    if not change_id:
        return None

    # Format: uuid-stackname-N
    parts = change_id.split('-')
    if len(parts) >= 3:
        # Return everything between first uuid and last number
        return '-'.join(parts[1:-1])
    return None


def generate_change_id(stack_name: str, position: int) -> str:
    """
    Generate a new Change-Id using UUID, stack name, and position.

    Args:
        stack_name: The name of the stack
        position: The position in the stack (1-indexed)

    Returns:
        A Change-Id in format: uuid-stackname-position (e.g., "a1b2c3d4-feature-1")
    """
    return f"{str(uuid.uuid4())[:8]}-{stack_name}-{position}"


def get_branch_name(change_id: str) -> str:
    """
    Format branch name for a given Change-Id.

    Args:
        change_id: The Change-Id

    Returns:
        Branch name in format: lgulich/stack-<change-id>
    """
    user_name = os.getenv('USER')
    return f"{user_name}/stack-{change_id}"


def load_mapping(path: Path) -> dict[str, Any]:
    """
    Load the Change-Id to MR mapping from file.

    Args:
        path: Path to the mapping JSON file

    Returns:
        Dictionary containing the mapping, empty dict if file doesn't exist
    """
    if not path.exists():
        return {}

    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_mapping(path: Path, data: dict[str, Any]) -> None:
    """
    Save the Change-Id to MR mapping to file.

    Args:
        path: Path to the mapping JSON file
        data: Dictionary to save
    """
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
        '## 📚 Stacked MRs',
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
            # Add blank line before current MR for visual separation
            if i > 0:
                lines.append('')
            prefix = '  - ➡️  **'
            suffix = '** (this MR)'
        else:
            prefix = '  - '
            suffix = ''

        # Format: - [!123](url) Title
        lines.append(
            f"{prefix}[!{mr_iid}]({mr_url}) {commit['subject']}{suffix}")

        # Add blank line after current MR for visual separation
        if i == current_index and i < len(chain) - 1:
            lines.append('')

    lines.append('')
    lines.append('---')
    lines.append('')

    return '\n'.join(lines)


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
    # Leave room for ellipsis
    return title[:max_length - 3] + '...'


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

    # Strip origin/ prefix for MR target branches (GitLab uses local branch names)
    target_base_branch = base_branch.replace('origin/', '')

    for i, commit in enumerate(commits):
        commit_copy = commit.copy()

        # First commit targets base branch
        if i == 0:
            commit_copy['target_branch'] = target_base_branch
        else:
            # Subsequent commits target previous commit's branch
            prev_change_id = commits[i - 1]['change_id']
            commit_copy['target_branch'] = get_branch_name(prev_change_id)

        # Source branch is this commit's branch
        commit_copy['source_branch'] = get_branch_name(commit['change_id'])

        chain.append(commit_copy)

    return chain


class GitStackPush:
    """Main class for managing stacked MRs."""

    def __init__(self,
                 dry_run: bool = False,
                 mapping_path: Path | None = None,
                 stack_name: str | None = None,
                 client: GitHostingClient | None = None):
        """
        Initialize GitStackPush.

        Args:
            dry_run: If True, don't execute any commands
            mapping_path: Path to mapping file (defaults to
                ~/.config/stacked-mrs-map.json or GIT_STACK_MAPPING_FILE
                env var)
            stack_name: Optional stack name to use (if not provided,
                will be detected or prompted)
            client: GitHostingClient instance (defaults to GitLabClient)
        """
        self.dry_run = dry_run
        self.stack_name_override = stack_name

        # Set up mapping path with environment variable support
        if mapping_path is None:
            env_path = os.getenv('GIT_STACK_MAPPING_FILE')
            if env_path:
                self.mapping_path = Path(env_path)
            else:
                self.mapping_path = Path.home(
                ) / '.config' / 'stacked-mrs-map.json'
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
        result = subprocess.run(['git'] + args,
                                capture_output=True,
                                text=True,
                                check=False)

        if check and result.returncode != 0:
            error_msg = result.stderr.strip(
            ) if result.stderr else result.stdout.strip()
            print(f"Error running git command: git {' '.join(args)}",
                  file=sys.stderr)
            print(f"Error output: {error_msg}", file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode,
                                                ['git'] + args, result.stdout,
                                                result.stderr)

        return result.stdout.strip()

    def _validate_environment(self) -> None:
        """Validate that required tools and environment are available."""
        # Check if in git repo
        try:
            self._run_git_command(['rev-parse', '--git-dir'])
        except subprocess.CalledProcessError:
            print('Error: Not in a git repository', file=sys.stderr)
            sys.exit(1)

    def _get_commits(self, base_branch: str) -> list[dict[str, Any]]:
        """
        Get list of commits between base branch and HEAD.

        Args:
            base_branch: Base branch to compare against (will use
                origin/<branch> if not already prefixed)

        Returns:
            List of commit dictionaries
        """
        # Ensure we're using the remote branch
        if not base_branch.startswith('origin/'):
            base_branch = f'origin/{base_branch}'

        # Get list of commit SHAs
        try:
            commit_shas = self._run_git_command(
                ['rev-list', '--reverse', f'{base_branch}..HEAD']).split('\n')
        except subprocess.CalledProcessError:
            print(
                f"Error: Unable to get commits. Is '{base_branch}' a valid branch?",
                file=sys.stderr)
            sys.exit(1)

        if not commit_shas or commit_shas == ['']:
            return []

        commits = []
        for sha in commit_shas:
            # Get commit message
            message = self._run_git_command(['log', '-1', '--format=%B', sha])
            subject = self._run_git_command(['log', '-1', '--format=%s', sha])

            # Extract or generate Change-Id
            change_id = extract_change_id(message)

            commits.append({
                'sha': sha,
                'change_id': change_id,
                'subject': subject,
                'message': message
            })

        return commits

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def _add_change_ids_to_commits(
            self, commits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Add Change-Ids to commits that don't have them.

        Args:
            commits: List of commit dictionaries

        Returns:
            Updated list with Change-Ids added
        """
        commits_needing_ids = [c for c in commits if c['change_id'] is None]

        if not commits_needing_ids:
            return commits

        # Determine stack name
        stack_name = None

        # Check if stack name was provided via command line
        if self.stack_name_override:
            stack_name = self.stack_name_override
            print(f"\nUsing stack name '{stack_name}' from command line")
        else:
            # Try to get stack name from ANY existing commit (not just those needing IDs)
            for commit in commits:
                if commit['change_id']:
                    stack_name = extract_stack_name(commit['change_id'])
                    if stack_name:
                        print(
                            f"\nUsing stack name '{stack_name}' from existing commits"
                        )
                        break

            # If no stack name found, prompt for one
            if not stack_name:
                if self.dry_run:
                    stack_name = 'example'
                else:
                    while True:
                        stack_name = input(
                            '\nEnter stack name '
                            "(e.g., 'feature', 'bugfix-123'): ").strip()
                        if stack_name and re.match(r'^[a-z0-9-]+$',
                                                   stack_name):
                            break
                        print('  Error: Stack name must contain only '
                              'lowercase letters, numbers, and hyphens')

        # Determine starting position based on existing commits
        start_position = 1
        for commit in commits:
            if commit['change_id']:
                # Extract position from change_id (format: uuid-stackname-N)
                parts = commit['change_id'].split('-')
                if parts and parts[-1].isdigit():
                    pos = int(parts[-1])
                    if pos >= start_position:
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
                    print(
                        f"  {commit['sha'][:8]}: {commit['subject']} -> Change-Id: {new_id}"
                    )
                else:
                    # Extract position from existing change_id
                    parts = commit['change_id'].split('-')
                    if parts and parts[-1].isdigit():
                        position = int(parts[-1])
                position += 1
            return commits

        # We need to rewrite commits to add Change-Ids
        print(f"\nAdding Change-Ids to {len(commits_needing_ids)} "
              f"commit(s) with stack name '{stack_name}'...")

        # Save current branch/ref
        original_ref = self._run_git_command(['symbolic-ref', '-q', 'HEAD'],
                                             check=False)
        if not original_ref:
            # We're already in detached HEAD, get the commit
            original_ref = self._run_git_command(['rev-parse', 'HEAD'])

        # Get the base commit (parent of first commit)
        base_sha = self._run_git_command(
            ['rev-parse', f'{commits[0]["sha"]}~1'])

        # Checkout the base
        self._run_git_command(['checkout', base_sha], check=False)

        # Cherry-pick each commit and amend with Change-Id
        position = 1
        for commit in commits:
            if commit['change_id'] is None:
                # Generate new Change-Id with stack name and position
                new_change_id = generate_change_id(stack_name, position)
                commit['change_id'] = new_change_id

                # Cherry-pick the commit
                self._run_git_command(['cherry-pick', commit['sha']],
                                      check=False)

                # Amend with new message including Change-Id
                new_message = add_change_id_to_message(commit['message'],
                                                       new_change_id)
                self._run_git_command(['commit', '--amend', '-m', new_message])

                # Update commit info
                new_sha = self._run_git_command(['rev-parse', 'HEAD'])
                commit['sha'] = new_sha
                commit['message'] = new_message

                print(
                    f"  {commit['sha'][:8]}: {commit['subject']} -> Change-Id: {new_change_id}"
                )
            else:
                # Commit already has Change-Id, just cherry-pick it
                self._run_git_command(['cherry-pick', commit['sha']],
                                      check=False)
                new_sha = self._run_git_command(['rev-parse', 'HEAD'])
                commit['sha'] = new_sha
                # Extract position from existing change_id
                parts = commit['change_id'].split('-')
                if parts and parts[-1].isdigit():
                    position = int(parts[-1])

            position += 1

        # Return to original branch/ref
        if original_ref.startswith('refs/heads/'):
            # Was on a branch, check it out and update it
            branch_name = original_ref.replace('refs/heads/', '')
            self._run_git_command(['checkout', branch_name], check=False)
            # Update branch to point to new HEAD
            self._run_git_command(['reset', '--hard', commits[-1]['sha']],
                                  check=False)
        else:
            # Was in detached HEAD, just checkout the last commit
            self._run_git_command(['checkout', commits[-1]['sha']],
                                  check=False)

        return commits

    def _create_or_update_branches(self, chain: list[dict[str, Any]]) -> None:
        """
        Create or update branches for each commit in the chain.
        Batches all pushes into a single git push command for efficiency.

        Args:
            chain: List of commits with target/source branches
        """
        print('\nCreating/updating branches...')

        # Get current branch to check if we're on one of the branches we're updating
        try:
            current_branch = self._run_git_command(
                ['symbolic-ref', '--short', 'HEAD'], check=False).strip()
        except subprocess.CalledProcessError:
            current_branch = None  # Detached HEAD

        if self.dry_run:
            for commit in chain:
                branch_name = commit['source_branch']
                print(
                    f"[DRY-RUN] Would create/update branch: {branch_name} at {commit['sha'][:8]}"
                )

            # Show the batched push command
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
                # Skip if we're currently on this branch (can't force update it)
                if current_branch != branch_name:
                    self._run_git_command(
                        ['branch', '-f', branch_name, commit['sha']])

            # Batch push all branches in a single command
            refspecs = [
                f"{commit['sha']}:refs/heads/{commit['source_branch']}"
                for commit in chain
            ]
            push_cmd = ['push', '-f', 'origin'] + refspecs
            self._run_git_command(push_cmd)

            # Print success messages
            for commit in chain:
                print(f"  ✓ {commit['source_branch']} at {commit['sha'][:8]}")

    # pylint: disable=too-many-locals,too-many-branches
    def _create_or_update_mrs(self, chain: list[dict[str, Any]]) -> None:
        """
        Create or update MRs for each commit in the chain.
        Uses parallel execution for better performance.

        Args:
            chain: List of commits with target/source branches
        """
        print('\nCreating/updating MRs...')

        if self.dry_run:
            # Dry run - just print what would happen
            for commit in chain:
                change_id = commit['change_id']
                source_branch = commit['source_branch']
                target_branch = commit['target_branch']
                existing_mr = self.mapping.get(change_id)

                if existing_mr:
                    mr_iid = existing_mr['mr_iid']
                    print(f"[DRY-RUN] Would update MR !{mr_iid}")
                    print(f"           Title: {commit['subject']}")
                    print(
                        f"           Source: {source_branch} -> Target: {target_branch}"
                    )
                else:
                    print('[DRY-RUN] Would create new MR')
                    print(f"           Title: {commit['subject']}")
                    print(
                        f"           Source: {source_branch} -> Target: {target_branch}"
                    )
        else:
            # Helper function to process a single MR
            def process_mr(commit):
                change_id = commit['change_id']
                source_branch = commit['source_branch']
                target_branch = commit['target_branch']
                existing_mr = self.mapping.get(change_id)

                if existing_mr:
                    # Update existing MR
                    mr_iid = existing_mr['mr_iid']
                    title = truncate_mr_title(commit['subject'])
                    self.client.update_mr(mr_iid, title)
                    return ('update', mr_iid, existing_mr['mr_url'],
                            commit['subject'], None)

                # Create new MR
                title = truncate_mr_title(commit['subject'])
                result = self.client.create_mr(source_branch=source_branch,
                                               target_branch=target_branch,
                                               title=title,
                                               description=commit['message'])
                return ('create', result['mr_iid'], result['mr_url'],
                        commit['subject'], change_id)

            # Process all MRs in parallel
            results = []
            errors = []

            with ThreadPoolExecutor(
                    max_workers=min(len(chain), 4)) as executor:
                futures = {
                    executor.submit(process_mr, commit): commit
                    for commit in chain
                }

                for future in as_completed(futures):
                    commit = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        errors.append((commit['subject'], str(e)))

            # Update mapping for all new MRs
            new_mrs_created = False
            for action, mr_iid, mr_url, subject, change_id in results:
                if action == 'create':
                    self.mapping[change_id] = {
                        'mr_iid': mr_iid,
                        'mr_url': mr_url,
                        'project_id': self._get_project_id()
                    }
                    new_mrs_created = True

            # Save mapping once if any new MRs were created
            if new_mrs_created:
                save_mapping(self.mapping_path, self.mapping)

            # Print results
            for action, mr_iid, mr_url, subject, change_id in results:
                if action == 'create':
                    print(f"  ✓ Created MR !{mr_iid}: {subject}")
                    print(f"    {mr_url}")
                else:
                    print(f"  ✓ Updated MR !{mr_iid}: {subject}")
                    print(f"    {mr_url}")

            # Print errors
            for subject, error in errors:
                print(f"  ⚠️  Failed to process MR for {subject}: {error}")

    def _set_mr_dependencies(self, chain: list[dict[str, Any]]) -> None:
        """
        Set MR dependencies so each MR depends on the previous one in the chain.
        Uses parallel execution for better performance.

        Args:
            chain: List of commits with target/source branches
        """
        print('\nSetting MR dependencies...')

        if self.dry_run:
            # Dry run - just print what would happen
            for i, commit in enumerate(chain):
                if i == 0:
                    continue  # First MR has no dependencies

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
        else:
            # Helper function to set dependency for a single MR
            def set_dependency(i, commit):
                if i == 0:
                    return None  # First MR has no dependencies

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
                    return ('success', mr_iid, prev_mr_iid)
                except ValueError as e:
                    # Feature not available (requires Premium/Ultimate)
                    return ('not_available', str(e))
                except Exception as e:
                    return ('error', mr_iid, prev_mr_iid, str(e))

            # Process all dependencies in parallel
            feature_not_available = False
            with ThreadPoolExecutor(
                    max_workers=min(len(chain), 4)) as executor:
                futures = {
                    executor.submit(set_dependency, i, commit): (i, commit)
                    for i, commit in enumerate(chain)
                }

                for future in as_completed(futures):
                    result = future.result()
                    if result is None:
                        continue

                    if result[0] == 'success':
                        mr_iid = result[1]
                        prev_mr_iid = result[2]
                        print(
                            f"  ✓ Set MR !{mr_iid} to depend on !{prev_mr_iid}"
                        )
                    elif result[0] == 'not_available':
                        if not feature_not_available:
                            feature_not_available = True
                            error_msg = result[1]
                            print(
                                f'  ⚠️  Skipping MR dependencies: {error_msg}')
                            print(
                                '     (Dependencies can still be set manually '
                                'in the GitLab UI)')
                        break  # No point trying the rest
                    else:
                        mr_iid = result[1]
                        prev_mr_iid = result[2]
                        error = result[3]
                        print(f'  ⚠️  Failed to set dependency for '
                              f'MR !{mr_iid} on !{prev_mr_iid}: {error}')

    def _update_mr_stack_links(self, chain: list[dict[str, Any]]) -> None:
        """
        Update MR comments with stack chain links.
        Uses parallel execution for better performance.

        Creates or updates a non-resolvable comment containing links to all MRs
        in the current stack.

        Args:
            chain: List of commits with target/source branches
        """
        print('\nUpdating MR stack links...')

        if self.dry_run:
            # Dry run - just print what would happen
            for i, commit in enumerate(chain):
                change_id = commit['change_id']
                if change_id not in self.mapping:
                    continue
                mr_iid = self.mapping[change_id]['mr_iid']
                print(
                    f"[DRY-RUN] Would update stack links comment for MR !{mr_iid}"
                )
        else:
            # Helper function to update a single MR's stack links
            def update_stack_link(i, commit):
                change_id = commit['change_id']

                if change_id not in self.mapping:
                    return None

                mr_iid = self.mapping[change_id]['mr_iid']
                stack_description = build_stack_chain_description(
                    chain, i, self.mapping)

                try:
                    # Get existing notes and find stack chain comment
                    existing_notes = self.client.get_mr_notes(mr_iid)
                    stack_note_id = None
                    for note in existing_notes:
                        if '<!-- git-stack-chain -->' in note['body']:
                            stack_note_id = note['id']
                            break

                    # Update existing comment or create new one
                    if stack_note_id:
                        self.client.update_mr_note(mr_iid, stack_note_id,
                                                   stack_description)
                    else:
                        self.client.add_mr_note(mr_iid, stack_description)

                    return ('success', mr_iid)
                except Exception as e:
                    return ('error', mr_iid, str(e))

            # Process all stack link updates in parallel
            with ThreadPoolExecutor(
                    max_workers=min(len(chain), 4)) as executor:
                futures = {
                    executor.submit(update_stack_link, i, commit): (i, commit)
                    for i, commit in enumerate(chain)
                }

                for future in as_completed(futures):
                    result = future.result()
                    if result is None:
                        continue

                    if result[0] == 'success':
                        mr_iid = result[1]
                        print(
                            f"  ✓ Updated stack links comment for MR !{mr_iid}"
                        )
                    else:
                        mr_iid = result[1]
                        error = result[2]
                        print(
                            f"  ⚠️  Failed to update stack links comment for MR !{mr_iid}: {error}"
                        )

    def _get_project_id(self) -> str:
        """Get the GitLab project ID from git remote."""
        try:
            remote_url = self._run_git_command(['remote', 'get-url', 'origin'])
            # Extract project path from URL
            # Example: git@gitlab.com:user/project.git -> user/project
            match = re.search(r'[:/]([^/]+/[^/]+?)(?:\.git)?$', remote_url)
            if match:
                return match.group(1)
        except subprocess.CalledProcessError:
            pass
        return 'unknown'

    def push(self, base_branch: str) -> dict[str, Any] | None:
        """
        Process commits and create/update stacked MRs.

        Args:
            base_branch: Base branch to stack on

        Returns:
            Dict with execution plan if dry_run, None otherwise
        """
        self._validate_environment()

        # Get commits
        commits = self._get_commits(base_branch)

        if not commits:
            print(f"No commits found between {base_branch} and HEAD")
            return None

        print(f"\nFound {len(commits)} commit(s) to process")

        # Add Change-Ids to commits without them
        commits = self._add_change_ids_to_commits(commits)

        # Build MR chain
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

        # Create/update branches
        self._create_or_update_branches(chain)

        # Create/update MRs
        self._create_or_update_mrs(chain)

        # Set MR dependencies
        self._set_mr_dependencies(chain)

        # Update MR descriptions with stack links
        self._update_mr_stack_links(chain)

        print('\n✓ Stack processing complete!')
        return None

    def clean(self) -> None:
        """Remove entries from mapping file for closed MRs."""
        if not self.mapping:
            print('No MRs in mapping file')
            return

        print(f"\nChecking {len(self.mapping)} MR(s) for closed status...")

        closed_count = 0
        to_remove = []

        for change_id, mr_info in self.mapping.items():
            mr_iid = mr_info['mr_iid']

            try:
                # Get MR state using client
                state = self.client.get_mr_state(mr_iid)

                if state in ['closed', 'merged']:
                    print(f"  MR !{mr_iid} is {state}, removing from mapping")
                    to_remove.append(change_id)
                    closed_count += 1
                elif state:
                    print(f"  MR !{mr_iid} is {state}, keeping in mapping")
                else:
                    print(
                        f"  Warning: Could not determine state for MR !{mr_iid}, keeping in mapping"
                    )
            except (subprocess.CalledProcessError, ValueError):
                print(
                    f"  Warning: Could not check MR !{mr_iid}, keeping in mapping"
                )

        # Remove closed MRs from mapping
        for change_id in to_remove:
            del self.mapping[change_id]

        if closed_count > 0:
            save_mapping(self.mapping_path, self.mapping)
            print(f"\n✓ Removed {closed_count} closed MR(s) from mapping")
        else:
            print('\n✓ No closed MRs found')

    def reindex(self, base_branch: str) -> None:
        """Remove all Change-Ids, close old MRs, and create new Change-Ids."""
        print('\nReindexing stack...')

        # Get commits
        commits = self._get_commits(base_branch)

        if not commits:
            print(f"No commits found between {base_branch} and HEAD")
            return

        print(f"\nFound {len(commits)} commit(s) to reindex")

        # Close existing MRs for these commits
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
                            print(
                                f"  Closed MR !{mr_iid} for Change-Id {commit['change_id']}"
                            )
                            del self.mapping[commit['change_id']]
                            closed_count += 1
                        except (subprocess.CalledProcessError, ValueError):
                            print(f"  Warning: Could not close MR !{mr_iid}")

        if closed_count > 0 and not self.dry_run:
            save_mapping(self.mapping_path, self.mapping)
            print(f"\n✓ Closed {closed_count} MR(s)")

        # Remove Change-Ids from all commits
        print('\nRemoving old Change-Ids and creating new ones...')

        # Force all commits to need new IDs and strip Change-Id from messages
        for commit in commits:
            commit['change_id'] = None
            # Remove Change-Id line from commit message
            lines = commit['message'].split('\n')
            new_lines = []
            for line in lines:
                if not line.strip().startswith('Change-Id:'):
                    new_lines.append(line)
            commit['message'] = '\n'.join(new_lines).rstrip() + '\n'

        # Add new Change-Ids
        commits = self._add_change_ids_to_commits(commits)

        if not self.dry_run:
            print(
                "\n✓ Reindexing complete! Run 'git_stack.py push' to create new MRs"
            )

    def list(self) -> None:
        """List all stacks with their branches and MRs."""
        if not self.mapping:
            print('No stacks found (mapping file is empty)')
            return

        # Group by stack name
        stacks: dict[str, list[dict[str, Any]]] = {}
        for change_id, mr_info in self.mapping.items():
            stack_name = extract_stack_name(change_id)
            if not stack_name:
                stack_name = 'unknown'

            if stack_name not in stacks:
                stacks[stack_name] = []

            # Extract position from change_id
            parts = change_id.split('-')
            position = int(parts[-1]) if parts and parts[-1].isdigit() else 0

            stacks[stack_name].append({
                'change_id': change_id,
                'position': position,
                'mr_iid': mr_info['mr_iid'],
                'mr_url': mr_info['mr_url'],
                'branch': get_branch_name(change_id)
            })

        # Sort stacks by name
        for stack_name in sorted(stacks.keys()):
            items = sorted(stacks[stack_name], key=lambda x: x['position'])

            print(f"\n📚 Stack: {stack_name}")
            print(f"   Commits: {len(items)}")

            # Show the last (highest position) branch
            last_item = items[-1]
            print(f"   Last branch: {last_item['branch']}")
            print(
                f"   Last MR: !{last_item['mr_iid']} ({last_item['mr_url']})")

            # Show all MRs in the stack
            print('\n   MRs in stack:')
            for item in items:
                print(
                    f"     {item['position']}. !{item['mr_iid']} - {item['branch']}"
                )

        print(f"\n✓ Found {len(stacks)} stack(s)")

    def checkout(self, stack_name: str) -> None:
        """Checkout the latest branch from a stack."""
        if not self.mapping:
            print('No stacks found (mapping file is empty)')
            return

        # Find all commits in the specified stack
        stack_items: list[dict[str, Any]] = []
        for change_id, _ in self.mapping.items():
            current_stack_name = extract_stack_name(change_id)
            if current_stack_name == stack_name:
                # Extract position from change_id
                parts = change_id.split('-')
                position = int(
                    parts[-1]) if parts and parts[-1].isdigit() else 0

                stack_items.append({
                    'change_id': change_id,
                    'position': position,
                    'branch': get_branch_name(change_id)
                })

        if not stack_items:
            print(f"Error: Stack '{stack_name}' not found")
            print('\nAvailable stacks:')
            # Show available stacks
            available_stacks = set()
            for change_id in self.mapping.keys():
                sn = extract_stack_name(change_id)
                if sn:
                    available_stacks.add(sn)
            for sn in sorted(available_stacks):
                print(f"  - {sn}")
            return

        # Sort by position and get the last one
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
                print(f"\n✓ Checked out {last_item['branch']}")
            except subprocess.CalledProcessError:
                print(
                    f"\nError: Could not checkout branch {last_item['branch']}",
                    file=sys.stderr)
                print(
                    f"You may need to fetch it first: git fetch origin {last_item['branch']}",
                    file=sys.stderr)

    # pylint: disable=too-many-branches
    def remove(self, stack_name: str) -> None:
        """Remove all branches and close all MRs for a stack."""
        if not self.mapping:
            print('No stacks found (mapping file is empty)')
            return

        # Find all commits in the specified stack
        stack_items: list[dict[str, Any]] = []
        for change_id, mr_info in self.mapping.items():
            current_stack_name = extract_stack_name(change_id)
            if current_stack_name == stack_name:
                # Extract position from change_id
                parts = change_id.split('-')
                position = int(
                    parts[-1]) if parts and parts[-1].isdigit() else 0

                stack_items.append({
                    'change_id': change_id,
                    'position': position,
                    'branch': get_branch_name(change_id),
                    'mr_iid': mr_info['mr_iid']
                })

        if not stack_items:
            print(f"Error: Stack '{stack_name}' not found")
            print('\nAvailable stacks:')
            # Show available stacks
            available_stacks = set()
            for change_id in self.mapping.keys():
                sn = extract_stack_name(change_id)
                if sn:
                    available_stacks.add(sn)
            for sn in sorted(available_stacks):
                print(f"  - {sn}")
            return

        # Sort by position
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
                    # Delete local branch
                    self._run_git_command(['branch', '-D', item['branch']],
                                          check=False)
                    # Delete remote branch
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
            print(f"\n✓ Removed stack '{stack_name}'")
            print(f"  Closed {closed_count} MR(s)")
            print(f"  Deleted {deleted_count} branch(es)")
        else:
            print(
                f"\n[DRY-RUN] Would remove {len(stack_items)} items from mapping"
            )

    # pylint: disable=too-many-branches
    def show(self) -> None:
        """Show information about the current commit's stack."""
        # Get current commit SHA
        try:
            current_sha = self._run_git_command(['rev-parse', 'HEAD']).strip()
        except subprocess.CalledProcessError:
            print('Error: Could not get current commit', file=sys.stderr)
            return

        # Get current commit message
        try:
            commit_message = self._run_git_command(
                ['log', '-1', '--format=%B', current_sha])
            commit_subject = self._run_git_command(
                ['log', '-1', '--format=%s', current_sha])
        except subprocess.CalledProcessError:
            print('Error: Could not get commit message', file=sys.stderr)
            return

        # Extract Change-ID from commit message
        change_id = extract_change_id(commit_message)

        if not change_id:
            print('\n❌ Current commit has no Change-ID')
            print(f"   Commit: {current_sha[:8]}")
            print(f"   Subject: {commit_subject}")
            print(
                "\nRun 'git_stack.py push' to add a Change-ID and create an MR"
            )
            return

        # Extract stack name and position
        stack_name = extract_stack_name(change_id)
        parts = change_id.split('-')
        position = int(parts[-1]) if parts and parts[-1].isdigit() else None

        print('\n📍 Current Commit')
        print(f"   SHA: {current_sha[:8]}")
        print(f"   Subject: {commit_subject}")
        print(f"   Change-ID: {change_id}")

        if stack_name:
            print(f"\n📚 Stack: {stack_name}")
            if position is not None:
                print(f"   Position: {position}")

        # Check if there's an MR for this commit
        if change_id in self.mapping:
            mr_info = self.mapping[change_id]
            print('\n🔗 Merge Request')
            print(f"   MR: !{mr_info['mr_iid']}")
            print(f"   URL: {mr_info['mr_url']}")
            print(f"   Branch: {get_branch_name(change_id)}")
        else:
            print('\n❌ No MR found for this commit')
            print("   Run 'git_stack.py push' to create an MR")

        # Show other commits in the same stack
        if stack_name and self.mapping:
            stack_commits = []
            for cid, mr_info in self.mapping.items():
                sn = extract_stack_name(cid)
                if sn == stack_name:
                    parts = cid.split('-')
                    pos = int(
                        parts[-1]) if parts and parts[-1].isdigit() else 0
                    stack_commits.append({
                        'change_id': cid,
                        'position': pos,
                        'mr_iid': mr_info['mr_iid'],
                        'is_current': cid == change_id
                    })

            if len(stack_commits) > 1:
                stack_commits.sort(key=lambda x: x['position'])
                print(f"\n📋 Other commits in '{stack_name}' stack:")
                for sc in stack_commits:
                    if not sc['is_current']:
                        marker = '  ' if sc['position'] < (position
                                                           or 0) else '  '
                        print(f"   {marker}{sc['position']}. !{sc['mr_iid']}")

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-nested-blocks
    def status(self, base_branch: str) -> None:
        """Show status of all commits in the current stack."""
        # Get commits
        commits = self._get_commits(base_branch)

        if not commits:
            print(f"No commits found between {base_branch} and HEAD")
            return

        # Add Change-IDs if missing
        commits = self._add_change_ids_to_commits(commits)

        # Get stack name from first commit
        if not commits[0]['change_id']:
            print("No Change-IDs found. Run 'git_stack.py push' first.")
            return

        stack_name = extract_stack_name(commits[0]['change_id'])

        print(f"\n📚 Stack: {stack_name}")
        print(f"   Base: {base_branch}")
        print(f"   Commits: {len(commits)}")
        print()

        # Check status of each commit
        for i, commit in enumerate(commits, 1):
            change_id = commit['change_id']
            branch_name = get_branch_name(change_id)

            # Check if MR exists
            if change_id not in self.mapping:
                status_icon = '❌'
                status_text = 'No MR'
                detail_text = None
            else:
                # Check if local commit matches remote branch
                try:
                    # Get remote branch SHA
                    remote_sha = self._run_git_command(
                        ['rev-parse', f'origin/{branch_name}'],
                        check=False).strip()

                    if not remote_sha:
                        status_icon = '⚠️ '
                        status_text = 'Not pushed'
                        detail_text = None
                    elif remote_sha == commit['sha']:
                        status_icon = '✓'
                        status_text = 'Up-to-date'
                        detail_text = None
                    else:
                        status_icon = '⚠️ '
                        status_text = 'Out of sync'
                        # Get more details about what's different
                        try:
                            # Check if local is ahead, behind, or diverged
                            ahead_behind = self._run_git_command(
                                [
                                    'rev-list', '--left-right', '--count',
                                    f'{remote_sha}...{commit["sha"]}'
                                ],
                                check=False).strip()

                            if ahead_behind:
                                behind, ahead = ahead_behind.split()
                                if ahead != '0' and behind != '0':
                                    detail_text = (
                                        f"Local has {ahead} commit(s) ahead, "
                                        f"{behind} behind remote")
                                elif ahead != '0':
                                    detail_text = (
                                        f"Local has {ahead} commit(s) "
                                        f"not pushed to remote")
                                elif behind != '0':
                                    detail_text = (
                                        f"Remote has {behind} commit(s) "
                                        f"not in local")
                                else:
                                    detail_text = (
                                        f"Local: {commit['sha'][:8]}, "
                                        f"Remote: {remote_sha[:8]}")
                            else:
                                detail_text = (f"Local: {commit['sha'][:8]}, "
                                               f"Remote: {remote_sha[:8]}")
                        except subprocess.CalledProcessError:
                            detail_text = (f"Local: {commit['sha'][:8]}, "
                                           f"Remote: {remote_sha[:8]}")
                except subprocess.CalledProcessError:
                    status_icon = '⚠️ '
                    status_text = 'Not pushed'
                    detail_text = None

            # Print commit info
            mr_text = (f"!{self.mapping[change_id]['mr_iid']}"
                       if change_id in self.mapping else 'no MR')
            print(f"  {status_icon} {i}. {commit['subject'][:60]}")
            print(
                f"      SHA: {commit['sha'][:8]}  MR: {mr_text}  Status: {status_text}"
            )
            if detail_text:
                print(f"      {detail_text}")


def cmd_push(args):
    """Handle push subcommand."""
    stack = GitStackPush(dry_run=args.dry_run, stack_name=args.stack_name)
    stack.push(base_branch=args.base)


def cmd_clean(args):
    """Handle clean subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.clean()


def cmd_reindex(args):
    """Handle reindex subcommand."""
    stack = GitStackPush(dry_run=args.dry_run, stack_name=args.stack_name)
    stack.reindex(base_branch=args.base)


def cmd_list(_args):
    """Handle list subcommand."""
    stack = GitStackPush()
    stack.list()


def cmd_checkout(args):
    """Handle checkout subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.checkout(stack_name=args.stack_name)


def cmd_remove(args):
    """Handle remove subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.remove(stack_name=args.stack_name)


def cmd_show(_args):
    """Handle show subcommand."""
    stack = GitStackPush()
    stack.show()


def cmd_status(args):
    """Handle status subcommand."""
    stack = GitStackPush()
    stack.status(base_branch=args.base)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage stacked GitLab MRs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    # Push subcommand
    push_parser = subparsers.add_parser(
        'push',
        help='Create or update stacked MRs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s push                              # Create MRs stacked on 'main'
  %(prog)s push --base develop               # Stack on 'develop' branch
  %(prog)s push --stack-name feature         # Use 'feature' as stack name
  %(prog)s push --dry-run                    # Show what would be done
        """)
    push_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to stack on (default: origin/main)')
    push_parser.add_argument(
        '--stack-name',
        default=None,
        help='Stack name to use (default: auto-detect or prompt)'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    push_parser.add_argument('--dry-run',
                             action='store_true',
                             help='Show what would be done without executing')
    push_parser.set_defaults(func=cmd_push)

    # Clean subcommand
    clean_parser = subparsers.add_parser(
        'clean',
        help='Remove closed/merged MRs from mapping file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s clean           # Remove closed MRs from mapping
  %(prog)s clean --dry-run # Show which MRs would be removed
        """)
    clean_parser.add_argument('--dry-run',
                              action='store_true',
                              help='Show what would be done without executing')
    clean_parser.set_defaults(func=cmd_clean)

    # Reindex subcommand
    reindex_parser = subparsers.add_parser(
        'reindex',
        help='Remove all Change-Ids, close old MRs, and create new Change-Ids',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s reindex                              # Reindex stack on 'main'
  %(prog)s reindex --base develop               # Reindex stack on 'develop'
  %(prog)s reindex --stack-name feature         # Use 'feature' as stack name
  %(prog)s reindex --dry-run                    # Show what would be done
        """)
    reindex_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to stack on (default: origin/main)')
    reindex_parser.add_argument(
        '--stack-name',
        default=None,
        help='Stack name to use (default: prompt)'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    reindex_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing')
    reindex_parser.set_defaults(func=cmd_reindex)

    # List subcommand
    list_parser = subparsers.add_parser(
        'list',
        help='List all stacks with their branches and MRs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list           # List all stacks
        """)
    list_parser.set_defaults(func=cmd_list)

    # Checkout subcommand
    checkout_parser = subparsers.add_parser(
        'checkout',
        help='Checkout the latest branch from a stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s checkout myfeature         # Checkout latest branch from 'myfeature' stack
  %(prog)s checkout myfeature --dry-run  # Show what would be done
        """)
    checkout_parser.add_argument(
        'stack_name', help='Name of the stack to checkout'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    checkout_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing')
    checkout_parser.set_defaults(func=cmd_checkout)

    # Remove subcommand
    remove_parser = subparsers.add_parser(
        'remove',
        help='Remove all branches and close all MRs for a stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s remove myfeature         # Remove 'myfeature' stack
  %(prog)s remove myfeature --dry-run  # Show what would be done
        """)
    remove_parser.add_argument(
        'stack_name', help='Name of the stack to remove'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    remove_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing')
    remove_parser.set_defaults(func=cmd_remove)

    # Show subcommand
    show_parser = subparsers.add_parser(
        'show',
        help='Show information about the current commit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s show           # Show current commit's stack and MR info
        """)
    show_parser.set_defaults(func=cmd_show)

    # Status subcommand
    status_parser = subparsers.add_parser(
        'status',
        help='Show status of all commits in the current stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show status of commits on current stack
  %(prog)s status --base develop     # Show status with develop as base
        """)
    status_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to compare against (default: origin/main)')
    status_parser.set_defaults(func=cmd_status)

    # Enable argcomplete if available
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
