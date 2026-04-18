# Test and debugging phase guide

## Goal

Run the required test command, debug failures methodically, and produce reproducible passing evidence.

## Trigger and instruction

Trigger: development evidence exists and `current_phase=run_tests_and_debug`
Instruction:
- run the required test command or document why a narrower command is justified first
- capture exact command, failures, fixes, and final result in `test_results.md`
- keep a chronological debug narrative in `debug_log.md`
- if failures expose weak tests or misunderstood requirements, record rollback and go back

## Mandatory loop

1. Run the required test command exactly, or document why a narrower command is needed first.
2. Capture stdout/stderr or a concise summary in `test_results.md`.
3. If the command fails, identify the smallest plausible root cause.
4. Patch minimally.
5. Record the hypothesis, change, and result in `debug_log.md`.
6. Re-run the affected tests and then the required command.
7. Repeat until pass or a grounded blocker is recorded.

## Required contents

### test_results.md
- exact command run
- environment notes if relevant
- failures observed
- root cause summary for each fix
- final passing result or blocker

### debug_log.md
- timestamped step or sequence number
- failing symptom
- hypothesis
- patch summary
- rerun outcome

## Exit criteria

The phase passes only when:
- the required test command succeeds and `test_results.md` is `verified`, or
- a blocker is documented with enough evidence that a human can reproduce it, `rollback_target` is set to an earlier recovery phase, and `rollback_reason` is recorded
- `debug_log.md` is `ready` or `verified`

If the phase exits with `tests_status=blocked`, the workflow should resume from the recorded rollback target rather than continue to `git_commit`.

A local git commit is allowed only after a passing result is recorded unless the user explicitly asked for a checkpoint commit despite failures.
