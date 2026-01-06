---
description: Process for addressing MR comments
---

# Addressing MR Comments

## Step 1: Get Open Comments

Use this command to retrieve all unresolved comments for the current MR:

```bash
glab mr view --per-page=9999 --comments --output=json | jq '.Notes[] | select(.resolvable == true and .resolved == false)'
```

Note: Must source brew environment first for glab to work.

## Step 2: Address Common Issues

Create a todo list of all open comments and address each comment.
Work as if you're a senior developer that writes clean and maintainable code.

## Resolving Comments

Note: glab CLI doesn't support resolving comments directly. Comments are addressed through code fixes, and reviewers verify/resolve manually.

## Troubleshooting

### "Command not found: glab"
Source brew environment: `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"`
