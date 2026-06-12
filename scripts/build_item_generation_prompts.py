#!/usr/bin/env python
"""Build prompt packages for passage-grounded item generation.

Prompt packages now use the question type schema derived from
sample_question.md/sample_question.jsonl instead of the temporary item_type
labels used in earlier experiments. The old --item-types option is accepted
only as a compatibility shim and is converted into question requests.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
JSONL_DIR = ROOT / "rag_jsonl_output"
DOCS_DIR = ROOT / "docs"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "item_generation_prompt_samples"
QUESTION_SCHEMA_PATH = DOCS_DIR / "question_type_schema.json"

EXPECTED_OUTPUT_SCHEMA = {
    "passage_id": "string",
    "unit": "integer",
    "skill": "reading|listening",
    "comprehension_type": "factual|inferential|evaluative",
    "comprehension_type_label": "사실적 문항|추론적 문항|평가적 문항",
    "stem_type": "string from docs/question_type_schema.json",
    "stem_template": "string from the selected stem_type templates or close variant",
    "question": "string",
    "options": ["string", "string", "string", "string"],
    "answer": "integer 1-4",
    "rationale": "string",
    "evidence": "string grounded in the passage",
    "grammar_constraints_used": ["string"],
    "vocabulary_constraints_used": ["string"],
    "difficulty": "easy|medium|hard",
    "difficulty_rationale": "string",
    "teacher_edit_suggestions": ["string"],
}

LEGACY_ITEM_TYPE_MAP = {
    "content_match": {"comprehension_type": "factual", "stem_type": "내용 일치"},
    "detail_info": {"comprehension_type": "factual", "stem_type": "세부 내용 파악"},
    "sequence": {"comprehension_type": "factual", "stem_type": "순서 파악"},
    "blank_completion": {"comprehension_type": "factual", "stem_type": "빈칸 내용 파악"},
    "main_idea": {"comprehension_type": "inferential", "stem_type": "주제 파악"},
    "inference": {"comprehension_type": "inferential", "stem_type": "내용 추론"},
}

STEM_TYPE_SLUGS = {
    "내용 일치": "content_match",
    "세부 내용 파악": "detail_info",
    "순서 파악": "sequence",
    "빈칸 내용 파악": "blank_completion",
    "주제 파악": "main_idea",
    "내용 추론": "content_inference",
    "이유/근거 추론": "reason_inference",
    "필자 태도 평가": "author_attitude",
    "심정/기분 평가": "feeling_evaluation",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def slug(text: str) -> str:
    if text in STEM_TYPE_SLUGS:
        return STEM_TYPE_SLUGS[text]
    value = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", text).strip("_").lower()
    return value or "prompt"


def infer_passage_title(passage: dict[str, Any]) -> str:
    text = str(passage.get("passage", "")).strip()
    first_sentence = re.split(r"(?<=[.!?。])\s+", text, maxsplit=1)[0]
    if len(first_sentence) > 80:
        first_sentence = first_sentence[:80].rstrip() + "..."
    return first_sentence or str(passage.get("id", ""))


def load_constraints(path: Path) -> dict[int, dict[str, Any]]:
    return {record["unit_no"]: record for record in read_jsonl(path)}


def load_question_schema(path: Path) -> list[dict[str, Any]]:
    schema = read_json(path)
    if not isinstance(schema, list):
        raise ValueError("question_type_schema.json must contain a list.")
    return schema


def schema_by_stem_type(schema: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["stem_type"]: record for record in schema}


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


def distribute_counts(total: int, passages: list[dict[str, Any]]) -> dict[str, int]:
    if not passages:
        return {}
    base = total // len(passages)
    remainder = total % len(passages)
    return {passage["id"]: base + (1 if index < remainder else 0) for index, passage in enumerate(passages)}


def normalize_question_request(
    request: dict[str, Any],
    schema_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    comprehension_type = request.get("comprehension_type")
    stem_type = request.get("stem_type") or request.get("question_type")
    if not stem_type:
        raise ValueError(f"Question request is missing stem_type: {request}")
    if stem_type not in schema_lookup:
        raise ValueError(f"Unknown stem_type in question plan: {stem_type}")
    schema_entry = schema_lookup[stem_type]
    if comprehension_type and comprehension_type != schema_entry["comprehension_type"]:
        raise ValueError(
            f"comprehension_type={comprehension_type} does not match stem_type={stem_type}"
        )
    return {
        "comprehension_type": schema_entry["comprehension_type"],
        "comprehension_type_label": schema_entry["comprehension_type_label"],
        "stem_type": stem_type,
        "stem_templates": schema_entry.get("stem_templates", []),
        "difficulty": request.get("difficulty") or schema_entry.get("default_difficulty", "medium"),
        "notes": request.get("notes") or schema_entry.get("notes", ""),
    }


def legacy_item_types_to_plan(item_types: str, schema_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    plan = []
    for item_type in [part.strip() for part in item_types.split(",") if part.strip()]:
        mapped = LEGACY_ITEM_TYPE_MAP.get(item_type)
        if not mapped:
            raise ValueError(f"Unsupported legacy item_type: {item_type}")
        plan.append(normalize_question_request(mapped, schema_lookup))
    return plan


def load_question_plan(args: argparse.Namespace, schema_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if args.question_plan:
        plan_path = Path(args.question_plan)
        raw_plan = read_json(plan_path)
        if not isinstance(raw_plan, list):
            raise ValueError("--question-plan must point to a JSON list.")
        return [normalize_question_request(record, schema_lookup) for record in raw_plan]

    if args.item_types:
        return legacy_item_types_to_plan(args.item_types, schema_lookup)

    stem_type = args.stem_type or args.question_type
    if not stem_type:
        if args.comprehension_type:
            matches = [
                entry
                for entry in schema_lookup.values()
                if entry["comprehension_type"] == args.comprehension_type
            ]
            if not matches:
                raise ValueError(f"No schema entry for comprehension_type={args.comprehension_type}")
            stem_type = matches[0]["stem_type"]
        else:
            stem_type = "내용 일치"

    request = {
        "comprehension_type": args.comprehension_type,
        "stem_type": stem_type,
        "difficulty": args.difficulty,
    }
    base_request = normalize_question_request(request, schema_lookup)
    return [base_request for _ in range(args.item_count)]


def expand_or_trim_plan(plan: list[dict[str, Any]], total: int) -> list[dict[str, Any]]:
    if total <= 0:
        raise ValueError("--item-count must be positive.")
    if not plan:
        raise ValueError("Question plan is empty.")
    if len(plan) == total:
        return plan
    expanded = []
    while len(expanded) < total:
        expanded.extend(plan)
    return expanded[:total]


def split_plan_by_passage(
    plan: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    total: int,
    passage_id: str | None,
) -> dict[str, list[dict[str, Any]]]:
    if passage_id:
        return {passages[0]["id"]: expand_or_trim_plan(plan, total)}
    counts = distribute_counts(total, passages)
    cursor = 0
    full_plan = expand_or_trim_plan(plan, total)
    result: dict[str, list[dict[str, Any]]] = {}
    for passage in passages:
        count = counts.get(passage["id"], 0)
        result[passage["id"]] = full_plan[cursor : cursor + count]
        cursor += count
    return result


def build_prompt(
    passage: dict[str, Any],
    constraints: dict[str, Any],
    question_requests: list[dict[str, Any]],
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
- Generate {len(question_requests)} Korean proficiency assessment item(s) for the selected existing textbook passage.
- Generate only question stems and answer options.
- Do not create a new passage.
- Do not modify the selected passage.
- Follow the question type system derived from sample_question.md.

Question requests:
{json.dumps(question_requests, ensure_ascii=False, indent=2)}

Passage metadata and text:
{json.dumps(passage_payload, ensure_ascii=False, indent=2)}

Unit grammar and vocabulary constraints:
{json.dumps(constraint_payload, ensure_ascii=False, indent=2)}

Constraints:
- factual questions check information explicitly stated in the passage.
- inferential questions ask what can be judged from passage evidence even when not directly stated.
- evaluative questions judge appropriateness, validity, attitude, purpose, feeling, or stance, but must not require background knowledge outside the passage.
- Use one of the listed stem_templates for each requested stem_type, or a very close variant.
- The correct answer must be clearly grounded in the passage.
- Distractors must be plausible but inconsistent with, unsupported by, or different from the passage.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Avoid excessive use of advanced grammar not taught in this unit.
- evidence must be a non-empty passage-grounded string.
- Return only valid JSON.

Expected output JSON schema:
{json.dumps(EXPECTED_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)}
"""


