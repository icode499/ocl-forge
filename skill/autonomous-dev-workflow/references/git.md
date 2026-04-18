# Git commit phase guide

## Goal

Create a clean local commit that reflects the completed work and follows the provided commit policy.

## Trigger and instruction

Trigger: verified passing test evidence exists, or the user explicitly allowed a checkpoint commit, and `current_phase=git_commit`
Instruction:
- inspect `git status`
- confirm only intended files will be committed
- write `commit_message.txt`
- commit locally
- record the commit hash and final workflow status in `task_state.xml`

## Mandatory actions

1. Review `git status` and confirm only intended files will be staged.
2. Cross-check staged files against `change_log.md`.
3. Confirm `test_results.md` shows a pass before staging unless checkpoint commit permission is explicit.
4. Write `commit_message.txt` before running `git commit`.
5. Use the user's commit policy for format, scope, and issue references.
6. Record the commit hash in `task_state.xml` and mark the workflow complete.

## Suggested commit message structure

- first line: concise summary following the policy
- optional body: what changed, why, and test evidence

## Exit criteria

The phase passes only when:
- staged content matches intended task output
- local commit succeeds
- `commit_message.txt` is `verified`
- `task_state.xml` contains the commit hash and marks workflow complete

Entry to this phase does not require `commit_message.txt` yet; that file is created during the phase.
