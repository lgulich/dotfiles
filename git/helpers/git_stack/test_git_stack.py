#!/usr/bin/env python3
"""
Unit tests for git_stack.py

Tests the CLI behavior of git_stack using real git commands and a mock
GitHostingClient to simulate GitLab/GitHub interactions.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from io import StringIO
from unittest.mock import patch

# Add current directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from git_stack import GitStackPush, extract_change_id, extract_stack_name
from git_hosting_client import MockGitHostingClient
from git_helpers import (
    create_git_repo, create_commit, amend_commit, create_branch,
    checkout, get_commit_message, get_current_sha, get_current_branch,
    branch_exists, create_remote
)


class GitStackTestCase(unittest.TestCase):
    """Base test case for git_stack tests."""
    
    def setUp(self):
        """Set up test environment with temp directories and mock client."""
        # Create temp directory structure
        self.test_dir = Path(tempfile.mkdtemp())
        self.repo_path = self.test_dir / "repo"
        self.bare_repo_path = self.test_dir / "bare_repo"
        self.mapping_file = self.test_dir / "mapping.json"
        self.mock_operations_file = self.test_dir / "operations.json"
        self.mock_database_file = self.test_dir / "mock_mr_db.json"
        
        # Create mock client
        self.mock_client = MockGitHostingClient(
            operations_file=self.mock_operations_file,
            database_file=self.mock_database_file
        )
        
        # Create bare repo to act as origin
        self.bare_repo_path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ['git', 'init', '--bare'],
            cwd=self.bare_repo_path,
            capture_output=True,
            check=True
        )
        
        # Create working repo
        create_git_repo(self.repo_path)
        
        # Add remote origin pointing to bare repo
        create_remote(self.repo_path, 'origin', self.bare_repo_path)
        
        # Push main to origin
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )
        
        # Fetch to create origin/main
        subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )
        
        # Set environment variable for mapping file
        os.environ['GIT_STACK_MAPPING_FILE'] = str(self.mapping_file)
        
        # Store original directory
        self.original_dir = Path.cwd()
        
        # Change to repo directory
        os.chdir(self.repo_path)
    
    def tearDown(self):
        """Clean up test environment."""
        # Change back to original directory
        os.chdir(self.original_dir)
        
        # Remove temp directory
        shutil.rmtree(self.test_dir)
        
        # Clean up environment variable
        if 'GIT_STACK_MAPPING_FILE' in os.environ:
            del os.environ['GIT_STACK_MAPPING_FILE']
    
    def create_stack_instance(self, dry_run=False, stack_name=None):
        """
        Create a GitStackPush instance configured for testing.
        
        Args:
            dry_run: Whether to run in dry-run mode
            stack_name: Optional stack name
            
        Returns:
            GitStackPush instance
        """
        return GitStackPush(
            dry_run=dry_run,
            mapping_path=self.mapping_file,
            stack_name=stack_name,
            client=self.mock_client
        )
    
    def read_operations(self):
        """
        Read operations recorded by mock client.
        
        Returns:
            List of operation dicts
        """
        if not self.mock_operations_file.exists():
            return []
        
        return json.loads(self.mock_operations_file.read_text())
    
    def read_mapping(self):
        """
        Read the mapping file.
        
        Returns:
            Mapping dict
        """
        if not self.mapping_file.exists():
            return {}
        
        return json.loads(self.mapping_file.read_text())
    
    def assertChangeIdFormat(self, change_id: str, stack_name: str) -> None:
        """
        Assert that a change ID has the correct format.
        
        Args:
            change_id: Change ID to check
            stack_name: Expected stack name
        """
        self.assertIsNotNone(change_id)
        self.assertIn(stack_name, change_id)
        # Format: uuid-stackname-position
        parts = change_id.split('-')
        self.assertGreaterEqual(len(parts), 3)
        self.assertTrue(parts[-1].isdigit())
        self.assertEqual(extract_stack_name(change_id), stack_name)
    
    def get_change_id(self, repo_path: Path, ref: str = 'HEAD') -> str:
        """
        Get Change-ID from a commit.
        
        Args:
            repo_path: Path to repository
            ref: Reference to get Change-ID from (default: HEAD)
            
        Returns:
            Change-ID string
        """
        msg = get_commit_message(repo_path, ref)
        return extract_change_id(msg)
    
    def check_operations(self, operations: list[dict], expected_operations: list[dict], 
                        order_matters: bool = False) -> None:
        """
        Check that operations match expected operations.
        Compares operation type and args, ignoring result field.
        String values in expected args are treated as regex patterns.
        
        Args:
            operations: List of actual operations
            expected_operations: List of expected operations
            order_matters: If True, operations must match in order. If False, 
                         operations can match in any order (for parallel execution)
        """
        # Check number of operations
        self.assertEqual(len(operations), len(expected_operations),
                        f"Expected {len(expected_operations)} operations, got {len(operations)}")
        
        if order_matters:
            # Sequential matching - operations must be in order
            for i, (actual, expected) in enumerate(zip(operations, expected_operations)):
                self._match_operation(actual, expected, i)
        else:
            # Parallel matching - operations can be in any order
            # Create a list to track which actual operations have been matched
            matched = [False] * len(operations)
            
            for exp_idx, expected in enumerate(expected_operations):
                # Try to find a matching actual operation that hasn't been matched yet
                found_match = False
                for act_idx, actual in enumerate(operations):
                    if matched[act_idx]:
                        continue
                    
                    # Try to match this pair
                    try:
                        self._match_operation(actual, expected, act_idx, raise_on_mismatch=False)
                        matched[act_idx] = True
                        found_match = True
                        break
                    except AssertionError:
                        continue
                
                if not found_match:
                    self.fail(f"Could not find match for expected operation {exp_idx}: "
                            f"{expected['operation']} with args {expected['args']}")
    
    def _match_operation(self, actual: dict, expected: dict, index: int, 
                        raise_on_mismatch: bool = True) -> None:
        """Helper to match a single operation against expected."""
        # Check operation type
        if actual['operation'] != expected['operation']:
            if raise_on_mismatch:
                self.assertEqual(actual['operation'], expected['operation'],
                               f"Operation {index}: expected '{expected['operation']}', got '{actual['operation']}'")
            else:
                raise AssertionError("Operation type mismatch")
        
        # Check args (ignore result field)
        # For each arg, if expected value is a string, treat it as regex pattern
        if set(actual['args'].keys()) != set(expected['args'].keys()):
            if raise_on_mismatch:
                self.assertEqual(set(actual['args'].keys()), set(expected['args'].keys()),
                               f"Operation {index}: arg keys don't match")
            else:
                raise AssertionError("Arg keys mismatch")
        
        for key, expected_value in expected['args'].items():
            actual_value = actual['args'][key]
            
            if isinstance(expected_value, str):
                # Treat as regex pattern (use DOTALL flag so . matches newlines)
                if not re.fullmatch(expected_value, str(actual_value), re.DOTALL):
                    if raise_on_mismatch:
                        self.assertIsNotNone(re.fullmatch(expected_value, str(actual_value), re.DOTALL),
                                           f"Operation {index}: arg '{key}' value '{actual_value}' does not match pattern '{expected_value}'")
                    else:
                        raise AssertionError(f"Arg value mismatch for '{key}'")
            else:
                # Direct comparison for non-string values
                if actual_value != expected_value:
                    if raise_on_mismatch:
                        self.assertEqual(actual_value, expected_value,
                                       f"Operation {index}: arg '{key}' doesn't match")
                    else:
                        raise AssertionError(f"Arg value mismatch for '{key}'")


class TestPushBasicStack(GitStackTestCase):
    """Test basic push functionality."""
    
    def test_push_basic_stack(self):
        """
        Test creating a basic stack with 3 commits.
        
        Steps:
        1. Create 3 commits on a feature branch
        2. Run git_stack.py push --stack-name test-feature
        3. Verify 3 MRs created with correct chain structure
        4. Verify branches created
        5. Verify mapping file contains 3 entries
        """
        # Create feature branch
        create_branch(self.repo_path, 'feature', 'origin/main')
        
        # Create 3 commits
        sha1 = create_commit(self.repo_path, 'file1.txt', 'First commit')
        sha2 = create_commit(self.repo_path, 'file2.txt', 'Second commit')
        sha3 = create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        # Run push
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Read operations
        operations = self.read_operations()
        
        expected_operations = [
            {
                'operation': 'create_mr',
                'args': {
                    'source_branch': '.*',
                    'target_branch': '.*',
                    'title': 'First commit',
                    'description': 'First commit.*',
                },
            },
            {
                'operation': 'create_mr',
                'args': {
                    'source_branch': '.*',
                    'target_branch': '.*',
                    'title': 'Second commit',
                    'description': 'Second commit.*',
                },
            },
            {
                'operation': 'create_mr',
                'args': {
                    'source_branch': '.*',
                    'target_branch': '.*',
                    'title': 'Third commit',
                    'description': 'Third commit.*',
                },
            },
            # Stack link updates - get notes, add notes for each MR
            {'operation': 'get_mr_notes', 'args': {'mr_iid': 1}},
            {'operation': 'add_mr_note', 'args': {'mr_iid': 1, 'body': '.*git-stack-chain.*'}},
            {'operation': 'get_mr_notes', 'args': {'mr_iid': 2}},
            {'operation': 'add_mr_note', 'args': {'mr_iid': 2, 'body': '.*git-stack-chain.*'}},
            {'operation': 'get_mr_notes', 'args': {'mr_iid': 3}},
            {'operation': 'add_mr_note', 'args': {'mr_iid': 3, 'body': '.*git-stack-chain.*'}},
        ]
        
        self.check_operations(operations, expected_operations)
        
        # Verify mapping file
        mapping = self.read_mapping()
        self.assertEqual(len(mapping), 3)
        
        # Verify Change-IDs in commits and mapping
        change_id1 = self.get_change_id(self.repo_path, 'HEAD~2')
        self.assertChangeIdFormat(change_id1, 'test-feature')
        self.assertIn(change_id1, mapping)
        
        change_id2 = self.get_change_id(self.repo_path, 'HEAD~1')
        self.assertChangeIdFormat(change_id2, 'test-feature')
        self.assertIn(change_id2, mapping)
        
        change_id3 = self.get_change_id(self.repo_path, 'HEAD')
        self.assertChangeIdFormat(change_id3, 'test-feature')
        self.assertIn(change_id3, mapping)
        

class TestPushWithAmend(GitStackTestCase):
    """Test push with amended commits."""
    
    def test_push_with_amend(self):
        """
        Test amending a commit and re-pushing.
        
        Steps:
        1. Create 3 commits and push
        2. Amend middle commit
        3. Push again
        4. Verify same MRs updated (not recreated)
        5. Verify Change-IDs preserved
        """
        # Create feature branch and commits
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        # First push
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Get Change-IDs before amend
        change_id1_before = self.get_change_id(self.repo_path, 'HEAD~2')
        change_id2_before = self.get_change_id(self.repo_path, 'HEAD~1')
        change_id3_before = self.get_change_id(self.repo_path, 'HEAD')
        
        # Get MR IIDs from first push
        mapping_before = self.read_mapping()
        mr_iid1 = mapping_before[change_id1_before]['mr_iid']
        mr_iid2 = mapping_before[change_id2_before]['mr_iid']
        mr_iid3 = mapping_before[change_id3_before]['mr_iid']
        
        # Clear operations log
        self.mock_operations_file.unlink()
        
        # Recreate mock client to clear in-memory operations
        self.mock_client = MockGitHostingClient(
            operations_file=self.mock_operations_file,
            database_file=self.mock_database_file
        )
        
        # Amend middle commit (commit_back=1 means HEAD~1)
        amend_commit(self.repo_path, 'file2_amended.txt', commit_back=1, content='amended content')
        
        # Second push (should update, not create new) with new client
        stack2 = self.create_stack_instance(stack_name='test-feature')
        stack2.push(base_branch='main')
        
        # Get Change-IDs after amend
        change_id1_after = self.get_change_id(self.repo_path, 'HEAD~2')
        change_id2_after = self.get_change_id(self.repo_path, 'HEAD~1')
        change_id3_after = self.get_change_id(self.repo_path, 'HEAD')
        
        # Change-IDs should be preserved
        self.assertEqual(change_id1_before, change_id1_after)
        self.assertEqual(change_id2_before, change_id2_after)
        self.assertEqual(change_id3_before, change_id3_after)
        
        # Read operations from second push
        operations = self.read_operations()
        
        # Verify update operations
        expected_operations = [
            {
                'operation': 'update_mr',
                'args': {
                    'mr_iid': mr_iid1,
                    'title': 'First commit',
                },
            },
            {
                'operation': 'update_mr',
                'args': {
                    'mr_iid': mr_iid2,
                    'title': 'Second commit',
                },
            },
            {
                'operation': 'update_mr',
                'args': {
                    'mr_iid': mr_iid3,
                    'title': 'Third commit',
                },
            },
            # Stack link updates - get notes and update existing ones
            {'operation': 'get_mr_notes', 'args': {'mr_iid': mr_iid1}},
            {'operation': 'update_mr_note', 'args': {'mr_iid': mr_iid1, 'note_id': '.*', 'body': '.*git-stack-chain.*'}},
            {'operation': 'get_mr_notes', 'args': {'mr_iid': mr_iid2}},
            {'operation': 'update_mr_note', 'args': {'mr_iid': mr_iid2, 'note_id': '.*', 'body': '.*git-stack-chain.*'}},
            {'operation': 'get_mr_notes', 'args': {'mr_iid': mr_iid3}},
            {'operation': 'update_mr_note', 'args': {'mr_iid': mr_iid3, 'note_id': '.*', 'body': '.*git-stack-chain.*'}},
        ]
        
        self.check_operations(operations, expected_operations)
        
        # Verify mapping still has 3 entries with same Change-IDs
        mapping_after = self.read_mapping()
        self.assertEqual(len(mapping_after), 3)
        self.assertIn(change_id1_after, mapping_after)
        self.assertIn(change_id2_after, mapping_after)
        self.assertIn(change_id3_after, mapping_after)


class TestPushAddCommit(GitStackTestCase):
    """Test adding commits to existing stack."""
    
    def test_push_add_commit_to_stack(self):
        """
        Test adding a commit to an existing stack.
        
        Steps:
        1. Create 2 commits and push
        2. Add 1 more commit
        3. Push again
        4. Verify new MR created for 3rd commit
        5. Verify 3rd MR targets 2nd commit's branch
        """
        # Create feature branch and 2 commits
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        
        # First push
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Get Change-IDs
        change_id1 = self.get_change_id(self.repo_path, 'HEAD~1')
        change_id2 = self.get_change_id(self.repo_path, 'HEAD')
        
        # Get MR IIDs and branch of second commit
        mapping = self.read_mapping()
        mr_iid1 = mapping[change_id1]['mr_iid']
        mr_iid2 = mapping[change_id2]['mr_iid']
        second_commit_branch = f"lgulich/stack-{change_id2}"
        
        # Clear operations log
        self.mock_operations_file.unlink()
        
        # Recreate mock client to clear in-memory operations
        self.mock_client = MockGitHostingClient(
            operations_file=self.mock_operations_file,
            database_file=self.mock_database_file
        )
        
        # Add third commit
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        # Second push with new client
        stack2 = self.create_stack_instance(stack_name='test-feature')
        stack2.push(base_branch='main')
        
        # Read operations
        operations = self.read_operations()
        
        # Verify operations: 2 updates and 1 create, plus stack link updates
        expected_operations = [
            {
                'operation': 'update_mr',
                'args': {
                    'mr_iid': mr_iid1,
                    'title': 'First commit',
                },
            },
            {
                'operation': 'update_mr',
                'args': {
                    'mr_iid': mr_iid2,
                    'title': 'Second commit',
                },
            },
            {
                'operation': 'create_mr',
                'args': {
                    'source_branch': '.*',
                    'target_branch': second_commit_branch,
                    'title': 'Third commit',
                    'description': 'Third commit.*',
                },
            },
            # Stack link updates for all 3 MRs
            # First 2 MRs have existing notes from first push - update them
            {'operation': 'get_mr_notes', 'args': {'mr_iid': mr_iid1}},
            {'operation': 'update_mr_note', 'args': {'mr_iid': mr_iid1, 'note_id': '.*', 'body': '.*git-stack-chain.*'}},
            {'operation': 'get_mr_notes', 'args': {'mr_iid': mr_iid2}},
            {'operation': 'update_mr_note', 'args': {'mr_iid': mr_iid2, 'note_id': '.*', 'body': '.*git-stack-chain.*'}},
            # Third MR is new, no existing notes - add new one
            {'operation': 'get_mr_notes', 'args': {'mr_iid': '.*'}},
            {'operation': 'add_mr_note', 'args': {'mr_iid': '.*', 'body': '.*git-stack-chain.*'}},
        ]
        
        self.check_operations(operations, expected_operations)
        
        # Verify Change-IDs in commits and mapping
        change_id1_after = self.get_change_id(self.repo_path, 'HEAD~2')
        self.assertEqual(change_id1, change_id1_after)
        self.assertIn(change_id1_after, mapping)
        
        change_id2_after = self.get_change_id(self.repo_path, 'HEAD~1')
        self.assertEqual(change_id2, change_id2_after)
        self.assertIn(change_id2_after, mapping)
        
        change_id3 = self.get_change_id(self.repo_path, 'HEAD')
        self.assertChangeIdFormat(change_id3, 'test-feature')
        
        # Mapping should now have 3 entries
        mapping_after = self.read_mapping()
        self.assertEqual(len(mapping_after), 3)
        self.assertIn(change_id3, mapping_after)


class TestClean(GitStackTestCase):
    """Test clean functionality."""
    
    def test_clean_removes_merged_mrs(self):
        """
        Test that clean removes merged MRs from mapping.
        
        Steps:
        1. Create stack with 3 MRs
        2. Mark 2 MRs as merged
        3. Run clean
        4. Verify mapping has only 1 entry
        """
        # Create and push stack
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Get mapping
        mapping = self.read_mapping()
        self.assertEqual(len(mapping), 3)
        
        # Get MR IIDs
        mr_iids = [info['mr_iid'] for info in mapping.values()]
        
        # Mark first two as merged
        self.mock_client.set_mr_state(mr_iids[0], 'merged')
        self.mock_client.set_mr_state(mr_iids[1], 'merged')
        
        # Run clean
        stack2 = self.create_stack_instance()
        stack2.clean()
        
        # Check mapping - should have only 1 entry
        mapping_after = self.read_mapping()
        self.assertEqual(len(mapping_after), 1)
        
        # The remaining MR should be the third one
        remaining_iids = [info['mr_iid'] for info in mapping_after.values()]
        self.assertEqual(remaining_iids, [mr_iids[2]])
    
    def test_clean_keeps_open_mrs(self):
        """
        Test that clean keeps open MRs.
        
        Steps:
        1. Create stack with 3 MRs (all open)
        2. Run clean
        3. Verify all 3 MRs still in mapping
        """
        # Create and push stack
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Get mapping
        mapping_before = self.read_mapping()
        self.assertEqual(len(mapping_before), 3)
        
        # Run clean (all MRs are open by default)
        stack2 = self.create_stack_instance()
        stack2.clean()
        
        # Check mapping - should still have 3 entries
        mapping_after = self.read_mapping()
        self.assertEqual(len(mapping_after), 3)
        
        # Same entries should be present
        self.assertEqual(set(mapping_before.keys()), set(mapping_after.keys()))


class TestReindex(GitStackTestCase):
    """Test reindex functionality."""
    
    def test_reindex_creates_new_ids(self):
        """
        Test reindexing creates new Change-IDs.
        
        Steps:
        1. Create stack with 3 commits
        2. Run reindex with new stack name
        3. Verify old MRs closed
        4. Verify commits have new Change-IDs with new prefix
        5. Verify old mapping entries removed
        """
        # Create and push stack
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        stack = self.create_stack_instance(stack_name='old-feature')
        stack.push(base_branch='main')
        
        # Get old Change-IDs
        old_change_id1 = self.get_change_id(self.repo_path, 'HEAD~2')
        old_change_id2 = self.get_change_id(self.repo_path, 'HEAD~1')
        old_change_id3 = self.get_change_id(self.repo_path, 'HEAD')
        
        # Get MR IIDs
        mapping_before = self.read_mapping()
        old_mr_iids = {info['mr_iid'] for info in mapping_before.values()}
        mr_iid1 = mapping_before[old_change_id1]['mr_iid']
        mr_iid2 = mapping_before[old_change_id2]['mr_iid']
        mr_iid3 = mapping_before[old_change_id3]['mr_iid']
        
        # Clear operations
        self.mock_operations_file.unlink()
        
        # Recreate mock client to clear in-memory operations
        self.mock_client = MockGitHostingClient(
            operations_file=self.mock_operations_file,
            database_file=self.mock_database_file
        )
        
        # Run reindex with new client
        stack2 = self.create_stack_instance(stack_name='new-feature')
        stack2.reindex(base_branch='main')
        
        # Check operations - old MRs should be closed
        operations = self.read_operations()
        expected_operations = [
            {'operation': 'close_mr', 'args': {'mr_iid': mr_iid1}},
            {'operation': 'close_mr', 'args': {'mr_iid': mr_iid2}},
            {'operation': 'close_mr', 'args': {'mr_iid': mr_iid3}},
        ]
        
        self.check_operations(operations, expected_operations)
        
        # Get new Change-IDs
        new_change_id1 = self.get_change_id(self.repo_path, 'HEAD~2')
        new_change_id2 = self.get_change_id(self.repo_path, 'HEAD~1')
        new_change_id3 = self.get_change_id(self.repo_path, 'HEAD')
        
        # Change-IDs should be different
        self.assertNotEqual(old_change_id1, new_change_id1)
        self.assertNotEqual(old_change_id2, new_change_id2)
        self.assertNotEqual(old_change_id3, new_change_id3)
        
        # New Change-IDs should have new stack name
        self.assertChangeIdFormat(new_change_id1, 'new-feature')
        self.assertChangeIdFormat(new_change_id2, 'new-feature')
        self.assertChangeIdFormat(new_change_id3, 'new-feature')
        
        # Old Change-IDs should not be in mapping
        mapping_after = self.read_mapping()
        self.assertNotIn(old_change_id1, mapping_after)
        self.assertNotIn(old_change_id2, mapping_after)
        self.assertNotIn(old_change_id3, mapping_after)


class TestList(GitStackTestCase):
    """Test list functionality."""
    
    def test_list_shows_all_stacks(self):
        """
        Test that list shows all stacks.
        
        Steps:
        1. Create 2 different stacks
        2. Run list
        3. Verify output shows both stacks
        """
        # Create first stack
        create_branch(self.repo_path, 'feature1', 'origin/main')
        create_commit(self.repo_path, 'f1_file1.txt', 'Feature 1 - commit 1')
        create_commit(self.repo_path, 'f1_file2.txt', 'Feature 1 - commit 2')
        
        stack1 = self.create_stack_instance(stack_name='feature-one')
        stack1.push(base_branch='main')
        
        # Create second stack
        checkout(self.repo_path, 'main')
        create_branch(self.repo_path, 'feature2', 'origin/main')
        create_commit(self.repo_path, 'f2_file1.txt', 'Feature 2 - commit 1')
        create_commit(self.repo_path, 'f2_file2.txt', 'Feature 2 - commit 2')
        create_commit(self.repo_path, 'f2_file3.txt', 'Feature 2 - commit 3')
        
        stack2 = self.create_stack_instance(stack_name='feature-two')
        stack2.push(base_branch='main')
        
        # Run list and capture output
        stack_list = self.create_stack_instance()
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            stack_list.list()
        
        output = captured_output.getvalue()
        
        # Verify both stack names appear
        self.assertIn('feature-one', output)
        self.assertIn('feature-two', output)
        
        # Verify commit counts
        self.assertIn('2', output)  # feature-one has 2 commits
        self.assertIn('3', output)  # feature-two has 3 commits


class TestCheckout(GitStackTestCase):
    """Test checkout functionality."""
    
    def test_checkout_switches_to_latest_branch(self):
        """
        Test checkout switches to latest branch in stack.
        
        Steps:
        1. Create stack with 3 commits
        2. Checkout different branch
        3. Run checkout command
        4. Verify current branch is 3rd commit's branch
        """
        # Create stack
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Get Change-ID of third commit
        change_id3 = self.get_change_id(self.repo_path, 'HEAD')
        expected_branch = f"lgulich/stack-{change_id3}"
        
        # Checkout main
        checkout(self.repo_path, 'main')
        self.assertEqual(get_current_branch(self.repo_path), 'main')
        
        # Run checkout
        stack2 = self.create_stack_instance()
        stack2.checkout('test-feature')
        
        # Verify we're on the third commit's branch
        current_branch = get_current_branch(self.repo_path)
        self.assertEqual(current_branch, expected_branch)


class TestRemove(GitStackTestCase):
    """Test remove functionality."""
    
    def test_rm_removes_entire_stack(self):
        """
        Test removing an entire stack.
        
        Steps:
        1. Create stack with 3 MRs
        2. Run rm command
        3. Verify all MRs closed
        4. Verify all branches deleted
        5. Verify mapping empty
        """
        # Create stack
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Get Change-IDs and info before removal
        change_id1 = self.get_change_id(self.repo_path, 'HEAD~2')
        change_id2 = self.get_change_id(self.repo_path, 'HEAD~1')
        change_id3 = self.get_change_id(self.repo_path, 'HEAD')
        
        mapping_before = self.read_mapping()
        mr_iid1 = mapping_before[change_id1]['mr_iid']
        mr_iid2 = mapping_before[change_id2]['mr_iid']
        mr_iid3 = mapping_before[change_id3]['mr_iid']
        
        # Get branch names
        branch1 = f"lgulich/stack-{change_id1}"
        branch2 = f"lgulich/stack-{change_id2}"
        branch3 = f"lgulich/stack-{change_id3}"
        
        # Checkout main so we're not on a branch being deleted
        checkout(self.repo_path, 'main')
        
        # Clear operations
        self.mock_operations_file.unlink()
        
        # Recreate mock client to clear in-memory operations
        self.mock_client = MockGitHostingClient(
            operations_file=self.mock_operations_file,
            database_file=self.mock_database_file
        )
        
        # Run remove with new client
        stack2 = self.create_stack_instance()
        stack2.remove('test-feature')
        
        # Check operations - all MRs should be closed
        operations = self.read_operations()
        expected_operations = [
            {'operation': 'close_mr', 'args': {'mr_iid': mr_iid1}},
            {'operation': 'close_mr', 'args': {'mr_iid': mr_iid2}},
            {'operation': 'close_mr', 'args': {'mr_iid': mr_iid3}},
        ]
        
        self.check_operations(operations, expected_operations)
        
        # Check mapping - should be empty
        mapping_after = self.read_mapping()
        self.assertEqual(len(mapping_after), 0)
        
        # Check branches - should be deleted locally
        self.assertFalse(branch_exists(self.repo_path, branch1))
        self.assertFalse(branch_exists(self.repo_path, branch2))
        self.assertFalse(branch_exists(self.repo_path, branch3))


class TestShow(GitStackTestCase):
    """Test show functionality."""
    
    def test_show_displays_current_commit_info(self):
        """
        Test show displays current commit information.
        
        Steps:
        1. Create stack with 3 commits
        2. Checkout 2nd commit's branch
        3. Run show
        4. Verify output shows Change-ID, stack name, position, MR info
        """
        # Create stack
        create_branch(self.repo_path, 'feature', 'origin/main')
        create_commit(self.repo_path, 'file1.txt', 'First commit')
        create_commit(self.repo_path, 'file2.txt', 'Second commit')
        create_commit(self.repo_path, 'file3.txt', 'Third commit')
        
        stack = self.create_stack_instance(stack_name='test-feature')
        stack.push(base_branch='main')
        
        # Get info about second commit
        change_id2 = self.get_change_id(self.repo_path, 'HEAD~1')
        branch2 = f"lgulich/stack-{change_id2}"
        
        mapping = self.read_mapping()
        mr_iid2 = mapping[change_id2]['mr_iid']
        
        # Checkout second commit's branch
        checkout(self.repo_path, branch2)
        
        # Run show and capture output
        stack2 = self.create_stack_instance()
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            stack2.show()
        
        output = captured_output.getvalue()
        
        # Verify output contains expected information
        self.assertIn(change_id2, output)
        self.assertIn('test-feature', output)
        self.assertIn('Second commit', output)
        self.assertIn(str(mr_iid2), output)
        self.assertIn('Position', output)


if __name__ == '__main__':
    unittest.main()

