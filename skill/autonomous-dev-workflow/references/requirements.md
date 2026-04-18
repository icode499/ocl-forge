# Requirements phase guide

## Goal

Transform raw requirements text into a stable execution contract that later phases can trust without re-reading chat history.

## Trigger and instruction

Trigger: `task_state.xml` shows `current_phase=read_requirements`
Instruction:
- read the full requirements source before creating tests or code
- extract atomic acceptance criteria into `acceptance_criteria.md`
- summarize scope, constraints, edge cases, and assumptions in `requirements_summary.md`
- create initial requirement rows in `traceability_matrix.md`
- update `task_state.xml` statuses and evidence fields

## Mandatory actions

1. Read the entire requirements source before writing code or tests.
2. Extract explicit acceptance criteria as atomic bullets with stable identifiers.
3. Identify implicit constraints from wording such as performance, compatibility, migration, safety, and backward compatibility.
4. Log ambiguities as assumptions instead of silently guessing.
5. Create or update `requirements_summary.md`, `acceptance_criteria.md`, and `traceability_matrix.md`.
6. Mark these artifacts as `ready`, then `verified` after self-check.
7. Update `task_state.xml` with discovered scope, assumptions, and the next phase.

## Minimum contents

### requirements_summary.md
- problem statement
- in-scope behavior
- out-of-scope behavior
- constraints and non-functional requirements
- edge cases
- assumptions
- touched modules or suspected repo areas

### acceptance_criteria.md
- one requirement id per criterion
- concise pass condition
- notes for ambiguity or special handling

## Exit criteria

The phase passes only when:
- every requirement is represented in `acceptance_criteria.md`
- assumptions are explicit
- at least one traceability row exists per requirement
- `requirements_summary.md`, `acceptance_criteria.md`, and `traceability_matrix.md` are `verified`
- no coding has started
