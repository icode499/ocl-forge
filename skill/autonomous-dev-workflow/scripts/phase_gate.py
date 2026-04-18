#!/usr/bin/env python3
"""Enforce evidence-based phase entry and exit checks for task_state.xml."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PHASE_ORDER = [
    "read_requirements",
    "write_test_cases",
    "code_development",
    "run_tests_and_debug",
    "git_commit",
]

ENTRY_REQUIREMENTS = {
    "read_requirements": [],
    "write_test_cases": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md"],
    "code_development": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md", "test_cases.md"],
    "run_tests_and_debug": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md", "test_cases.md", "change_log.md"],
    "git_commit": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md", "test_cases.md", "change_log.md", "test_results.md", "debug_log.md"],
}

EXIT_REQUIREMENTS = {
    "read_requirements": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md"],
    "write_test_cases": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md", "test_cases.md"],
    "code_development": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md", "test_cases.md", "change_log.md"],
    "run_tests_and_debug": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md", "test_cases.md", "change_log.md", "test_results.md", "debug_log.md"],
    "git_commit": ["requirements_summary.md", "acceptance_criteria.md", "traceability_matrix.md", "test_cases.md", "change_log.md", "test_results.md", "debug_log.md", "commit_message.txt"],
}

NEXT_PHASE = {
    "read_requirements": "write_test_cases",
    "write_test_cases": "code_development",
    "code_development": "run_tests_and_debug",
    "run_tests_and_debug": "git_commit",
    "git_commit": "done",
}

ALLOWED_STATUSES = {"ready", "verified"}


def artifact_statuses(root: ET.Element) -> dict[str, str]:
    return {
        artifact.get("name"): artifact.get("status", "missing")
        for artifact in root.findall("./artifacts/artifact")
        if artifact.get("name")
    }


def current_phase(root: ET.Element) -> str:
    node = root.find("current_phase")
    return (node.text or "").strip() if node is not None and node.text else ""


def rollback_target(root: ET.Element) -> str:
    node = root.find("rollback_target")
    return (node.text or "").strip() if node is not None and node.text else ""


def evidence_map(root: ET.Element) -> dict[str, str]:
    return {
        item.get("key"): (item.text or "").strip()
        for item in root.findall("./completion_evidence/item")
        if item.get("key")
    }


def phase_index(name: str) -> int:
    return PHASE_ORDER.index(name)


def has_nonempty_text(root: ET.Element, tag: str) -> bool:
    node = root.find(tag)
    return node is not None and bool((node.text or "").strip())


def validate_phase_alignment(root: ET.Element, requested_phase: str) -> str | None:
    active_phase = current_phase(root)
    rollback = rollback_target(root)
    if active_phase and requested_phase == active_phase:
        return None
    if rollback and requested_phase != rollback and phase_index(requested_phase) > phase_index(rollback):
        return f"rollback_required={rollback}"
    if active_phase and requested_phase != active_phase:
        return f"current_phase={active_phase}"
    return None


def missing_required(statuses: dict[str, str], names: list[str]) -> list[str]:
    return [name for name in names if statuses.get(name) not in ALLOWED_STATUSES]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="task_state.xml")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--mode", choices=["entry", "exit"], required=True)
    args = parser.parse_args()

    root = ET.parse(Path(args.state)).getroot()
    statuses = artifact_statuses(root)
    evidence = evidence_map(root)

    alignment_error = validate_phase_alignment(root, args.phase)
    if alignment_error:
        print(f"FAIL {alignment_error} phase={args.phase}")
        sys.exit(1)

    required = ENTRY_REQUIREMENTS[args.phase] if args.mode == "entry" else EXIT_REQUIREMENTS[args.phase]
    missing = missing_required(statuses, required)
    if missing:
        print("FAIL missing_artifacts=" + ",".join(missing))
        sys.exit(1)

    if args.mode == "exit":
        if args.phase == "read_requirements" and evidence.get("requirements_verified") != "true":
            print("FAIL evidence=requirements_verified")
            sys.exit(1)
        if args.phase == "write_test_cases" and evidence.get("tests_planned") != "true":
            print("FAIL evidence=tests_planned")
            sys.exit(1)
        if args.phase == "code_development" and evidence.get("implementation_complete") != "true":
            print("FAIL evidence=implementation_complete")
            sys.exit(1)
        if args.phase == "run_tests_and_debug" and evidence.get("tests_status") not in {"pass", "blocked"}:
            print("FAIL evidence=tests_status")
            sys.exit(1)
        if args.phase == "run_tests_and_debug" and evidence.get("tests_status") == "blocked":
            rollback = rollback_target(root)
            if rollback not in {"read_requirements", "write_test_cases", "run_tests_and_debug"}:
                print("FAIL evidence=rollback_target")
                sys.exit(1)
            if not has_nonempty_text(root, "rollback_reason"):
                print("FAIL evidence=rollback_reason")
                sys.exit(1)
        if args.phase == "git_commit":
            commit_hash = (root.findtext("commit_hash") or "").strip()
            if statuses.get("commit_message.txt") not in ALLOWED_STATUSES:
                print("FAIL missing_artifacts=commit_message.txt")
                sys.exit(1)
            if not commit_hash:
                print("FAIL evidence=commit_hash")
                sys.exit(1)
        if args.phase == "run_tests_and_debug" and evidence.get("tests_status") == "blocked":
            print(f"PASS next_phase={rollback_target(root)}")
            return
        print(f"PASS next_phase={NEXT_PHASE[args.phase]}")
        return

    if args.phase == "git_commit":
        checkpoint_allowed = evidence.get("checkpoint_commit_allowed", "false") == "true"
        tests_status = evidence.get("tests_status")
        if not checkpoint_allowed and tests_status != "pass":
            print("FAIL evidence=tests_status_pass_required")
            sys.exit(1)

    print("PASS")


if __name__ == "__main__":
    main()
