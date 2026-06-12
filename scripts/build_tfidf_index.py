#!/usr/bin/env python
"""Build TF-IDF retrieval indices for KRAG JSONL datasets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer


FIELD_PRIORITY = (
    "text",
    "title",
    "unit",
    "subunit",
    "activity_area",
    "object_type",
    "grammar_items",
    "vocabulary",
    "question_category",
    "qid",
    "macro_type",
    "raw_item_id",
    "passage",
    "stem",
    "options",
)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def flatten_value(value: Any) -> list[str]:
    if value is None or value is False:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            parts.extend(flatten_value(item))
        return parts
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            parts.extend(flatten_value(value[key]))
        return parts
    return [str(value)]


def build_search_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for field in FIELD_PRIORITY:
        for value in flatten_value(record.get(field)):
            value = normalize_space(value)
            if value and value not in seen:
                seen.add(value)
                parts.append(value)
    return normalize_space(" ".join(parts))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            records.append(record)
    return records


def build_index(input_path: Path, output_dir: Path) -> dict[str, Any]:
    records = read_jsonl(input_path)
    docstore = []
    texts = []
    for index, record in enumerate(records):
        search_text = build_search_text(record)
        if not search_text:
            raise ValueError(f"Empty search_text for record {record.get('id')} in {input_path}")
        docstore.append({"index": index, "search_text": search_text, "record": record})
        texts.append(search_text)

    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(texts)

    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, output_dir / "vectorizer.joblib")
    joblib.dump(matrix, output_dir / "matrix.joblib")
    (output_dir / "docstore.json").write_text(json.dumps(docstore, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "documents": len(records),
        "vocabulary_size": len(vectorizer.vocabulary_),
        "output_dir": str(output_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TF-IDF indices for KRAG retrieval.")
    parser.add_argument("--jsonl-dir", type=Path, default=Path.cwd() / "rag_jsonl_output")
    parser.add_argument("--index-dir", type=Path, default=Path.cwd() / "rag_index")
    args = parser.parse_args()

    knowledge = build_index(args.jsonl_dir / "textbook_knowledge.jsonl", args.index_dir / "tfidf_knowledge")
    examples = build_index(args.jsonl_dir / "sample_question.jsonl", args.index_dir / "tfidf_examples")

    summary = {
        "knowledge_documents": knowledge["documents"],
        "example_documents": examples["documents"],
        "knowledge_vocabulary_size": knowledge["vocabulary_size"],
        "example_vocabulary_size": examples["vocabulary_size"],
        "knowledge_output_dir": knowledge["output_dir"],
        "examples_output_dir": examples["output_dir"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
