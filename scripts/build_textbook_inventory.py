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

UNIT2_EXPECTED_PASSAGES = {
    "딸기 축제 대화": ["딸기 축제", "겉옷"],
    "태풍 ‘나비’ 일기예보": ["태풍 '나비'", "일기 예보"],
    "발리 여행 계획 대화": ["발리", "요가", "비행기표"],
    "발리에서 제주도로 여행 계획을 변경하는 대화": ["발리에 못 가게", "제주도", "고기국수"],
    "여행사랑 카페 요청 글": ["여행사랑 카페", "추천해 주세요"],
    "오로라 투어 안내문": ["오로라투어", "옐로나이프"],
    "수원 1박 2일 여행 안내 글": ["1박2일 수원 여행", "화성"],
    "꽃샘추위 설명문": ["꽃샘추위", "일교차"],
}

UNIT5_EXPECTED_PASSAGES = {
    "영화 보기 전 국수/튀김 대화": ["점심을 일찍 먹어서", "이렇게 맛있을 줄 몰랐어요"],
    "로티를 만들어 먹는 대화": ["아침을 일찍 먹어서", "우리 고향 사람들이 즐겨 먹어요"],
    "꿀떡 광고": ["아침 식사를 거르는", "꿀떡", "주문해 보세요"],
    "고기 안 들어간 한국 음식 대화": ["히엔 씨", "식당이 정해지면 다시 말씀드릴게요"],
    "김밥 맛집 대화": ["다리가 너무 아파", "누구나 다 좋아할 것 같아"],
    "집들이 음식 추천: 궁중떡볶이": ["집들이", "궁중떡볶이", "한번 만들어 보세요"],
    "불고기 만들기": ["불고기 만들기", "과일을 넣으면 더 맛있거든요"],
    "언제나 그리운 내 고향 음식, 쌀국수": ["언제나 그리운 내 고향 음식, 쌀국수", "직접 만든 쌀국수를 드셔 보는 건 어떠세요"],
    "국과 찌개": ["국과 찌개", "끓인 것은 '찌개"],
}


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


def source_activity(record: dict[str, Any]) -> str:
    object_type = record.get("object_type")
    mapping = {
        "reading": "reading",
        "listening": "listening",
        "speaking": "speaking",
        "culture": "culture",
        "task": "task",
    }
    return mapping.get(object_type, "other")


def has_dialogue_markers(text: str) -> bool:
    return len(re.findall(r"(?:^|\s)[가-힣A-Za-z]{1,8}:", text)) >= 2 or ("남:" in text and "여:" in text)


def has_unlabeled_dialogue_shape(text: str) -> bool:
    if has_dialogue_markers(text):
        return True
    short_question_turns = len(re.findall(r"(?:요\?|까\?|예요\?|뭐예요\?)", text))
    first_person_turns = len(re.findall(r"(?:저는|같이|네\.|그래요|뭐예요|어때요)", text))
    return short_question_turns >= 2 and first_person_turns >= 3


def sentence_like_count(text: str) -> int:
    return len(re.findall(r"(?:다|요|까|죠|지|네|습니다|습니까|세요)[.!?]?(?:\s|$)", text))


def looks_like_list_only(text: str) -> bool:
    if len(text) < 45:
        return True
    option_hits = len(re.findall(r"(?:^|\s)[1-4][).]\s", text))
    if option_hits >= 2:
        return True
    slash_count = text.count("/")
    if slash_count >= 4 and sentence_like_count(text) < 2 and not has_dialogue_markers(text):
        return True
    english_words = len(re.findall(r"[A-Za-z]{2,}", text))
    korean_chars = len(re.findall(r"[가-힣]", text))
    if english_words >= 5 and korean_chars < 25:
        return True
    return False


def usable_text_candidate(text: str, strong_source: bool) -> bool:
    text = clean_text(text)
    if not text:
        return False
    if strong_source:
        return len(text) >= 45
    if looks_like_list_only(text):
        return False
    return has_dialogue_markers(text) or has_unlabeled_dialogue_shape(text) or sentence_like_count(text) >= 2


