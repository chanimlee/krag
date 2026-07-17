from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_EXCEL = ROOT / "data" / "raw" / "RAG_textbook_chapter_input_template.xlsx"
PROCESSED = ROOT / "data" / "processed"
PROMPTS = ROOT / "prompts"
OUTPUTS = ROOT / "outputs"
FINAL = ROOT / "final"


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def prepare_dataframe_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna("").astype(str)


@lru_cache(maxsize=64)
def load_jsonl_cached(path_text: str) -> tuple[dict[str, Any], ...]:
    path = resolve_path(path_text)
    if not path.exists():
        return tuple()
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return tuple(rows)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return list(load_jsonl_cached(str(path)))


def load_embedded_excel(path: str | Path = RAW_EXCEL) -> pd.ExcelFile:
    excel_path = resolve_path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Embedded Excel file not found: {excel_path}")
    return pd.ExcelFile(excel_path)


def get_excel_sheet_names(path: str | Path = RAW_EXCEL) -> list[str]:
    return load_embedded_excel(path).sheet_names


def load_excel_sheet_preview(path: str | Path = RAW_EXCEL, sheet_name: str | None = None, max_rows: int = 30) -> pd.DataFrame:
    excel_path = resolve_path(path)
    sheets = get_excel_sheet_names(excel_path)
    selected = sheet_name or (sheets[0] if sheets else 0)
    return pd.read_excel(excel_path, sheet_name=selected, nrows=max_rows)


def load_passages() -> list[dict[str, Any]]:
    return load_jsonl(PROCESSED / "passages.jsonl")


def load_passage_catalog() -> list[dict[str, Any]]:
    catalog = []
    for row in load_passages():
        skill = str(row.get("skill", ""))
        if skill not in {"reading", "culture"} and "reading" not in skill and "culture" not in skill:
            continue
        text = str(row.get("source_text", ""))
        preview = text.replace("\n", " ")[:50]
        item = dict(row)
        item["preview"] = preview
        item["display_label"] = f"{row.get('chapter_id', 'NA')} | {skill} | {row.get('passage_id', 'NA')} | {preview}"
        catalog.append(item)
    return catalog


def get_passage_by_id(passage_id: str) -> dict[str, Any] | None:
    for row in load_passages():
        if str(row.get("passage_id")) == str(passage_id):
            return row
    return None


def load_prompt_packages(mode: str = "existing") -> list[dict[str, Any]]:
    if mode == "similar":
        return load_jsonl(PROMPTS / "similar_passage_item_prompts.jsonl")
    return load_jsonl(PROMPTS / "existing_passage_item_prompts.jsonl")


def get_prompt_for_passage(passage_id: str) -> dict[str, Any] | None:
    for pkg in load_prompt_packages("existing"):
        target = pkg.get("target", {})
        if str(target.get("passage_id")) == str(passage_id) or str(pkg.get("prompt_id", "")).endswith(str(passage_id)):
            return pkg
    return None


def get_similar_prompt_for_chapter(chapter_id: str) -> dict[str, Any] | None:
    return get_similar_passage_prompt_package(chapter_id=chapter_id)


def get_similar_passage_prompt_package(chapter_id: str | None = None, passage_id: str | None = None) -> dict[str, Any] | None:
    packages = load_prompt_packages("similar")
    selected_chapter = chapter_id
    if not selected_chapter and passage_id:
        passage = get_passage_by_id(passage_id) or {}
        selected_chapter = passage.get("chapter_id")
    if selected_chapter:
        for pkg in packages:
            if str(pkg.get("target", {}).get("chapter_id")) == str(selected_chapter):
                return pkg
        for pkg in packages:
            if str(selected_chapter) in str(pkg.get("prompt_id", "")):
                return pkg
        unit_prefix = str(selected_chapter).rsplit("-", 1)[0]
        for pkg in packages:
            if unit_prefix and unit_prefix in str(pkg.get("prompt_id", "")):
                return pkg
    return packages[0] if packages else None


