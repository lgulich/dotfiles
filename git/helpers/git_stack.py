#!/usr/bin/env python3
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
from pathlib import Path
from typing import Dict, List, Optional, Any

# Try to import argcomplete for shell completion
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


class StackNameCompleter:
    """Custom completer for stack names."""
    
    def __call__(self, prefix, parsed_args, **kwargs):
        """Return list of stack names for completion."""
        try:
            # Get the mapping file path
            repo_root = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
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
    match = re.search(r'Change-Id:\s+([a-f0-9]+-[a-z0-9-]+-\d+)', commit_message)
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


def load_mapping(path: Path) -> Dict[str, Any]:
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


def save_mapping(path: Path, data: Dict[str, Any]) -> None:
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


def build_mr_chain(commits: List[Dict[str, Any]], base_branch: str) -> List[Dict[str, Any]]:
    """
    Build MR chain with target branches for each commit.
    
    Args:
        commits: List of commit dicts with 'sha', 'change_id', 'subject'
        base_branch: The base branch name
        
    Returns:
        List of commits with added 'target_branch' and 'source_branch' fields
    """
    chain = []
    
    for i, commit in enumerate(commits):
        commit_copy = commit.copy()
        
        # First commit targets base branch
        if i == 0:
            commit_copy['target_branch'] = base_branch
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
    
    def __init__(self, dry_run: bool = False, mapping_path: Path | None = None, stack_name: str | None = None):
        """
        Initialize GitStackPush.
        
        Args:
            dry_run: If True, don't execute any commands
            mapping_path: Path to mapping file (defaults to ~/.config/stacked-mrs-map.json)
            stack_name: Optional stack name to use (if not provided, will be detected or prompted)
        """
        self.dry_run = dry_run
        self.stack_name_override = stack_name
        
        if mapping_path is None:
            self.mapping_path = Path.home() / '.config' / 'stacked-mrs-map.json'
        else:
            self.mapping_path = mapping_path
        
        self.mapping = load_mapping(self.mapping_path)
    
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
            check=False
        )
        
        if check and result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            print(f"Error running git command: git {' '.join(args)}", file=sys.stderr)
            print(f"Error output: {error_msg}", file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, ['git'] + args, result.stdout, result.stderr)
        
        return result.stdout.strip()
    
    def _run_glab_command(self, args: list[str], check: bool = True) -> str:
        """
        Run a glab command and return output.
        
        Args:
            args: Glab command arguments
            check: Whether to raise exception on error
            
        Returns:
            Command output as string
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would run: glab {' '.join(args)}")
            return ""
        
        try:
            result = subprocess.run(
                ['glab'] + args,
                capture_output=True,
                text=True,
                check=False
            )
        except FileNotFoundError:
            print("Error: glab CLI not found. Install from: https://gitlab.com/gitlab-org/cli", file=sys.stderr)
            sys.exit(1)
        
        if check and result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            print(f"Error running glab command: glab {' '.join(args)}", file=sys.stderr)
            print(f"Error output: {error_msg}", file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, ['glab'] + args, result.stdout, result.stderr)
        
        return result.stdout.strip()
    
    def _validate_environment(self) -> None:
        """Validate that required tools and environment are available."""
        # Check if in git repo
        try:
            self._run_git_command(['rev-parse', '--git-dir'])
        except subprocess.CalledProcessError:
            print("Error: Not in a git repository", file=sys.stderr)
            sys.exit(1)
        
        # Check if glab is installed
        try:
            subprocess.run(['glab', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: glab CLI not found. Install from: https://gitlab.com/gitlab-org/cli", file=sys.stderr)
            sys.exit(1)
    
    def _get_commits(self, base_branch: str) -> list[dict[str, any]]:
        """
        Get list of commits between base branch and HEAD.
        
        Args:
            base_branch: Base branch to compare against
            
        Returns:
            List of commit dictionaries
        """
        # Get list of commit SHAs
        try:
            commit_shas = self._run_git_command([
                'rev-list', '--reverse', f'{base_branch}..HEAD'
            ]).split('\n')
        except subprocess.CalledProcessError as e:
            print(f"Error: Unable to get commits. Is '{base_branch}' a valid branch?", file=sys.stderr)
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
    
    def _add_change_ids_to_commits(self, commits: list[dict[str, any]]) -> list[dict[str, any]]:
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
                        print(f"\nUsing stack name '{stack_name}' from existing commits")
                        break
            
            # If no stack name found, prompt for one
            if not stack_name:
                if self.dry_run:
                    stack_name = "example"
                else:
                    while True:
                        stack_name = input("\nEnter stack name (e.g., 'feature', 'bugfix-123'): ").strip()
                        if stack_name and re.match(r'^[a-z0-9-]+$', stack_name):
                            break
                        print("  Error: Stack name must contain only lowercase letters, numbers, and hyphens")
        
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
            print(f"\n[DRY-RUN] Would add Change-Ids to {len(commits_needing_ids)} commit(s) with stack name '{stack_name}'")
            position = 1
            for commit in commits:
                if commit['change_id'] is None:
                    new_id = generate_change_id(stack_name, position)
                    commit['change_id'] = new_id
                    print(f"  {commit['sha'][:8]}: {commit['subject']} -> Change-Id: {new_id}")
                else:
                    # Extract position from existing change_id
                    parts = commit['change_id'].split('-')
                    if parts and parts[-1].isdigit():
                        position = int(parts[-1])
                position += 1
            return commits
        
        # We need to rewrite commits to add Change-Ids
        print(f"\nAdding Change-Ids to {len(commits_needing_ids)} commit(s) with stack name '{stack_name}'...")
        
        # Save current branch/ref
        original_ref = self._run_git_command(['symbolic-ref', '-q', 'HEAD'], check=False)
        if not original_ref:
            # We're already in detached HEAD, get the commit
            original_ref = self._run_git_command(['rev-parse', 'HEAD'])
        
        # Get the base commit (parent of first commit)
        base_sha = self._run_git_command(['rev-parse', f'{commits[0]["sha"]}~1'])
        
        # Checkout the base
        self._run_git_command(['checkout', base_sha], check=False)
        
        # Cherry-pick each commit and amend with Change-Id
        position = 1
        for i, commit in enumerate(commits):
            if commit['change_id'] is None:
                # Generate new Change-Id with stack name and position
                new_change_id = generate_change_id(stack_name, position)
                commit['change_id'] = new_change_id
                
                # Cherry-pick the commit
                self._run_git_command(['cherry-pick', commit['sha']], check=False)
                
                # Amend with new message including Change-Id
                new_message = add_change_id_to_message(commit['message'], new_change_id)
                self._run_git_command(['commit', '--amend', '-m', new_message])
                
                # Update commit info
                new_sha = self._run_git_command(['rev-parse', 'HEAD'])
                commit['sha'] = new_sha
                commit['message'] = new_message
                
                print(f"  {commit['sha'][:8]}: {commit['subject']} -> Change-Id: {new_change_id}")
            else:
                # Commit already has Change-Id, just cherry-pick it
                self._run_git_command(['cherry-pick', commit['sha']], check=False)
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
            self._run_git_command(['reset', '--hard', commits[-1]['sha']], check=False)
        else:
            # Was in detached HEAD, just checkout the last commit
            self._run_git_command(['checkout', commits[-1]['sha']], check=False)
        
        return commits
    
    def _create_or_update_branches(self, chain: list[dict[str, any]]) -> None:
        """
        Create or update branches for each commit in the chain.
        
        Args:
            chain: List of commits with target/source branches
        """
        print("\nCreating/updating branches...")
        
        # Get current branch to check if we're on one of the branches we're updating
        try:
            current_branch = self._run_git_command(['symbolic-ref', '--short', 'HEAD'], check=False).strip()
        except subprocess.CalledProcessError:
            current_branch = None  # Detached HEAD
        
        for commit in chain:
            branch_name = commit['source_branch']
            
            if self.dry_run:
                print(f"[DRY-RUN] Would create/update branch: {branch_name} at {commit['sha'][:8]}")
                print(f"[DRY-RUN] Would push: git push -f origin {commit['sha']}:refs/heads/{branch_name}")
            else:
                # If we're currently on this branch, we can't force update it
                # Instead, we'll just push directly (the branch pointer will be updated by the push)
                if current_branch == branch_name:
                    # Just push - the remote will be updated
                    self._run_git_command(['push', '-f', 'origin', f"{commit['sha']}:refs/heads/{branch_name}"])
                else:
                    # Create/update local branch at commit
                    self._run_git_command(['branch', '-f', branch_name, commit['sha']])
                    # Push to remote (use full refspec when pushing a commit SHA)
                    self._run_git_command(['push', '-f', 'origin', f"{commit['sha']}:refs/heads/{branch_name}"])
                
                print(f"  ✓ {branch_name} at {commit['sha'][:8]}")
    
    def _create_or_update_mrs(self, chain: list[dict[str, any]]) -> None:
        """
        Create or update MRs for each commit in the chain.
        
        Args:
            chain: List of commits with target/source branches
        """
        print("\nCreating/updating MRs...")
        
        for commit in chain:
            change_id = commit['change_id']
            source_branch = commit['source_branch']
            target_branch = commit['target_branch']
            
            # Check if MR already exists for this Change-Id
            existing_mr = self.mapping.get(change_id)
            
            if existing_mr:
                # Update existing MR
                mr_iid = existing_mr['mr_iid']
                
                if self.dry_run:
                    print(f"[DRY-RUN] Would update MR !{mr_iid}")
                    print(f"           Title: {commit['subject']}")
                    print(f"           Source: {source_branch} -> Target: {target_branch}")
                else:
                    # Update MR title and description
                    self._run_glab_command([
                        'mr', 'update', str(mr_iid),
                        '--title', commit['subject'],
                        '--description', commit['message']
                    ])
                    
                    print(f"  ✓ Updated MR !{mr_iid}: {commit['subject']}")
                    print(f"    {existing_mr['mr_url']}")
            else:
                # Create new MR
                if self.dry_run:
                    print(f"[DRY-RUN] Would create new MR")
                    print(f"           Title: {commit['subject']}")
                    print(f"           Source: {source_branch} -> Target: {target_branch}")
                else:
                    output = self._run_glab_command([
                        'mr', 'create',
                        '--source-branch', source_branch,
                        '--target-branch', target_branch,
                        '--title', commit['subject'],
                        '--description', commit['message'],
                        '--yes'
                    ])
                    
                    # Parse MR URL from output
                    mr_url = None
                    mr_iid = None
                    for line in output.split('\n'):
                        if 'merge_requests' in line and 'http' in line:
                            mr_url = line.strip()
                            # Extract IID from URL
                            match = re.search(r'/merge_requests/(\d+)', mr_url)
                            if match:
                                mr_iid = int(match.group(1))
                    
                    if mr_iid and mr_url:
                        # Save to mapping
                        self.mapping[change_id] = {
                            'mr_iid': mr_iid,
                            'mr_url': mr_url,
                            'project_id': self._get_project_id()
                        }
                        save_mapping(self.mapping_path, self.mapping)
                        
                        print(f"  ✓ Created MR !{mr_iid}: {commit['subject']}")
                        print(f"    {mr_url}")
                    else:
                        print(f"  ⚠ Created MR but couldn't parse URL from output")
    
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
        return "unknown"
    
    def process(self, base_branch: str) -> dict[str, any] | None:
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
            print("\n" + "="*60)
            print("DRY-RUN: MR Chain Plan")
            print("="*60)
            for i, commit in enumerate(chain, 1):
                print(f"\n{i}. {commit['subject']}")
                print(f"   SHA: {commit['sha'][:8]}")
                print(f"   Change-Id: {commit['change_id']}")
                print(f"   Branch: {commit['source_branch']}")
                print(f"   Target: {commit['target_branch']}")
                existing = self.mapping.get(commit['change_id'])
                if existing:
                    print(f"   Action: UPDATE existing MR !{existing['mr_iid']}")
                else:
                    print(f"   Action: CREATE new MR")
            print("\n" + "="*60)
            
            return {
                'commits': commits,
                'chain': chain
            }
        
        # Create/update branches
        self._create_or_update_branches(chain)
        
        # Create/update MRs
        self._create_or_update_mrs(chain)
        
        print("\n✓ Stack processing complete!")
        return None


    def clean(self) -> None:
        """Remove entries from mapping file for closed MRs."""
        if not self.mapping:
            print("No MRs in mapping file")
            return
        
        print(f"\nChecking {len(self.mapping)} MR(s) for closed status...")
        
        closed_count = 0
        to_remove = []
        
        for change_id, mr_info in self.mapping.items():
            mr_iid = mr_info['mr_iid']
            
            try:
                # Get MR state using glab (parse text output)
                output = self._run_glab_command(['mr', 'view', str(mr_iid)])
                
                # Parse the output to find state
                state = None
                for line in output.split('\n'):
                    if 'state:' in line.lower() or 'status:' in line.lower():
                        # Extract state from line like "state: merged" or "• State: Merged"
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            state = parts[1].strip().lower()
                            break
                
                if not state:
                    # Try to detect from output text
                    output_lower = output.lower()
                    if 'merged' in output_lower:
                        state = 'merged'
                    elif 'closed' in output_lower:
                        state = 'closed'
                    elif 'open' in output_lower:
                        state = 'open'
                
                if state in ['closed', 'merged']:
                    print(f"  MR !{mr_iid} is {state}, removing from mapping")
                    to_remove.append(change_id)
                    closed_count += 1
                elif state:
                    print(f"  MR !{mr_iid} is {state}, keeping in mapping")
                else:
                    print(f"  Warning: Could not determine state for MR !{mr_iid}, keeping in mapping")
            except subprocess.CalledProcessError as e:
                print(f"  Warning: Could not check MR !{mr_iid}, keeping in mapping")
        
        # Remove closed MRs from mapping
        for change_id in to_remove:
            del self.mapping[change_id]
        
        if closed_count > 0:
            save_mapping(self.mapping_path, self.mapping)
            print(f"\n✓ Removed {closed_count} closed MR(s) from mapping")
        else:
            print(f"\n✓ No closed MRs found")
    
    def reindex(self, base_branch: str) -> None:
        """Remove all Change-Ids, close old MRs, and create new Change-Ids."""
        print("\nReindexing stack...")
        
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
                        print(f"[DRY-RUN] Would close MR !{mr_iid} for Change-Id {commit['change_id']}")
                    else:
                        try:
                            self._run_glab_command(['mr', 'close', str(mr_iid)])
                            print(f"  Closed MR !{mr_iid} for Change-Id {commit['change_id']}")
                            del self.mapping[commit['change_id']]
                            closed_count += 1
                        except subprocess.CalledProcessError:
                            print(f"  Warning: Could not close MR !{mr_iid}")
        
        if closed_count > 0 and not self.dry_run:
            save_mapping(self.mapping_path, self.mapping)
            print(f"\n✓ Closed {closed_count} MR(s)")
        
        # Remove Change-Ids from all commits
        print("\nRemoving old Change-Ids and creating new ones...")
        
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
            print("\n✓ Reindexing complete! Run 'git_stack.py push' to create new MRs")
    
    def list_stacks(self) -> None:
        """List all stacks with their branches and MRs."""
        if not self.mapping:
            print("No stacks found (mapping file is empty)")
            return
        
        # Group by stack name
        stacks = {}
        for change_id, mr_info in self.mapping.items():
            stack_name = extract_stack_name(change_id)
            if not stack_name:
                stack_name = "unknown"
            
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
            print(f"   Last MR: !{last_item['mr_iid']} ({last_item['mr_url']})")
            
            # Show all MRs in the stack
            print(f"\n   MRs in stack:")
            for item in items:
                print(f"     {item['position']}. !{item['mr_iid']} - {item['branch']}")
        
        print(f"\n✓ Found {len(stacks)} stack(s)")
    
    def checkout_stack(self, stack_name: str) -> None:
        """Checkout the latest branch from a stack."""
        if not self.mapping:
            print("No stacks found (mapping file is empty)")
            return
        
        # Find all commits in the specified stack
        stack_items = []
        for change_id, mr_info in self.mapping.items():
            current_stack_name = extract_stack_name(change_id)
            if current_stack_name == stack_name:
                # Extract position from change_id
                parts = change_id.split('-')
                position = int(parts[-1]) if parts and parts[-1].isdigit() else 0
                
                stack_items.append({
                    'change_id': change_id,
                    'position': position,
                    'branch': get_branch_name(change_id)
                })
        
        if not stack_items:
            print(f"Error: Stack '{stack_name}' not found")
            print("\nAvailable stacks:")
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
        print(f"  Branch: {last_item['branch']} (position {last_item['position']})")
        
        if self.dry_run:
            print(f"[DRY-RUN] Would run: git checkout {last_item['branch']}")
        else:
            try:
                self._run_git_command(['checkout', last_item['branch']])
                print(f"\n✓ Checked out {last_item['branch']}")
            except subprocess.CalledProcessError:
                print(f"\nError: Could not checkout branch {last_item['branch']}", file=sys.stderr)
                print(f"You may need to fetch it first: git fetch origin {last_item['branch']}", file=sys.stderr)
    
    def remove_stack(self, stack_name: str) -> None:
        """Remove all branches and close all MRs for a stack."""
        if not self.mapping:
            print("No stacks found (mapping file is empty)")
            return
        
        # Find all commits in the specified stack
        stack_items = []
        for change_id, mr_info in self.mapping.items():
            current_stack_name = extract_stack_name(change_id)
            if current_stack_name == stack_name:
                # Extract position from change_id
                parts = change_id.split('-')
                position = int(parts[-1]) if parts and parts[-1].isdigit() else 0
                
                stack_items.append({
                    'change_id': change_id,
                    'position': position,
                    'branch': get_branch_name(change_id),
                    'mr_iid': mr_info['mr_iid']
                })
        
        if not stack_items:
            print(f"Error: Stack '{stack_name}' not found")
            print("\nAvailable stacks:")
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
        
        print(f"\nRemoving stack '{stack_name}' ({len(stack_items)} commits)...")
        
        # Close MRs
        closed_count = 0
        for item in stack_items:
            if self.dry_run:
                print(f"[DRY-RUN] Would close MR !{item['mr_iid']}")
            else:
                try:
                    self._run_glab_command(['mr', 'close', str(item['mr_iid'])])
                    print(f"  Closed MR !{item['mr_iid']}")
                    closed_count += 1
                except subprocess.CalledProcessError:
                    print(f"  Warning: Could not close MR !{item['mr_iid']}")
        
        # Delete branches
        deleted_count = 0
        for item in stack_items:
            if self.dry_run:
                print(f"[DRY-RUN] Would delete branch {item['branch']}")
            else:
                try:
                    # Delete local branch
                    self._run_git_command(['branch', '-D', item['branch']], check=False)
                    # Delete remote branch
                    self._run_git_command(['push', 'origin', '--delete', item['branch']], check=False)
                    print(f"  Deleted branch {item['branch']}")
                    deleted_count += 1
                except subprocess.CalledProcessError:
                    print(f"  Warning: Could not delete branch {item['branch']}")
        
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
            print(f"\n[DRY-RUN] Would remove {len(stack_items)} items from mapping")


def cmd_push(args):
    """Handle push subcommand."""
    stack = GitStackPush(dry_run=args.dry_run, stack_name=args.stack_name)
    stack.process(base_branch=args.base)


def cmd_clean(args):
    """Handle clean subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.clean()


