---
name: ship
description: Commit, push, ensure CI passes (fix if needed), and request review. Use when you want to ship your current changes — commit, create or update a PR, verify CI, and request a code review.
argument-hint: [optional commit message]
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, Agent
user-invocable: true
---

# Ship: Commit → PR → CI → Review

Automate the full shipping flow for the current branch.

## Arguments

- `$ARGUMENTS`: Optional commit message. If omitted, generate one from the diff.

## Steps

### 1. Commit

1. Run `git status` (never `-uall`) and `git diff --stat` to understand staged/unstaged changes.
2. If there are no changes, inform the user and stop.
3. Stage relevant files (`git add` by specific file — never `git add -A`). Do NOT commit `.env`, credentials, or secrets.
4. Draft a concise commit message:
   - If `$ARGUMENTS` is provided, use it as the basis.
   - Otherwise, summarize the diff (new feature → `feat:`, bug fix → `fix:`, etc.).
   - End with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`.
5. Create the commit via HEREDOC.

### 2. Push & PR

1. Check if a PR already exists for the current branch:
   ```bash
   gh pr list --head "$(git branch --show-current)" --json number,url
   ```
2. **PR exists** → `git push`.
3. **No PR** → `git push -u origin HEAD`, then create a PR:
   ```bash
   gh pr create --title "<title>" --body "$(cat <<'EOF'
   ## Summary
   <bullets>

   ## Test plan
   - [ ] ...

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```
4. Print the PR URL.

### 3. CI check & fix loop

1. Wait a few seconds, then poll CI status:
   ```bash
   gh pr checks <number> --watch --fail-fast
   ```
   Use `--watch` with a timeout of 10 minutes.
2. If **all checks pass** → proceed to step 4.
3. If **a check fails**:
   a. Read the failing check logs:
      ```bash
      gh run view <run-id> --log-failed
      ```
   b. Diagnose and fix the issue locally (formatting, lint, type errors, test failures, etc.).
      - For formatter issues: run the project's format command (e.g., `npm run format:check` / `prettier --write`).
      - For lint issues: run the project's lint command and fix violations.
      - For type errors: run the project's typecheck command and fix.
      - For test failures: read test output, fix the code, re-run locally to confirm.
   c. Commit the fix (new commit, not amend) with a descriptive message.
   d. Push and go back to step 3.1 (re-check CI). Maximum 3 fix attempts — after that, report the failure to the user.

### 4. Request review

1. Add a PR comment requesting review with `@codex`:
   ```bash
   gh pr comment <number> --body "@codex レビューをお願いします。"
   ```

## Important rules

- Never force-push or amend published commits.
- Never skip hooks (`--no-verify`).
- Never commit secrets or `.env` files.
- If the branch has no remote tracking, use `git push -u origin HEAD`.
- Keep commit messages in the language matching the codebase convention (this project uses Japanese comments).
- If CI fails more than 3 times, stop and report the remaining issues to the user.