def infer_candidate_type(record: dict[str, Any], text: str, title: str, strong_source: bool) -> tuple[str, str, bool, str]:
    activity = source_activity(record)
    combined = f"{title} {text}"
    if "불고기 만들기" in combined or "만드는 방법" in combined or "조리법" in combined or "만들려면" in combined:
        if "질문" in combined and "어때요" in combined and "추천" in combined:
            return "qna_reading", "high", True, "Question-answer recommendation text reusable as a reading item passage."
        return "recipe", "high", True, "Recipe/procedure text reusable as a reading item passage."
    if activity == "listening" and (strong_source or title == "듣기 지문"):
        if "광고" in combined or "주문해 보세요" in combined:
            return "ad", "high", True, "Listening advertisement script from textbook activity."
        return "core_listening", "high", True, "Explicit listening script from textbook activity."
    if activity == "reading" and strong_source:
        if "질문" in combined and "어때요" in combined:
            return "qna_reading", "high", True, "Question-answer recommendation text from reading activity."
        if "카페" in combined or "블로그" in combined:
            return "blog", "high", True, "Reading passage in online post/blog-like format."
        if "광고" in combined:
            return "ad", "high", True, "Reading passage in advertisement format."
        if "안내" in combined or "투어" in combined or "여행" in combined:
            return "guide", "high", True, "Reading passage in guide/notice format."
        if "기사" in combined:
            return "article", "high", True, "Reading passage in article format."
        return "core_reading", "high", True, "Explicit reading passage from textbook activity."
    if has_dialogue_markers(text) or has_unlabeled_dialogue_shape(text):
        priority = "medium" if activity in {"speaking", "task"} else "high"
        return "reusable_dialogue", priority, True, "Complete dialogue reusable as an assessment passage."
    if activity == "culture":
        return "culture_text", "medium", True, "Culture page explanatory text reusable as an assessment passage."
    if activity == "task":
        return "task_text", "medium", True, "Task page text reusable as a short assessment passage."
    if "안내" in combined:
        return "notice", "medium", True, "Notice-like explanatory text."
    if "광고" in combined:
        return "ad", "medium", True, "Advertisement-like text."
    if "기사" in combined:
        return "article", "medium", True, "Article-like text."
    if "블로그" in combined or "카페" in combined:
        return "blog", "medium", True, "Blog or cafe post-like text."
    if "가이드" in combined or "여행" in combined:
        return "guide", "medium", True, "Guide-like informational text."
    if "질문" in combined and "어때요" in combined:
        return "qna_reading", "medium", True, "Question-answer text reusable as a reading item passage."
    return "etc", "low", False, "Potential passage-like text but lower priority for exam use."


def iter_text_candidates(record: dict[str, Any]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for section in record.get("raw_sections") or []:
        title = clean_text(section.get("title"))
        text = clean_text(section.get("text"))
        if not text:
            continue
        strong = title in {"지문", "듣기 지문"}
        if title in {"질문", "어휘", "문법과 표현", "문법 항목", "문법 형식", "발음", "자기평가", "표"}:
            continue
        if title == "내용" and record.get("object_type") in {"vocabulary", "unit_intro"}:
            continue
        if usable_text_candidate(text, strong):
            candidates.append({"title": title, "text": text, "strong": str(strong)})
    return candidates


def build_passage_bank(textbook_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters: dict[tuple[int, str], int] = defaultdict(int)
    passages: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for record in textbook_records:
        for candidate in iter_text_candidates(record):
            passage = clean_text(candidate["text"])
            strong = candidate["strong"] == "True"
            dedupe_key = (record.get("id") or "", passage)
            if not passage or dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            activity = source_activity(record)
            skill = "listening" if activity == "listening" else "reading"
            candidate_type, priority, usable_for_exam, reason = infer_candidate_type(record, passage, candidate["title"], strong)
            unit_no = int(record.get("unit_no") or 0)
            counters[(unit_no, skill)] += 1
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
                    "source_activity": activity,
                    "candidate_type": candidate_type,
                    "usable_for_exam": usable_for_exam,
                    "priority": priority,
                    "extraction_reason": reason,
                    "passage_type": "existing_textbook_passage",
                    "passage": passage,
                    "source_record_id": record.get("id"),
                    "available_question_prompts": flatten(record.get("questions")),
                    "linked_grammar_items": flatten(record.get("grammar_items")) + flatten(record.get("grammar_expressions")) + flatten(record.get("grammar_forms")),
                    "linked_vocabulary": flatten(record.get("vocabulary")),
                    "note": "" if strong else f"Extracted from raw section title: {candidate['title']}",
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
    usable_counts: dict[int, dict[str, int]] = defaultdict(lambda: {"reading": 0, "listening": 0})
    candidate_type_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for passage in passages:
        passage_counts[int(passage["unit_no"])][passage["skill"]] += 1
        candidate_type_counts[int(passage["unit_no"])][passage["candidate_type"]] += 1
        if passage.get("usable_for_exam") and passage.get("priority") in {"high", "medium"}:
            usable_counts[int(passage["unit_no"])][passage["skill"]] += 1

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
                "usable_reading_passage_count": usable_counts[unit_no]["reading"],
                "usable_listening_passage_count": usable_counts[unit_no]["listening"],
                "candidate_type_counts": dict(sorted(candidate_type_counts[unit_no].items())),
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
            "usable_exam_passages": sum(1 for item in passages if item.get("usable_for_exam") and item.get("priority") in {"high", "medium"}),
            "chapter_constraints": len(constraints),
            "unit2_expected_passage_check": check_expected_passages(passages, 2, UNIT2_EXPECTED_PASSAGES),
            "unit5_expected_passage_check": check_expected_passages(passages, 5, UNIT5_EXPECTED_PASSAGES),
        },
        "units": units,
    }


