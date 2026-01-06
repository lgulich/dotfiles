---
description: Jira CLI usage guide for listing, creating, and managing issues
---

# Jira CLI Usage Guide

## Basic Commands

### Listing Issues

List all issues authored by current user:
```bash
jira issue list --jql "reporter = currentUser()" --plain
```

List issues assigned to current user:
```bash
jira issue list --jql "assignee = currentUser()" --plain
```

List issues by status:
```bash
jira issue list --jql "status = 'In Progress'" --plain
```

List issues in a specific project:
```bash
jira issue list --jql "project = ISAACOS" --plain
```

### Viewing Issue Details

View details of a specific issue:
```bash
jira issue view ISAACOS-120
```

### Creating Issues

**Basic syntax:**
```bash
jira issue create -pPROJECT_KEY -tISSUE_TYPE -s"Summary" -b"Description" -yPRIORITY [flags]
```

**Common flags:**
- `-p, --project`: Project key (e.g., `ISAACOS`)
- `-t, --type`: Issue type (`Task`, `Story`, `Bug`, `Epic`)
- `-s, --summary`: Issue summary/title
- `-b, --body`: Issue description (use `-b` not `--description`)
- `-y, --priority`: Priority (`Low`, `Medium`, `High`, `Critical`)
- `-a, --assignee`: Assign to user (username, email, or display name)
- `-l, --label`: Add labels (can be used multiple times: `-lbug -lurgent`)
- `-C, --component`: Add components
- `--no-input`: Disable interactive prompts (ALWAYS use this when creating tickets programmatically)
- `--web`: Open issue in browser after creation
- `--template`: Read description from file (use `-` for stdin)

**Examples:**

Create a Task in ISAACOS with high priority:
```bash
jira issue create -pISAACOS -tTask -s"Add CMake macros" -yHigh -b"Description here" --no-input
```

Create with labels:
```bash
jira issue create -pISAACOS -tTask -s"Fix bug" -yHigh -lbug -lurgent -b"Bug description" --no-input
```

Create with multi-line description:
```bash
jira issue create -pISAACOS -tTask -s"Summary" -yHigh -b"Line 1

Line 2

## Section
Content here" --no-input
```

**Best practices for ticket creation:**
- Always use `--no-input` flag when creating tickets programmatically to avoid prompts
- Use `Task` type for ISAACOS project (Story may not be available in all projects)
- Wrap summary and description in quotes if they contain spaces or special characters
- Use `-b` for body/description (the flag is `--body`, not `--description`)
- Keep descriptions concise but include:
  - Clear problem statement or feature request
  - Examples when relevant (use code blocks)
  - References to related discussions, PRs, or documentation
- Project key is `ISAACOS` for Isaac OS project

### Updating Issues

Update issue status:
```bash
jira issue move ISAACOS-120 "In Progress"
```

Add comment to issue:
```bash
jira issue comment add ISAACOS-120 "Comment text"
```

Edit issue fields:
```bash
jira issue edit ISAACOS-120 -s"New summary" -yHigh --no-input
```

### JQL Query Tips

- Use quotes around JQL queries that contain special characters.
- `currentUser()` is a function that represents the logged-in user.
- Combine filters with `AND`: `"status = 'To Do' AND assignee = currentUser()"`.
- Order results: `"reporter = currentUser() ORDER BY created DESC"`.

### Output Formats

- `--plain`: Simple table format (good for quick viewing).
- `--json`: JSON output (good for parsing/scripting).
- No flag: Default formatted output.

### Common Use Cases

Get all my open tasks:
```bash
jira issue list --jql "assignee = currentUser() AND status != Done" --plain
```

Get recently updated issues:
```bash
jira issue list --jql "updated >= -7d ORDER BY updated DESC" --plain
```

Find issues by text:
```bash
jira issue list --jql "text ~ 'test coverage'" --plain
```

## Important Notes

- JQL (Jira Query Language) is powerful - refer to Atlassian docs for advanced queries.
- The `--plain` flag provides cleaner output for terminal viewing.
- Project key is `ISAACOS` for Isaac OS project.
- When creating tickets, always use `--no-input` to avoid interactive prompts.
- Use `-b` flag for description body, not `--description`.
- Issue type `Task` works for ISAACOS; `Story` may not be available in all projects.
