#!/usr/bin/env python
"""Propose an exam blueprint from textbook passage inventory."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


READING_QUESTION_TYPES = [
    {"comprehension_type": "factual", "stem_type": "내용 일치", "stem_template": "윗글의 내용과 같은 것을 고르십시오.", "difficulty": "easy", "ratio": 0.35},
    {"comprehension_type": "factual", "stem_type": "빈칸 내용 파악", "stem_template": "( )에 들어갈 말로 가장 알맞은 것을 고르십시오.", "difficulty": "medium", "ratio": 0.15},
    {"comprehension_type": "inferential", "stem_type": "주제 파악", "stem_template": "다음을 읽고 글의 주제로 가장 알맞은 것을 고르십시오.", "difficulty": "medium", "ratio": 0.20},
    {"comprehension_type": "inferential", "stem_type": "내용 추론", "stem_template": "윗글의 내용으로 알 수 있는 것을 고르십시오.", "difficulty": "medium", "ratio": 0.15},
    {"comprehension_type": "evaluative", "stem_type": "필자 태도 평가", "stem_template": "밑줄 친 부분에 나타난 필자의 태도로 알맞은 것을 고르십시오.", "difficulty": "hard", "ratio": 0.15},
]

LISTENING_QUESTION_TYPES = [
    {"comprehension_type": "factual", "stem_type": "내용 일치", "stem_template": "다음을 읽고 글의 내용과 같은 것을 고르십시오.", "difficulty": "easy", "ratio": 0.45},
    {"comprehension_type": "factual", "stem_type": "세부 내용 파악", "stem_template": "무엇에 대한 내용인지 맞는 것을 고르십시오.", "difficulty": "easy", "ratio": 0.25},
    {"comprehension_type": "inferential", "stem_type": "내용 추론", "stem_template": "윗글의 내용으로 알 수 있는 것을 고르십시오.", "difficulty": "medium", "ratio": 0.20},
    {"comprehension_type": "evaluative", "stem_type": "심정/기분 평가", "stem_template": "밑줄 친 부분에 나타난 나의 심정으로 알맞은 것을 고르십시오.", "difficulty": "medium", "ratio": 0.10},
]


def parse_units(spec: str) -> list[int]:
    if "-" in spec:
        start, end = spec.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(spec)]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def allocate_by_weight(total: int, units: list[dict[str, Any]], weight_key: str, minimum_one: bool) -> dict[int, int]:
    allocation = {unit["unit_no"]: 0 for unit in units}
    eligible = [unit for unit in units if unit[weight_key] > 0]
    if total <= 0 or not eligible:
        return allocation

    if minimum_one:
        for unit in eligible:
            allocation[unit["unit_no"]] = 1
        remaining = total - len(eligible)
        if remaining < 0:
            # If there are more eligible units than items, assign to highest-weight units only.
            allocation = {unit["unit_no"]: 0 for unit in units}
            ranked = sorted(eligible, key=lambda unit: (unit[weight_key], -unit["unit_no"]), reverse=True)
            for unit in ranked[:total]:
                allocation[unit["unit_no"]] = 1
            return allocation
    else:
        remaining = total

    weight_sum = sum(unit[weight_key] for unit in eligible)
    raw = [(unit, remaining * unit[weight_key] / weight_sum if weight_sum else 0) for unit in eligible]
    for unit, value in raw:
        add = math.floor(value)
        allocation[unit["unit_no"]] += add
        remaining -= add
    for unit, _ in sorted(raw, key=lambda item: (item[1] - math.floor(item[1]), item[0][weight_key]), reverse=True):
        if remaining <= 0:
            break
        allocation[unit["unit_no"]] += 1
        remaining -= 1
    return allocation


def split_total(total: int, reading_ratio: float, listening_ratio: float, has_reading: bool, has_listening: bool) -> tuple[int, int]:
    if not has_reading:
        return 0, total
    if not has_listening:
        return total, 0
    ratio_sum = reading_ratio + listening_ratio
    if ratio_sum <= 0:
        reading_ratio, listening_ratio, ratio_sum = 1.0, 0.0, 1.0
    reading_total = round(total * reading_ratio / ratio_sum)
    listening_total = total - reading_total
    return reading_total, listening_total


def allocate_question_types(total: int, question_types: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if total <= 0:
        return [{key: value for key, value in question_type.items() if key != "ratio"} | {"count": 0} for question_type in question_types]
    allocation = [math.floor(total * question_type["ratio"]) for question_type in question_types]
    remaining = total - sum(allocation)
    ranked = sorted(
        range(len(question_types)),
        key=lambda index: (total * question_types[index]["ratio"]) - math.floor(total * question_types[index]["ratio"]),
        reverse=True,
    )
    for index in ranked:
        if remaining <= 0:
            break
        allocation[index] += 1
        remaining -= 1
    result = []
    for question_type, count in zip(question_types, allocation):
        entry = {key: value for key, value in question_type.items() if key != "ratio"}
        entry["count"] = count
        result.append(entry)
    return result


def propose(units_spec: str, total_items: int, reading_ratio: float, listening_ratio: float, inventory_path: Path) -> dict[str, Any]:
    inventory = load_json(inventory_path)
    selected_numbers = parse_units(units_spec)
    units = [unit for unit in inventory["units"] if unit["unit_no"] in selected_numbers]
    if not units:
        raise ValueError(f"No units matched: {units_spec}")

    for unit in units:
        unit["blueprint_reading_count"] = unit.get("usable_reading_passage_count", unit["reading_passage_count"])
        unit["blueprint_listening_count"] = unit.get("usable_listening_passage_count", unit["listening_passage_count"])

    has_reading = any(unit["blueprint_reading_count"] > 0 for unit in units)
    has_listening = any(unit["blueprint_listening_count"] > 0 for unit in units)
    reading_total, listening_total = split_total(total_items, reading_ratio, listening_ratio, has_reading, has_listening)

    reading_alloc = allocate_by_weight(reading_total, units, "blueprint_reading_count", minimum_one=reading_total >= len([u for u in units if u["blueprint_reading_count"] > 0]))
    listening_alloc = allocate_by_weight(listening_total, units, "blueprint_listening_count", minimum_one=listening_total >= len([u for u in units if u["blueprint_listening_count"] > 0]))

    unit_blueprints = []
    for unit in units:
        reading_items = reading_alloc[unit["unit_no"]]
        listening_items = listening_alloc[unit["unit_no"]]
        unit_blueprints.append(
            {
                "unit_no": unit["unit_no"],
                "unit_title": unit.get("unit_title"),
                "reading_passage_count": unit["reading_passage_count"],
                "listening_passage_count": unit["listening_passage_count"],
                "usable_reading_passage_count": unit["blueprint_reading_count"],
                "usable_listening_passage_count": unit["blueprint_listening_count"],
                "reading_items": reading_items,
                "listening_items": listening_items,
                "total_items": reading_items + listening_items,
            }
        )

    return {
        "units": selected_numbers,
        "total_items": total_items,
        "reading_ratio": reading_ratio,
        "listening_ratio": listening_ratio,
        "reading_items": sum(unit["reading_items"] for unit in unit_blueprints),
        "listening_items": sum(unit["listening_items"] for unit in unit_blueprints),
        "reading_question_types": allocate_question_types(sum(unit["reading_items"] for unit in unit_blueprints), READING_QUESTION_TYPES),
        "listening_question_types": allocate_question_types(sum(unit["listening_items"] for unit in unit_blueprints), LISTENING_QUESTION_TYPES),
        "unit_blueprints": unit_blueprints,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose a textbook-based exam blueprint.")
    parser.add_argument("--units", required=True, help="Unit range, e.g. 1-9, 3, 3-5.")
    parser.add_argument("--total-items", type=int, required=True)
    parser.add_argument("--reading-ratio", type=float, default=0.7)
    parser.add_argument("--listening-ratio", type=float, default=0.3)
    parser.add_argument("--inventory", type=Path, default=Path.cwd() / "reports" / "textbook_inventory.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    blueprint = propose(args.units, args.total_items, args.reading_ratio, args.listening_ratio, args.inventory)
    text = json.dumps(blueprint, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
