"""Generate Korean assessment items from prompt package JSONL files.

Only the OpenAI provider is implemented. Provider calls are isolated so other
providers can be added later without changing parsing, validation, or export.
API keys are read only from environment variables and are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
QUESTION_SCHEMA_PATH = Path("docs") / "question_type_schema.json"


EXPECTED_OUTPUT_SCHEMA: dict[str, Any] = {
    "item_id": "string",
    "prompt_id": "string",
    "unit": "integer",
    "passage_id": "string",
    "skill": "reading | listening",
    "comprehension_type": "factual | inferential | evaluative",
    "comprehension_type_label": "사실적 문항 | 추론적 문항 | 평가적 문항",
    "stem_type": "string from docs/question_type_schema.json",
    "stem_template": "string from the selected stem_type templates or close variant",
    "question": "string",
    "options": ["string", "string", "string", "string"],
    "answer": "integer from 1 to 4",
    "rationale": "string",
    "evidence": "string",
    "grammar_constraints_used": ["string"],
    "vocabulary_constraints_used": ["string"],
    "difficulty": "easy | medium | hard",
    "difficulty_rationale": "string",
    "teacher_edit_suggestions": ["string"],
    "generation_model": "string",
    "generated_at": "ISO-8601 timestamp",
}


class GenerationError(Exception):
    """Recoverable generation error for one prompt package."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate item JSONL/Markdown from prompt package JSONL.")
    parser.add_argument("--input", required=True, help="Prompt package JSONL path.")
    parser.add_argument("--output-dir", default="reports/generated_item_samples")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--mock-response-text", default=None, help=argparse.SUPPRESS)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
            if not isinstance(value, dict):
                raise SystemExit(f"Expected object at {path}:{line_no}")
            records.append(value)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def safe_stem(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", path.stem).strip("_")


def ensure_can_write(paths: list[Path], overwrite: bool) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing and not overwrite:
        joined = "\n".join(f"- {path}" for path in existing)
        raise SystemExit(f"Output file(s) already exist. Use --overwrite to replace them:\n{joined}")


def load_question_schema(path: Path = QUESTION_SCHEMA_PATH) -> dict[str, dict[str, Any]]:
    schema = read_json(path)
    if not isinstance(schema, list):
        raise SystemExit("docs/question_type_schema.json must contain a list.")
    return {str(record["stem_type"]): record for record in schema}


def get_prompt_text(package: dict[str, Any]) -> str:
    prompt = package.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise GenerationError("prompt field is missing or empty")
    return prompt.strip()


def get_item_count(package: dict[str, Any]) -> int:
    try:
        count = int(package.get("item_count", 1))
    except (TypeError, ValueError):
        count = 1
    return max(1, count)


def get_question_requests(package: dict[str, Any]) -> list[dict[str, Any]]:
    requests = package.get("requested_questions") or package.get("question_requests")
    if isinstance(requests, list):
        return [request for request in requests if isinstance(request, dict)]

    # Compatibility for prompt packages created before the schema migration.
    old_types = package.get("item_types", [])
    if isinstance(old_types, str):
        old_types = [part.strip() for part in old_types.split(",")]
    legacy_map = {
        "content_match": ("factual", "사실적 문항", "내용 일치"),
        "detail_info": ("factual", "사실적 문항", "세부 내용 파악"),
        "sequence": ("factual", "사실적 문항", "순서 파악"),
        "blank_completion": ("factual", "사실적 문항", "빈칸 내용 파악"),
        "main_idea": ("inferential", "추론적 문항", "주제 파악"),
        "inference": ("inferential", "추론적 문항", "내용 추론"),
    }
    converted = []
    for old_type in old_types if isinstance(old_types, list) else []:
        mapped = legacy_map.get(str(old_type))
        if mapped:
            comprehension_type, label, stem_type = mapped
            converted.append(
                {
                    "comprehension_type": comprehension_type,
                    "comprehension_type_label": label,
                    "stem_type": stem_type,
                    "stem_templates": [],
                    "difficulty": "medium",
                }
            )
    return converted


def build_provider_prompt(package: dict[str, Any]) -> str:
    question_requests = get_question_requests(package)
    request_summary = [
        {
            "comprehension_type": request.get("comprehension_type"),
            "stem_type": request.get("stem_type"),
            "stem_templates": request.get("stem_templates", []),
            "difficulty": request.get("difficulty"),
        }
        for request in question_requests
    ]
    item_count = get_item_count(package)
    schema = json.dumps(EXPECTED_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
    return (
        "You are generating Korean language assessment items for a teacher.\n"
        "Return ONLY valid JSON. Do not wrap the JSON in Markdown fences.\n"
        f"There are {item_count} requested question(s).\n"
        "Return a JSON object with two lists: items and skipped_requests.\n"
        "Generate an item only when the requested question type is suitable for the passage.\n"
        "If a request is unsuitable, put it in skipped_requests instead of forcing an item.\n"
        "At least one of items or skipped_requests must be non-empty.\n"
        "Each item must follow one requested question type.\n"
        "Use the existing passage only. Do not create or modify the passage.\n"
        "Use options as a 4-element array and answer as an integer from 1 to 4.\n"
        "Use rationale, evidence, difficulty_rationale as non-empty strings.\n"
        "Use teacher_edit_suggestions as an array, even if empty.\n\n"
        "Requested question types:\n"
        f"{json.dumps(request_summary, ensure_ascii=False, indent=2)}\n\n"
        "Required output schema:\n"
        f"{schema}\n\n"
        "Prompt package:\n"
        f"{get_prompt_text(package)}"
    )


def call_provider(
    provider: str,
    prompt: str,
    model: str,
    temperature: float,
    mock_response_text: str | None = None,
) -> str:
    if mock_response_text is not None:
        return mock_response_text
    if provider != "openai":
        raise GenerationError(f"Unsupported provider: {provider}")
    return call_openai_responses(prompt=prompt, model=model, temperature=temperature)


def call_openai_responses(prompt: str, model: str, temperature: float) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise GenerationError("OPENAI_API_KEY is not set")

    payload = {"model": model, "input": prompt, "temperature": temperature}
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GenerationError(f"OpenAI HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise GenerationError(f"OpenAI connection error: {exc.reason}") from exc

    try:
        response_json = json.loads(response_body)
    except json.JSONDecodeError:
        return response_body
    return extract_response_text(response_json)


def extract_response_text(response_json: dict[str, Any]) -> str:
    output_text = response_json.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    pieces: list[str] = []
    output = response_json.get("output", [])
    if isinstance(output, list):
        for output_item in output:
            if not isinstance(output_item, dict):
                continue
            content = output_item.get("content", [])
            if isinstance(content, list):
                for content_item in content:
                    if isinstance(content_item, dict) and isinstance(content_item.get("text"), str):
                        pieces.append(content_item["text"])
    return "\n".join(pieces) if pieces else json.dumps(response_json, ensure_ascii=False)


def parse_json_response(text: str) -> Any:
    candidates = [text.strip()]
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidates.append(fence_match.group(1).strip())
    stripped = text.strip()
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start = stripped.find(start_char)
        end = stripped.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            candidates.append(stripped[start : end + 1])

    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
    if last_error is None:
        raise GenerationError("Empty response")
    raise GenerationError(f"JSON parse failed: {last_error}")


def normalize_options(options: Any) -> list[str]:
    if isinstance(options, list):
        return [str(value).strip() for value in options]
    if isinstance(options, dict):
        normalized: list[str] = []
        for key in ["1", "2", "3", "4", 1, 2, 3, 4]:
            if key in options:
                normalized.append(str(options[key]).strip())
        return normalized
    return []


def normalize_answer(answer: Any) -> int | None:
    if isinstance(answer, int):
        return answer
    if isinstance(answer, str):
        match = re.search(r"[1-4]", answer)
        if match:
            return int(match.group(0))
    return None


def normalize_rationale(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts = []
        for key in sorted(value.keys(), key=lambda item: str(item)):
            text = str(value[key]).strip()
            if text:
                parts.append(f"{key}: {text}")
        return "\n".join(parts)
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return ""


def normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_generated_payload(payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if isinstance(payload, list):
        items = payload
        skipped_requests = []
    elif isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            items = payload["items"]
            skipped_requests = payload.get("skipped_requests", [])
        elif isinstance(payload.get("generated_items"), list):
            items = payload["generated_items"]
            skipped_requests = payload.get("skipped_requests", [])
        elif isinstance(payload.get("skipped_requests"), list):
            items = []
            skipped_requests = payload["skipped_requests"]
        else:
            items = [payload]
            skipped_requests = []
    else:
        raise GenerationError("Parsed JSON is not an object or array")
    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            raise GenerationError("Parsed item is not an object")
        normalized_items.append(item)
    normalized_skips = []
    if not isinstance(skipped_requests, list):
        raise GenerationError("skipped_requests must be a list")
    for skipped_request in skipped_requests:
        if not isinstance(skipped_request, dict):
            raise GenerationError("skipped_request is not an object")
        normalized_skips.append(skipped_request)
    if not normalized_items and not normalized_skips:
        raise GenerationError("At least one of items or skipped_requests must be non-empty")
    return normalized_items, normalized_skips


def request_for_index(package: dict[str, Any], item_index: int) -> dict[str, Any]:
    requests = get_question_requests(package)
    if not requests:
        return {}
    return requests[min(item_index - 1, len(requests) - 1)]


def stem_template_allowed(stem_template: str, stem_type: str, schema_lookup: dict[str, dict[str, Any]]) -> bool:
    if not stem_template:
        return False
    templates = schema_lookup.get(stem_type, {}).get("stem_templates", [])
    if stem_template in templates:
        return True
    normalized = stem_template.replace(" ", "")
    return any(template.replace(" ", "") in normalized or normalized in template.replace(" ", "") for template in templates)


def enrich_and_validate_item(
    raw_item: dict[str, Any],
    package: dict[str, Any],
    item_index: int,
    model: str,
    generated_at: str,
    schema_lookup: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    request = request_for_index(package, item_index)
    stem_type = str(raw_item.get("stem_type") or request.get("stem_type") or "").strip()
    schema_entry = schema_lookup.get(stem_type, {})
    comprehension_type = str(
        raw_item.get("comprehension_type")
        or request.get("comprehension_type")
        or schema_entry.get("comprehension_type")
        or ""
    ).strip()
    label = str(
        raw_item.get("comprehension_type_label")
        or request.get("comprehension_type_label")
        or schema_entry.get("comprehension_type_label")
        or ""
    ).strip()
    templates = schema_entry.get("stem_templates", [])
    stem_template = str(raw_item.get("stem_template") or (templates[0] if templates else "")).strip()

    prompt_id = str(package.get("prompt_id", "prompt")).strip()
    passage_id = str(package.get("passage_id", "")).strip()
    item_id = f"item_{prompt_id}_{item_index:03d}"

    item = {
        "item_id": item_id,
        "prompt_id": prompt_id,
        "unit": package.get("unit"),
        "passage_id": passage_id,
        "skill": package.get("skill"),
        "comprehension_type": comprehension_type,
        "comprehension_type_label": label,
        "stem_type": stem_type,
        "stem_template": stem_template,
        "question": str(raw_item.get("question") or raw_item.get("stem") or stem_template).strip(),
        "options": normalize_options(raw_item.get("options")),
        "answer": normalize_answer(raw_item.get("answer")),
        "rationale": normalize_rationale(raw_item.get("rationale")),
        "evidence": str(raw_item.get("evidence") or "").strip(),
        "grammar_constraints_used": normalize_list(raw_item.get("grammar_constraints_used") or raw_item.get("used_grammar")),
        "vocabulary_constraints_used": normalize_list(raw_item.get("vocabulary_constraints_used") or raw_item.get("used_vocabulary")),
        "difficulty": str(raw_item.get("difficulty") or request.get("difficulty") or "medium").strip(),
        "difficulty_rationale": str(raw_item.get("difficulty_rationale") or "").strip(),
        "teacher_edit_suggestions": normalize_list(raw_item.get("teacher_edit_suggestions")),
        "generation_model": model,
        "generated_at": generated_at,
    }

    errors: list[str] = []
    if item["comprehension_type"] not in {"factual", "inferential", "evaluative"}:
        errors.append("comprehension_type must be factual, inferential, or evaluative")
    if item["stem_type"] not in schema_lookup:
        errors.append("stem_type must exist in docs/question_type_schema.json")
    if stem_type in schema_lookup and schema_lookup[stem_type]["comprehension_type"] != item["comprehension_type"]:
        errors.append("comprehension_type must match the selected stem_type")
    if stem_type in schema_lookup and not stem_template_allowed(item["stem_template"], stem_type, schema_lookup):
        errors.append("stem_template must match or closely follow the selected stem_type templates")
    if item["answer"] not in {1, 2, 3, 4}:
        errors.append("answer must be an integer from 1 to 4")
    if len(item["options"]) != 4 or any(not option for option in item["options"]):
        errors.append("options must contain exactly four non-empty strings")
    for field in ["question", "rationale", "evidence", "difficulty_rationale"]:
        if not item[field]:
            errors.append(f"{field} must not be empty")
    return item, errors


def enrich_and_validate_skipped_request(
    raw_skip: dict[str, Any],
    package: dict[str, Any],
    skip_index: int,
    model: str,
    generated_at: str,
    schema_lookup: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    stem_type = str(raw_skip.get("stem_type") or "").strip()
    schema_entry = schema_lookup.get(stem_type, {})
    comprehension_type = str(
        raw_skip.get("comprehension_type")
        or schema_entry.get("comprehension_type")
        or ""
    ).strip()
    requested_difficulty = str(raw_skip.get("requested_difficulty") or raw_skip.get("difficulty") or "").strip()
    suggested_alternatives = raw_skip.get("suggested_alternatives", [])
    if not isinstance(suggested_alternatives, list):
        suggested_alternatives = []

    skipped = {
        "skip_id": f"skip_{package.get('prompt_id', 'prompt')}_{skip_index:03d}",
        "prompt_id": package.get("prompt_id"),
        "unit": package.get("unit"),
        "passage_id": package.get("passage_id"),
        "skill": package.get("skill"),
        "comprehension_type": comprehension_type,
        "stem_type": stem_type,
        "requested_difficulty": requested_difficulty,
        "reason": str(raw_skip.get("reason") or "").strip(),
        "suggested_alternatives": suggested_alternatives,
        "generation_model": model,
        "generated_at": generated_at,
    }

    errors: list[str] = []
    if skipped["comprehension_type"] not in {"factual", "inferential", "evaluative"}:
        errors.append("skipped_request comprehension_type must be factual, inferential, or evaluative")
    if skipped["stem_type"] not in schema_lookup:
        errors.append("skipped_request stem_type must exist in docs/question_type_schema.json")
    if stem_type in schema_lookup and schema_lookup[stem_type]["comprehension_type"] != skipped["comprehension_type"]:
        errors.append("skipped_request comprehension_type must match the selected stem_type")
    if not skipped["reason"]:
        errors.append("skipped_request reason must not be empty")
    if not isinstance(skipped["suggested_alternatives"], list):
        errors.append("skipped_request suggested_alternatives must be a list")
    return skipped, errors


def write_raw_response(raw_dir: Path, prompt_id: str, text: str) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    safe_prompt_id = re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", prompt_id).strip("_") or "prompt"
    path = raw_dir / f"{safe_prompt_id}_raw_response.txt"
    path.write_text(text, encoding="utf-8")
    return path


def format_markdown(
    items: list[dict[str, Any]],
    skipped_requests: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> str:
    lines = ["# Generated Item Samples", ""]
    if items:
        for item in items:
            lines.extend(
                [
                    f"## {item['item_id']}",
                    "",
                    f"- prompt_id: `{item['prompt_id']}`",
                    f"- passage_id: `{item['passage_id']}`",
                    f"- unit: {item['unit']}",
                    f"- skill: {item['skill']}",
                    f"- comprehension_type: {item['comprehension_type']} ({item['comprehension_type_label']})",
                    f"- stem_type: {item['stem_type']}",
                    f"- stem_template: {item['stem_template']}",
                    f"- difficulty: {item['difficulty']}",
                    f"- answer: {item['answer']}",
                    "",
                    "### Question",
                    "",
                    item["question"],
                    "",
                    "### Options",
                    "",
                ]
            )
            for index, option in enumerate(item["options"], start=1):
                lines.append(f"{index}. {option}")
            lines.extend(
                [
                    "",
                    "### Rationale",
                    "",
                    item["rationale"],
                    "",
                    "### Evidence",
                    "",
                    item["evidence"],
                    "",
                    "### Difficulty Rationale",
                    "",
                    item["difficulty_rationale"],
                    "",
                ]
            )
    else:
        lines.extend(["No valid generated items were produced.", ""])

    lines.extend(["## Skipped Requests", ""])
    if skipped_requests:
        for skipped in skipped_requests:
            alternatives = skipped.get("suggested_alternatives", [])
            lines.extend(
                [
                    f"### {skipped['skip_id']}",
                    "",
                    f"- comprehension_type: {skipped['comprehension_type']}",
                    f"- stem_type: {skipped['stem_type']}",
                    f"- requested_difficulty: {skipped['requested_difficulty']}",
                    f"- reason: {skipped['reason']}",
                    "- suggested_alternatives:",
                ]
            )
            if alternatives:
                for alternative in alternatives:
                    lines.append(f"  - {json.dumps(alternative, ensure_ascii=False)}")
            else:
                lines.append("  - none")
            lines.append("")
    else:
        lines.extend(["No skipped requests were recorded.", ""])

    if errors:
        lines.extend(["# Errors", ""])
        for error in errors:
            lines.extend(
                [
                    f"- prompt_id: `{error.get('prompt_id')}`",
                    f"  - error_type: `{error.get('error_type')}`",
                    f"  - message: {error.get('message')}",
                ]
            )
            raw_path = error.get("raw_response_path")
            if raw_path:
                lines.append(f"  - raw_response_path: `{raw_path}`")
        lines.append("")
    return "\n".join(lines)


def write_dry_run_plan(path: Path, packages: list[dict[str, Any]], model: str, temperature: float) -> None:
    plan = {
        "mode": "dry_run",
        "model": model,
        "temperature": temperature,
        "prompt_package_count": len(packages),
        "packages": [
            {
                "prompt_id": package.get("prompt_id"),
                "unit": package.get("unit"),
                "passage_id": package.get("passage_id"),
                "skill": package.get("skill"),
                "requested_questions": get_question_requests(package),
                "suitability_hints": package.get("suitability_hints", []),
                "allow_skip": package.get("allow_skip", True),
                "item_count": get_item_count(package),
                "prompt_characters": len(get_prompt_text(package)),
            }
            for package in packages
        ],
    }
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    schema_lookup = load_question_schema()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_stem = safe_stem(input_path)

    packages = read_jsonl(input_path)
    if args.limit is not None:
        packages = packages[: max(0, args.limit)]
    if not packages:
        raise SystemExit("No prompt packages to process.")

    items_path = output_dir / f"generated_items_{input_stem}.jsonl"
    skipped_path = output_dir / f"skipped_requests_{input_stem}.jsonl"
    md_path = output_dir / f"generated_items_{input_stem}.md"
    errors_path = output_dir / f"generation_errors_{input_stem}.jsonl"
    dry_run_path = output_dir / f"dry_run_{input_stem}.json"
    raw_dir = output_dir / "raw_responses"

    if args.dry_run:
        ensure_can_write([dry_run_path], args.overwrite)
        write_dry_run_plan(dry_run_path, packages, args.model, args.temperature)
        print("Dry run completed.")
        print(f"Prompt packages: {len(packages)}")
        print(f"Model: {args.model}")
        print(f"Dry-run plan: {dry_run_path}")
        return 0

    ensure_can_write([items_path, skipped_path, md_path, errors_path], args.overwrite)

    generated_items: list[dict[str, Any]] = []
    skipped_requests: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    generated_at = datetime.now(timezone.utc).isoformat()

    for package_index, package in enumerate(packages, start=1):
        prompt_id = str(package.get("prompt_id", f"prompt_{package_index:03d}"))
        raw_text: str | None = None
        try:
            provider_prompt = build_provider_prompt(package)
            raw_text = call_provider(
                provider="openai",
                prompt=provider_prompt,
                model=args.model,
                temperature=args.temperature,
                mock_response_text=args.mock_response_text,
            )
            parsed = parse_json_response(raw_text)
            raw_items, raw_skipped_requests = normalize_generated_payload(parsed)
        except GenerationError as exc:
            raw_path = write_raw_response(raw_dir, prompt_id, raw_text) if isinstance(raw_text, str) else None
            errors.append(
                {
                    "prompt_id": prompt_id,
                    "passage_id": package.get("passage_id"),
                    "unit": package.get("unit"),
                    "error_type": "generation_or_parse_error",
                    "message": str(exc),
                    "raw_response_path": str(raw_path) if raw_path else "",
                    "generation_model": args.model,
                    "generated_at": generated_at,
                }
            )
            continue

        for item_index, raw_item in enumerate(raw_items, start=1):
            item, validation_errors = enrich_and_validate_item(
                raw_item=raw_item,
                package=package,
                item_index=item_index,
                model=args.model,
                generated_at=generated_at,
                schema_lookup=schema_lookup,
            )
            if validation_errors:
                errors.append(
                    {
                        "prompt_id": prompt_id,
                        "passage_id": package.get("passage_id"),
                        "unit": package.get("unit"),
                        "error_type": "validation_error",
                        "message": "; ".join(validation_errors),
                        "raw_item": raw_item,
                        "generation_model": args.model,
                        "generated_at": generated_at,
                    }
                )
                continue
            generated_items.append(item)

        for skip_index, raw_skip in enumerate(raw_skipped_requests, start=1):
            skipped, validation_errors = enrich_and_validate_skipped_request(
                raw_skip=raw_skip,
                package=package,
                skip_index=skip_index,
                model=args.model,
                generated_at=generated_at,
                schema_lookup=schema_lookup,
            )
            if validation_errors:
                errors.append(
                    {
                        "prompt_id": prompt_id,
                        "passage_id": package.get("passage_id"),
                        "unit": package.get("unit"),
                        "error_type": "skipped_request_validation_error",
                        "message": "; ".join(validation_errors),
                        "raw_skipped_request": raw_skip,
                        "generation_model": args.model,
                        "generated_at": generated_at,
                    }
                )
                continue
            skipped_requests.append(skipped)

    write_jsonl(items_path, generated_items)
    write_jsonl(skipped_path, skipped_requests)
    write_jsonl(errors_path, errors)
    md_path.write_text(format_markdown(generated_items, skipped_requests, errors), encoding="utf-8")

    print("Generation completed.")
    print(f"Prompt packages processed: {len(packages)}")
    print(f"Valid generated items: {len(generated_items)}")
    print(f"Skipped requests: {len(skipped_requests)}")
    print(f"Errors: {len(errors)}")
    print(f"Items JSONL: {items_path}")
    print(f"Skipped JSONL: {skipped_path}")
    print(f"Markdown: {md_path}")
    print(f"Errors JSONL: {errors_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
