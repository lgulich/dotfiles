#!/usr/bin/env python3
"""
Git hosting client abstraction layer.

This module provides an abstraction for interacting with git hosting services
(GitLab, GitHub, etc.) to manage merge/pull requests.
"""

import json
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path


class GitHostingClient(ABC):
    """Abstract base class for git hosting service clients."""
    
    @abstractmethod
    def create_mr(self, source_branch: str, target_branch: str, title: str, description: str) -> dict[str, any]:
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
        pass
    
    @abstractmethod
    def update_mr(self, mr_iid: int, title: str) -> None:
        """
        Update a merge/pull request title.
        
        Args:
            mr_iid: MR/PR ID
            title: New title
        """
        pass
    
    @abstractmethod
    def get_mr_state(self, mr_iid: int) -> str:
        """
        Get the state of a merge/pull request.
        
        Args:
            mr_iid: MR/PR ID
            
        Returns:
            State string: 'open', 'closed', or 'merged'
        """
        pass
    
    @abstractmethod
    def close_mr(self, mr_iid: int) -> None:
        """
        Close a merge/pull request.
        
        Args:
            mr_iid: MR/PR ID
        """
        pass
    
    @abstractmethod
    def add_mr_note(self, mr_iid: int, body: str) -> None:
        """
        Add a note/comment to merge/pull request.
        
        Args:
            mr_iid: MR/PR ID
            body: Comment body text
        """
        pass
    
    @abstractmethod
    def get_mr_notes(self, mr_iid: int) -> list[dict[str, any]]:
        """
        Get all notes/comments from merge/pull request.
        
        Args:
            mr_iid: MR/PR ID
            
        Returns:
            List of notes with 'id' and 'body' fields
        """
        pass
    
    @abstractmethod
    def delete_mr_note(self, mr_iid: int, note_id: int) -> None:
        """
        Delete a note/comment from merge/pull request.
        
        Args:
            mr_iid: MR/PR ID
            note_id: Note/comment ID
        """
        pass


class GitLabClient(GitHostingClient):
    """GitLab client using glab CLI."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize GitLab client.
        
        Args:
            dry_run: If True, print commands instead of executing
        """
        self.dry_run = dry_run
    
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
    
    def create_mr(self, source_branch: str, target_branch: str, title: str, description: str) -> dict[str, any]:
        """Create a GitLab merge request."""
        output = self._run_glab_command([
            'mr', 'create',
            '--source-branch', source_branch,
            '--target-branch', target_branch,
            '--title', title,
            '--description', description,
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
        
        if not mr_iid or not mr_url:
            raise ValueError(f"Could not parse MR IID/URL from glab output: {output}")
        
        return {
            'mr_iid': mr_iid,
            'mr_url': mr_url
        }
    
    def update_mr(self, mr_iid: int, title: str) -> None:
        """Update a GitLab merge request title."""
        self._run_glab_command([
            'mr', 'update', str(mr_iid),
            '--title', title
        ])
    
    def get_mr_state(self, mr_iid: int) -> str:
        """Get GitLab merge request state."""
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
        
        if not state:
            raise ValueError(f"Could not determine state for MR !{mr_iid}")
        
        return state
    
    def close_mr(self, mr_iid: int) -> None:
        """Close a GitLab merge request."""
        self._run_glab_command(['mr', 'close', str(mr_iid)])
    
    def add_mr_note(self, mr_iid: int, body: str) -> None:
        """Add a note/comment to GitLab merge request."""
        self._run_glab_command([
            'mr', 'note', str(mr_iid),
            '--message', body
        ])
    
    def get_mr_notes(self, mr_iid: int) -> list[dict[str, any]]:
        """Get all notes from GitLab merge request."""
        try:
            # Use GitLab API via glab to get notes
            output = self._run_glab_command([
                'api', f'projects/:id/merge_requests/{mr_iid}/notes'
            ])
            
            import json
            notes = json.loads(output)
            
            # Return simplified structure
            return [
                {'id': note['id'], 'body': note['body']}
                for note in notes
                if not note.get('system', False)  # Exclude system notes
            ]
        except Exception:
            return []
    
    def delete_mr_note(self, mr_iid: int, note_id: int) -> None:
        """Delete a note from GitLab merge request."""
        self._run_glab_command([
            'api', '-X', 'DELETE',
            f'projects/:id/merge_requests/{mr_iid}/notes/{note_id}'
        ])


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
        self.operations = []
        self.next_iid = 1
        self.next_note_id = 1
        
        # Load or initialize database
        if self.database_file.exists():
            with open(self.database_file, 'r') as f:
                data = json.load(f)
                self.mrs = data.get('mrs', {})
                self.next_iid = data.get('next_iid', 1)
                self.next_note_id = data.get('next_note_id', 1)
        else:
            self.mrs = {}
    
    def _save_database(self) -> None:
        """Save MR database to file."""
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.database_file, 'w') as f:
            json.dump({
                'mrs': self.mrs,
                'next_iid': self.next_iid,
                'next_note_id': self.next_note_id
            }, f, indent=2)
    
    def _save_operations(self) -> None:
        """Save operations log to file."""
        self.operations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.operations_file, 'w') as f:
            json.dump(self.operations, f, indent=2)
    
    def create_mr(self, source_branch: str, target_branch: str, title: str, description: str) -> dict[str, any]:
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
            'state': 'open',
            'notes': []
        }
        
        # Record operation
        self.operations.append({
            'operation': 'create_mr',
            'args': {
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description
            },
            'result': {
                'mr_iid': mr_iid,
                'mr_url': f'https://gitlab.example.com/project/merge_requests/{mr_iid}'
            }
        })
        
        self._save_database()
        self._save_operations()
        
        return {
            'mr_iid': mr_iid,
            'mr_url': f'https://gitlab.example.com/project/merge_requests/{mr_iid}'
        }
    
    def update_mr(self, mr_iid: int, title: str) -> None:
        """Update a mock merge request."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")
        
        self.mrs[mr_key]['title'] = title
        
        # Record operation
        self.operations.append({
            'operation': 'update_mr',
            'args': {
                'mr_iid': mr_iid,
                'title': title
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
            'result': self.mrs[mr_key]['state']
        })
        
        self._save_operations()
        
        return self.mrs[mr_key]['state']
    
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
        
        self.mrs[mr_key]['notes'].append({
            'id': note_id,
            'body': body
        })
        
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
    
    def get_mr_notes(self, mr_iid: int) -> list[dict[str, any]]:
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
        return self.mrs[mr_key].get('notes', [])
    
    def delete_mr_note(self, mr_iid: int, note_id: int) -> None:
        """Delete a note from mock merge request."""
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")
        
        # Ensure notes list exists
        if 'notes' not in self.mrs[mr_key]:
            self.mrs[mr_key]['notes'] = []
        
        # Filter out the note with the given ID
        self.mrs[mr_key]['notes'] = [
            note for note in self.mrs[mr_key]['notes']
            if note['id'] != note_id
        ]
        
        # Record operation
        self.operations.append({
            'operation': 'delete_mr_note',
            'args': {
                'mr_iid': mr_iid,
                'note_id': note_id
            }
        })
        
        self._save_database()
        self._save_operations()
    
    def set_mr_state(self, mr_iid: int, state: str) -> None:
        """
        Helper method for tests to manually set MR state.
        
        Args:
            mr_iid: MR ID
            state: State to set ('open', 'closed', 'merged')
        """
        mr_key = str(mr_iid)
        if mr_key not in self.mrs:
            raise ValueError(f"MR !{mr_iid} not found")
        
        self.mrs[mr_key]['state'] = state
        self._save_database()

