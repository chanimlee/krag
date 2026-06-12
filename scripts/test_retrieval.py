#!/usr/bin/env python
"""Query KRAG TF-IDF retrieval indices."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import joblib


TARGETS = {
    "knowledge": "tfidf_knowledge",
    "examples": "tfidf_examples",
}


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def preview(text: str, limit: int = 300) -> str:
    text = normalize_space(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def load_index(index_dir: Path) -> tuple[Any, Any, list[dict[str, Any]]]:
    vectorizer = joblib.load(index_dir / "vectorizer.joblib")
    matrix = joblib.load(index_dir / "matrix.joblib")
    docstore = json.loads((index_dir / "docstore.json").read_text(encoding="utf-8"))
    return vectorizer, matrix, docstore


def metadata(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": record.get("source_type"),
        "question_category": record.get("question_category") or record.get("macro_type"),
        "unit_no": record.get("unit_no"),
        "page": record.get("page"),
        "object_type": record.get("object_type"),
        "qid": record.get("qid") or record.get("raw_item_id"),
    }


def search(index_root: Path, target: str, query: str, top_k: int) -> list[dict[str, Any]]:
    vectorizer, matrix, docstore = load_index(index_root / TARGETS[target])
    query_vector = vectorizer.transform([query])
    scores = (matrix @ query_vector.T).toarray().ravel()
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
    results = []
    for rank, (idx, score) in enumerate(ranked, start=1):
        item = docstore[idx]
        record = item["record"]
        meta = metadata(record)
        results.append(
            {
                "rank": rank,
                "score": float(score),
                "id": record.get("id"),
                **meta,
                "preview": preview(item["search_text"]),
            }
        )
    return results


def print_results(results_by_target: dict[str, list[dict[str, Any]]]) -> None:
    for target, results in results_by_target.items():
        print()
        print(f"[{target}]")
        for result in results:
            meta = result.get("source_type") or result.get("question_category") or ""
            print(f"{result['rank']:>2}. {result['score']:.4f} {result['id']} {meta}")
            print(f"    {result['preview']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search KRAG TF-IDF indices.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--target", choices=["knowledge", "examples", "both"], default="both")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--index-dir", type=Path, default=Path.cwd() / "rag_index")
    args = parser.parse_args()

    targets = ["knowledge", "examples"] if args.target == "both" else [args.target]
    results_by_target = {target: search(args.index_dir, target, args.query, args.top_k) for target in targets}
    payload = {"query": args.query, "top_k": args.top_k, "target": args.target, "results": results_by_target}

    print_results(results_by_target)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nSaved: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
