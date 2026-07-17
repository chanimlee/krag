from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .prompt_service import build_user_prompt
from .validation_service import sort_options_shortest_to_longest, validate_item, validate_similar_generation

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "outputs" / "webapp_runs"


def get_config_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default


DEFAULT_MODEL_NAME = "gpt-5.5"
MODEL_NAME = get_config_value("OPENAI_MODEL", DEFAULT_MODEL_NAME)


def has_api_key() -> bool:
    return bool(get_config_value("OPENAI_API_KEY"))


def normalize_options(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    if isinstance(value, list):
        if all(isinstance(v, dict) for v in value):
            out = {}
            for idx, row in enumerate(value, 1):
                key = str(row.get("number") or row.get("key") or row.get("id") or idx)
                out[key] = row.get("text") or row.get("option") or row.get("value") or ""
            return out
        return {str(i + 1): v for i, v in enumerate(value)}
    return {}


def normalize_generated_passage(generated: dict[str, Any]) -> dict[str, Any]:
    gp = generated.get("generated_passage") or generated.get("passage") or generated.get("reading_passage")
    if isinstance(gp, dict):
        text = gp.get("text") or gp.get("source_text") or gp.get("passage") or ""
        gp = dict(gp)
        gp["text"] = text
        return gp
    if isinstance(gp, str):
        return {"text": gp}
    for key in ["text", "source_text", "generated_text"]:
        if generated.get(key):
            return {"text": generated.get(key)}
    return {"text": ""}


def normalize_answer(item: dict[str, Any]) -> None:
    options = item.get("options", {})
    answer = str(item.get("answer", "")).strip()
    circled = {"①": "1", "②": "2", "③": "3", "④": "4"}
    if answer in circled:
        item["answer"] = circled[answer]
        return
    if answer in {"1", "2", "3", "4"}:
        item["answer"] = answer
        return
    for key, value in options.items():
        if str(value).strip() == answer:
            item["answer"] = str(key)
            return


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    if "construct" not in out and "type" in out:
        out["construct"] = out["type"]
    if "construct" not in out and "item_type" in out:
        out["construct"] = out["item_type"]
    if "item_type" not in out and out.get("construct"):
        out["item_type"] = out.get("construct")
    if "question" not in out and "question_text" in out:
        out["question"] = out["question_text"]
    if "rationale" not in out and "explanation" in out:
        out["rationale"] = out["explanation"]
    if "evidence_sentence" not in out and "evidence" in out:
        out["evidence_sentence"] = out["evidence"]
    out["options"] = normalize_options(out.get("options"))
    normalize_answer(out)
    order = sort_options_shortest_to_longest(out)
    out["options"] = order["options"]
    out["answer"] = order["answer"]
    out.update({k: v for k, v in order.items() if k not in {"options", "answer"}})
    return out


def normalize_generated_response(parsed: dict[str, Any], generation_mode: str = "existing") -> dict[str, Any]:
    generated = dict(parsed)
    if "items" not in generated:
        for key in ["questions", "generated_items"]:
            if key in generated:
                generated["items"] = generated[key]
                break
    if generation_mode == "similar":
        generated["generated_passage"] = normalize_generated_passage(generated)
        generated["mode"] = "similar_passage"
    items = generated.get("items", [])
    if isinstance(items, list):
        generated["items"] = [normalize_item(item) for item in items if isinstance(item, dict)]
    else:
        generated["items"] = []
    return generated


def run_id() -> str:
    return datetime.now().strftime("webapp_%Y%m%d_%H%M%S")


def call_openai_json(system_message: str, user_message: str) -> tuple[dict[str, Any], dict[str, Any]]:
    from openai import OpenAI

    client = OpenAI(api_key=get_config_value("OPENAI_API_KEY"))
    system_message = f"{system_message}\n\nYou must respond with a valid JSON object only. Do not include Markdown fences or explanatory text."
    user_message = f"{user_message}\n\nReturn only a valid JSON object that conforms to the output_schema."
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
    except Exception as exc:
        raise RuntimeError(
            f"OpenAI 모델 '{MODEL_NAME}' 호출에 실패했습니다. "
            "이 모델의 사용 권한과 모델명을 확인하세요. 사용할 수 없는 경우 "
            "OPENAI_MODEL 환경변수 또는 Streamlit Secrets를 접근 가능한 모델명으로 변경하세요. "
            f"원본 오류: {exc}"
        ) from exc
    raw = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON parse failed. Raw preview: {raw[:500]}") from exc
    return parsed, {"raw_response": raw, "model": MODEL_NAME}


def save_run_files(run_dir: Path, payload: dict[str, Any], prompt_package: dict[str, Any], meta: dict[str, Any], generated_passage: dict[str, Any] | None = None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(payload["config"], ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "passage.json").write_text(json.dumps(payload["passage"], ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "prompt_package.json").write_text(json.dumps(prompt_package, ensure_ascii=False, indent=2), encoding="utf-8")
    if generated_passage is not None:
        (run_dir / "generated_passage.json").write_text(json.dumps(generated_passage, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "generated_items.json").write_text(json.dumps(payload["generated"], ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "validation.json").write_text(json.dumps(payload["validation"], ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "raw_response.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    from .export_service import to_markdown_bytes, to_xlsx_bytes

    export_payload = {
        "summary": {"mode": "api", "run_id": payload.get("run_id"), **payload.get("config", {})},
        "passage": payload.get("passage", {}),
        "generated_passage": generated_passage,
        "items": payload.get("generated", {}).get("items", []),
        "validation": payload.get("validation", []),
        "rag_context": {},
        "raw_response": "saved under raw_response.json",
    }
    (run_dir / "generated_items.xlsx").write_bytes(to_xlsx_bytes(export_payload))
    (run_dir / "generated_items.md").write_bytes(to_markdown_bytes(export_payload))


def generate_items(pkg: dict[str, Any], passage: dict[str, Any], n_items: int, construct_counts: dict[str, int], generation_mode: str = "existing") -> dict[str, Any]:
    if not has_api_key():
        raise RuntimeError("OPENAI_API_KEY is not set.")
    user_message = build_user_prompt(pkg, n_items, construct_counts, generation_mode=generation_mode)
    parsed, meta = call_openai_json(pkg.get("system_prompt", ""), user_message)
    generated = normalize_generated_response(parsed, generation_mode=generation_mode)
    rid = run_id()
    run_dir = RUNS / rid
    if generation_mode == "similar":
        generated_passage = generated.get("generated_passage", {})
        passage_text = str(generated_passage.get("text", ""))
        validation_bundle = validate_similar_generation(passage_text, generated.get("items", []), pkg, str(passage.get("source_text", "")))
        validations = validation_bundle["item_validations"]
    else:
        generated_passage = None
        passage_text = str(passage.get("source_text") or "")
        validations = [validate_item(item, passage_text) for item in generated.get("items", [])]
        validation_bundle = {"item_validations": validations}
    payload = {
        "run_id": rid,
        "config": {"n_items": n_items, "construct_counts": construct_counts, "model": MODEL_NAME, "generation_mode": generation_mode},
        "passage": passage,
        "generated": generated,
        "generated_passage": generated_passage,
        "validation": validations,
        "passage_validation": validation_bundle.get("passage_validation"),
    }
    save_run_files(run_dir, payload, pkg, meta, generated_passage)
    return payload


def generate_similar_passage_items_api(prompt_package: dict[str, Any], passage: dict[str, Any], n_items: int, construct_counts: dict[str, int]) -> dict[str, Any]:
    return generate_items(prompt_package, passage, n_items, construct_counts, generation_mode="similar")

