# Test design phase guide

## Goal

Define the tests before implementation so the workflow preserves intent and coverage.

## Trigger and instruction

Trigger: verified requirement artifacts exist and `current_phase=write_test_cases`
Instruction:
- convert each acceptance criterion into concrete tests
- cover happy path, edge cases, negative cases, and regression risks where relevant
- extend `traceability_matrix.md` so each requirement maps to one or more tests
- write or update `test_cases.md`
- update `task_state.xml` statuses and evidence fields

## Mandatory actions

1. Convert each acceptance criterion into one or more test cases.
2. Prefer the repository's existing testing style and folder layout.
3. Capture waived coverage explicitly with justification.
4. Keep identifiers stable so downstream phases can reference them.
5. Mark `test_cases.md` and `traceability_matrix.md` as `ready`, then `verified` after self-check.
6. Update `task_state.xml` to mark this phase complete before entering development.

## Minimum contents for test_cases.md

For each test case capture:
- test id
- linked requirement id
- purpose
- setup
- steps
- expected result
- implementation target or test file location if known
- coverage class: happy path, edge case, negative case, or regression

## Exit criteria

The phase passes only when:
- every requirement has one or more mapped tests
- important edge cases are covered or explicitly waived with justification
- the planned tests are specific enough to implement without re-reading the requirements from scratch
- `test_cases.md` and `traceability_matrix.md` are `verified`
