"""Generate Korean assessment items from prompt package JSONL files.

This script intentionally implements only the OpenAI provider for now. The
provider call is isolated so other providers can be added later without
changing the prompt loading, parsing, validation, or export flow.
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


EXPECTED_OUTPUT_SCHEMA: dict[str, Any] = {
    "item_id": "string",
    "prompt_id": "string",
    "unit": "integer",
    "passage_id": "string",
    "skill": "reading | listening",
    "item_type": "content_match | detail_info | main_idea | inference | blank_completion | other requested type",
    "question": "string",
    "options": ["string", "string", "string", "string"],
    "answer": "integer from 1 to 4",
    "rationale": "string",
    "evidence": "string",
    "grammar_constraints_used": ["string"],
    "vocabulary_constraints_used": ["string"],
    "difficulty": "easy | medium | hard",
    "generation_model": "string",
    "generated_at": "ISO-8601 timestamp",
}


class GenerationError(Exception):
    """Recoverable generation error for one prompt package."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate item JSONL/Markdown from prompt package JSONL."
    )
    parser.add_argument("--input", required=True, help="Prompt package JSONL path.")
    parser.add_argument(
        "--output-dir",
        default="reports/generated_item_samples",
        help="Directory for generated item outputs.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="OpenAI model name. Defaults to OPENAI_MODEL or gpt-4.1-mini.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read prompts and print/write an execution plan without API calls.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first n prompt packages.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Generation temperature.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    parser.add_argument(
        "--mock-response-text",
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


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
        raise SystemExit(
            "Output file(s) already exist. Use --overwrite to replace them:\n"
            f"{joined}"
        )


def get_prompt_text(package: dict[str, Any]) -> str:
    prompt = package.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise GenerationError("prompt field is missing or empty")
    return prompt.strip()


def get_requested_item_types(package: dict[str, Any]) -> list[str]:
    item_types = package.get("item_types", [])
    if isinstance(item_types, str):
        item_types = [part.strip() for part in item_types.split(",")]
    if not isinstance(item_types, list):
        return []
    return [str(item_type).strip() for item_type in item_types if str(item_type).strip()]


def get_item_count(package: dict[str, Any]) -> int:
    try:
        count = int(package.get("item_count", 1))
    except (TypeError, ValueError):
        count = 1
    return max(1, count)


def build_provider_prompt(package: dict[str, Any]) -> str:
    requested_types = get_requested_item_types(package)
    requested_types_text = ", ".join(requested_types) if requested_types else "(prompt package item_types)"
    item_count = get_item_count(package)
    schema = json.dumps(EXPECTED_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
    return (
        "You are generating Korean language assessment items for a teacher.\n"
        "Return ONLY valid JSON. Do not wrap the JSON in Markdown fences.\n"
        f"Return a JSON array with exactly {item_count} item object(s).\n"
        f"Each item_type must be one of: {requested_types_text}.\n"
        "Use the existing passage only. Do not create or modify the passage.\n"
        "Use options as a 4-element array and answer as an integer from 1 to 4.\n"
        "Use rationale and evidence as non-empty strings.\n\n"
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

    payload = {
        "model": model,
        "input": prompt,
        "temperature": temperature,
    }
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
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
                    if not isinstance(content_item, dict):
                        continue
                    text = content_item.get("text")
                    if isinstance(text, str):
                        pieces.append(text)
    if pieces:
        return "\n".join(pieces)
    return json.dumps(response_json, ensure_ascii=False)


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
        if normalized:
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


def normalize_generated_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            items = payload["items"]
        elif isinstance(payload.get("generated_items"), list):
            items = payload["generated_items"]
        else:
            items = [payload]
    else:
        raise GenerationError("Parsed JSON is not an object or array")
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            raise GenerationError("Parsed item is not an object")
        normalized.append(item)
    return normalized


def enrich_and_validate_item(
    raw_item: dict[str, Any],
    package: dict[str, Any],
    item_index: int,
    model: str,
    generated_at: str,
) -> tuple[dict[str, Any], list[str]]:
    requested_types = get_requested_item_types(package)
    item_type = str(raw_item.get("item_type") or "").strip()
    if not item_type and len(requested_types) == 1:
        item_type = requested_types[0]

    prompt_id = str(package.get("prompt_id", "prompt")).strip()
    passage_id = str(package.get("passage_id", "")).strip()
    item_id = f"item_{prompt_id}_{item_index:03d}"

    item = {
        "item_id": item_id,
        "prompt_id": prompt_id,
        "unit": package.get("unit"),
        "passage_id": passage_id,
        "skill": package.get("skill"),
        "item_type": item_type,
        "question": str(raw_item.get("question") or raw_item.get("stem") or "").strip(),
        "options": normalize_options(raw_item.get("options")),
        "answer": normalize_answer(raw_item.get("answer")),
        "rationale": normalize_rationale(raw_item.get("rationale")),
        "evidence": str(raw_item.get("evidence") or "").strip(),
        "grammar_constraints_used": normalize_list(
            raw_item.get("grammar_constraints_used") or raw_item.get("used_grammar")
        ),
        "vocabulary_constraints_used": normalize_list(
            raw_item.get("vocabulary_constraints_used") or raw_item.get("used_vocabulary")
        ),
        "difficulty": str(raw_item.get("difficulty") or "medium").strip(),
        "generation_model": model,
        "generated_at": generated_at,
    }

    errors: list[str] = []
    if item["answer"] not in {1, 2, 3, 4}:
        errors.append("answer must be an integer from 1 to 4")
    if len(item["options"]) != 4 or any(not option for option in item["options"]):
        errors.append("options must contain exactly four non-empty strings")
    for field in ["question", "rationale", "evidence"]:
        if not item[field]:
            errors.append(f"{field} must not be empty")
    if requested_types and item["item_type"] not in requested_types:
        errors.append(
            f"item_type must be one of requested item_types: {', '.join(requested_types)}"
        )
    return item, errors


def write_raw_response(raw_dir: Path, prompt_id: str, text: str) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    safe_prompt_id = re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", prompt_id).strip("_") or "prompt"
    path = raw_dir / f"{safe_prompt_id}_raw_response.txt"
    path.write_text(text, encoding="utf-8")
    return path


def format_markdown(items: list[dict[str, Any]], errors: list[dict[str, Any]]) -> str:
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
                    f"- item_type: {item['item_type']}",
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
                ]
            )
    else:
        lines.extend(["No valid generated items were produced.", ""])

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
                "item_types": get_requested_item_types(package),
                "item_count": get_item_count(package),
                "prompt_characters": len(get_prompt_text(package)),
            }
            for package in packages
        ],
    }
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
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

    ensure_can_write([items_path, md_path, errors_path], args.overwrite)

    generated_items: list[dict[str, Any]] = []
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
            raw_items = normalize_generated_payload(parsed)
        except GenerationError as exc:
            raw_path = None
            if isinstance(raw_text, str):
                raw_path = write_raw_response(raw_dir, prompt_id, raw_text)
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

    write_jsonl(items_path, generated_items)
    write_jsonl(errors_path, errors)
    md_path.write_text(format_markdown(generated_items, errors), encoding="utf-8")

    print("Generation completed.")
    print(f"Prompt packages processed: {len(packages)}")
    print(f"Valid generated items: {len(generated_items)}")
    print(f"Errors: {len(errors)}")
    print(f"Items JSONL: {items_path}")
    print(f"Markdown: {md_path}")
    print(f"Errors JSONL: {errors_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