def get_context_for_passage(passage_id: str, generation_mode: str = "existing") -> dict[str, Any]:
    passage = get_passage_by_id(passage_id) or {}
    if generation_mode == "similar":
        pkg = get_similar_passage_prompt_package(chapter_id=str(passage.get("chapter_id", "")), passage_id=passage_id)
    else:
        pkg = get_prompt_for_passage(passage_id)
        if not pkg and passage.get("chapter_id"):
            pkg = get_similar_passage_prompt_package(chapter_id=str(passage.get("chapter_id")))
    ctx = (pkg or {}).get("retrieved_context", {})
    return {
        "prompt_package": pkg or {},
        "target_passage": ctx.get("target_passage") or passage,
        "chapter_context": ctx.get("chapter_context", {}),
        "vocabulary_context": ctx.get("vocabulary_context", []),
        "grammar_context": ctx.get("grammar_context", []),
        "grammar_detail_context": ctx.get("grammar_detail_context", []),
        "source_question_examples": ctx.get("source_question_examples", []),
        "topik_sample_examples": ctx.get("topik_sample_examples", []),
        "similar_source_passages": ctx.get("similar_source_passages", []),
    }


def load_final_candidates() -> list[dict[str, Any]]:
    return load_jsonl(FINAL / "final_item_candidates.jsonl")


def get_sample_generated_items(passage_id: str, generation_mode: str = "existing") -> list[dict[str, Any]]:
    passage = get_passage_by_id(passage_id) or {}
    chapter_id = str(passage.get("chapter_id", ""))
    rows = load_final_candidates()
    if generation_mode == "similar":
        matched = [r for r in rows if r.get("mode") == "similar_passage_and_item_generation" and str(r.get("chapter_id")) == chapter_id]
    else:
        matched = [r for r in rows if str(r.get("passage_id")) == str(passage_id)]
    if matched:
        return matched
    generated = load_jsonl(OUTPUTS / "generated_all_items.jsonl")
    fallback: list[dict[str, Any]] = []
    for result in generated:
        target = result.get("target", {})
        if generation_mode == "similar":
            if result.get("mode") != "similar_passage_and_item_generation" or str(target.get("chapter_id")) != chapter_id:
                continue
        elif str(target.get("passage_id")) != str(passage_id):
            continue
        for item in result.get("generated", {}).get("items", []):
            fallback.append({
                "candidate_id": item.get("item_id", "ITEM"),
                "prompt_id": result.get("prompt_id"),
                "mode": result.get("mode"),
                "chapter_id": target.get("chapter_id"),
                "passage_id": target.get("passage_id"),
                "final_decision": "sample",
                "validation_status": "NA",
                "question": item.get("question"),
                "options": item.get("options", {}),
                "answer": item.get("answer"),
                "rationale": item.get("rationale"),
                "evidence_sentence": item.get("evidence_sentence"),
                "target_or_generated_passage": result.get("generated", {}).get("generated_passage", {}).get("text", ""),
                "checks": {},
            })
    return fallback


def get_validation_for_items(item_ids: list[str] | None = None, passage_id: str | None = None) -> list[dict[str, Any]]:
    rows = load_jsonl(OUTPUTS / "validation_all_items.jsonl")
    if item_ids:
        keys = set(map(str, item_ids))
        return [r for r in rows if str(r.get("item_id")) in keys]
    if passage_id:
        return [r for r in rows if str(r.get("passage_id")) == str(passage_id)]
    return rows


def data_status() -> list[dict[str, Any]]:
    paths = [
        RAW_EXCEL,
        PROCESSED / "passages.jsonl",
        PROCESSED / "vocabulary.jsonl",
        PROCESSED / "grammar.jsonl",
        PROCESSED / "grammar_details.jsonl",
        PROCESSED / "source_questions.jsonl",
        PROCESSED / "sample_questions.jsonl",
        PROMPTS / "existing_passage_item_prompts.jsonl",
        PROMPTS / "similar_passage_item_prompts.jsonl",
        OUTPUTS / "generated_all_items.jsonl",
        OUTPUTS / "validation_all_items.jsonl",
        FINAL / "final_item_candidates.jsonl",
    ]
    return [{"path": str(p.relative_to(ROOT)), "exists": p.exists()} for p in paths]
