from __future__ import annotations

import re
from typing import Any


def norm_ws(text: Any) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def get_options(item: dict[str, Any]) -> dict[str, Any]:
    opts = item.get("options", {})
    if isinstance(opts, list):
        return {str(i + 1): v for i, v in enumerate(opts)}
    return opts if isinstance(opts, dict) else {}


def char_ngrams(text: str, n: int) -> set[str]:
    s = norm_ws(text)
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def jaccard(a: str, b: str, n: int) -> float:
    aa, bb = char_ngrams(a, n), char_ngrams(b, n)
    if not aa or not bb:
        return 0.0
    return round(len(aa & bb) / len(aa | bb), 4)


def option_sort_key(entry: tuple[str, Any]) -> tuple[int, int, int]:
    key, value = entry
    text = str(value or "")
    return (len(norm_ws(text)), len(text), int(key) if str(key).isdigit() else 99)


def normalize_answer_symbol(answer: Any) -> str:
    text = str(answer or "").strip()
    circled = {"①": "1", "②": "2", "③": "3", "④": "4"}
    return circled.get(text, text)


def sort_options_shortest_to_longest(item: dict[str, Any]) -> dict[str, Any]:
    options = get_options(item)
    answer = normalize_answer_symbol(item.get("answer", ""))
    if answer not in {"1", "2", "3", "4"}:
        answer_text = str(item.get("answer", "")).strip()
        for key, value in options.items():
            if str(value).strip() == answer_text:
                answer = str(key)
                break
    normalized = {str(i): options.get(str(i), "") for i in range(1, 5)}
    answer_text = str(normalized.get(answer, "")).strip() if answer in {"1", "2", "3", "4"} else ""
    sorted_items = sorted(normalized.items(), key=option_sort_key)
    reordered = {str(i + 1): value for i, (_, value) in enumerate(sorted_items)}
    new_answer = ""
    for key, value in reordered.items():
        if str(value).strip() == answer_text:
            new_answer = key
            break
    warning = "" if new_answer else "answer text could not be matched after option reorder"
    return {
        "options": reordered,
        "answer": new_answer or answer,
        "option_order_rule": "shortest_to_longest_without_spaces",
        "option_order_changed": reordered != normalized,
        "original_options": normalized,
        "original_answer": answer,
        "reordered_options": reordered,
        "reordered_answer": new_answer or answer,
        "answer_recalculated": bool(new_answer and new_answer != answer),
        "answer_recalculation_warning": warning,
    }


def evidence_match(evidence: str, passage: str) -> dict[str, Any]:
    exact = bool(evidence and evidence in passage)
    normalized = bool(evidence and norm_ws(evidence) in norm_ws(passage))
    return {"status": "pass" if exact or normalized else "warning", "exact_match": exact, "normalized_match": normalized}


def option_copy_check(item: dict[str, Any], passage: str) -> dict[str, Any]:
    options = get_options(item)
    passage_norm = norm_ws(passage)
    results: dict[str, dict[str, Any]] = {}
    warning_options = []
    for key in ["1", "2", "3", "4"]:
        text = str(options.get(key, "") or "")
        text_norm = norm_ws(text)
        score = jaccard(text, passage, 3 if len(text_norm) < 10 else 5)
        copied_exact = bool(text and text in passage)
        copied_normalized = bool(text_norm and text_norm in passage_norm)
        warning = copied_exact or copied_normalized or score >= 0.80
        if warning:
            warning_options.append(key)
        results[key] = {
            "option_text": text,
            "char_len_no_space": len(text_norm),
            "copied_exact": copied_exact,
            "copied_normalized": copied_normalized,
            "ngram_overlap_score": score,
            "note": "option text overlaps heavily with passage" if warning else "",
        }
    return {"status": "warning" if warning_options else "pass", "option_results": results, "warning_options": warning_options}


def option_order_check(item: dict[str, Any]) -> dict[str, Any]:
    options = get_options(item)
    actual = [(str(i), options.get(str(i), "")) for i in range(1, 5)]
    sorted_actual = sorted(actual, key=option_sort_key)
    return {"status": "pass" if actual == sorted_actual else "warning", "rule": "shortest_to_longest_without_spaces"}


