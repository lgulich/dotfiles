#!/usr/bin/env python3
"""
Test helper functions for git_stack tests.

Provides utilities for creating and manipulating git repositories in tests.
"""

import subprocess
from pathlib import Path


def _run_git(repo_path: Path,
             args: list[str],
             check: bool = True,
             input_text: str | None = None) -> str:
    """
    Run a git command in the specified repository.

    Args:
        repo_path: Path to repository
        args: Git command arguments
        check: Whether to raise on error
        input_text: Optional stdin input

    Returns:
        Command output as string
    """
    result = subprocess.run(['git'] + args,
                            cwd=repo_path,
                            capture_output=True,
                            text=True,
                            check=check,
                            input=input_text)
    return result.stdout.strip()


def create_git_repo(path: Path) -> None:
    """
    Initialize a git repository with initial commit.

    Args:
        path: Path where repository should be created
    """
    path.mkdir(parents=True, exist_ok=True)

    # Initialize repo
    _run_git(path, ['init'])

    # Configure user
    _run_git(path, ['config', 'user.name', 'Test User'])
    _run_git(path, ['config', 'user.email', 'test@example.com'])

    # Create initial commit
    initial_file = path / '.gitkeep'
    initial_file.write_text('initial\n')
    _run_git(path, ['add', '.gitkeep'])
    _run_git(path, ['commit', '-m', 'Initial commit'])

    # Create main branch (ensure we have a branch named 'main')
    _run_git(path, ['branch', '-M', 'main'])


def create_commit(repo_path: Path,
                  filename: str,
                  message: str,
                  content: str | None = None) -> str:
    """
    Create a file and commit it.

    Args:
        repo_path: Path to repository
        filename: Name of file to create
        message: Commit message
        content: File content (defaults to filename if not provided)

    Returns:
        Commit SHA
    """
    if content is None:
        content = f"Content for {filename}\n"

    file_path = repo_path / filename
    file_path.write_text(content)

    _run_git(repo_path, ['add', filename])
    _run_git(repo_path, ['commit', '-m', message])

    return _run_git(repo_path, ['rev-parse', 'HEAD'])


# pylint: disable=too-many-branches
def amend_commit(repo_path: Path,
                 filename: str,
                 commit_back: int = 0,
                 content: str | None = None) -> str:
    """
    Amend a file to a commit N steps back from HEAD.

    For commit_back=0, amends to HEAD.
    For commit_back=1, amends to HEAD~1, etc.

    This function:
    1. Saves the current HEAD
    2. Resets to the target commit
    3. Creates/modifies the file
    4. Amends the commit
    5. Cherry-picks subsequent commits if any
    6. Updates the original branch pointer

    Args:
        repo_path: Path to repository
        filename: Name of file to create/modify
        commit_back: How many commits back to amend (0=HEAD, 1=HEAD~1, etc.)
        content: File content (defaults to "amended: {filename}")

    Returns:
        New commit SHA of the amended commit
    """
    if content is None:
        content = f"amended: {filename}\n"

    # Get current branch name
    current_branch: str | None
    try:
        current_branch = _run_git(repo_path,
                                  ['symbolic-ref', '--short', 'HEAD'],
                                  check=False)
        if not current_branch:
            current_branch = None
    except subprocess.CalledProcessError:
        current_branch = None

    # Get the SHA of the commit to amend
    target_ref = 'HEAD' if commit_back == 0 else f'HEAD~{commit_back}'
    target_sha = _run_git(repo_path, ['rev-parse', target_ref])

    # Get commits that come after the target (if any)
    if commit_back > 0:
        # Get SHAs of commits after target
        later_commits = _run_git(
            repo_path,
            ['rev-list', '--reverse', f'{target_sha}..HEAD']).split('\n')
        if later_commits == ['']:
            later_commits = []
    else:
        later_commits = []

    # Get parent of target commit
    parent_sha = _run_git(repo_path, ['rev-parse', f'{target_sha}~1'],
                          check=False)

    # Reset to parent
    if parent_sha:
        _run_git(repo_path, ['reset', '--hard', parent_sha])
    else:
        # Target is the initial commit, need to handle differently
        _run_git(repo_path, ['checkout', '--orphan', 'temp_amend'])

    # Cherry-pick the target commit
    try:
        _run_git(repo_path, ['cherry-pick', target_sha])
    except subprocess.CalledProcessError:
        # If cherry-pick fails, continue anyway (might be orphan case)
        pass

    # Modify the file
    file_path = repo_path / filename
    file_path.write_text(content)
    _run_git(repo_path, ['add', filename])

    # Amend the commit
    _run_git(repo_path, ['commit', '--amend', '--no-edit'])

    # Get new SHA of amended commit
    new_sha = _run_git(repo_path, ['rev-parse', 'HEAD'])

    # Cherry-pick later commits
    for commit_sha in later_commits:
        try:
            _run_git(repo_path, ['cherry-pick', commit_sha])
        except subprocess.CalledProcessError:
            # Handle merge conflicts by just taking ours
            _run_git(repo_path, ['add', '-A'])
            _run_git(repo_path, ['cherry-pick', '--continue'], input_text='\n')

    # Update branch pointer or checkout final commit
    final_sha = _run_git(repo_path, ['rev-parse', 'HEAD'])

    if current_branch and current_branch != 'temp_amend':
        _run_git(repo_path, ['checkout', current_branch])
        _run_git(repo_path, ['reset', '--hard', final_sha])
    elif current_branch == 'temp_amend':
        _run_git(repo_path, ['checkout', '-b', 'main'])
        _run_git(repo_path, ['branch', '-D', 'temp_amend'], check=False)
    else:
        # Was in detached HEAD
        _run_git(repo_path, ['checkout', final_sha])

    return new_sha


