"""Tests for git-stack functionality."""
# pylint: disable=too-few-public-methods, too-many-locals

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

from git_stack.change_id import (
    CHANGE_ID_DELIMITER,
    extract_change_id,
    extract_position,
    extract_stack_name,
    generate_change_id,
    get_branch_name,
    validate_stack_name,
)

from .conftest import (
    GitStackTestFixture,
    branch_exists,
    checkout,
    create_branch,
    create_commit,
    get_commit_message,
    get_current_branch,
    run_git,
)


class TestChangeId:
    """Tests for Change-ID functions."""

    def test_generate_change_id(self) -> None:
        """Test Change-ID generation."""
        change_id = generate_change_id('my-feature', 1)
        assert CHANGE_ID_DELIMITER in change_id
        assert 'my-feature' in change_id
        assert change_id.endswith(f"{CHANGE_ID_DELIMITER}1")

    def test_extract_change_id_new_format(self) -> None:
        """Test extracting Change-ID in new format."""
        message = 'Fix bug\n\nChange-Id: abc12345@my-feature@3'
        change_id = extract_change_id(message)
        assert change_id == 'abc12345@my-feature@3'

    def test_extract_change_id_old_format(self) -> None:
        """Test extracting Change-ID in old format (backward compat)."""
        message = 'Fix bug\n\nChange-Id: abc12345-my-feature-3'
        change_id = extract_change_id(message)
        assert change_id == 'abc12345-my-feature-3'

    def test_extract_stack_name_new_format(self) -> None:
        """Test extracting stack name from new format."""
        assert extract_stack_name('abc12345@my-feature@3') == 'my-feature'

    def test_extract_stack_name_old_format(self) -> None:
        """Test extracting stack name from old format."""
        assert extract_stack_name('abc12345-my-feature-3') == 'my-feature'

    def test_extract_stack_name_with_hyphens(self) -> None:
        """Test extracting stack name with hyphens in name."""
        # New format handles this correctly
        assert extract_stack_name(
            'abc12345@my-cool-feature@3') == 'my-cool-feature'

    def test_extract_position(self) -> None:
        """Test extracting position from Change-ID."""
        assert extract_position('abc12345@my-feature@3') == 3
        assert extract_position('abc12345-my-feature-3') == 3
        assert extract_position('abc12345@my-feature@1') == 1

    def test_validate_stack_name(self) -> None:
        """Test stack name validation."""
        assert validate_stack_name('feature') is True
        assert validate_stack_name('my-feature') is True
        assert validate_stack_name('fix-123') is True
        assert validate_stack_name('') is False
        assert validate_stack_name('-invalid') is False
        assert validate_stack_name('invalid-') is False
        assert validate_stack_name('UPPERCASE') is False
        assert validate_stack_name('with@symbol') is False


class TestPushBasicStack:
    """Test basic push functionality."""

    def test_push_basic_stack(self,
                              git_stack_fixture: GitStackTestFixture) -> None:
        """Test creating a basic stack with 3 commits."""
        # Create feature branch
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')

        # Create 3 commits
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')
        create_commit(git_stack_fixture.repo_path, 'file3.txt', 'Third commit')

        # Run push
        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        # Read operations
        operations = git_stack_fixture.read_operations()

        # Should have 3 create_mr operations
        create_ops = [
            op for op in operations if op['operation'] == 'create_mr'
        ]
        assert len(create_ops) == 3

        # Verify mapping file
        mapping = git_stack_fixture.read_mapping()
        assert len(mapping) == 3

        # Verify Change-IDs in commits
        msg1 = get_commit_message(git_stack_fixture.repo_path, 'HEAD~2')
        msg2 = get_commit_message(git_stack_fixture.repo_path, 'HEAD~1')
        msg3 = get_commit_message(git_stack_fixture.repo_path, 'HEAD')

        cid1 = extract_change_id(msg1)
        cid2 = extract_change_id(msg2)
        cid3 = extract_change_id(msg3)

        assert cid1 is not None
        assert cid2 is not None
        assert cid3 is not None
        assert extract_stack_name(cid1) == 'test-feature'
        assert extract_stack_name(cid2) == 'test-feature'
        assert extract_stack_name(cid3) == 'test-feature'


