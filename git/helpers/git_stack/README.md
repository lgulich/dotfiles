# git-stack

Manage stacked GitLab MRs with Change-IDs.

## Overview

git-stack helps manage stacked GitLab Merge Requests where each MR targets the previous commit's MR branch. It uses Change-Ids (similar to Gerrit) to track commits across rebases.

## Installation

```bash
# Install with uv
uv pip install -e .

# Or with pip
pip install -e .
```

## Usage

### Creating a Stack

```bash
# Create a feature branch with commits
git checkout -b feature origin/main
# ... make commits ...

# Create stacked MRs
git-stack push --stack-name my-feature
```

### Commands

- `git-stack push` - Create or update stacked MRs
- `git-stack list` - List all stacks
- `git-stack checkout <name>` - Checkout latest branch from a stack
- `git-stack status` - Show status of current stack
- `git-stack show` - Show info about current commit
- `git-stack clean` - Remove closed/merged MRs from mapping
- `git-stack remove <name>` - Remove a stack (close MRs, delete branches)
- `git-stack reindex` - Create new Change-IDs for commits

### Options

- `--base <branch>` - Base branch to stack on (default: main)
- `--stack-name <name>` - Stack name to use
- `--dry-run` - Show what would be done without executing

## Change-ID Format

Change-IDs use the format: `uuid@stackname@position`

Example: `a1b2c3d4@my-feature@1`

This format ensures unambiguous parsing even when stack names contain hyphens.

## Configuration

### Environment Variables

- `GIT_STACK_MAPPING_FILE` - Override mapping file location
- `GIT_STACK_USER` - Override username for branch naming

### Branch Naming

By default, branches are named `username/stack-<change-id>`.

The username is determined from:
1. `GIT_STACK_USER` environment variable
2. `git config user.name` (sanitized)
3. `USER` environment variable

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Type checking
uv run mypy src

# Linting
uv run ruff check src tests
```

## Requirements

- Python >= 3.11
- glab CLI (for GitLab API access)
- git
