#!/usr/bin/env python
"""Run baseline retrieval smoke tests and write JSON/Markdown reports."""

from __future__ import annotations

import json
from pathlib import Path

from test_retrieval import search


QUERIES = [
    "-는다고 하다를 활용한 읽기 문항",
    "-어 보니까를 활용한 경험 서술 문항",
    "-을 텐데를 활용한 추측 표현 문항",
    "피동 표현을 활용한 문항",
    "-도록을 활용한 문제 해결 문항",
    "중고 거래 광고를 읽고 내용과 같은 것을 고르는 문항",
    "한국 생활 문제와 해결에 관한 읽기 지문",
    "사고와 부상 상황을 다룬 읽기 문항",
    "분실물 안내문을 활용한 읽기 문항",
    "소비 습관에 관한 읽기 문항",
    "사실적 이해 문항",
    "중심 내용 고르기 문항",
    "빈칸에 들어갈 말 고르기 문항",
    "글의 순서 배열 문항",
    "내용과 같은 것을 고르는 문항",
]


def escape_md(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def metadata_summary(result: dict[str, object]) -> str:
    fields = []
    for key in ("source_type", "question_category", "unit_no", "page", "object_type", "qid"):
        value = result.get(key)
        if value not in (None, ""):
            fields.append(f"{key}={value}")
    return "; ".join(fields)


def markdown_table(results: list[dict[str, object]]) -> str:
    lines = [
        "| Rank | Score | ID | Metadata | Preview |",
        "|---:|---:|---|---|---|",
    ]
    for result in results:
        lines.append(
            "| {rank} | {score:.4f} | `{id}` | {metadata} | {preview} |".format(
                rank=result["rank"],
                score=float(result["score"]),
                id=escape_md(result["id"]),
                metadata=escape_md(metadata_summary(result)),
                preview=escape_md(result["preview"]),
            )
        )
    return "\n".join(lines)


def write_markdown(report: dict[str, object], path: Path) -> None:
    lines = [
        "# Retrieval Smoke Test",
        "",
        "TF-IDF baseline retrieval results for the KRAG dataset.",
        "",
    ]
    for item in report["queries"]:
        lines.append(f"## {item['query']}")
        lines.append("")
        lines.append("### Knowledge Top 5")
        lines.append("")
        lines.append(markdown_table(item["knowledge"]))
        lines.append("")
        lines.append("### Examples Top 5")
        lines.append("")
        lines.append(markdown_table(item["examples"]))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    index_dir = Path.cwd() / "rag_index"
    reports_dir = Path.cwd() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    payload = {"top_k": 5, "queries": []}
    for query in QUERIES:
        payload["queries"].append(
            {
                "query": query,
                "knowledge": search(index_dir, "knowledge", query, 5),
                "examples": search(index_dir, "examples", query, 5),
            }
        )

    json_path = reports_dir / "retrieval_smoke_test.json"
    md_path = reports_dir / "retrieval_smoke_test.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, md_path)

    print(json.dumps({"queries": len(QUERIES), "json_report": str(json_path), "markdown_report": str(md_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
