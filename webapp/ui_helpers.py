from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

NON_DISPLAY_VALUES = {"", "NA", "N/A", "nan", "None"}

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

DECISION_LABELS = {
    "accept": "채택 후보",
    "accept_candidate": "채택 후보",
    "pass": "채택 후보",
    "revise": "수정 후보",
    "revise_candidate": "수정 후보",
    "warning": "수정 후보",
    "reject": "제외 후보",
    "reject_candidate": "제외 후보",
    "fail": "제외 후보",
}


def is_displayable(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text not in NON_DISPLAY_VALUES


def display_text(value: Any, default: str = "") -> str:
    return str(value).strip() if is_displayable(value) else default


def prepare_dataframe_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna("").astype(str)


def construct_label(item: dict[str, Any]) -> str:
    raw = item.get("construct") or item.get("item_type") or item.get("checks", {}).get("construct") or ""
    return CONSTRUCT_LABELS.get(str(raw).strip().lower(), "")


def decision_value(item: dict[str, Any]) -> str:
    return str(item.get("final_decision") or item.get("preliminary_decision") or item.get("validation_status") or "").strip()


def decision_label(status: str) -> str:
    return DECISION_LABELS.get(str(status).strip(), str(status).strip())


def status_badge(status: str) -> None:
    label = decision_label(status)
    raw = str(status or "").strip()
    if raw in {"accept", "accept_candidate", "pass"}:
        color, background = "#166534", "#dcfce7"
    elif raw in {"revise", "revise_candidate", "warning", "sample"}:
        color, background = "#854d0e", "#fef9c3"
    elif raw in {"reject", "reject_candidate", "fail"}:
        color, background = "#991b1b", "#fee2e2"
    else:
        color, background = "#374151", "#f3f4f6"
    st.markdown(
        f'<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
        f'font-size:0.82rem;background:{background};color:{color};">{label}</span>',
        unsafe_allow_html=True,
    )


def render_context_table(title: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with st.expander(title, expanded=False):
        if not rows:
            st.caption("표시할 항목이 없습니다.")
            return
        df = pd.DataFrame(rows)
        view = df[[c for c in columns if c in df.columns]]
        st.dataframe(prepare_dataframe_for_streamlit(view), width="stretch")


def render_passage_validation(passage_validation: dict[str, Any] | None) -> None:
    if not passage_validation:
        return
    st.subheader("생성 지문 검증")
    checks = passage_validation.get("checks", {})
    rows = []
    for name, check in checks.items():
        row = {"check": name, **(check if isinstance(check, dict) else {"value": check})}
        rows.append(row)
    if rows:
        st.dataframe(prepare_dataframe_for_streamlit(pd.DataFrame(rows)), width="stretch")


def render_item_card(item: dict[str, Any], idx: int) -> None:
    question = display_text(item.get("question"), "(발문 없음)")
    label = construct_label(item)
    st.markdown(f"#### 문항 {idx}. {question}")
    if label:
        st.caption(f"유형: {label}")
    opts = item.get("options", {}) if isinstance(item.get("options"), dict) else {}
    option_marks = {"1": "①", "2": "②", "3": "③", "4": "④"}
    for key in ["1", "2", "3", "4"]:
        option = display_text(opts.get(key))
        if option:
            st.markdown(f"{option_marks[key]} {option}")
    answer = display_text(item.get("answer"))
    if answer in option_marks:
        answer = option_marks[answer]
    cols = st.columns([1, 1, 3])
    with cols[0]:
        if answer:
            st.markdown(f"정답: **{answer}**")
    with cols[1]:
        status_badge(decision_value(item) or item.get("validation_status", ""))
    rationale = display_text(item.get("rationale") or item.get("explanation"))
    evidence = display_text(item.get("evidence_sentence") or item.get("evidence"))
    if rationale:
        st.markdown(f"해설: {rationale}")
    if evidence:
        st.markdown(f"근거: {evidence}")
    checks = item.get("checks", {}) if isinstance(item.get("checks"), dict) else {}
    if checks.get("option_copy_check", {}).get("status") == "warning":
        st.caption("선택지 표현 검토 필요")
    with st.expander("검증 세부 정보", expanded=False):
        if item.get("option_order_changed"):
            st.caption("선택지 길이순 정렬 적용")
        if item.get("answer_recalculated"):
            st.caption("정답 번호 재계산 적용")
        notes = item.get("validation_notes", [])
        if isinstance(notes, list):
            notes = [str(n) for n in notes if is_displayable(n)]
        elif is_displayable(notes):
            notes = [str(notes)]
        else:
            notes = []
        if notes:
            st.caption("검증 메모: " + "; ".join(notes))
        compact = {
            "validation_status": item.get("validation_status"),
            "final_decision": item.get("final_decision"),
            "evidence_match": checks.get("evidence_match_check"),
            "option_copy": checks.get("option_copy_check"),
            "option_order": checks.get("option_order_check"),
            "answer_consistency": checks.get("answer_consistency_check"),
        }
        compact = {k: v for k, v in compact.items() if is_displayable(v)}
        if compact:
            st.json(compact)
