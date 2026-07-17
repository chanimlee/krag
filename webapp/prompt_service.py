from __future__ import annotations

from typing import Any

from .data_loader import get_prompt_for_passage, get_similar_passage_prompt_package


TYPE_PRESETS = {
    "자동 구성": {},
    "사실적 이해 중심": {"factual": 3, "inferential": 0, "evaluative": 0},
    "사실적 + 추론적": {"factual": 2, "inferential": 1, "evaluative": 0},
    "사실적 + 추론적 + 평가적": {"factual": 1, "inferential": 1, "evaluative": 1},
}


def type_config(label: str, n_items: int, custom: dict[str, int] | None = None) -> dict[str, int]:
    if label == "사용자 지정":
        return custom or {}
    preset = dict(TYPE_PRESETS.get(label, {}))
    if not preset:
        return {"auto": n_items}
    total = sum(preset.values())
    if total and total != n_items:
        scale = n_items / total
        keys = list(preset)
        scaled = {k: int(round(v * scale)) for k, v in preset.items()}
        diff = n_items - sum(scaled.values())
        scaled[keys[0]] += diff
        return scaled
    return preset


def construct_count_is_valid(construct_counts: dict[str, int], n_items: int) -> bool:
    if "auto" in construct_counts:
        return True
    return sum(int(v) for v in construct_counts.values()) == int(n_items)


def get_prompt_package(passage_id: str, chapter_id: str, generation_mode: str) -> dict[str, Any] | None:
    if generation_mode == "similar":
        return get_similar_passage_prompt_package(chapter_id=chapter_id, passage_id=passage_id)
    return get_prompt_for_passage(passage_id)


def build_user_prompt(pkg: dict[str, Any], n_items: int, construct_counts: dict[str, int], generation_mode: str = "existing") -> str:
    base = pkg.get("user_prompt", "")
    common = (
        f"{base}\n\n"
        f"Demo generation settings:\n"
        f"- Generate exactly {n_items} items.\n"
        f"- Construct counts: {construct_counts}.\n"
        "- Level: Korean level 3 / Seoul National University Korean 3A.\n"
        "- Each item must have exactly four options.\n"
        "- Each item must include construct, question, options, answer, rationale, and evidence_sentence.\n"
        "- Do not copy full sentences from the passage as answer options or distractors.\n"
        "- After writing all options, order them from shortest to longest by Korean character length excluding spaces.\n"
        "- Recalculate the answer number after reordering options.\n"
        "Return only a valid JSON object that conforms to the output_schema."
    )
    if generation_mode != "similar":
        return common
    return (
        common
        + "\n\n"
        "You must generate one new Korean reading passage and multiple-choice items based on the provided chapter-level vocabulary, grammar, and sample item context.\n"
        "The response must be a valid JSON object only.\n"
        "The JSON object must include:\n"
        "- generated_passage\n"
        "- items\n"
        "Each item must include:\n"
        "- construct\n"
        "- question\n"
        "- options\n"
        "- answer\n"
        "- rationale\n"
        "- evidence_sentence\n"
        "The generated_passage must be long enough to support all items.\n"
        "All answers must be clearly inferable from the generated_passage.\n"
        "Do not rely on information outside the generated_passage.\n"
        "Do not copy full option sentences directly from the generated_passage unless unavoidable.\n"
    )
