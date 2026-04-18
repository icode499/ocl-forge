#!/usr/bin/env python3
"""Initialize or refresh task_state.xml for the autonomous dev workflow skill."""

from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


PHASES = [
    "read_requirements",
    "write_test_cases",
    "code_development",
    "run_tests_and_debug",
    "git_commit",
]

ARTIFACTS = [
    "requirements_summary.md",
    "acceptance_criteria.md",
    "traceability_matrix.md",
    "test_cases.md",
    "change_log.md",
    "test_results.md",
    "debug_log.md",
    "commit_message.txt",
]


def load_requirements(args: argparse.Namespace) -> str:
    if args.requirements_file:
        return Path(args.requirements_file).read_text(encoding="utf-8")
    return args.requirements_text or ""


def ensure_template(output_path: Path) -> ET.ElementTree:
    if output_path.exists():
        return ET.parse(output_path)
    template_path = Path(__file__).resolve().parent.parent / "assets" / "task_state_template.xml"
    shutil.copyfile(template_path, output_path)
    return ET.parse(output_path)


def set_text(parent: ET.Element, tag: str, value: str) -> None:
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = value


def ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    return node


def append_assumption(parent: ET.Element, key: str, value: str) -> None:
    existing = parent.find(f"./assumption[@key='{key}']")
    if existing is not None:
        existing.text = value
        return
    ET.SubElement(parent, "assumption", {"key": key}).text = value


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--requirements-file")
    group.add_argument("--requirements-text")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--test-command", default="")
    parser.add_argument("--commit-policy", default="")
    parser.add_argument("--output", default="task_state.xml")
    args = parser.parse_args()

    requirements_text = load_requirements(args)
    output_path = Path(args.output).resolve()
    existed = output_path.exists()
    tree = ensure_template(output_path)
    root = tree.getroot()

    inputs = ensure_child(root, "inputs")
    source_value = args.requirements_file or "inline-requirements"
    set_text(inputs, "requirements_source", source_value)
    set_text(inputs, "repo_path", args.repo)
    previous_test_command = root.findtext("./inputs/test_command") or ""
    previous_commit_policy = root.findtext("./inputs/commit_policy") or ""
    test_command = args.test_command or previous_test_command
    commit_policy = args.commit_policy or previous_commit_policy
    set_text(inputs, "test_command", test_command)
    set_text(inputs, "commit_policy", commit_policy)

    if not existed:
        set_text(root, "current_phase", "read_requirements")
        set_text(root, "phase_status", "in_progress")
        set_text(root, "rollback_target", "")
        set_text(root, "rollback_reason", "")

    notes = root.find("requirements_excerpt")
    if notes is None:
        notes = ET.SubElement(root, "requirements_excerpt")
    notes.text = requirements_text[:4000]

    phases = ensure_child(root, "phases")
    existing = {p.get("name"): p for p in phases.findall("phase")}
    for phase in PHASES:
        node = existing.get(phase)
        if node is None:
            node = ET.SubElement(phases, "phase", {"name": phase, "status": "pending"})
        elif node.get("status") is None:
            node.set("status", "pending")

    artifacts = ensure_child(root, "artifacts")
    existing_artifacts = {a.get("name"): a for a in artifacts.findall("artifact")}
    for artifact_name in ARTIFACTS:
        node = existing_artifacts.get(artifact_name)
        if node is None:
            ET.SubElement(artifacts, "artifact", {"name": artifact_name, "status": "missing"})
        elif node.get("status") is None:
            node.set("status", "missing")

    completion = ensure_child(root, "completion_evidence")
    evidence_defaults = {
        "requirements_verified": "",
        "tests_planned": "",
        "implementation_complete": "",
        "tests_status": "",
        "checkpoint_commit_allowed": "false",
    }
    seen = {item.get("key"): item for item in completion.findall("item")}
    for key, default in evidence_defaults.items():
        node = seen.get(key)
        if node is None:
            node = ET.SubElement(completion, "item", {"key": key})
        if node.text is None:
            node.text = default

    for tag in ["assumptions", "failed_checks", "blockers"]:
        ensure_child(root, tag)

    assumptions = ensure_child(root, "assumptions")
    if not test_command:
        append_assumption(
            assumptions,
            "test_command",
            "No explicit test command was provided. Derive one from the repository before running tests.",
        )
    if not commit_policy:
        append_assumption(
            assumptions,
            "commit_policy",
            "No explicit commit policy was provided. Use the repository default unless the user specifies otherwise.",
        )

    tree.write(output_path, encoding="utf-8", xml_declaration=False)
    print(output_path)


if __name__ == "__main__":
    main()