def create_branch(repo_path: Path,
                  branch_name: str,
                  from_ref: str = 'HEAD') -> None:
    """
    Create and checkout a branch.

    Args:
        repo_path: Path to repository
        branch_name: Name of new branch
        from_ref: Reference to create branch from (default: HEAD)
    """
    _run_git(repo_path, ['checkout', '-b', branch_name, from_ref])


def checkout(repo_path: Path, ref: str) -> None:
    """
    Checkout a reference.

    Args:
        repo_path: Path to repository
        ref: Reference to checkout (branch name, SHA, etc.)
    """
    _run_git(repo_path, ['checkout', ref])


def get_commit_message(repo_path: Path, ref: str = 'HEAD') -> str:
    """
    Get commit message for a reference.

    Args:
        repo_path: Path to repository
        ref: Reference to get message from (default: HEAD)

    Returns:
        Full commit message
    """
    return _run_git(repo_path, ['log', '-1', '--format=%B', ref])


def get_current_sha(repo_path: Path) -> str:
    """
    Get current HEAD SHA.

    Args:
        repo_path: Path to repository

    Returns:
        Current HEAD SHA
    """
    return _run_git(repo_path, ['rev-parse', 'HEAD'])


def get_current_branch(repo_path: Path) -> str | None:
    """
    Get current branch name.

    Args:
        repo_path: Path to repository

    Returns:
        Current branch name, or None if in detached HEAD
    """
    try:
        branch = _run_git(repo_path, ['symbolic-ref', '--short', 'HEAD'],
                          check=False)
        return branch if branch else None
    except subprocess.CalledProcessError:
        return None


def create_remote(repo_path: Path, remote_name: str,
                  remote_path: Path) -> None:
    """
    Add a remote to the repository.

    Args:
        repo_path: Path to repository
        remote_name: Name of remote (e.g., 'origin')
        remote_path: Path to remote repository
    """
    _run_git(repo_path, ['remote', 'add', remote_name, str(remote_path)])


def push_branch(repo_path: Path,
                remote_name: str,
                branch_name: str,
                force: bool = False) -> None:
    """
    Push a branch to remote.

    Args:
        repo_path: Path to repository
        remote_name: Name of remote
        branch_name: Name of branch to push
        force: Whether to force push
    """
    args = ['push', remote_name, branch_name]
    if force:
        args.insert(1, '-f')
    _run_git(repo_path, args)


def fetch(repo_path: Path, remote_name: str = 'origin') -> None:
    """
    Fetch from remote.

    Args:
        repo_path: Path to repository
        remote_name: Name of remote to fetch from
    """
    _run_git(repo_path, ['fetch', remote_name])


def branch_exists(repo_path: Path, branch_name: str) -> bool:
    """
    Check if a branch exists.

    Args:
        repo_path: Path to repository
        branch_name: Name of branch to check

    Returns:
        True if branch exists
    """
    try:
        _run_git(repo_path, ['rev-parse', '--verify', branch_name])
        return True
    except subprocess.CalledProcessError:
        return False


def get_file_content(repo_path: Path, filename: str) -> str:
    """
    Get content of a file in the repository.

    Args:
        repo_path: Path to repository
        filename: Name of file

    Returns:
        File content
    """
    file_path = repo_path / filename
    return file_path.read_text()
