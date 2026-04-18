# Development phase guide

## Goal

Implement the smallest correct change set that satisfies the traced requirements and planned tests.

## Trigger and instruction

Trigger: verified requirements and test-planning artifacts exist and `current_phase=code_development`
Instruction:
- re-read `task_state.xml`, `requirements_summary.md`, `acceptance_criteria.md`, `traceability_matrix.md`, and `test_cases.md`
- implement the minimum code and test changes needed
- update `change_log.md`
- do not commit
- if a requirement or test gap appears, roll back instead of improvising

## Mandatory actions

1. Keep changes scoped to the task.
2. Match existing project conventions unless the requirements demand otherwise.
3. Update or add tests alongside production code as appropriate.
4. Record major edits and touched files in `change_log.md`.
5. Mark `change_log.md` as `ready` after meaningful edits, then `verified` when the file list and rationale are complete.
6. If implementation reveals a missing requirement, update `task_state.xml` and roll back to `read_requirements`.
7. If implementation reveals missing or weak tests, update `task_state.xml` and roll back to `write_test_cases`.

## Guardrails

- Do not broaden scope without recording the reason.
- Do not rewrite unrelated code for style alone.
- Prefer reversible, reviewable patches.
- Keep the repo buildable if possible after each meaningful patch.

## Exit criteria

The phase passes only when:
- the required code and tests are written
- changed files are logged in `change_log.md`
- unresolved requirement gaps are absent, or rollback has been recorded
- `change_log.md` is `verified`
