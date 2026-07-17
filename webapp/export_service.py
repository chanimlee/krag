from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd

CONSTRUCT_LABELS = {
    "factual": "사실적 이해",
    "factual_detail": "사실적 이해",
    "inferential": "추론적 이해",
    "inference": "추론적 이해",
    "evaluative": "평가적 이해",
    "evaluation": "평가적 이해",
    "main_idea": "중심 내용",
    "sequencing": "순서 배열",
    "matching": "대응/연결",
}


def construct_label(item: dict[str, Any]) -> str:
    raw = item.get("construct") or item.get("item_type") or item.get("checks", {}).get("construct") or ""
    return CONSTRUCT_LABELS.get(str(raw).strip().lower(), "")


def item_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for idx, item in enumerate(items, 1):
        opts = item.get("options", {})
        rows.append({
            "no": idx,
            "candidate_id": item.get("candidate_id") or item.get("item_id"),
            "construct": item.get("construct"),
            "construct_label": construct_label(item),
            "item_type": item.get("item_type"),
            "question": item.get("question"),
            "option_1": opts.get("1"),
            "option_2": opts.get("2"),
            "option_3": opts.get("3"),
            "option_4": opts.get("4"),
            "answer": item.get("answer"),
            "rationale": item.get("rationale"),
            "evidence_sentence": item.get("evidence_sentence"),
            "validation_status": item.get("validation_status"),
            "final_decision": item.get("final_decision"),
        })
    return rows


def to_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def validation_rows(validation: Any) -> list[dict[str, Any]]:
    if isinstance(validation, list):
        return validation
    if isinstance(validation, dict):
        return [validation]
    return []


def to_xlsx_bytes(payload: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    items = payload.get("items", [])
    validation = payload.get("validation", [])
    context = payload.get("rag_context", {})
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame([payload.get("summary", {})]).to_excel(writer, sheet_name="summary", index=False)
        if payload.get("generated_passage"):
            pd.DataFrame([payload.get("generated_passage", {})]).to_excel(writer, sheet_name="generated_passage", index=False)
        else:
            pd.DataFrame([payload.get("passage", {})]).to_excel(writer, sheet_name="passage", index=False)
        pd.DataFrame(item_rows(items)).to_excel(writer, sheet_name="generated_items", index=False)
        pd.DataFrame(validation_rows(validation)).to_excel(writer, sheet_name="validation", index=False)
        pd.DataFrame({
            "section": ["vocabulary", "grammar", "grammar_detail", "source_questions", "topik_samples"],
            "count": [
                len(context.get("vocabulary_context", [])),
                len(context.get("grammar_context", [])),
                len(context.get("grammar_detail_context", [])),
                len(context.get("source_question_examples", [])),
                len(context.get("topik_sample_examples", [])),
            ],
        }).to_excel(writer, sheet_name="rag_context", index=False)
        if payload.get("raw_response"):
            pd.DataFrame([{"raw_response": payload.get("raw_response")}]).to_excel(writer, sheet_name="raw_response", index=False)
    return buf.getvalue()


def to_markdown(payload: dict[str, Any]) -> str:
    generated_passage = payload.get("generated_passage") or {}
    if generated_passage:
        title = "# 유사 지문 생성 + 문항 생성 결과"
        passage_title = "## 생성 지문"
        passage_text = generated_passage.get("text", "")
    else:
        title = "# RAG 기반 한국어 평가 문항 생성 결과"
        passage_title = "## 지문"
        passage = payload.get("passage", {})
        passage_text = passage.get("source_text") or passage.get("text") or ""
    lines = [title, "", passage_title, "", str(passage_text), "", "## 문항"]
    for idx, item in enumerate(payload.get("items", []), 1):
        opts = item.get("options", {})
        label = construct_label(item)
        heading = f"### [{label}] 문항 {idx}" if label else f"### 문항 {idx}"
        lines.extend([
            "",
            heading,
            "",
            str(item.get("question", "")),
            "",
            f"1. {opts.get('1', '')}",
            f"2. {opts.get('2', '')}",
            f"3. {opts.get('3', '')}",
            f"4. {opts.get('4', '')}",
            f"- 정답: {item.get('answer', '')}",
            f"- 해설: {item.get('rationale', '')}",
            f"- 근거: {item.get('evidence_sentence', '')}",
            f"- 검증: {item.get('validation_status') or item.get('final_decision', '')}",
        ])
    return "\n".join(lines) + "\n"


def to_markdown_bytes(payload: dict[str, Any]) -> bytes:
    return to_markdown(payload).encode("utf-8")
