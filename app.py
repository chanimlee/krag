from __future__ import annotations

import pandas as pd
import streamlit as st

from webapp.data_loader import (
    RAW_EXCEL,
    data_status,
    get_context_for_passage,
    get_excel_sheet_names,
    get_passage_by_id,
    get_sample_generated_items,
    load_excel_sheet_preview,
    load_passage_catalog,
    prepare_dataframe_for_streamlit,
)
from webapp.export_service import to_json_bytes, to_markdown_bytes, to_xlsx_bytes
from webapp.generation_service import MODEL_NAME, generate_items, has_api_key
from webapp.prompt_service import construct_count_is_valid, get_prompt_package, type_config
from webapp.ui_helpers import render_context_table, render_item_card, render_passage_validation, prepare_dataframe_for_streamlit as prep_df
from webapp.validation_service import validate_item


st.set_page_config(page_title="RAG 기반 한국어 평가 문항 생성 데모", layout="wide")

st.title("RAG 기반 한국어 평가 문항 생성 데모")
st.caption("교재 지문, 어휘·문법 정보, 문항 샘플을 활용하여 한국어 읽기 평가 문항을 생성하는 시연용 웹앱")

catalog = load_passage_catalog()
if not catalog:
    st.error("표시할 reading/culture 지문이 없습니다. data/processed/passages.jsonl을 확인하세요.")
    st.stop()

with st.sidebar:
    st.header("데이터 상태")
    for row in data_status():
        st.write(("✅ " if row["exists"] else "❌ ") + row["path"])

    st.header("생성 설정")
    st.caption(f"현재 모델: {MODEL_NAME}")
    labels = [p["display_label"] for p in catalog]
    selected_label = st.selectbox("기준 지문/단원 선택", labels)
    selected = catalog[labels.index(selected_label)]
    passage_id = selected["passage_id"]
    generation_mode_label = st.selectbox("생성 모드", ["기존 지문 기반 문항 생성", "유사 지문 생성 + 문항 생성"])
    generation_mode = "similar" if generation_mode_label.startswith("유사") else "existing"
    run_mode = st.radio("생성 방식", ["샘플 결과 보기", "새 문항 생성하기"], index=0)
    n_items = st.slider("문항 수", 1, 5, 3)
    type_label = st.selectbox("문항 유형 구성", ["자동 구성", "사실적 이해 중심", "사실적 + 추론적", "사실적 + 추론적 + 평가적", "사용자 지정"])
    custom = None
    custom_count_warning = False
    if type_label == "사용자 지정":
        factual = st.number_input("factual 개수", min_value=0, max_value=5, value=1)
        inferential = st.number_input("inferential 개수", min_value=0, max_value=5, value=1)
        evaluative = st.number_input("evaluative 개수", min_value=0, max_value=5, value=1)
        custom = {"factual": int(factual), "inferential": int(inferential), "evaluative": int(evaluative)}
        if sum(custom.values()) != n_items:
            custom_count_warning = True
            st.warning("사용자 지정 유형 개수의 총합이 문항 수와 다릅니다.")
    construct_counts = type_config(type_label, n_items, custom)
    if not construct_count_is_valid(construct_counts, n_items):
        custom_count_warning = True
        st.warning("문항 유형 구성 총합이 문항 수와 다릅니다.")
    st.info("난이도: 한국어 3급 / 서울대 한국어 3A 수준")
    st.caption("선택지는 4지선다형으로 생성됩니다. 선택지를 모두 만든 뒤 공백 제외 글자 수 기준으로 짧은 것부터 긴 것 순서로 배열하며, 선택지 순서 변경 후 정답 번호는 자동으로 재계산됩니다. 오답지는 지문 문장을 그대로 복사하지 않도록 검증합니다.")
    api_ready = has_api_key()
    if run_mode == "새 문항 생성하기" and not api_ready:
        st.warning("OPENAI_API_KEY가 없어 API mode 실행 버튼이 비활성화됩니다.")
    run_clicked = st.button("실행", disabled=(run_mode == "새 문항 생성하기" and (not api_ready or custom_count_warning)))

passage = get_passage_by_id(passage_id) or selected
context = get_context_for_passage(passage_id, generation_mode=generation_mode)

col1, col2 = st.columns([1.15, 0.85])
with col1:
    st.subheader("기준 지문/단원" if generation_mode == "similar" else "선택 지문")
    st.write(f"passage_id: `{passage.get('passage_id')}`")
    st.write(f"chapter_id: `{passage.get('chapter_id')}` / skill: `{passage.get('skill')}`")
    st.markdown(str(passage.get("source_text", "")).replace("\n", "  \n"))

with col2:
    st.subheader("생성 설정 요약")
    st.json({
        "generation_mode": generation_mode_label,
        "run_mode": run_mode,
        "n_items": n_items,
        "construct_counts": construct_counts,
        "option_order_rule": "shortest_to_longest_without_spaces",
        "model": MODEL_NAME,
    })
    if generation_mode == "similar":
        st.caption("유사 지문 생성은 선택한 기준 지문이 속한 단원의 어휘·문법·샘플 문항 context를 바탕으로 새 지문과 문항을 생성합니다. 품질 편차가 있을 수 있으므로 생성 지문 검증 결과를 함께 확인하세요.")

