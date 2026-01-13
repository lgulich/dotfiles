"""Pytest configuration and fixtures for git-stack tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from git_stack.hosting_client import MockGitHostingClient
from git_stack.stack import GitStackPush


def run_git(repo_path: Path, args: list[str], check: bool = True) -> str:
    """Run a git command in the specified repository."""
    result = subprocess.run(
        ['git'] + args,
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def create_git_repo(path: Path) -> None:
    """Initialize a git repository with initial commit."""
    path.mkdir(parents=True, exist_ok=True)
    run_git(path, ['init'])
    run_git(path, ['config', 'user.name', 'Test User'])
    run_git(path, ['config', 'user.email', 'test@example.com'])

    initial_file = path / '.gitkeep'
    initial_file.write_text('initial\n')
    run_git(path, ['add', '.gitkeep'])
    run_git(path, ['commit', '-m', 'Initial commit'])
    run_git(path, ['branch', '-M', 'main'])


def create_commit(repo_path: Path,
                  filename: str,
                  message: str,
                  content: str | None = None) -> str:
    """Create a file and commit it."""
    if content is None:
        content = f"Content for {filename}\n"

    file_path = repo_path / filename
    file_path.write_text(content)
    run_git(repo_path, ['add', filename])
    run_git(repo_path, ['commit', '-m', message])
    return run_git(repo_path, ['rev-parse', 'HEAD'])


def create_branch(repo_path: Path,
                  branch_name: str,
                  from_ref: str = 'HEAD') -> None:
    """Create and checkout a branch."""
    run_git(repo_path, ['checkout', '-b', branch_name, from_ref])


def checkout(repo_path: Path, ref: str) -> None:
    """Checkout a reference."""
    run_git(repo_path, ['checkout', ref])


def get_commit_message(repo_path: Path, ref: str = 'HEAD') -> str:
    """Get commit message for a reference."""
    return run_git(repo_path, ['log', '-1', '--format=%B', ref])


def get_current_branch(repo_path: Path) -> str | None:
    """Get current branch name."""
    try:
        branch = run_git(repo_path, ['symbolic-ref', '--short', 'HEAD'],
                         check=False)
        return branch if branch else None
    except subprocess.CalledProcessError:
        return None


def branch_exists(repo_path: Path, branch_name: str) -> bool:
    """Check if a branch exists."""
    try:
        run_git(repo_path, ['rev-parse', '--verify', branch_name])
        return True
    except subprocess.CalledProcessError:
        return False


class GitStackTestFixture:
    """Test fixture with git repo and mock client."""

    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.repo_path = test_dir / 'repo'
        self.bare_repo_path = test_dir / 'bare_repo'
        self.mapping_file = test_dir / 'mapping.json'
        self.mock_operations_file = test_dir / 'operations.json'
        self.mock_database_file = test_dir / 'mock_mr_db.json'

        self.mock_client = MockGitHostingClient(
            operations_file=self.mock_operations_file,
            database_file=self.mock_database_file,
        )

        # Create bare repo
        self.bare_repo_path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ['git', 'init', '--bare'],
            cwd=self.bare_repo_path,
            capture_output=True,
            check=True,
        )

        # Create working repo
        create_git_repo(self.repo_path)

        # Add remote
        run_git(self.repo_path,
                ['remote', 'add', 'origin',
                 str(self.bare_repo_path)])

        # Push main
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=self.repo_path,
            capture_output=True,
            check=True,
        )

        # Fetch
        subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=self.repo_path,
            capture_output=True,
            check=True,
        )

    def create_stack_instance(self,
                              dry_run: bool = False,
                              stack_name: str | None = None) -> GitStackPush:
        """Create a GitStackPush instance for testing."""
        return GitStackPush(
            dry_run=dry_run,
            mapping_path=self.mapping_file,
            stack_name=stack_name,
            client=self.mock_client,
        )

    def read_operations(self) -> list[dict[str, Any]]:
        """Read operations recorded by mock client."""
        if not self.mock_operations_file.exists():
            return []
        return json.loads(self.mock_operations_file.read_text())

    def read_mapping(self) -> dict[str, Any]:
        """Read the mapping file."""
        if not self.mapping_file.exists():
            return {}
        return json.loads(self.mapping_file.read_text())

    def reset_mock_client(self) -> None:
        """Reset mock client for a fresh test."""
        if self.mock_operations_file.exists():
            self.mock_operations_file.unlink()
        self.mock_client = MockGitHostingClient(
            operations_file=self.mock_operations_file,
            database_file=self.mock_database_file,
        )


@pytest.fixture
def git_stack_fixture() -> Generator[GitStackTestFixture, None, None]:
    """Create a test fixture with git repo and mock client."""
    test_dir = Path(tempfile.mkdtemp())
    original_dir = Path.cwd()

    fixture = GitStackTestFixture(test_dir)

    # Set env var for mapping file
    os.environ['GIT_STACK_MAPPING_FILE'] = str(fixture.mapping_file)

    # Change to repo directory
    os.chdir(fixture.repo_path)

    try:
        yield fixture
    finally:
        os.chdir(original_dir)
        shutil.rmtree(test_dir)
        if 'GIT_STACK_MAPPING_FILE' in os.environ:
            del os.environ['GIT_STACK_MAPPING_FILE']
