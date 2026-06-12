#!/usr/bin/env python
"""Build prompt packages for passage-grounded item generation.

This script does not call an LLM API. It packages selected textbook passages,
unit constraints, and item requests into JSONL and Markdown prompt files.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
JSONL_DIR = ROOT / "rag_jsonl_output"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "item_generation_prompt_samples"

EXPECTED_OUTPUT_SCHEMA = {
    "passage_id": "string",
    "unit_no": "integer",
    "skill": "reading|listening",
    "item_type": "string",
    "stem": "string",
    "options": {"1": "string", "2": "string", "3": "string", "4": "string"},
    "answer": "1|2|3|4",
    "rationale": {"1": "string", "2": "string", "3": "string", "4": "string"},
    "used_grammar": ["string"],
    "used_vocabulary": ["string"],
    "constraint_check": {
        "within_unit_grammar": "boolean",
        "within_unit_vocabulary": "boolean",
        "answer_grounded_in_passage": "boolean",
    },
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def slug(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣]+", "_", text).strip("_").lower()
    return value or "prompt"


def infer_passage_title(passage: dict[str, Any]) -> str:
    text = passage.get("passage", "").strip()
    first_sentence = re.split(r"(?<=[.!?。])\s+", text, maxsplit=1)[0]
    if len(first_sentence) > 80:
        first_sentence = first_sentence[:80].rstrip() + "..."
    return first_sentence or passage.get("id", "")


def parse_item_types(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def allocate_counts(total: int, item_types: list[str]) -> dict[str, int]:
    if not item_types:
        raise ValueError("--item-types must include at least one item type.")
    if len(item_types) == total:
        return dict(Counter(item_types))
    unique_types = list(dict.fromkeys(item_types))
    base = total // len(unique_types)
    remainder = total % len(unique_types)
    return {item_type: base + (1 if index < remainder else 0) for index, item_type in enumerate(unique_types)}


def distribute_counts(total: int, passages: list[dict[str, Any]]) -> dict[str, int]:
    if not passages:
        return {}
    base = total // len(passages)
    remainder = total % len(passages)
    return {passage["id"]: base + (1 if index < remainder else 0) for index, passage in enumerate(passages)}


def load_constraints(path: Path) -> dict[int, dict[str, Any]]:
    return {record["unit_no"]: record for record in read_jsonl(path)}


def select_passages(args: argparse.Namespace, passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if args.passage_id:
        matches = [passage for passage in passages if passage.get("id") == args.passage_id]
        if not matches:
            raise ValueError(f"No passage found for --passage-id {args.passage_id}")
        return matches

    selected = [
        passage
        for passage in passages
        if passage.get("usable_for_exam") is True
        and passage.get("priority") in {"high", "medium"}
        and (args.unit is None or passage.get("unit_no") == args.unit)
    ]
    if args.skill != "all":
        selected = [passage for passage in selected if passage.get("skill") == args.skill]
    selected.sort(key=lambda p: (p.get("unit_no") or 0, p.get("page") or 0, p.get("priority") != "high", p.get("id") or ""))
    if not selected:
        raise ValueError("No usable passages matched the selection criteria.")
    return selected


def build_prompt(
    passage: dict[str, Any],
    constraints: dict[str, Any],
    item_type: str,
    item_count: int,
) -> str:
    title = infer_passage_title(passage)
    passage_payload = {
        "unit_no": passage.get("unit_no"),
        "unit_title": passage.get("unit_title"),
        "passage_id": passage.get("id"),
        "skill": passage.get("skill"),
        "source_activity": passage.get("source_activity"),
        "candidate_type": passage.get("candidate_type"),
        "priority": passage.get("priority"),
        "passage_title": title,
        "passage_text": passage.get("passage"),
    }
    constraint_payload = {
        "unit_no": constraints.get("unit_no"),
        "unit_title": constraints.get("unit_title"),
        "grammar_items": constraints.get("grammar_items", []),
        "grammar_forms": constraints.get("grammar_forms", []),
        "vocabulary": constraints.get("vocabulary", []),
    }
    return f"""You are an assistant for Korean language teachers.

Task:
- Generate {item_count} Korean proficiency assessment item(s) for the selected existing textbook passage.
- Item type: {item_type}
- Generate only question stems and answer options.
- Do not create a new passage.
- Do not modify the selected passage.