st.subheader("원자료 엑셀 데이터")
st.caption("이 엑셀 파일은 교재 지문, 어휘, 문법, 문항 샘플을 구조화하기 위한 원자료 입력 양식입니다. 현재 데모에서는 이 파일을 바탕으로 생성된 processed JSONL과 prompt package를 사용하여 문항을 생성합니다. 교사는 별도의 파일을 업로드하지 않고, 미리 탑재된 교재 지문을 선택하여 문항을 생성할 수 있습니다.")
try:
    sheets = get_excel_sheet_names(RAW_EXCEL)
    sheet = st.selectbox("엑셀 시트 preview", sheets)
    preview_df = prepare_dataframe_for_streamlit(load_excel_sheet_preview(RAW_EXCEL, sheet, max_rows=30))
    st.dataframe(preview_df, width="stretch")
    with open(RAW_EXCEL, "rb") as f:
        st.download_button("원자료 엑셀 양식 다운로드", f.read(), file_name=RAW_EXCEL.name)
except Exception as exc:
    st.error(f"원자료 엑셀을 읽을 수 없습니다: {exc}")

st.subheader("RAG context")
st.caption("이 context는 사전 생성된 RAG prompt package에서 불러온 것입니다.")
render_context_table("어휘 context", context.get("vocabulary_context", []), ["word", "meaning", "vocab_id"])
render_context_table("문법 context", context.get("grammar_context", []), ["form", "meaning_function", "grammar_id"])
render_context_table("문법 세부 context", context.get("grammar_detail_context", []), ["form", "detail_type", "detail_contents", "grammar_id"])
render_context_table("교재 내 질문 예시", context.get("source_question_examples", []), ["question_text", "source_text", "answer"])
render_context_table("TOPIK 샘플", context.get("topik_sample_examples", []), ["construct", "stem", "answer"])

result_payload = None
if run_clicked or run_mode == "샘플 결과 보기":
    if run_mode == "샘플 결과 보기":
        items = get_sample_generated_items(passage_id, generation_mode)
        display_passage_text = items[0].get("target_or_generated_passage") if generation_mode == "similar" and items else passage.get("source_text", "")
        validation = [validate_item(item, item.get("target_or_generated_passage") or display_passage_text or passage.get("source_text", "")) for item in items]
        generated_passage = {"text": display_passage_text} if generation_mode == "similar" and display_passage_text else None
        result_payload = {
            "summary": {"mode": "sample", "generation_mode": generation_mode, "item_count": len(items[:n_items])},
            "passage": passage,
            "generated_passage": generated_passage,
            "items": items[:n_items],
            "validation": validation[:n_items],
            "rag_context": context,
        }
    else:
        pkg = get_prompt_package(passage_id, str(passage.get("chapter_id")), generation_mode)
        if not pkg:
            st.error("선택한 기준 지문/단원에 대응하는 prompt package를 찾을 수 없습니다.")
        else:
            try:
                api_result = generate_items(pkg, passage, n_items, construct_counts, generation_mode=generation_mode)
                items = api_result["generated"].get("items", [])
                for item, val in zip(items, api_result["validation"]):
                    item["validation_status"] = val.get("validation_status")
                    item["validation_notes"] = val.get("validation_notes", [])
                    item["checks"] = val.get("checks", {})
                result_payload = {
                    "summary": {"mode": "api", "generation_mode": generation_mode, "run_id": api_result["run_id"], "item_count": len(items)},
                    "passage": passage,
                    "generated_passage": api_result.get("generated_passage"),
                    "items": items,
                    "validation": api_result["validation"],
                    "passage_validation": api_result.get("passage_validation"),
                    "rag_context": context,
                    "raw_response": "saved under outputs/webapp_runs",
                }
                st.success(f"API 생성 완료: {api_result['run_id']}")
            except Exception as exc:
                st.error(f"API 생성 실패: {exc}")

if result_payload:
    if result_payload.get("generated_passage"):
        st.subheader("생성 지문")
        st.markdown(str(result_payload["generated_passage"].get("text", "")).replace("\n", "  \n"))
        render_passage_validation(result_payload.get("passage_validation"))
    st.subheader("생성 결과")
    if not result_payload["items"]:
        st.warning("선택한 지문에 표시할 샘플 문항이 없습니다.")
    for idx, item in enumerate(result_payload["items"], 1):
        render_item_card(item, idx)
        st.divider()
    st.subheader("자동 검증 결과")
    st.dataframe(prep_df(pd.DataFrame(result_payload["validation"])), width="stretch")
    st.subheader("다운로드")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("JSON 다운로드", to_json_bytes(result_payload), file_name="generated_items.json", mime="application/json")
    with c2:
        st.download_button("XLSX 다운로드", to_xlsx_bytes(result_payload), file_name="generated_items.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c3:
        st.download_button("Markdown 다운로드", to_markdown_bytes(result_payload), file_name="generated_items.md", mime="text/markdown")