def check_expected_passages(passages: list[dict[str, Any]], unit_no: int, expected: dict[str, list[str]]) -> dict[str, Any]:
    unit_passages = [item for item in passages if item.get("unit_no") == unit_no]
    results = {}
    for label, needles in expected.items():
        matches = [
            {
                "id": item["id"],
                "source_activity": item.get("source_activity"),
                "candidate_type": item.get("candidate_type"),
                "usable_for_exam": item.get("usable_for_exam"),
                "priority": item.get("priority"),
            }
            for item in unit_passages
            if all(needle in item.get("passage", "") for needle in needles)
        ]
        results[label] = {"found": bool(matches), "matches": matches, "passage_ids": [match["id"] for match in matches]}
    return {
        "passed": all(value["found"] for value in results.values()),
        "items": results,
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
        if isinstance(value, (dict, list)):
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Unit Overview",
            "",
            "| unit_no | unit_title | reading passages | listening passages | usable reading | usable listening | candidate types | grammar items | vocabulary | main grammar items | sample vocabulary | page range |",
            "|---:|---|---:|---:|---:|---:|---|---:|---:|---|---|---|",
        ]
    )
    for unit in inventory["units"]:
        pages = unit["page_range"]
        page_range = f"{pages[0]}-{pages[1]}" if pages else ""
        grammar = "<br>".join(unit["sample_grammar_items"])
        vocab = "<br>".join(unit["sample_vocabulary"])
        candidate_types = "<br>".join(f"{key}:{value}" for key, value in unit["candidate_type_counts"].items())
        lines.append(
            "| {unit_no} | {unit_title} | {reading} | {listening} | {usable_reading} | {usable_listening} | {candidate_types} | {grammar_count} | {vocab_count} | {grammar} | {vocab} | {pages} |".format(
                unit_no=unit["unit_no"],
                unit_title=unit.get("unit_title") or "",
                reading=unit["reading_passage_count"],
                listening=unit["listening_passage_count"],
                usable_reading=unit["usable_reading_passage_count"],
                usable_listening=unit["usable_listening_passage_count"],
                candidate_types=candidate_types.replace("|", "\\|"),
                grammar_count=unit["grammar_item_count"],
                vocab_count=unit["vocabulary_count"],
                grammar=grammar.replace("|", "\\|"),
                vocab=vocab.replace("|", "\\|"),
                pages=page_range,
            )
        )
    for heading, check_key in [
        ("Unit 2 Expected Passage Coverage", "unit2_expected_passage_check"),
        ("Unit 5 Expected Passage Coverage", "unit5_expected_passage_check"),
    ]:
        check = inventory["summary"].get(check_key, {})
        if not check:
            continue
        lines.extend(
            [
                "",
                f"## {heading}",
                "",
                f"- passed: {check.get('passed')}",
                "",
                "| expected passage | found | passage_ids | metadata |",
                "|---|---|---|---|",
            ]
        )
        for label, result in check.get("items", {}).items():
            metadata = "<br>".join(
                "{id}: {source_activity}/{candidate_type}/usable={usable_for_exam}/priority={priority}".format(**match)
                for match in result.get("matches", [])
            )
            lines.append(
                "| {label} | {found} | {ids} | {metadata} |".format(
                    label=label.replace("|", "\\|"),
                    found=result.get("found"),
                    ids=", ".join(result.get("passage_ids", [])),
                    metadata=metadata.replace("|", "\\|"),
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