Passage metadata and text:
{json.dumps(passage_payload, ensure_ascii=False, indent=2)}

Unit grammar and vocabulary constraints:
{json.dumps(constraint_payload, ensure_ascii=False, indent=2)}

Constraints:
- The correct answer must be clearly grounded in the passage.
- Distractors must be plausible but inconsistent with, unsupported by, or different from the passage.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Avoid excessive use of advanced grammar not taught in this unit.
- Return only valid JSON.

Expected output JSON schema:
{json.dumps(EXPECTED_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)}
"""


def build_packages(args: argparse.Namespace) -> list[dict[str, Any]]:
    passages = read_jsonl(JSONL_DIR / "passage_bank.jsonl")
    constraints_by_unit = load_constraints(JSONL_DIR / "chapter_constraints.jsonl")
    item_types = parse_item_types(args.item_types)
    selected = select_passages(args, passages)
    passage_counts = {selected[0]["id"]: args.item_count} if args.passage_id else distribute_counts(args.item_count, selected)

    packages: list[dict[str, Any]] = []
    for passage in selected:
        passage_item_count = passage_counts.get(passage["id"], 0)
        if passage_item_count <= 0:
            continue
        per_type_counts = allocate_counts(passage_item_count, item_types)
        constraints = constraints_by_unit.get(passage.get("unit_no"))
        if not constraints:
            raise ValueError(f"No chapter constraints found for unit {passage.get('unit_no')}")
        for item_type, count in per_type_counts.items():
            if count <= 0:
                continue
            prompt_id = f"prompt_{passage['id']}_{slug(item_type)}_{count}items"
            packages.append(
                {
                    "prompt_id": prompt_id,
                    "unit": passage.get("unit_no"),
                    "passage_id": passage.get("id"),
                    "skill": passage.get("skill"),
                    "source_activity": passage.get("source_activity"),
                    "candidate_type": passage.get("candidate_type"),
                    "priority": passage.get("priority"),
                    "passage_title": infer_passage_title(passage),
                    "item_types": [item_type],
                    "item_count": count,
                    "prompt": build_prompt(passage, constraints, item_type, count),
                    "expected_output_schema": EXPECTED_OUTPUT_SCHEMA,
                }
            )
    return packages


def write_markdown(packages: list[dict[str, Any]], path: Path) -> None:
    lines = ["# Item Generation Prompt Packages", ""]
    for package in packages:
        lines.extend(
            [
                f"## {package['prompt_id']}",
                "",
                f"- unit: {package['unit']}",
                f"- passage_id: `{package['passage_id']}`",
                f"- skill: {package['skill']}",
                f"- source_activity: {package['source_activity']}",
                f"- candidate_type: {package['candidate_type']}",
                f"- priority: {package['priority']}",
                f"- item_types: {', '.join(package['item_types'])}",
                f"- item_count: {package['item_count']}",
                "",
                "### Prompt",
                "",
                "```text",
                package["prompt"].rstrip(),
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def output_stem(args: argparse.Namespace, packages: list[dict[str, Any]]) -> str:
    if args.passage_id:
        return f"prompts_{args.passage_id}"
    unit = f"u{args.unit:02d}" if args.unit is not None else "all_units"
    skill = args.skill
    return f"prompts_{unit}_{skill}_{args.item_count}items"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build item generation prompt packages from passage bank.")
    parser.add_argument("--passage-id")
    parser.add_argument("--unit", type=int)
    parser.add_argument("--skill", choices=["reading", "listening", "all"], default="all")
    parser.add_argument("--item-count", type=int, required=True)
    parser.add_argument("--item-types", required=True, help="Comma-separated item types.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if args.item_count <= 0:
        raise ValueError("--item-count must be positive.")
    packages = build_packages(args)
    if not packages:
        raise ValueError("No prompt packages were created.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(args, packages)
    jsonl_path = args.output_dir / f"{stem}.jsonl"
    md_path = args.output_dir / f"{stem}.md"
    write_jsonl(packages, jsonl_path)
    write_markdown(packages, md_path)

    print(json.dumps(
        {
            "packages": len(packages),
            "total_requested_items": sum(package["item_count"] for package in packages),
            "jsonl": str(jsonl_path),
            "markdown": str(md_path),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
