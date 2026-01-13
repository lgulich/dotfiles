"""
Change-ID handling for git-stack.

Change-IDs uniquely identify commits across rebases and are used to track
which commits map to which MRs.

Format: uuid@stackname@position (e.g., "a1b2c3d4@my-feature@1")

The @ delimiter is used because:
- Stack names can contain hyphens (e.g., "my-cool-feature")
- @ is not allowed in stack names, making parsing unambiguous
- @ is valid in git commit messages

For backward compatibility, we also parse the old format: uuid-stackname-N
"""

from __future__ import annotations

import re
import subprocess
import uuid

# Delimiter for Change-ID components (new format)
CHANGE_ID_DELIMITER = '@'

# Pattern for new format: uuid@stackname@position
NEW_CHANGE_ID_PATTERN = re.compile(
    r'Change-Id:\s+([a-f0-9]+)@([a-z0-9-]+)@(\d+)', re.IGNORECASE)

# Pattern for old format (backward compatibility): uuid-stackname-N
# More permissive to match stack names with letters beyond a-f
OLD_CHANGE_ID_PATTERN = re.compile(r'Change-Id:\s+([a-z0-9-]+)', re.IGNORECASE)


def extract_change_id(commit_message: str | None) -> str | None:
    """
    Extract Change-Id from a commit message.

    Supports both new format (uuid@stackname@position) and old format
    (uuid-stackname-position) for backward compatibility.

    Args:
        commit_message: The commit message text

    Returns:
        The Change-Id string if found, None otherwise
    """
    if not commit_message:
        return None

    # Try new format first: uuid@stackname@position
    match = NEW_CHANGE_ID_PATTERN.search(commit_message)
    if match:
        uuid_part, stack_name, position = match.groups()
        return f"{uuid_part}{CHANGE_ID_DELIMITER}{stack_name}{CHANGE_ID_DELIMITER}{position}"

    # Fall back to old format for backward compatibility
    match = OLD_CHANGE_ID_PATTERN.search(commit_message)
    if match:
        return match.group(1)

    return None


def extract_stack_name(change_id: str | None) -> str | None:
    """
    Extract stack name from a Change-Id.

    Args:
        change_id: The Change-Id string

    Returns:
        The stack name if found, None otherwise
    """
    if not change_id:
        return None

    # New format: uuid@stackname@position
    if CHANGE_ID_DELIMITER in change_id:
        parts = change_id.split(CHANGE_ID_DELIMITER)
        if len(parts) == 3:
            return parts[1]
        return None

    # Old format: uuid-stackname-N
    # This is fragile but needed for backward compatibility
    parts = change_id.split('-')
    if len(parts) >= 3:
        # Return everything between first uuid part and last number
        return '-'.join(parts[1:-1])

    return None


def extract_position(change_id: str | None) -> int | None:
    """
    Extract position from a Change-Id.

    Args:
        change_id: The Change-Id string

    Returns:
        The position (1-indexed) if found, None otherwise
    """
    if not change_id:
        return None

    # New format: uuid@stackname@position
    if CHANGE_ID_DELIMITER in change_id:
        parts = change_id.split(CHANGE_ID_DELIMITER)
        if len(parts) == 3 and parts[2].isdigit():
            return int(parts[2])
        return None

    # Old format: uuid-stackname-N
    parts = change_id.split('-')
    if parts and parts[-1].isdigit():
        return int(parts[-1])

    return None


def generate_change_id(stack_name: str, position: int) -> str:
    """
    Generate a new Change-Id using UUID, stack name, and position.

    Args:
        stack_name: The name of the stack
        position: The position in the stack (1-indexed)

    Returns:
        A Change-Id in format: uuid@stackname@position (e.g., "a1b2c3d4@feature@1")
    """
    uuid_part = str(uuid.uuid4())[:8]
    return f"{uuid_part}{CHANGE_ID_DELIMITER}{stack_name}{CHANGE_ID_DELIMITER}{position}"


def get_git_username() -> str:
    """
    Get the username for branch naming.

    Tries in order:
    1. GIT_STACK_USER environment variable
    2. git config user.name (sanitized)
    3. USER environment variable
    4. "user" as fallback

    Returns:
        Username suitable for branch naming (lowercase, alphanumeric + hyphen)
    """
    import os  # pylint: disable=import-outside-toplevel

    # Check environment override first
    env_user = os.getenv('GIT_STACK_USER')
    if env_user:
        return _sanitize_username(env_user)

    # Try git config
    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return _sanitize_username(result.stdout.strip())
    except FileNotFoundError:
        pass

    # Fall back to USER env var
    user = os.getenv('USER')
    if user:
        return _sanitize_username(user)

    return 'user'


def _sanitize_username(name: str) -> str:
    """
    Sanitize a username for use in branch names.

    Converts to lowercase and replaces invalid characters with hyphens.

    Args:
        name: Raw username

    Returns:
        Sanitized username (lowercase, only alphanumeric and hyphens)
    """
    # Convert to lowercase
    name = name.lower()
    # Replace spaces and underscores with hyphens
    name = re.sub(r'[\s_]+', '-', name)
    # Remove any characters that aren't alphanumeric or hyphen
    name = re.sub(r'[^a-z0-9-]', '', name)
    # Remove leading/trailing hyphens and collapse multiple hyphens
    name = re.sub(r'-+', '-', name).strip('-')

    return name or 'user'


def get_branch_name(change_id: str) -> str:
    """
    Format branch name for a given Change-Id.

    Args:
        change_id: The Change-Id

    Returns:
        Branch name in format: username/stack-<change-id>
    """
    user_name = get_git_username()
    return f"{user_name}/stack-{change_id}"


def validate_stack_name(stack_name: str) -> bool:
    """
    Validate that a stack name is valid.

    Stack names must:
    - Contain only lowercase letters, numbers, and hyphens
    - Not start or end with a hyphen
    - Not be empty
    - Not contain the @ character (used as delimiter)

    Args:
        stack_name: The stack name to validate

    Returns:
        True if valid, False otherwise
    """
    if not stack_name:
        return False

    if CHANGE_ID_DELIMITER in stack_name:
        return False

    return bool(
        re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', stack_name))