class TestPushWithExistingChangeIds:
    """Test push with pre-existing Change-IDs."""

    def test_push_preserves_change_ids(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test that existing Change-IDs are preserved on re-push."""
        # Create and push initial stack
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        # Get Change-IDs before second push
        cid1_before = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD~1'))
        cid2_before = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD'))

        # Reset mock client
        git_stack_fixture.reset_mock_client()

        # Push again
        stack2 = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack2.push(base_branch='main')

        # Get Change-IDs after second push
        cid1_after = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD~1'))
        cid2_after = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD'))

        # Change-IDs should be preserved
        assert cid1_before == cid1_after
        assert cid2_before == cid2_after

        # Should have update operations, not create
        operations = git_stack_fixture.read_operations()
        update_ops = [
            op for op in operations if op['operation'] == 'update_mr'
        ]
        assert len(update_ops) == 2


class TestPushAddCommit:
    """Test adding commits to existing stack."""

    def test_push_add_commit(self,
                             git_stack_fixture: GitStackTestFixture) -> None:
        """Test adding a commit to an existing stack."""
        # Create initial stack
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        mapping_before = git_stack_fixture.read_mapping()
        assert len(mapping_before) == 2

        git_stack_fixture.reset_mock_client()

        # Add third commit
        create_commit(git_stack_fixture.repo_path, 'file3.txt', 'Third commit')

        # Push again
        stack2 = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack2.push(base_branch='main')

        # Should have 2 update and 1 create
        operations = git_stack_fixture.read_operations()
        update_ops = [
            op for op in operations if op['operation'] == 'update_mr'
        ]
        create_ops = [
            op for op in operations if op['operation'] == 'create_mr'
        ]
        assert len(update_ops) == 2
        assert len(create_ops) == 1

        # Mapping should have 3 entries
        mapping_after = git_stack_fixture.read_mapping()
        assert len(mapping_after) == 3


class TestPushRemoveCommit:
    """Test removing commits from a stack."""

    def test_target_branch_updated_on_commit_removal(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test that target branch is updated when a commit is removed."""
        # Create stack with 2 commits
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        mapping_before = git_stack_fixture.read_mapping()
        assert len(mapping_before) == 2

        # Get the second commit's MR and its original target
        cid2 = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD'))
        assert cid2 is not None
        mr2_iid = mapping_before[cid2]['mr_iid']

        # Check that MR2 originally targeted MR1's branch (not main)
        create_ops = git_stack_fixture.read_operations()
        mr2_create = [
            op for op in create_ops if op['operation'] == 'create_mr'
            and op['args'].get('source_branch') == get_branch_name(cid2)
        ]
        assert len(mr2_create) == 1
        original_target = mr2_create[0]['args']['target_branch']
        assert original_target != 'main'  # Should target first commit's branch

        git_stack_fixture.reset_mock_client()

        # Remove first commit via interactive rebase simulation
        # (keep only the second commit, rebase onto main)
        second_commit_sha = run_git(git_stack_fixture.repo_path,
                                    ['rev-parse', 'HEAD'])
        run_git(git_stack_fixture.repo_path,
                ['reset', '--hard', 'origin/main'])
        run_git(git_stack_fixture.repo_path,
                ['cherry-pick', second_commit_sha])

        # Remove old mapping entry for first commit (simulating what user would do)
        mapping_after_remove = {cid2: mapping_before[cid2]}
        git_stack_fixture.mapping_file.write_text(
            json.dumps(mapping_after_remove, indent=2))

        # Push again
        stack2 = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack2.push(base_branch='main')

        # Check that update_mr was called with main as target_branch
        update_ops = [
            op for op in git_stack_fixture.read_operations()
            if op['operation'] == 'update_mr'
        ]
        assert len(update_ops) == 1
        assert update_ops[0]['args']['mr_iid'] == mr2_iid
        assert update_ops[0]['args']['target_branch'] == 'main'


class TestInsertCommitAtBeginning:
    """Test inserting a new commit at the beginning of a stack."""

    def test_insert_commit_updates_target_branches(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test inserting a commit before existing ones updates MR targets.

        When inserting a new commit at the beginning of a stack:
        - The new commit gets a Change-ID with the next available position
          (max existing + 1), NOT position 1
        - Existing Change-IDs are preserved (stable identifiers)
        - The MR target branches are updated based on actual commit order
        """
        # Create stack with 4 commits
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')
        create_commit(git_stack_fixture.repo_path, 'file3.txt', 'Third commit')
        create_commit(git_stack_fixture.repo_path, 'file4.txt',
                      'Fourth commit')

        # Push the initial stack
        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        mapping_before = git_stack_fixture.read_mapping()
        assert len(mapping_before) == 4

        # Get the first commit's Change-ID and MR info
        first_commit_sha = run_git(git_stack_fixture.repo_path,
                                   ['rev-parse', 'HEAD~3'])
        first_cid = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, first_commit_sha))
        assert first_cid is not None
        first_mr_iid = mapping_before[first_cid]['mr_iid']

        # Verify original first commit targets main
        create_ops = [
            op for op in git_stack_fixture.read_operations()
            if op['operation'] == 'create_mr'
        ]
        first_create = [
            op for op in create_ops if op['args']['title'] == 'First commit'
        ]
        assert len(first_create) == 1
        assert first_create[0]['args']['target_branch'] == 'main'

        git_stack_fixture.reset_mock_client()

        # Insert a new commit at the beginning:
        # 1. Save current HEAD
        head_sha = run_git(git_stack_fixture.repo_path, ['rev-parse', 'HEAD'])

        # 2. Reset to main and create new commit
        run_git(git_stack_fixture.repo_path,
                ['reset', '--hard', 'origin/main'])
        create_commit(git_stack_fixture.repo_path, 'file0.txt',
                      'Zeroth commit')

        # 3. Cherry-pick all original commits on top (need ~4..HEAD to include all 4)
        run_git(git_stack_fixture.repo_path,
                ['cherry-pick', f'{head_sha}~4..{head_sha}'])

        # Verify we now have 5 commits
        local_commits = run_git(git_stack_fixture.repo_path,
                                ['log', '--oneline', 'origin/main..HEAD'])
        assert len(local_commits.strip().split('\n')) == 5

        # Push again - new commit gets Change-ID, existing ones preserved
        stack2 = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack2.push(base_branch='main')

        # Verify a new MR was created for the new commit
        create_ops = [
            op for op in git_stack_fixture.read_operations()
            if op['operation'] == 'create_mr'
        ]
        new_commit_creates = [
            op for op in create_ops if op['args']['title'] == 'Zeroth commit'
        ]
        assert len(new_commit_creates) == 1
        # The new commit is first in order, so it targets main
        assert new_commit_creates[0]['args']['target_branch'] == 'main'

        # Verify the original first commit's MR target was updated
        # to point to the new commit's branch (based on commit order)
        update_ops = [
            op for op in git_stack_fixture.read_operations()
            if op['operation'] == 'update_mr'
        ]
        first_mr_update = [
            op for op in update_ops if op['args']['mr_iid'] == first_mr_iid
        ]
        assert len(first_mr_update) == 1
        # Should now target the new zeroth commit's branch, not main
        assert first_mr_update[0]['args']['target_branch'] != 'main'

        # Verify the new commit got position 5 (max existing 4 + 1)
        new_commit_cid = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD~4'))
        assert new_commit_cid is not None
        assert extract_position(new_commit_cid) == 5


class TestDownstreamRebase:
    """Test rebasing downstream commits from remote."""

    def test_rebase_downstream_on_amend(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test that amending commit 3 rebases commit 4 from remote."""
        # Create stack with 4 commits
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')
        create_commit(git_stack_fixture.repo_path, 'file3.txt', 'Third commit')
        create_commit(git_stack_fixture.repo_path, 'file4.txt',
                      'Fourth commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        mapping_before = git_stack_fixture.read_mapping()
        assert len(mapping_before) == 4

        # Get commit 4's Change-ID for later verification
        cid4 = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD'))
        assert cid4 is not None

        # Get commit 3's SHA before amend
        commit3_sha = run_git(git_stack_fixture.repo_path,
                              ['rev-parse', 'HEAD~1'])

        git_stack_fixture.reset_mock_client()

        # Simulate amending commit 3:
        # 1. Reset to commit 2
        # 2. Cherry-pick commit 3 with modification
        run_git(git_stack_fixture.repo_path, ['reset', '--hard', 'HEAD~2'])

        # Cherry-pick commit 3 (preserves Change-ID in message)
        run_git(git_stack_fixture.repo_path, ['cherry-pick', commit3_sha])

        # Amend commit 3 with a change
        file3_path = git_stack_fixture.repo_path / 'file3.txt'
        file3_path.write_text('Third commit - amended content\n')
        run_git(git_stack_fixture.repo_path, ['add', 'file3.txt'])
        run_git(git_stack_fixture.repo_path,
                ['commit', '--amend', '--no-edit'])

        # Now we have commits 1, 2, 3' locally (commit 4 is only on remote)
        local_commits = run_git(git_stack_fixture.repo_path,
                                ['log', '--oneline', 'origin/main..HEAD'])
        assert len(local_commits.strip().split('\n')) == 3

        # Push again - should fetch and rebase commit 4
        stack2 = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack2.push(base_branch='main')

        # Verify we now have 4 commits locally
        local_commits_after = run_git(
            git_stack_fixture.repo_path,
            ['log', '--oneline', 'origin/main..HEAD'])
        assert len(local_commits_after.strip().split('\n')) == 4

        # Verify commit 4's Change-ID is preserved
        cid4_after = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD'))
        assert cid4_after == cid4

        # Verify commit 4's content is present
        file4_path = git_stack_fixture.repo_path / 'file4.txt'
        assert file4_path.exists()


class TestMergeAndRebase:
    """Test rebasing after MR is merged."""

    def test_target_updated_after_merge(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test that MR targets are updated after first MR is merged."""
        # Create stack with 4 commits
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')
        create_commit(git_stack_fixture.repo_path, 'file3.txt', 'Third commit')
        create_commit(git_stack_fixture.repo_path, 'file4.txt',
                      'Fourth commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        mapping_before = git_stack_fixture.read_mapping()
        assert len(mapping_before) == 4

        # Get Change-IDs and MR IIDs
        cid1 = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD~3'))
        cid2 = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD~2'))
        assert cid1 is not None
        assert cid2 is not None

        mr1_iid = mapping_before[cid1]['mr_iid']
        mr2_iid = mapping_before[cid2]['mr_iid']

        # Verify MR2 initially targets MR1's branch
        create_ops = git_stack_fixture.read_operations()
        mr2_create = [
            op for op in create_ops if op['operation'] == 'create_mr'
            and op['args'].get('source_branch') == get_branch_name(cid2)
        ]
        assert len(mr2_create) == 1
        assert mr2_create[0]['args']['target_branch'] != 'main'

        # Mark MR1 as merged
        git_stack_fixture.mock_client.set_mr_state(mr1_iid, 'merged')

        git_stack_fixture.reset_mock_client()

        # Simulate merge: remove commit 1 from local history
        # (In real workflow, main would be updated and user would rebase)
        commit2_sha = run_git(git_stack_fixture.repo_path,
                              ['rev-parse', 'HEAD~2'])
        commit3_sha = run_git(git_stack_fixture.repo_path,
                              ['rev-parse', 'HEAD~1'])
        commit4_sha = run_git(git_stack_fixture.repo_path,
                              ['rev-parse', 'HEAD'])

        # Reset to main and cherry-pick commits 2-4
        run_git(git_stack_fixture.repo_path,
                ['reset', '--hard', 'origin/main'])
        run_git(git_stack_fixture.repo_path, ['cherry-pick', commit2_sha])
        run_git(git_stack_fixture.repo_path, ['cherry-pick', commit3_sha])
        run_git(git_stack_fixture.repo_path, ['cherry-pick', commit4_sha])

        # Remove MR1 from mapping (it's merged)
        mapping_after_merge = {
            k: v
            for k, v in mapping_before.items() if k != cid1
        }
        git_stack_fixture.mapping_file.write_text(
            json.dumps(mapping_after_merge, indent=2))

        # Push again
        stack2 = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack2.push(base_branch='main')

        # Verify MR2 now targets main
        update_ops = [
            op for op in git_stack_fixture.read_operations()
            if op['operation'] == 'update_mr'
        ]
        mr2_update = [
            op for op in update_ops if op['args']['mr_iid'] == mr2_iid
        ]
        assert len(mr2_update) == 1
        assert mr2_update[0]['args']['target_branch'] == 'main'


class TestClean:
    """Test clean functionality."""

    def test_clean_removes_merged_mrs(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test that clean removes merged MRs from mapping."""
        # Create and push stack
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')
        create_commit(git_stack_fixture.repo_path, 'file3.txt', 'Third commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        mapping = git_stack_fixture.read_mapping()
        assert len(mapping) == 3

        mr_iids = [info['mr_iid'] for info in mapping.values()]

        # Mark first two as merged
        git_stack_fixture.mock_client.set_mr_state(mr_iids[0], 'merged')
        git_stack_fixture.mock_client.set_mr_state(mr_iids[1], 'merged')

        # Run clean
        stack2 = git_stack_fixture.create_stack_instance()
        stack2.clean()

        # Should have only 1 entry
        mapping_after = git_stack_fixture.read_mapping()
        assert len(mapping_after) == 1


class TestList:
    """Test list functionality."""

    def test_list_shows_stacks(self,
                               git_stack_fixture: GitStackTestFixture) -> None:
        """Test that list shows all stacks."""
        # Create first stack
        create_branch(git_stack_fixture.repo_path, 'feature1', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'f1_file1.txt',
                      'Feature 1 commit 1')
        create_commit(git_stack_fixture.repo_path, 'f1_file2.txt',
                      'Feature 1 commit 2')

        stack1 = git_stack_fixture.create_stack_instance(
            stack_name='feature-one')
        stack1.push(base_branch='main')

        # Create second stack
        checkout(git_stack_fixture.repo_path, 'main')
        create_branch(git_stack_fixture.repo_path, 'feature2', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'f2_file1.txt',
                      'Feature 2 commit 1')

        stack2 = git_stack_fixture.create_stack_instance(
            stack_name='feature-two')
        stack2.push(base_branch='main')

        # Run list
        stack_list = git_stack_fixture.create_stack_instance()

        captured = StringIO()
        with patch('sys.stdout', captured):
            stack_list.list()

        output = captured.getvalue()
        assert 'feature-one' in output
        assert 'feature-two' in output


class TestCheckout:
    """Test checkout functionality."""

    def test_checkout_switches_branch(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test checkout switches to latest branch in stack."""
        # Create stack
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        # Get expected branch
        cid = extract_change_id(
            get_commit_message(git_stack_fixture.repo_path, 'HEAD'))
        assert cid is not None
        expected_branch = get_branch_name(cid)

        # Checkout main
        checkout(git_stack_fixture.repo_path, 'main')
        assert get_current_branch(git_stack_fixture.repo_path) == 'main'

        # Run checkout command
        stack2 = git_stack_fixture.create_stack_instance()
        stack2.checkout('test-feature')

        assert get_current_branch(
            git_stack_fixture.repo_path) == expected_branch


class TestRemove:
    """Test remove functionality."""

    def test_remove_closes_mrs(self,
                               git_stack_fixture: GitStackTestFixture) -> None:
        """Test remove closes all MRs and deletes branches."""
        # Create stack
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')
        create_commit(git_stack_fixture.repo_path, 'file2.txt',
                      'Second commit')

        stack = git_stack_fixture.create_stack_instance(
            stack_name='test-feature')
        stack.push(base_branch='main')

        mapping_before = git_stack_fixture.read_mapping()
        assert len(mapping_before) == 2

        # Get branch names
        branches = [get_branch_name(cid) for cid in mapping_before]

        # Checkout main
        checkout(git_stack_fixture.repo_path, 'main')

        git_stack_fixture.reset_mock_client()

        # Run remove
        stack2 = git_stack_fixture.create_stack_instance()
        stack2.remove('test-feature')

        # Check MRs were closed
        operations = git_stack_fixture.read_operations()
        close_ops = [op for op in operations if op['operation'] == 'close_mr']
        assert len(close_ops) == 2

        # Mapping should be empty
        mapping_after = git_stack_fixture.read_mapping()
        assert len(mapping_after) == 0

        # Branches should be deleted
        for branch in branches:
            assert not branch_exists(git_stack_fixture.repo_path, branch)


class TestDryRun:
    """Test dry-run mode."""

    def test_dry_run_no_changes(
            self, git_stack_fixture: GitStackTestFixture) -> None:
        """Test dry-run doesn't make actual changes."""
        # Create commits
        create_branch(git_stack_fixture.repo_path, 'feature', 'origin/main')
        create_commit(git_stack_fixture.repo_path, 'file1.txt', 'First commit')

        # Get original message
        original_msg = get_commit_message(git_stack_fixture.repo_path, 'HEAD')

        # Run push in dry-run mode
        stack = git_stack_fixture.create_stack_instance(
            dry_run=True, stack_name='test-feature')
        stack.push(base_branch='main')

        # Message should be unchanged (no Change-ID added)
        current_msg = get_commit_message(git_stack_fixture.repo_path, 'HEAD')
        assert current_msg == original_msg

        # No MRs should be created
        mapping = git_stack_fixture.read_mapping()
        assert len(mapping) == 0
