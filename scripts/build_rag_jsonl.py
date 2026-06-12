#!/usr/bin/env python
"""Build JSONL files for the Korean proficiency RAG study sources.

Inputs:
  - textbook.md: textbook body, parsed by unit/subunit/page/section
  - vocab.md: vocabulary index, parsed as one record per vocabulary line
  - grammar.md: chapter grammar explanations, parsed as one record per page
  - sample_question.md: TOPIK sample items, parsed separately

Outputs:
  - textbook.jsonl
  - vocab.jsonl
  - grammar.jsonl
  - textbook_knowledge.jsonl: textbook + vocab + grammar
  - sample_question.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BOOK_SOURCE = "서울대 한국어+ 3A Student's Book"
TOPIK_SOURCE = "TOPIK"

UNIT_RE = re.compile(r"^##\s+(?P<title>\d+\.\s+.+?)\s*$")
SUBUNIT_RE = re.compile(r"^###\s+(?P<title>\d+-\d+\.\s+.+?)\s*$")
PAGE_RE = re.compile(r"^####\s+p\.(?P<page>\d+)\s*\|\s*(?P<label>.+?)\s*$")
SECTION_RE = re.compile(r"^#####\s+(?P<title>.+?)\s*$")
QUESTION_CATEGORY_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
QUESTION_ID_RE = re.compile(r"^###\s+(?P<qid>.+?)\s*$")
OPTION_RE = re.compile(r"^(?P<num>[1-4])\.\s*(?P<text>.*)$")
BOLD_RE = re.compile(r"^\*\*(?P<label>.+?)\*\*\s*$")


SECTION_FIELD_MAP = {
    "질문": "questions",
    "지문": "passages",
    "듣기 지문": "listening_scripts",
    "문법과 표현": "grammar_expressions",
    "문법 항목": "grammar_items",
    "문법 형식": "grammar_forms",
    "어휘": "vocabulary",
    "내용": "contents",
    "표": "tables",
    "발음": "pronunciation",
    "자기 평가": "self_evaluation",
    "자기평가": "self_evaluation",
    "설명": "explanations",
    "예문": "examples",
    "활용": "usage",
}


@dataclass
class Section:
    title: str
    lines: list[str] = field(default_factory=list)


@dataclass
class TextbookPage:
    unit: str | None
    subunit: str | None
    page: int
    activity_area: str
    sections: list[Section] = field(default_factory=list)


@dataclass
class GrammarPage:
    page: int
    chapter_label: str
    sections: list[Section] = field(default_factory=list)


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


def clean_lines(lines: list[str]) -> list[str]:
    cleaned = [line.strip() for line in lines]
    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return cleaned


def join_text(lines: list[str]) -> str:
    return "\n".join(clean_lines(lines)).strip()


def split_simple_lines(lines: list[str]) -> list[str]:
    return [line for line in clean_lines(lines) if line]


def split_question_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for line in clean_lines(lines):
        if re.match(r"^\d+\s+", line) and current:
            items.append(join_text(current))
            current = [line]
        else:
            current.append(line)
    if current:
        items.append(join_text(current))
    return [item for item in items if item]


def split_vocab_lines(lines: list[str]) -> list[str]:
    entries: list[str] = []
    for line in clean_lines(lines):
        if not line:
            continue
        if re.search(r"[A-Za-z]", line):
            entries.append(line)
        else:
            entries.extend(part for part in re.split(r"\s+", line) if part)
    return entries


def unit_no(title: str | None) -> int | None:
    if not title:
        return None
    match = re.match(r"^(\d+)\.", title)
    return int(match.group(1)) if match else None


def subunit_no(title: str | None) -> str | None:
    if not title:
        return None
    match = re.match(r"^(\d+-\d+)\.", title)
    return match.group(1) if match else None


def chapter_no(label: str | None) -> int | None:
    if not label:
        return None
    match = re.search(r"(\d+)\s*단원", label)
    return int(match.group(1)) if match else None


def normalize_slug(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", text.strip().lower()).strip("_")
    return slug or "item"


def normalize_activity(activity_area: str) -> str:
    mapping = {
        "단원 도입": "unit_intro",
        "어휘": "vocabulary",
        "말하기": "speaking",
        "듣기": "listening",
        "읽기": "reading",
        "쓰기": "writing",
        "과제": "task",
        "문화": "culture",
    }
    return mapping.get(activity_area, normalize_slug(activity_area))


def parse_sectioned_pages(lines: list[str]) -> list[TextbookPage]:
    current_unit: str | None = None
    current_subunit: str | None = None
    current_page: TextbookPage | None = None
    current_section: Section | None = None
    pages: list[TextbookPage] = []

    def finish_section() -> None:
        nonlocal current_section
        if current_page and current_section:
            current_section.lines = clean_lines(current_section.lines)
            current_page.sections.append(current_section)
        current_section = None

    def finish_page() -> None:
        nonlocal current_page
        finish_section()
        if current_page:
            pages.append(current_page)
        current_page = None

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            finish_page()
            continue

        unit_match = UNIT_RE.match(line)
        if unit_match:
            finish_page()
            current_unit = unit_match.group("title")
            current_subunit = None
            continue

        subunit_match = SUBUNIT_RE.match(line)
        if subunit_match:
            finish_page()
            current_subunit = subunit_match.group("title")
            continue

        page_match = PAGE_RE.match(line)
        if page_match:
            finish_page()
            current_page = TextbookPage(
                unit=current_unit,
                subunit=current_subunit,
                page=int(page_match.group("page")),
                activity_area=page_match.group("label").strip(),
            )
            continue

        section_match = SECTION_RE.match(line)
        if section_match and current_page:
            finish_section()
            current_section = Section(section_match.group("title").strip())
            continue

        if current_section:
            current_section.lines.append(line)

    finish_page()
    return pages


def parse_grammar_pages(lines: list[str]) -> list[GrammarPage]:
    current_page: GrammarPage | None = None
    current_section: Section | None = None
    pages: list[GrammarPage] = []

    def finish_section() -> None:
        nonlocal current_section
        if current_page and current_section:
            current_section.lines = clean_lines(current_section.lines)
            current_page.sections.append(current_section)
        current_section = None

    def finish_page() -> None:
        nonlocal current_page
        finish_section()
        if current_page:
            pages.append(current_page)
        current_page = None

    for line in lines:
        page_match = PAGE_RE.match(line)
        if page_match:
            finish_page()
            current_page = GrammarPage(
                page=int(page_match.group("page")),
                chapter_label=page_match.group("label").strip(),
            )
            continue
        section_match = SECTION_RE.match(line)
        if section_match and current_page:
            finish_section()
            current_section = Section(section_match.group("title").strip())
            continue
        if current_section:
            current_section.lines.append(line)

    finish_page()
    return pages


def merge_sections(sections: list[Section]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "passages": [],
        "listening_scripts": [],
        "questions": [],
        "grammar_expressions": [],
        "grammar_items": [],
        "grammar_forms": [],
        "vocabulary": [],
        "contents": [],
        "tables": [],
        "pronunciation": [],
        "self_evaluation": [],
        "examples": [],
        "explanations": [],
        "usage": [],
        "raw_sections": [],
    }
    for section in sections:
        text = join_text(section.lines)
        if not text:
            continue
        field = SECTION_FIELD_MAP.get(section.title)
        record["raw_sections"].append({"title": section.title, "text": text})
        if field == "questions":
            record[field].extend(split_question_items(section.lines))
        elif field == "vocabulary":
            record[field].extend(split_vocab_lines(section.lines))
        elif field in {"grammar_expressions", "grammar_items", "grammar_forms"}:
            record[field].extend(split_simple_lines(section.lines))
        elif field:
            record.setdefault(field, []).append(text)
        else:
            record.setdefault("other_sections", []).append({"title": section.title, "text": text})
    return record


def build_textbook_records(path: Path) -> list[dict[str, Any]]:
    pages = parse_sectioned_pages(read_lines(path))
    records: list[dict[str, Any]] = []
    for idx, page in enumerate(pages, start=1):
        merged = merge_sections(page.sections)
        activity = normalize_activity(page.activity_area)
        u = unit_no(page.unit) or 0
        sub = (subunit_no(page.subunit) or "intro").replace("-", "_")
        text_parts = []
        for key in ("passages", "listening_scripts", "questions", "contents", "grammar_expressions", "vocabulary"):
            values = merged.get(key) or []
            if values:
                text_parts.append("\n".join(str(value) for value in values))
        text = "\n\n".join(text_parts).strip()
        if not text:
            text = "\n".join(
                part
                for part in [
                    page.unit,
                    page.subunit,
                    f"p.{page.page}",
                    page.activity_area,
                ]
                if part
            )
        records.append(
            {
                "id": f"snu3a_textbook_u{u:02d}_{sub}_p{page.page:03d}_{activity}_{idx:03d}",
                "collection": "textbook_knowledge",
                "source_file": path.name,
                "source_type": "textbook",
                "source": BOOK_SOURCE,
                "unit": page.unit,
                "unit_no": unit_no(page.unit),
                "subunit": page.subunit,
                "subunit_no": subunit_no(page.subunit),
                "page": page.page,
                "activity_area": page.activity_area,
                "object_type": activity,
                **merged,
                "text": text,
            }
        )
    return records


def split_vocab_entry(line: str) -> tuple[str, str | None]:
    line = line.strip()
    if not line:
        return "", None
    match = re.search(r"\s+(?=(?:to|the|a|an|one|by|plan|article|Business|domestic|advanced|same-day)\b)", line)
    if match:
        return line[: match.start()].strip(), line[match.start() :].strip()
    match = re.search(r"\s+([A-Za-z].*)$", line)
    if match:
        return line[: match.start()].strip(), match.group(1).strip()
    return line, None


def build_vocab_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    idx = 0
    for line in read_lines(path):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        idx += 1
        headword, gloss = split_vocab_entry(stripped)
        records.append(
            {
                "id": f"snu3a_vocab_{idx:04d}",
                "collection": "textbook_knowledge",
                "source_file": path.name,
                "source_type": "vocabulary_index",
                "source": BOOK_SOURCE,
                "headword": headword,
                "gloss": gloss,
                "entry": stripped,
                "text": stripped,
            }
        )
    return records


def build_grammar_records(path: Path) -> list[dict[str, Any]]:
    pages = parse_grammar_pages(read_lines(path))
    records: list[dict[str, Any]] = []
    for idx, page in enumerate(pages, start=1):
        merged = merge_sections(page.sections)
        ch = chapter_no(page.chapter_label)
        text_parts = []
        for key in ("grammar_items", "examples", "explanations", "usage"):
            values = merged.get(key) or []
            if values:
                text_parts.append("\n\n".join(str(value) for value in values))
        records.append(
            {
                "id": f"snu3a_grammar_ch{ch or 0:02d}_p{page.page:03d}_{idx:03d}",
                "collection": "textbook_knowledge",
                "source_file": path.name,
                "source_type": "grammar_explanation",
                "source": BOOK_SOURCE,
                "unit": f"{ch}단원" if ch else page.chapter_label,
                "unit_no": ch,
                "page": page.page,
                "chapter_label": page.chapter_label,
                "object_type": "grammar_explanation",
                **merged,
                "text": "\n\n".join(text_parts).strip(),
            }
        )
    return records


def parse_question_id(raw_id: str) -> dict[str, Any]:
    match = re.match(r"^(?P<year>\d{4})-(?P<round>[^-]+)-(?P<num>\d+)$", raw_id)
    if not match:
        return {"year": None, "round": None, "item_no": None}
    return {
        "year": int(match.group("year")),
        "round": match.group("round"),
        "item_no": int(match.group("num")),
    }


def finish_question_item(
    records: list[dict[str, Any]],
    path: Path,
    category: str | None,
    raw_id: str | None,
    body_lines: list[str],
    occurrence: int,
) -> None:
    if not raw_id:
        return
    passage_lines: list[str] = []
    stem_lines: list[str] = []
    options: dict[str, str] = {}
    mode: str | None = None
    current_option: str | None = None

    for line in body_lines:
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        bold = BOLD_RE.match(stripped)
        if bold:
            label = bold.group("label").strip()
            mode = "passage" if label == "지문" else "stem"
            current_option = None
            if mode == "stem":
                stem_lines.append(label)
            continue
        option = OPTION_RE.match(stripped)
        if option:
            current_option = option.group("num")
            options[current_option] = option.group("text").strip()
            mode = "options"
            continue
        if mode == "passage":
            passage_lines.append(stripped)
        elif mode == "stem":
            stem_lines.append(stripped)
        elif mode == "options" and current_option:
            options[current_option] = f"{options[current_option]} {stripped}".strip()
        else:
            passage_lines.append(stripped)

    parsed_id = parse_question_id(raw_id)
    category_slug = normalize_slug(category or "uncategorized")
    safe_raw_id = normalize_slug(raw_id)
    passage = join_text(passage_lines)
    stem = join_text(stem_lines)
    records.append(
        {
            "id": f"topik_{category_slug}_{safe_raw_id}_{occurrence:03d}",
            "collection": "sample_question",
            "source_file": path.name,
            "source_type": "topik_sample_question",
            "source": TOPIK_SOURCE,
            "macro_type": category,
            "year": parsed_id["year"],
            "round": parsed_id["round"],
            "item_no": parsed_id["item_no"],
            "raw_item_id": raw_id,
            "passage": passage,
            "stem": stem,
            "options": options,
            "answer": None,
            "answer_generated": None,
            "answer_verified": False,
            "rationale": {},
            "rationale_generated": {},
            "rationale_verified": False,
            "text": "\n\n".join(part for part in [passage, stem, "\n".join(f"{k}. {v}" for k, v in options.items())] if part),
        }
    )


def build_question_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    category: str | None = None
    raw_id: str | None = None
    body_lines: list[str] = []
    seen_ids: dict[str, int] = {}

    def flush() -> None:
        nonlocal body_lines
        if raw_id:
            key = f"{category or ''}:{raw_id}"
            occurrence = seen_ids.get(key, 0) + 1
            seen_ids[key] = occurrence
            finish_question_item(records, path, category, raw_id, body_lines, occurrence)
        body_lines = []

    for line in read_lines(path):
        category_match = QUESTION_CATEGORY_RE.match(line)
        if category_match:
            flush()
            category = category_match.group("title").strip()
            raw_id = None
            continue
        item_match = QUESTION_ID_RE.match(line)
        if item_match:
            flush()
            raw_id = item_match.group("qid").strip()
            continue
        if raw_id:
            body_lines.append(line)

    flush()
    return records


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def default_paths(base_dir: Path) -> dict[str, Path]:
    return {
        "textbook": base_dir / "textbook.md",
        "vocab": base_dir / "vocab.md",
        "grammar": base_dir / "grammar.md",
        "questions": base_dir / "sample_question.md",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert RAG source Markdown files to JSONL.")
    default_source_dir = Path.cwd() / "source_md"
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Deprecated alias for --source-dir.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Directory containing textbook.md, vocab.md, grammar.md, sample_question.md.",
    )
    parser.add_argument("-o", "--output-dir", type=Path, default=Path.cwd() / "rag_jsonl_output", help="Output directory.")
    parser.add_argument("--textbook", type=Path, help="Override textbook.md path.")
    parser.add_argument("--vocab", type=Path, help="Override vocab.md path.")
    parser.add_argument("--grammar", type=Path, help="Override grammar.md path.")
    parser.add_argument("--questions", type=Path, help="Override sample_question.md path.")
    args = parser.parse_args(argv)

    source_dir = args.source_dir or args.base_dir or default_source_dir
    paths = default_paths(source_dir)
    for key in ("textbook", "vocab", "grammar", "questions"):
        override = getattr(args, key)
        if override:
            paths[key] = override

    textbook_records = build_textbook_records(paths["textbook"])
    vocab_records = build_vocab_records(paths["vocab"])
    grammar_records = build_grammar_records(paths["grammar"])
    question_records = build_question_records(paths["questions"])
    knowledge_records = textbook_records + vocab_records + grammar_records

    outputs = {
        "textbook": args.output_dir / "textbook.jsonl",
        "vocab": args.output_dir / "vocab.jsonl",
        "grammar": args.output_dir / "grammar.jsonl",
        "textbook_knowledge": args.output_dir / "textbook_knowledge.jsonl",
        "sample_question": args.output_dir / "sample_question.jsonl",
    }
    write_jsonl(textbook_records, outputs["textbook"])
    write_jsonl(vocab_records, outputs["vocab"])
    write_jsonl(grammar_records, outputs["grammar"])
    write_jsonl(knowledge_records, outputs["textbook_knowledge"])
    write_jsonl(question_records, outputs["sample_question"])

    summary = {
        "outputs": {key: str(value) for key, value in outputs.items()},
        "counts": {
            "textbook": len(textbook_records),
            "vocab": len(vocab_records),
            "grammar": len(grammar_records),
            "textbook_knowledge": len(knowledge_records),
            "sample_question": len(question_records),
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
