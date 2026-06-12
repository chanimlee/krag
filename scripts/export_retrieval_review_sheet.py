#!/usr/bin/env python
"""Export retrieval smoke test results to human review sheets."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


COLUMNS = [
    "query_id",
    "query",
    "target",
    "rank",
    "score",
    "id",
    "source_type",
    "question_category",
    "unit_no",
    "page",
    "object_type",
    "qid",
    "preview",
    "relevance",
    "usefulness_for_item_generation",
    "error_type",
    "reviewer_note",
]


def clean_preview(value: Any, limit: int = 500) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def make_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for query_index, item in enumerate(payload.get("queries", []), start=1):
        query_id = f"q{query_index:02d}"
        query = item.get("query", "")
        for target in ("knowledge", "examples"):
            for result in item.get(target, []):
                rows.append(
                    {
                        "query_id": query_id,
                        "query": query,
                        "target": target,
                        "rank": result.get("rank", ""),
                        "score": result.get("score", ""),
                        "id": result.get("id", ""),
                        "source_type": result.get("source_type", ""),
                        "question_category": result.get("question_category", ""),
                        "unit_no": result.get("unit_no", ""),
                        "page": result.get("page", ""),
                        "object_type": result.get("object_type", ""),
                        "qid": result.get("qid", ""),
                        "preview": clean_preview(result.get("preview")),
                        "relevance": "",
                        "usefulness_for_item_generation": "",
                        "error_type": "",
                        "reviewer_note": "",
                    }
                )
    return rows


def write_delimited(path: Path, rows: list[dict[str, Any]], delimiter: str, encoding: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export retrieval smoke test results for human review.")
    parser.add_argument("--input", type=Path, default=Path.cwd() / "reports" / "retrieval_smoke_test.json")
    parser.add_argument("--tsv-output", type=Path, default=Path.cwd() / "reports" / "retrieval_review_sheet.tsv")
    parser.add_argument("--csv-output", type=Path, default=Path.cwd() / "reports" / "retrieval_review_sheet.csv")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    rows = make_rows(payload)

    write_delimited(args.tsv_output, rows, delimiter="\t", encoding="utf-8")
    write_delimited(args.csv_output, rows, delimiter=",", encoding="utf-8-sig")

    print(json.dumps(
        {
            "input": str(args.input),
            "tsv_output": str(args.tsv_output),
            "csv_output": str(args.csv_output),
            "rows": len(rows),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
