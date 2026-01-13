"""
git-stack: Manage stacked GitLab MRs

This package helps manage stacked GitLab MRs where each MR targets the previous
commit's MR branch. It uses Change-Ids (similar to Gerrit) to track commits
across rebases.
"""

from git_stack.change_id import (
    extract_change_id,
    extract_stack_name,
    generate_change_id,
    get_branch_name,
)
from git_stack.stack import GitStackPush

__all__ = [
    'GitStackPush',
    'extract_change_id',
    'extract_stack_name',
    'generate_change_id',
    'get_branch_name',
]

__version__ = '0.1.0'
