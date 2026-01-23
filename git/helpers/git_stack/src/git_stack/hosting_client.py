"""
Git hosting client abstraction layer.

This module provides an abstraction for interacting with git hosting services
(GitLab, GitHub, etc.) to manage merge/pull requests.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class GitHostingClient(ABC):
    """Abstract base class for git hosting service clients."""

    @abstractmethod
    def create_mr(self, source_branch: str, target_branch: str, title: str,
                  description: str) -> dict[str, Any]:
        """
        Create a merge/pull request.

        Args:
            source_branch: Source branch name
            target_branch: Target branch name
            title: MR/PR title
            description: MR/PR description

        Returns:
            Dictionary with 'mr_iid' (int) and 'mr_url' (str)
        """

    @abstractmethod
    def update_mr(self,
                  mr_iid: int,
                  title: str,
                  target_branch: str | None = None) -> None:
        """
        Update a merge/pull request.

        Args:
            mr_iid: MR/PR ID
            title: New title
            target_branch: New target branch (optional)
        """

    @abstractmethod
    def get_mr_state(self, mr_iid: int) -> str:
        """
        Get the state of a merge/pull request.

        Args:
            mr_iid: MR/PR ID

        Returns:
            State string: 'opened', 'closed', or 'merged'
        """

    @abstractmethod
    def close_mr(self, mr_iid: int) -> None:
        """
        Close a merge/pull request.

        Args:
            mr_iid: MR/PR ID
        """

    @abstractmethod
    def add_mr_note(self, mr_iid: int, body: str) -> None:
        """
        Add a note/comment to merge/pull request.

        Args:
            mr_iid: MR/PR ID
            body: Comment body text
        """

    @abstractmethod
    def get_mr_notes(self, mr_iid: int) -> list[dict[str, Any]]:
        """
        Get all notes/comments from merge/pull request.

        Args:
            mr_iid: MR/PR ID

        Returns:
            List of notes with 'id' and 'body' fields
        """

    @abstractmethod
    def update_mr_note(self, mr_iid: int, note_id: int, body: str) -> None:
        """
        Update a note/comment on merge/pull request.

        Args:
            mr_iid: MR/PR ID
            note_id: Note/comment ID
            body: New comment body text
        """

    @abstractmethod
    def set_mr_dependencies(self, mr_iid: int,
                            blocking_mr_iids: list[int]) -> None:
        """
        Set merge/pull request dependencies (blocking MRs).

        Args:
            mr_iid: MR/PR ID
            blocking_mr_iids: List of MR IDs that must be merged before this one
        """

    @abstractmethod
    def find_mrs_by_stack_name(self, stack_name: str) -> list[dict[str, Any]]:
        """
        Find all MRs belonging to a stack by stack name.

        Args:
            stack_name: The stack name to search for

        Returns:
            List of MR info dicts with 'mr_iid', 'source_branch', 'state'
        """

    @abstractmethod
    def find_mr_by_source_branch(self,
                                 source_branch: str) -> dict[str, Any] | None:
        """
        Find an open MR by its source branch name.

        Args:
            source_branch: The source branch name to search for

        Returns:
            MR info dict with 'mr_iid', 'mr_url', 'state' if found, None otherwise
        """


class GitLabClient(GitHostingClient):
    """GitLab client using glab CLI with JSON API for reliable parsing."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize GitLab client.

        Args:
            dry_run: If True, print commands instead of executing
        """
        self.dry_run = dry_run

    def _run_glab_command(self,
                          args: list[str],
                          check: bool = True,
                          retries: int = 3) -> str:
        """
        Run a glab command and return output with retry logic.

        Args:
            args: Glab command arguments
            check: Whether to raise exception on error
            retries: Number of retries for transient failures

        Returns:
            Command output as string
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would run: glab {' '.join(args)}")
            return ''

        last_error: subprocess.CalledProcessError | None = None

        for attempt in range(retries):
            try:
                result = subprocess.run(
                    ['glab'] + args,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError:
                print(
                    'Error: glab CLI not found. Install from: '
                    'https://gitlab.com/gitlab-org/cli',
                    file=sys.stderr,
                )
                sys.exit(1)

            if result.returncode == 0:
                return result.stdout.strip()

            # Check if this is a retryable error (network issues, rate limiting)
            error_output = result.stderr.lower() + result.stdout.lower()
            retryable = any(
                x in error_output for x in
                ['timeout', 'connection', 'rate limit', '503', '502', '504'])

            if retryable and attempt < retries - 1:
                import time  # pylint: disable=import-outside-toplevel

                time.sleep(2**attempt)  # Exponential backoff
                continue

            last_error = subprocess.CalledProcessError(result.returncode,
                                                       ['glab'] + args,
                                                       result.stdout,
                                                       result.stderr)

            if check:
                error_msg = (result.stderr.strip()
                             if result.stderr else result.stdout.strip())
                print(
                    f"Error running glab command: glab {' '.join(args)}",
                    file=sys.stderr,
                )
                print(f"Error output: {error_msg}", file=sys.stderr)
                raise last_error

            break

        return ''

    def _get_mr_via_api(self, mr_iid: int) -> dict[str, Any]:
        """
        Get MR details via GitLab API (JSON response).

        Args:
            mr_iid: MR ID

        Returns:
            MR data dictionary
        """
        output = self._run_glab_command(
            ['api', f"projects/:id/merge_requests/{mr_iid}"])
        return json.loads(output) if output else {}

    def create_mr(self, source_branch: str, target_branch: str, title: str,
                  description: str) -> dict[str, Any]:
        """Create a GitLab merge request."""
        output = self._run_glab_command([
            'mr',
            'create',
            '--source-branch',
            source_branch,
            '--target-branch',
            target_branch,
            '--title',
            title,
            '--description',
            description,
            '--remove-source-branch',
            '--yes',
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

        if not mr_iid or not mr_url:
            raise ValueError(
                f"Could not parse MR IID/URL from glab output: {output}")

        return {'mr_iid': mr_iid, 'mr_url': mr_url}

    def update_mr(self,
                  mr_iid: int,
                  title: str,
                  target_branch: str | None = None) -> None:
        """Update a GitLab merge request."""
        cmd = [
            'mr', 'update',
            str(mr_iid), '--title', title, '--remove-source-branch'
        ]
        if target_branch:
            cmd.extend(['--target-branch', target_branch])
        self._run_glab_command(cmd)

    def get_mr_state(self, mr_iid: int) -> str:
        """
        Get GitLab merge request state using JSON API.

        Returns:
            State string: 'opened', 'closed', or 'merged'
        """
        mr_data = self._get_mr_via_api(mr_iid)

        if not mr_data:
            raise ValueError(f"Could not get MR !{mr_iid} data")

        state = mr_data.get('state')
        if not state:
            raise ValueError(f"Could not determine state for MR !{mr_iid}")

        return str(state)

    def close_mr(self, mr_iid: int) -> None:
        """Close a GitLab merge request."""
        self._run_glab_command(['mr', 'close', str(mr_iid)])

    def add_mr_note(self, mr_iid: int, body: str) -> None:
        """Add a note/comment to GitLab merge request."""
        self._run_glab_command(['mr', 'note', str(mr_iid), '--message', body])

    def update_mr_note(self, mr_iid: int, note_id: int, body: str) -> None:
        """Update a note/comment on GitLab merge request."""
        self._run_glab_command([
            'api',
            '-X',
            'PUT',
            f"projects/:id/merge_requests/{mr_iid}/notes/{note_id}",
            '-f',
            f"body={body}",
        ])

    def get_mr_notes(self, mr_iid: int) -> list[dict[str, Any]]:
        """Get all notes from GitLab merge request using JSON API."""
        try:
            output = self._run_glab_command([
                'api',
                f"projects/:id/merge_requests/{mr_iid}/notes",
                '--paginate',
            ])

            if not output:
                return []

            notes = json.loads(output)

            # Return simplified structure, excluding system notes
            return [{
                'id': note['id'],
                'body': note['body']
            } for note in notes if not note.get('system', False)]
        except (json.JSONDecodeError, subprocess.CalledProcessError):
            return []

    def set_mr_dependencies(self, mr_iid: int,
                            blocking_mr_iids: list[int]) -> None:
        """Set GitLab merge request dependencies."""
        if not blocking_mr_iids:
            return

        # Use GitLab API to set blocking merge requests
        # Note: This feature requires GitLab Premium/Ultimate tier
        for blocking_mr_iid in blocking_mr_iids:
            try:
                self._run_glab_command([
                    'api',
                    '-X',
                    'POST',
                    f"projects/:id/merge_requests/{mr_iid}/blocks",
                    '-f',
                    f"blocking_merge_request_id={blocking_mr_iid}",
                ])
            except subprocess.CalledProcessError as e:
                # If we get a 404, the GitLab instance doesn't support
                # MR dependencies (requires Premium/Ultimate tier)
                if '404' in str(e.stderr) or '404' in str(e.stdout):
                    raise ValueError(
                        'GitLab MR dependencies feature is not available on '
                        'this instance (requires Premium/Ultimate tier)'
                    ) from e
                # Re-raise other errors
                raise

    def find_mrs_by_stack_name(self, stack_name: str) -> list[dict[str, Any]]:
        """Find all MRs belonging to a stack by searching branch names."""
        try:
            # List all open MRs and filter by branch name pattern
            output = self._run_glab_command([
                'api',
                'projects/:id/merge_requests',
                '-X',
                'GET',
                '--paginate',
                '-f',
                'state=opened',
            ])
            mrs_data: list[dict[str, Any]] = json.loads(output)

            # Filter MRs whose source branch contains the stack name
            # Branch format: user/stack-uuid@stackname@position
            result = []
            for mr in mrs_data:
                source_branch = mr.get('source_branch', '')
                if f'@{stack_name}@' in source_branch:
                    result.append({
                        'mr_iid': mr['iid'],
                        'source_branch': source_branch,
                        'target_branch': mr.get('target_branch', ''),
                        'state': mr.get('state', 'opened'),
                        'title': mr.get('title', ''),
                    })
            return result
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def find_mr_by_source_branch(self,
                                 source_branch: str) -> dict[str, Any] | None:
        """Find an open MR by its source branch name."""
        try:
            output = self._run_glab_command([
                'api',
                'projects/:id/merge_requests',
                '-X',
                'GET',
                '-f',
                'state=opened',
                '-f',
                f'source_branch={source_branch}',
            ])
            mrs_data: list[dict[str, Any]] = json.loads(output)

            if mrs_data:
                mr = mrs_data[0]
                return {
                    'mr_iid': mr['iid'],
                    'mr_url': mr.get('web_url', ''),
                    'state': mr.get('state', 'opened'),
                }
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None


class MockGitHostingClient(GitHostingClient):
    """Mock client for testing that stores operations in JSON files."""

    def __init__(self, operations_file: Path, database_file: Path):
        """
        Initialize mock client.

        Args:
            operations_file: Path to JSON file for recording operations
            database_file: Path to JSON file for storing MR state
        """
        self.operations_file = Path(operations_file)
        self.database_file = Path(database_file)
        self.operations: list[dict[str, Any]] = []
        self.next_iid = 1
        self.next_note_id = 1

        # Load or initialize database
        if self.database_file.exists():
            with open(self.database_file) as f:
                data = json.load(f)
                self.mrs: dict[str, Any] = data.get('mrs', {})
                self.next_iid = data.get('next_iid', 1)
                self.next_note_id = data.get('next_note_id', 1)
        else:
            self.mrs = {}

    def _save_database(self) -> None:
        """Save MR database to file."""
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.database_file, 'w') as f:
            json.dump(
                {
                    'mrs': self.mrs,
                    'next_iid': self.next_iid,
                    'next_note_id': self.next_note_id,
                },
                f,
                indent=2,
            )

    def _save_operations(self) -> None:
        """Save operations log to file."""
        self.operations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.operations_file, 'w') as f:
            json.dump(self.operations, f, indent=2)

    def create_mr(self, source_branch: str, target_branch: str, title: str,
                  description: str) -> dict[str, Any]:
        """Create a mock merge request."""
        mr_iid = self.next_iid
        self.next_iid += 1

        # Store MR in database
        self.mrs[str(mr_iid)] = {
            'mr_iid': mr_iid,
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': title,
            'description': description,
            'state': 'opened',
            'notes': [],
        }

        # Record operation
        self.operations.append({
            'operation': 'create_mr',
            'args': {
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description,
            },
            'result': {
                'mr_iid':
                mr_iid,
                'mr_url':
                f"https://gitlab.example.com/project/merge_requests/{mr_iid}",
            },
        })

        self._save_database()
        self._save_operations()

        return {
            'mr_iid':
            mr_iid,
            'mr_url':
            f"https://gitlab.example.com/project/merge_requests/{mr_iid}",
        }

    def update_mr(self,
                  mr_iid: int,
                  title: str,
                  target_branch: str | None = None) -> None:
        """Update a mock merge request."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        self.mrs[mr_key]['title'] = title
        if target_branch:
            self.mrs[mr_key]['target_branch'] = target_branch

        # Record operation
        self.operations.append({
            'operation': 'update_mr',
            'args': {
                'mr_iid': mr_iid,
                'title': title,
                'target_branch': target_branch
            }
        })

        self._save_database()
        self._save_operations()

    def get_mr_state(self, mr_iid: int) -> str:
        """Get mock merge request state."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        # Record operation
        self.operations.append({
            'operation': 'get_mr_state',
            'args': {
                'mr_iid': mr_iid
            },
            'result': self.mrs[mr_key]['state'],
        })

        self._save_operations()

        return str(self.mrs[mr_key]['state'])

    def close_mr(self, mr_iid: int) -> None:
        """Close a mock merge request."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        self.mrs[mr_key]['state'] = 'closed'

        # Record operation
        self.operations.append({
            'operation': 'close_mr',
            'args': {
                'mr_iid': mr_iid
            }
        })

        self._save_database()
        self._save_operations()

    def add_mr_note(self, mr_iid: int, body: str) -> None:
        """Add a note/comment to mock merge request."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        note_id = self.next_note_id
        self.next_note_id += 1

        # Ensure notes list exists
        if 'notes' not in self.mrs[mr_key]:
            self.mrs[mr_key]['notes'] = []

        self.mrs[mr_key]['notes'].append({'id': note_id, 'body': body})

        # Record operation
        self.operations.append({
            'operation': 'add_mr_note',
            'args': {
                'mr_iid': mr_iid,
                'body': body
            }
        })

        self._save_database()
        self._save_operations()

    def update_mr_note(self, mr_iid: int, note_id: int, body: str) -> None:
        """Update a note/comment on mock merge request."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        # Ensure notes list exists
        if 'notes' not in self.mrs[mr_key]:
            self.mrs[mr_key]['notes'] = []

        # Find and update the note
        note_found = False
        for note in self.mrs[mr_key]['notes']:
            if note['id'] == note_id:
                note['body'] = body
                note_found = True
                break

        if not note_found:
            raise ValueError(f"Note {note_id} not found in MR !{mr_iid}")

        # Record operation
        self.operations.append({
            'operation': 'update_mr_note',
            'args': {
                'mr_iid': mr_iid,
                'note_id': note_id,
                'body': body
            },
        })

        self._save_database()
        self._save_operations()

    def get_mr_notes(self, mr_iid: int) -> list[dict[str, Any]]:
        """Get all notes from mock merge request."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        # Record operation
        self.operations.append({
            'operation': 'get_mr_notes',
            'args': {
                'mr_iid': mr_iid
            }
        })

        self._save_operations()

        # Return notes (or empty list if not found)
        notes: list[dict[str, Any]] = self.mrs[mr_key].get('notes', [])
        return notes

    def set_mr_dependencies(self, mr_iid: int,
                            blocking_mr_iids: list[int]) -> None:
        """Set mock merge request dependencies."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        if 'blocking_mr_iids' not in self.mrs[mr_key]:
            self.mrs[mr_key]['blocking_mr_iids'] = []

        self.mrs[mr_key]['blocking_mr_iids'] = blocking_mr_iids

        # Record operation
        self.operations.append({
            'operation': 'set_mr_dependencies',
            'args': {
                'mr_iid': mr_iid,
                'blocking_mr_iids': blocking_mr_iids
            },
        })

        self._save_database()
        self._save_operations()

    def find_mrs_by_stack_name(self, stack_name: str) -> list[dict[str, Any]]:
        """Find all MRs belonging to a stack by searching branch names."""
        result = []
        for mr_key, mr_data in self.mrs.items():
            source_branch = mr_data.get('source_branch', '')
            # Branch format: user/stack-uuid@stackname@position
            if f'@{stack_name}@' in source_branch:
                result.append({
                    'mr_iid': int(mr_key),
                    'source_branch': source_branch,
                    'target_branch': mr_data.get('target_branch', ''),
                    'state': mr_data.get('state', 'opened'),
                    'title': mr_data.get('title', ''),
                })
        return result

    def find_mr_by_source_branch(self,
                                 source_branch: str) -> dict[str, Any] | None:
        """Find an open MR by its source branch name."""
        for mr_key, mr_data in self.mrs.items():
            if (mr_data.get('source_branch') == source_branch
                    and mr_data.get('state') == 'opened'):
                return {
                    'mr_iid': int(mr_key),
                    'mr_url':
                    f"https://gitlab.example.com/project/merge_requests/{mr_key}",
                    'state': mr_data.get('state', 'opened'),
                }
        return None

    def set_mr_state(self, mr_iid: int, state: str) -> None:
        """
        Helper method for tests to manually set MR state.

        Args:
            mr_iid: MR ID
            state: State to set ('opened', 'closed', 'merged')
        """
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")

        self.mrs[mr_key]['state'] = state
        self._save_database()
