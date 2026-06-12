#!/usr/bin/env python
"""Build textbook passage and chapter-constraint inventories for item drafting."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
JSONL_DIR = ROOT / "rag_jsonl_output"
REPORTS_DIR = ROOT / "reports"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def clean_text(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text).strip()


def flatten(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, str):
        return [clean_text(value)] if clean_text(value) else []
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            parts.extend(flatten(item))
        return parts
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            parts.extend(flatten(value[key]))
        return parts
    return [str(value)]


def ordered_unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    output = []
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if key not in seen and value not in (None, "", [], {}):
            seen.add(key)
            output.append(value)
    return output


def split_unit_title(unit: str | None) -> str | None:
    if not unit:
        return None
    return re.sub(r"^\d+\.\s*", "", unit).strip()


def split_subunit_title(subunit: str | None) -> str | None:
    if not subunit:
        return None
    return re.sub(r"^\d+-\d+\.\s*", "", subunit).strip()


def is_reading_record(record: dict[str, Any]) -> bool:
    return record.get("activity_area") == "읽기" or record.get("object_type") == "reading"


def is_listening_record(record: dict[str, Any]) -> bool:
    return record.get("activity_area") == "듣기" or record.get("object_type") == "listening"


def build_passage_bank(textbook_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters: dict[tuple[int, str], int] = defaultdict(int)
    passages: list[dict[str, Any]] = []

    for record in textbook_records:
        candidates: list[tuple[str, str]] = []
        if is_reading_record(record):
            candidates.extend(("reading", text) for text in flatten(record.get("passages")))
        if is_listening_record(record):
            candidates.extend(("listening", text) for text in flatten(record.get("listening_scripts")))

        for skill, passage in candidates:
            passage = clean_text(passage)
            if not passage:
                continue
            unit_no = int(record.get("unit_no") or 0)
            counters[(unit_no, skill)] += 1
            note = ""
            if "\n\n" in passage or len(flatten(record.get("passages" if skill == "reading" else "listening_scripts"))) > 1:
                note = "Multiple source passages may have been split from one textbook record."
            passages.append(
                {
                    "id": f"passage_u{unit_no:02d}_{skill}_{counters[(unit_no, skill)]:03d}",
                    "unit_no": record.get("unit_no"),
                    "unit_title": split_unit_title(record.get("unit")),
                    "subunit_no": record.get("subunit_no"),
                    "subunit_title": split_subunit_title(record.get("subunit")),
                    "skill": skill,
                    "page": record.get("page"),
                    "activity_area": record.get("activity_area"),
                    "passage_type": "existing_textbook_passage",
                    "passage": passage,
                    "source_record_id": record.get("id"),
                    "available_question_prompts": flatten(record.get("questions")),
                    "linked_grammar_items": flatten(record.get("grammar_items")) + flatten(record.get("grammar_expressions")) + flatten(record.get("grammar_forms")),
                    "linked_vocabulary": flatten(record.get("vocabulary")),
                    "note": note,
                }
            )
    return passages


def build_constraints(
    textbook_records: list[dict[str, Any]],
    grammar_records: list[dict[str, Any]],
    vocab_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_unit: dict[int, dict[str, Any]] = {}

    def ensure(unit_no: int, unit_title: str | None = None) -> dict[str, Any]:
        if unit_no not in by_unit:
            by_unit[unit_no] = {
                "unit_no": unit_no,
                "unit_title": unit_title,
                "grammar_items": [],
                "grammar_forms": [],
                "vocabulary": [],
                "pages": [],
                "source_record_ids": [],
            }
        elif unit_title and not by_unit[unit_no].get("unit_title"):
            by_unit[unit_no]["unit_title"] = unit_title
        return by_unit[unit_no]

    for record in textbook_records:
        unit_no = record.get("unit_no")
        if not isinstance(unit_no, int):
            continue
        entry = ensure(unit_no, split_unit_title(record.get("unit")))
        entry["grammar_items"].extend(flatten(record.get("grammar_items")) + flatten(record.get("grammar_expressions")))
        entry["grammar_forms"].extend(flatten(record.get("grammar_forms")))
        entry["vocabulary"].extend(flatten(record.get("vocabulary")))
        entry["pages"].append(record.get("page"))
        entry["source_record_ids"].append(record.get("id"))

    for record in grammar_records:
        unit_no = record.get("unit_no")
        if not isinstance(unit_no, int):
            continue
        entry = ensure(unit_no)
        entry["grammar_items"].extend(flatten(record.get("grammar_items")))
        entry["grammar_forms"].extend(flatten(record.get("grammar_forms")))
        entry["pages"].append(record.get("page"))
        entry["source_record_ids"].append(record.get("id"))

    # The vocabulary index is not unit-tagged. Keep it out of per-unit constraints unless
    # later source data adds unit metadata.
    _ = vocab_records

    constraints = []
    for unit_no in sorted(by_unit):
        entry = by_unit[unit_no]
        entry["grammar_items"] = ordered_unique(entry["grammar_items"])
        entry["grammar_forms"] = ordered_unique(entry["grammar_forms"])
        entry["vocabulary"] = ordered_unique(entry["vocabulary"])
        entry["pages"] = sorted(value for value in set(entry["pages"]) if isinstance(value, int))
        entry["source_record_ids"] = ordered_unique(entry["source_record_ids"])
        constraints.append(entry)
    return constraints


def make_inventory(
    textbook_records: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    passage_counts: dict[int, dict[str, int]] = defaultdict(lambda: {"reading": 0, "listening": 0})
    for passage in passages:
        passage_counts[int(passage["unit_no"])][passage["skill"]] += 1

    units = []
    for constraint in constraints:
        unit_no = constraint["unit_no"]
        pages = constraint["pages"]
        units.append(
            {
                "unit_no": unit_no,
                "unit_title": constraint.get("unit_title"),
                "reading_passage_count": passage_counts[unit_no]["reading"],
                "listening_passage_count": passage_counts[unit_no]["listening"],
                "grammar_item_count": len(constraint["grammar_items"]),
                "vocabulary_count": len(constraint["vocabulary"]),
                "sample_grammar_items": constraint["grammar_items"][:8],
                "sample_vocabulary": constraint["vocabulary"][:12],
                "page_range": [min(pages), max(pages)] if pages else [],
            }
        )

    return {
        "source_files": {
            "textbook": "rag_jsonl_output/textbook.jsonl",
            "grammar": "rag_jsonl_output/grammar.jsonl",
            "vocab": "rag_jsonl_output/vocab.jsonl",
        },
        "summary": {
            "textbook_records": len(textbook_records),
            "passage_bank_records": len(passages),
            "reading_passages": sum(1 for item in passages if item["skill"] == "reading"),
            "listening_passages": sum(1 for item in passages if item["skill"] == "listening"),
            "chapter_constraints": len(constraints),
        },
        "units": units,
    }


def write_markdown(inventory: dict[str, Any], path: Path) -> None:
    lines = [
        "# Textbook Inventory",
        "",
        "Inventory for selecting existing textbook reading/listening passages and constraining item generation by unit grammar and vocabulary.",
        "",
        "## Summary",
        "",
    ]
    for key, value in inventory["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Unit Overview",
            "",
            "| unit_no | unit_title | reading passages | listening passages | grammar items | vocabulary | main grammar items | sample vocabulary | page range |",
            "|---:|---|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for unit in inventory["units"]:
        pages = unit["page_range"]
        page_range = f"{pages[0]}-{pages[1]}" if pages else ""
        grammar = "<br>".join(unit["sample_grammar_items"])
        vocab = "<br>".join(unit["sample_vocabulary"])
        lines.append(
            "| {unit_no} | {unit_title} | {reading} | {listening} | {grammar_count} | {vocab_count} | {grammar} | {vocab} | {pages} |".format(
                unit_no=unit["unit_no"],
                unit_title=unit.get("unit_title") or "",
                reading=unit["reading_passage_count"],
                listening=unit["listening_passage_count"],
                grammar_count=unit["grammar_item_count"],
                vocab_count=unit["vocabulary_count"],
                grammar=grammar.replace("|", "\\|"),
                vocab=vocab.replace("|", "\\|"),
                pages=page_range,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    textbook_records = read_jsonl(JSONL_DIR / "textbook.jsonl")
    grammar_records = read_jsonl(JSONL_DIR / "grammar.jsonl")
    vocab_records = read_jsonl(JSONL_DIR / "vocab.jsonl")

    passages = build_passage_bank(textbook_records)
    constraints = build_constraints(textbook_records, grammar_records, vocab_records)
    inventory = make_inventory(textbook_records, passages, constraints)

    write_jsonl(passages, JSONL_DIR / "passage_bank.jsonl")
    write_jsonl(constraints, JSONL_DIR / "chapter_constraints.jsonl")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "textbook_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(inventory, REPORTS_DIR / "textbook_inventory.md")

    print(json.dumps(inventory["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
