---
name: autonomous-dev-workflow
description: Use when a coding task starts from requirements text plus a repository and must be executed autonomously with durable phase state, explicit artifacts, rollback handling, test evidence, and an optional local commit across a long-running terminal workflow.
---

# Autonomous Dev Workflow

## Overview

Use this skill to complete a coding task autonomously without losing process discipline during long runs. Treat `task_state.xml` as the single source of truth. Treat phase transitions as evidence checks, not memory-based decisions. Write required artifacts to disk so later phases read files, not chat history.

## Core operating rules

- Create or refresh `task_state.xml` before doing substantive work.
- Re-read `task_state.xml` at the start of every phase, after every failure, and before any commit.
- Use this fixed phase order unless an explicit rollback rule sends work backward:
  1. `read_requirements`
  2. `write_test_cases`
  3. `code_development`
  4. `run_tests_and_debug`
  5. `git_commit`
- Do not enter a phase until its entry gate passes.
- Do not leave a phase until its exit gate passes.
- Update `task_state.xml` after every material action: phase start, artifact completion, failure, rollback, test result, or commit.
- Write required artifacts to disk instead of relying on conversational memory.
- Do not create a final local commit until passing test evidence is recorded, unless the user explicitly requested a checkpoint commit despite failures.
- Do not push unless the user explicitly asked for a push.

## Required runtime inputs

Every run should have these inputs or derive them immediately:

- requirements text
- repository path
- test command
- commit policy

If any input is missing, record a grounded assumption in `task_state.xml` before proceeding.

## Required artifacts

Maintain these files in the working directory or a clearly named task subdirectory:

- `task_state.xml`
- `requirements_summary.md`
- `acceptance_criteria.md`
- `traceability_matrix.md`
- `test_cases.md`
- `change_log.md`
- `test_results.md`
- `debug_log.md`
- `commit_message.txt`

Mark artifact status in `task_state.xml` as one of `missing`, `draft`, `ready`, or `verified`.

## Standard execution loop

For every phase:

1. Read `task_state.xml`.
2. Run `python3 scripts/phase_gate.py --state task_state.xml --phase <phase> --mode entry`.
3. Read the phase reference file.
4. Execute only actions allowed in that phase.
5. Write or update the required artifacts.
6. Record evidence, assumptions, failures, or rollback reasons in `task_state.xml`.
7. Run `python3 scripts/phase_gate.py --state task_state.xml --phase <phase> --mode exit`.
8. Advance only if the exit gate passes.

## Workflow sequence

### STEP 1: Initialize durable state

- Run `python3 scripts/init_task_state.py --requirements-file <path>|--requirements-text <text> --repo <path> [--test-command <cmd>] [--commit-policy <text>] [--output task_state.xml]`.
- If `task_state.xml` already exists, refresh inputs but preserve evidence, blockers, and artifact statuses when still valid.
- If `test command` or `commit policy` is still unknown, leave it blank and record a grounded assumption in `task_state.xml`.
- Confirm current phase, rollback target, hard rules, and required evidence from the state file before acting.

### STEP 2: Read requirements

Consult `references/requirements.md`.

Required outputs:
- `requirements_summary.md`
- `acceptance_criteria.md`
- requirements rows in `traceability_matrix.md`
- updated `task_state.xml`

Entry gate focus:
- phase must be `read_requirements`

Exit gate focus:
- requirements summarized
- acceptance criteria extracted
- scope, constraints, edge cases, and assumptions recorded
- no coding has started

### STEP 3: Write test cases

Consult `references/testing.md`.

Required outputs:
- `test_cases.md`
- expanded `traceability_matrix.md`
- updated `task_state.xml`

Entry gate focus:
- verified requirements artifacts exist

Exit gate focus:
- each requirement maps to one or more tests
- happy path, edge cases, negative cases, and regression risks are covered or explicitly waived
- development is still blocked until this phase is verified

### STEP 4: Develop code

Consult `references/coding.md`.

Required outputs:
- code changes in the repo
- `change_log.md`
- updated `task_state.xml`

Entry gate focus:
- verified requirements and test-planning artifacts exist

Exit gate focus:
- implementation matches traced requirements
- changed files are logged
- unresolved requirement gaps are either fixed or cause rollback

### STEP 5: Run tests and debug

Consult `references/debugging.md`.

Required outputs:
- `test_results.md`
- `debug_log.md`
- updated `change_log.md`
- updated `task_state.xml`

Entry gate focus:
- development evidence exists

Exit gate focus:
- required test command passed and evidence is recorded, or
- blocker is recorded with reproducible evidence and rollback target

### STEP 6: Prepare commit and commit locally

Consult `references/git.md`.

Required outputs:
- `commit_message.txt`
- local git commit
- final updates to `task_state.xml`

Entry gate focus:
- verified passing test evidence exists unless checkpoint commit is explicitly allowed
- `commit_message.txt` is not required until this phase is executed

Exit gate focus:
- staged content matches intended task output
- `commit_message.txt` is written and verified
- local commit succeeds
- `task_state.xml` records the commit hash and marks the workflow complete

## Rollback rules

- If a later phase discovers missing or invalid requirements, roll back to `read_requirements`.
- If development or debugging exposes insufficient test coverage, roll back to `write_test_cases`.
- If commit preparation reveals missing passing evidence, roll back to `run_tests_and_debug`.
- If `run_tests_and_debug` ends in a blocker, keep the failure evidence, set a rollback target, and advance to that rollback target rather than to `git_commit`.
- Record every rollback in `task_state.xml` with `rollback_target`, `rollback_reason`, and the invalidated artifacts.
- After rollback, re-verify downstream artifacts before reusing them.

## Reporting contract

When reporting progress or completion, summarize in this order:

1. current phase or final status
2. verified requirements and assumptions
3. test coverage completed or still missing
4. code/files changed
5. exact test command run and result
6. rollback or blocker status if any
7. commit message and commit hash if created

## Resources

- `references/requirements.md` for requirement extraction and assumptions policy
- `references/testing.md` for test design, traceability, and coverage rules
- `references/coding.md` for implementation guardrails and rollback triggers
- `references/debugging.md` for the evidence-driven test and fix loop
- `references/git.md` for commit policy enforcement
- `references/output_templates.md` for artifact templates
- `assets/task_state_template.xml` for the durable state schema
- `scripts/init_task_state.py` to bootstrap `task_state.xml`
- `scripts/phase_gate.py` to enforce evidence-based entry and exit checks
