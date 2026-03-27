Create a pull request for the current branch following this project's conventions.

## Steps

1. Run the following commands in parallel to understand the current state:
   - `git status` — untracked and modified files
   - `git log main..HEAD --oneline` — commits on this branch
   - `git diff main...HEAD --stat` — files changed vs main

2. Analyze all commits and diffs to determine:
   - The primary type of change: `feat` / `fix` / `refactor` / `docs` / `chore` / `test`
   - A concise title (under 70 characters) in the format `<type>: <description>`
   - The motivation and impact of the changes

3. Draft a PR body using **exactly** this template:

```
## Summary
- <bullet point 1>
- <bullet point 2>
- <bullet point 3 if needed>

## Changes
- <specific file or component change 1>
- <specific file or component change 2>
- ...

## Test plan
- [ ] <testing step 1>
- [ ] <testing step 2>
- [ ] <testing step 3 if needed>

🤖 Generated with [Claude Code](https://claude.ai/claude-code)
```

4. If the current branch has no remote tracking branch, push it first:
   ```
   git push -u origin HEAD
   ```

5. Create the PR with:
   ```
   gh pr create --title "<title>" --body "<body>"
   ```

6. Return the PR URL.

## Rules

- **Title**: Always use `<type>: <description>` (conventional commit style). Match the type to the dominant change.
- **Summary**: 2–4 bullets, each explaining *why* — not just *what*. Focus on intent and impact.
- **Changes**: List notable files/components changed, grouped logically if many.
- **Test plan**: At least 2 concrete steps a reviewer can follow to verify the changes.
- **Base branch**: Always target `main` unless the user specifies otherwise.
- **Draft**: Create as a regular PR unless the user says "draft".
- Do NOT include unrelated files or staged changes that were not part of the intended work.