def validate_item(item: dict[str, Any], passage_text: str) -> dict[str, Any]:
    options = get_options(item)
    answer = normalize_answer_symbol(item.get("answer", ""))
    required_ok = all([
        item.get("question"),
        item.get("rationale") or item.get("explanation"),
        item.get("evidence_sentence") or item.get("evidence"),
        len(options) == 4,
        answer in {"1", "2", "3", "4"},
    ])
    checks = {
        "required_fields_check": {"status": "pass" if required_ok else "fail"},
        "option_count_check": {"status": "pass" if len(options) == 4 else "fail", "option_count": len(options)},
        "answer_format_check": {"status": "pass" if answer in {"1", "2", "3", "4"} else "fail", "answer": answer},
        "evidence_match_check": evidence_match(str(item.get("evidence_sentence") or item.get("evidence") or ""), passage_text),
        "option_copy_check": option_copy_check(item, passage_text),
        "option_order_check": option_order_check(item),
        "answer_consistency_check": {"status": "pass" if answer in options else "fail"},
    }
    statuses = [c.get("status") for c in checks.values()]
    status = "fail" if "fail" in statuses else ("warning" if "warning" in statuses else "pass")
    notes = []
    if checks["evidence_match_check"]["status"] == "warning":
        notes.append("evidence exact match review needed")
    if checks["option_copy_check"]["status"] == "warning":
        notes.append("option copy warning")
    if checks["option_order_check"]["status"] == "warning":
        notes.append("option order warning")
    return {"validation_status": status, "validation_notes": notes, "checks": checks}


def grammar_core(form: str) -> str:
    f = str(form or "")
    if "자고 하다" in f or "-자고" in f:
        return "자고"
    if "대요" in f or "-대" in f:
        return "대"
    f = re.sub(r"\[[^\]]+\]", "", f)
    f = f.replace("-", "").replace("(요)", "").replace(",", " ").strip()
    parts = [p for p in re.split(r"\s+|/", f) if len(p) >= 2]
    return parts[0] if parts else f


def validate_generated_passage(generated_passage: str, prompt_package: dict[str, Any], reference_passage: str = "") -> dict[str, Any]:
    text = str(generated_passage or "")
    ctx = prompt_package.get("retrieved_context", {})
    char_len = len(norm_ws(text))
    length_status = "pass" if char_len >= 120 else "warning"
    vocab_words = [str(v.get("word", "")) for v in ctx.get("vocabulary_context", [])]
    included_vocab = [w for w in vocab_words if w and w in text]
    vocab_status = "pass" if included_vocab else "warning"
    grammar_forms = [str(g.get("form", "")) for g in ctx.get("grammar_context", [])]
    included_grammar = []
    for form in grammar_forms:
        core = grammar_core(form)
        if core and core in text:
            included_grammar.append(form)
    grammar_status = "pass" if included_grammar else "warning"
    copy_score = jaccard(text, reference_passage, 5) if reference_passage else 0.0
    copy_status = "warning" if copy_score >= 0.5 or (norm_ws(text) and norm_ws(text) in norm_ws(reference_passage)) else "pass"
    presence_status = "pass" if text.strip() else "fail"
    checks = {
        "generated_passage_check": {"status": presence_status if presence_status == "fail" else length_status, "char_len_without_spaces": char_len, "min_char_len_without_spaces": 120},
        "vocabulary_inclusion_check": {"status": vocab_status, "included": included_vocab, "count": len(included_vocab)},
        "grammar_inclusion_check": {"status": grammar_status, "included": included_grammar, "count": len(included_grammar)},
        "passage_copy_check": {"status": copy_status, "ngram_overlap_score": copy_score},
    }
    statuses = [v["status"] for v in checks.values()]
    status = "fail" if "fail" in statuses else ("warning" if "warning" in statuses else "pass")
    return {"validation_status": status, "checks": checks}


def validate_similar_generation(generated_passage: str, items: list[dict[str, Any]], prompt_package: dict[str, Any], reference_passage: str = "") -> dict[str, Any]:
    passage_validation = validate_generated_passage(generated_passage, prompt_package, reference_passage)
    item_validations = [validate_item(item, generated_passage) for item in items]
    return {"passage_validation": passage_validation, "item_validations": item_validations}