def cmd_reindex(args):
    """Handle reindex subcommand."""
    stack = GitStackPush(dry_run=args.dry_run, stack_name=args.stack_name)
    stack.reindex(base_branch=args.base)


def cmd_list(args):
    """Handle list subcommand."""
    stack = GitStackPush()
    stack.list_stacks()


def cmd_checkout(args):
    """Handle checkout subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.checkout_stack(stack_name=args.stack_name)


def cmd_rm(args):
    """Handle rm subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.remove_stack(stack_name=args.stack_name)




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
        """
    )
    push_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to stack on (default: main)'
    )
    push_parser.add_argument(
        '--stack-name',
        default=None,
        help='Stack name to use (default: auto-detect or prompt)'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    push_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
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
        """
    )
    clean_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
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
        """
    )
    reindex_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to stack on (default: main)'
    )
    reindex_parser.add_argument(
        '--stack-name',
        default=None,
        help='Stack name to use (default: prompt)'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    reindex_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    reindex_parser.set_defaults(func=cmd_reindex)
    
    # List subcommand
    list_parser = subparsers.add_parser(
        'list',
        help='List all stacks with their branches and MRs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list           # List all stacks
        """
    )
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
        """
    )
    checkout_parser.add_argument(
        'stack_name',
        help='Name of the stack to checkout'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    checkout_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    checkout_parser.set_defaults(func=cmd_checkout)
    
    # Remove subcommand
    rm_parser = subparsers.add_parser(
        'rm',
        help='Remove all branches and close all MRs for a stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s rm myfeature         # Remove 'myfeature' stack
  %(prog)s rm myfeature --dry-run  # Show what would be done
        """
    )
    rm_parser.add_argument(
        'stack_name',
        help='Name of the stack to remove'
    ).completer = StackNameCompleter() if ARGCOMPLETE_AVAILABLE else None
    rm_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    rm_parser.set_defaults(func=cmd_rm)
    
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

