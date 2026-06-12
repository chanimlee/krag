#!/usr/bin/env python
"""Validate JSONL outputs for the Korean proficiency RAG dataset."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_FILES = {
    "textbook": "textbook.jsonl",
    "vocab": "vocab.jsonl",
    "grammar": "grammar.jsonl",
    "textbook_knowledge": "textbook_knowledge.jsonl",
    "sample_question": "sample_question.jsonl",
}

SAMPLE_REQUIRED_FIELDS = {
    "answer",
    "answer_generated",
    "answer_verified",
    "rationale",
    "rationale_generated",
    "rationale_verified",
}

OPTION_KEYS = {"1", "2", "3", "4"}


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return records, [{"line": None, "error": "file_not_found"}]

    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                errors.append({"line": line_no, "error": "blank_line"})
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append({"line": line_no, "error": "json_decode_error", "detail": str(exc)})
                continue
            if not isinstance(value, dict):
                errors.append({"line": line_no, "error": "record_not_object"})
                continue
            records.append(value)
    return records, errors


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for item in value.values():
            strings.extend(walk_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(walk_strings(item))
        return strings
    return []


def validate_id(records: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [record.get("id") for record in records]
    missing = [idx for idx, value in enumerate(ids, start=1) if not isinstance(value, str) or not value.strip()]
    counts = Counter(value for value in ids if isinstance(value, str) and value.strip())
    duplicated = sorted(value for value, count in counts.items() if count > 1)
    return {"missing_lines": missing, "duplicates": duplicated}


def validate_text(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    empty: list[dict[str, Any]] = []
    for line_no, record in enumerate(records, start=1):
        text = record.get("text")
        if not isinstance(text, str) or not text.strip():
            empty.append({"line": line_no, "id": record.get("id"), "field": "text"})
    return empty


def validate_sample_questions(records: list[dict[str, Any]]) -> dict[str, Any]:
    missing_fields: list[dict[str, Any]] = []
    bad_options: list[dict[str, Any]] = []
    for line_no, record in enumerate(records, start=1):
        missing = sorted(field for field in SAMPLE_REQUIRED_FIELDS if field not in record)
        if missing:
            missing_fields.append({"line": line_no, "id": record.get("id"), "missing": missing})

        options = record.get("options")
        if not isinstance(options, dict):
            bad_options.append({"line": line_no, "id": record.get("id"), "error": "options_not_object"})
            continue
        keys = set(options)
        empty_values = sorted(key for key, value in options.items() if not isinstance(value, str) or not value.strip())
        if keys != OPTION_KEYS or empty_values:
            bad_options.append(
                {
                    "line": line_no,
                    "id": record.get("id"),
                    "keys": sorted(keys),
                    "empty_values": empty_values,
                }
            )
    return {"missing_fields": missing_fields, "bad_options": bad_options}


def validate_no_vacab(records_by_name: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for name, records in records_by_name.items():
        for line_no, record in enumerate(records, start=1):
            if any("vacab.md" in value for value in walk_strings(record)):
                hits.append({"file": EXPECTED_FILES[name], "line": line_no, "id": record.get("id")})
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate generated RAG JSONL files.")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "rag_jsonl_output", help="JSONL output directory.")
    parser.add_argument("--report", type=Path, default=Path.cwd() / "reports" / "validation_report.json")
    args = parser.parse_args(argv)

    records_by_name: dict[str, list[dict[str, Any]]] = {}
    report: dict[str, Any] = {
        "output_dir": str(args.output_dir),
        "files": {},
        "checks": {},
        "passed": False,
    }

    has_error = False
    for name, filename in EXPECTED_FILES.items():
        path = args.output_dir / filename
        records, parse_errors = read_jsonl(path)
        records_by_name[name] = records
        id_check = validate_id(records)
        empty_text = validate_text(records)
        file_ok = not parse_errors and not id_check["missing_lines"] and not id_check["duplicates"] and not empty_text
        has_error = has_error or not file_ok
        report["files"][filename] = {
            "path": str(path),
            "record_count": len(records),
            "valid_jsonl": not parse_errors,
            "parse_errors": parse_errors,
            "missing_id_lines": id_check["missing_lines"],
            "duplicate_ids": id_check["duplicates"],
            "empty_text_records": empty_text,
        }

    counts = {EXPECTED_FILES[name]: len(records) for name, records in records_by_name.items()}
    knowledge_expected = counts["textbook.jsonl"] + counts["vocab.jsonl"] + counts["grammar.jsonl"]
    knowledge_actual = counts["textbook_knowledge.jsonl"]
    knowledge_ok = knowledge_actual == knowledge_expected

    sample_check = validate_sample_questions(records_by_name["sample_question"])
    sample_fields_ok = not sample_check["missing_fields"]
    options_ok = not sample_check["bad_options"]

    vacab_hits = validate_no_vacab(records_by_name)
    vacab_ok = not vacab_hits

    report["checks"] = {
        "record_counts": counts,
        "textbook_knowledge_sum": {
            "passed": knowledge_ok,
            "expected": knowledge_expected,
            "actual": knowledge_actual,
        },
        "sample_question_required_fields": {
            "passed": sample_fields_ok,
            "missing_fields": sample_check["missing_fields"],
        },
        "sample_question_options": {
            "passed": options_ok,
            "bad_options": sample_check["bad_options"],
        },
        "vacab_md_absent": {
            "passed": vacab_ok,
            "hits": vacab_hits,
        },
    }

    has_error = has_error or not knowledge_ok or not sample_fields_ok or not options_ok or not vacab_ok
    report["passed"] = not has_error

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "passed": report["passed"],
        "record_counts": counts,
        "valid_jsonl": all(file_info["valid_jsonl"] for file_info in report["files"].values()),
        "duplicate_ids": sum(len(file_info["duplicate_ids"]) for file_info in report["files"].values()),
        "empty_text_records": sum(len(file_info["empty_text_records"]) for file_info in report["files"].values()),
        "textbook_knowledge_sum": report["checks"]["textbook_knowledge_sum"],
        "sample_question_required_fields_ok": sample_fields_ok,
        "sample_question_options_ok": options_ok,
        "vacab_md_absent": vacab_ok,
        "report": str(args.report),
    }, ensure_ascii=False, indent=2))

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
