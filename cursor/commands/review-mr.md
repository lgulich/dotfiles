# Review Merge Request

Review an MR by analyzing diffs and generating a markdown file with proposed comments. User approves comments via checkboxes before publishing.

## Step 1: Get MR Information

The user will provide an MR number. Fetch the MR details:

```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && \
glab mr view <MR_NUMBER> --output=json
```

Extract key info: title, source branch, target branch, author, and diff_refs (needed for line-specific comments).

## Step 2: Get the Diff

Fetch the MR diff to analyze:

```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && \
glab mr diff <MR_NUMBER>
```

Alternatively, checkout the branch and use git diff:

```bash
git fetch origin
git diff origin/<target_branch>...origin/<source_branch>
```

## Step 3: Analyze the Changes

Review each changed file applying BOTH levels of review criteria:

### Code-Level (Junior/Mid)
- Logic errors, bugs, edge cases
- Code style and conventions
- Missing error handling and validation
- Test coverage gaps
- Documentation and comments
- Naming clarity

### Architecture-Level (Senior)
- **Clean Architecture**: Separation of concerns, proper layering, dependency direction
- **Big Picture Fit**: Alignment with system's overall design patterns
- **Abstractions**: Right level? Over/under-engineering?
- **API Design**: Intuitive and consistent interfaces
- **Extensibility**: Easy to modify/extend later
- **Technical Debt**: Introduces or reduces debt
- **Performance at Scale**: Broader system implications
- **Security**: Auth, authorization, input validation

You can also look at the rest of the repo to have more context of the change.
E.g. use this to see if the style is matching or if this is duplicating code.

## Step 4: Generate Review File

Create a markdown file at `.cursor/mr-reviews/mr-<number>-review.md` with this format:

```markdown
# MR Review: !<number> - <title>

**Branch**: `<source_branch>` -> `<target_branch>`
**Author**: @<username>
**Files changed**: <count>

**diff_refs** (for publishing):
- base_sha: `<base_sha>`
- start_sha: `<start_sha>`
- head_sha: `<head_sha>`

---

## Line-Specific Comments

### `path/to/file.py`

- [ ] **Line <N>** (<Type>): <Comment text>

- [ ] **Line <M>** (<Type>): <Comment text>

### `another/file.cc`

- [ ] **Line <X>** (<Type>): <Comment text>

---

## General Comments

- [ ] **<Type>**: <Comment text>

- [ ] **<Type>**: <Comment text>
```

Comment types: Bug, Suggestion, Question, Nitpick, Architecture, Security, Performance

## Step 5: User Reviews

Tell the user to open the generated file and check the boxes for comments they want to publish. They can also edit comment text directly.

## Step 6: Publish Approved Comments

When user says to publish, read the review file and find all checked items (`- [x]`).

### For General Comments

Use glab mr note:

```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && \
glab mr note <MR_NUMBER> -m "<comment text>"
```

### For Line-Specific Comments

Use glab api to create a discussion at the specific line:

```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && \
glab api POST /projects/:id/merge_requests/<MR_IID>/discussions \
  --field body="<comment text>" \
  --field "position[base_sha]=<base_sha>" \
  --field "position[start_sha]=<start_sha>" \
  --field "position[head_sha]=<head_sha>" \
  --field "position[position_type]=text" \
  --field "position[new_path]=<file_path>" \
  --field "position[new_line]=<line_number>"
```

Get project ID with: `glab api /projects/:fullpath | jq '.id'`

Report which comments were successfully published.

## Troubleshooting

### "Command not found: glab"
Source brew environment: `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"`

### Line comment fails
- Ensure the line number exists in the new version of the file (use new_line for additions)
- For deleted lines, use old_line and old_path instead
- Verify diff_refs are correct from the MR