def build_packages(args: argparse.Namespace) -> list[dict[str, Any]]:
    passages = read_jsonl(JSONL_DIR / "passage_bank.jsonl")
    constraints_by_unit = load_constraints(JSONL_DIR / "chapter_constraints.jsonl")
    question_schema = load_question_schema(QUESTION_SCHEMA_PATH)
    schema_lookup = schema_by_stem_type(question_schema)
    question_plan = load_question_plan(args, schema_lookup)
    selected = select_passages(args, passages)
    plan_by_passage = split_plan_by_passage(question_plan, selected, args.item_count, args.passage_id)

    packages: list[dict[str, Any]] = []
    for passage in selected:
        question_requests = plan_by_passage.get(passage["id"], [])
        if not question_requests:
            continue
        constraints = constraints_by_unit.get(passage.get("unit_no"))
        if not constraints:
            raise ValueError(f"No chapter constraints found for unit {passage.get('unit_no')}")
        request_slug = "_".join(slug(request["stem_type"]) for request in question_requests[:3])
        prompt_id = f"prompt_{passage['id']}_{request_slug}_{len(question_requests)}items"
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
                "question_requests": question_requests,
                "item_count": len(question_requests),
                "prompt": build_prompt(passage, constraints, question_requests),
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
                f"- item_count: {package['item_count']}",
                "",
                "### Question Requests",
                "",
            ]
        )
        for index, request in enumerate(package["question_requests"], start=1):
            lines.append(
                f"{index}. {request['comprehension_type_label']} / {request['stem_type']} / {request['difficulty']}"
            )
        lines.extend(["", "### Prompt", "", "```text", package["prompt"].rstrip(), "```", ""])
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
    parser.add_argument("--question-type", help="Alias for --stem-type.")
    parser.add_argument("--comprehension-type", choices=["factual", "inferential", "evaluative"])
    parser.add_argument("--stem-type")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"])
    parser.add_argument("--question-plan", help="Path to a JSON question plan list.")
    parser.add_argument("--item-types", help="Deprecated compatibility option for old item_type labels.")
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
