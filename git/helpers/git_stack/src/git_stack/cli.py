"""
Command-line interface for git-stack.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from git_stack.change_id import extract_stack_name
from git_stack.stack import GitStackPush

# Try to import argcomplete for shell completion
try:
    import argcomplete

    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


class StackNameCompleter:  # pylint: disable=too-few-public-methods
    """Custom completer for stack names."""

    def __call__(self, prefix: str, parsed_args: Any,
                 **kwargs: Any) -> list[str]:
        """Return list of stack names for completion."""
        try:
            import json  # pylint: disable=import-outside-toplevel

            repo_root = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            mapping_path = Path(repo_root) / '.git' / 'git-stack-mapping.json'

            if not mapping_path.exists():
                return []

            with open(mapping_path) as f:
                mapping = json.load(f)

            stack_names = set()
            for change_id in mapping:
                stack_name = extract_stack_name(change_id)
                if stack_name:
                    stack_names.add(stack_name)

            return sorted(stack_names)
        except Exception:  # pylint: disable=broad-exception-caught
            return []


def cmd_push(args: argparse.Namespace) -> None:
    """Handle push subcommand."""
    stack = GitStackPush(dry_run=args.dry_run, stack_name=args.stack_name)
    stack.push(base_branch=args.base)


def cmd_clean(args: argparse.Namespace) -> None:
    """Handle clean subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.clean()


def cmd_reindex(args: argparse.Namespace) -> None:
    """Handle reindex subcommand."""
    stack = GitStackPush(dry_run=args.dry_run, stack_name=args.stack_name)
    stack.reindex(base_branch=args.base)


def cmd_list(args: argparse.Namespace) -> None:  # pylint: disable=unused-argument
    """Handle list subcommand."""
    stack = GitStackPush()
    stack.list()


def cmd_checkout(args: argparse.Namespace) -> None:
    """Handle checkout subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.checkout(stack_name=args.stack_name)


def cmd_remove(args: argparse.Namespace) -> None:
    """Handle remove subcommand."""
    stack = GitStackPush(dry_run=args.dry_run)
    stack.remove(stack_name=args.stack_name)


def cmd_show(args: argparse.Namespace) -> None:  # pylint: disable=unused-argument
    """Handle show subcommand."""
    stack = GitStackPush()
    stack.show()


def cmd_status(args: argparse.Namespace) -> None:
    """Handle status subcommand."""
    stack = GitStackPush()
    stack.status(base_branch=args.base)


def main() -> None:
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
        """,
    )
    push_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to stack on (default: origin/main)',
    )
    stack_name_arg = push_parser.add_argument(
        '--stack-name',
        default=None,
        help='Stack name to use (default: auto-detect or prompt)',
    )
    if ARGCOMPLETE_AVAILABLE:
        stack_name_arg.completer = StackNameCompleter(  # type: ignore[attr-defined]
        )
    push_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing',
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
        """,
    )
    clean_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing',
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
        """,
    )
    reindex_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to stack on (default: origin/main)',
    )
    reindex_stack_arg = reindex_parser.add_argument(
        '--stack-name',
        default=None,
        help='Stack name to use (default: prompt)',
    )
    if ARGCOMPLETE_AVAILABLE:
        reindex_stack_arg.completer = StackNameCompleter(  # type: ignore[attr-defined]
        )
    reindex_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing',
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
        """,
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
        """,
    )
    checkout_stack_arg = checkout_parser.add_argument(
        'stack_name', help='Name of the stack to checkout')
    if ARGCOMPLETE_AVAILABLE:
        checkout_stack_arg.completer = StackNameCompleter(  # type: ignore[attr-defined]
        )
    checkout_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing',
    )
    checkout_parser.set_defaults(func=cmd_checkout)

    # Remove subcommand
    remove_parser = subparsers.add_parser(
        'remove',
        help='Remove all branches and close all MRs for a stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s remove myfeature         # Remove 'myfeature' stack
  %(prog)s remove myfeature --dry-run  # Show what would be done
        """,
    )
    remove_stack_arg = remove_parser.add_argument(
        'stack_name', help='Name of the stack to remove')
    if ARGCOMPLETE_AVAILABLE:
        remove_stack_arg.completer = StackNameCompleter(  # type: ignore[attr-defined]
        )
    remove_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing',
    )
    remove_parser.set_defaults(func=cmd_remove)

    # Show subcommand
    show_parser = subparsers.add_parser(
        'show',
        help='Show information about the current commit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s show           # Show current commit's stack and MR info
        """,
    )
    show_parser.set_defaults(func=cmd_show)

    # Status subcommand
    status_parser = subparsers.add_parser(
        'status',
        help='Show status of all commits in the current stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show status of commits on current stack
  %(prog)s status --base develop     # Show status with develop as base
        """,
    )
    status_parser.add_argument(
        '--base',
        default='main',
        help='Base branch to compare against (default: origin/main)',
    )
    status_parser.set_defaults(func=cmd_status)

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
