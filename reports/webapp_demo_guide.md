# Webapp Demo Guide

## 웹앱 목적
RAG 기반 한국어 평가 문항 생성 파이프라인을 발표 현장에서 시연하기 위한 로컬 Streamlit 웹앱이다.

## 실행 방법
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 탑재된 데이터
- `data/raw/RAG_textbook_chapter_input_template.xlsx`
- `data/processed/*.jsonl`
- `data/rag/*.jsonl`
- `prompts/*_prompts.jsonl`
- `outputs/generated_all_items.jsonl`
- `outputs/validation_all_items.jsonl`
- `final/final_item_candidates.jsonl`

## 파일 업로드가 필요 없는 구조
교사는 파일을 업로드하지 않는다. 앱은 미리 탑재된 원자료 엑셀과 processed JSONL, prompt package, 생성·검증 결과를 읽어 지문 선택형 데모를 제공한다.

## Sample Mode
`final/final_item_candidates.jsonl`의 검증된 후보 문항을 즉시 표시한다. `OPENAI_API_KEY`가 없어도 작동한다.

## API Mode
`OPENAI_API_KEY`가 환경변수에 있을 때만 활성화된다. 선택한 지문과 prompt package를 바탕으로 새 문항을 생성하고, 선택지 길이순 정렬과 자동 검증을 적용한다.

PowerShell 설정 예:
```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
streamlit run app.py
```
API key는 화면, 로그, 저장 파일에 출력하지 않는다.

## 지문 선택 방법
사이드바의 지문 선택 목록에서 `chapter_id | skill | passage_id | preview` 형식의 항목을 선택한다.

## 문항 생성 조건 설정
문항 수, 문항 유형 구성, 생성 모드, 생성 방식을 사이드바에서 설정한다.

## RAG Context 확인
메인 화면의 expander에서 어휘, 문법, 문법 세부, 교재 질문, TOPIK 샘플을 확인한다.

## 검증 결과 확인
문항별 판정, option copy warning, 선택지 길이순 정렬 적용 여부, validation dataframe을 확인한다.

## 다운로드 방법
결과는 JSON, XLSX, Markdown으로 다운로드할 수 있다.

## 발표 시연 추천 순서
1. 웹앱 실행
2. 원자료 엑셀 preview 확인
3. 지문 선택
4. RAG context 확인
5. sample mode 결과 표시
6. 선택지 정렬과 검증 결과 설명
7. 다운로드 버튼 확인
8. API mode는 선택 기능으로 설명

## Known Limitations
- sample mode는 기존 생성 결과가 있는 지문에 가장 적합하다.
- 유사 지문 API mode는 준비 중 안내를 표시한다.
- API mode는 네트워크와 `OPENAI_API_KEY`가 필요하다.


## 유사 지문 API Mode 시연 방법

1. PowerShell에서 `$env:OPENAI_API_KEY="YOUR_API_KEY"`를 설정한다.
2. `streamlit run app.py`로 앱을 실행한다.
3. 생성 모드에서 `유사 지문 생성 + 문항 생성`을 선택한다.
4. 생성 방식에서 `새 문항 생성하기`를 선택한다.
5. 기준 지문/단원, 문항 수, 문항 유형 구성을 설정하고 실행한다.
6. 화면의 `생성 지문`, `생성 지문 검증`, 문항별 검증 세부 정보를 확인한다.

Sample mode는 기존 저장 결과를 즉시 보여 주며 API key가 필요 없다. API mode는 새 유사 지문과 문항을 생성하므로 네트워크와 API key가 필요하다. 유사 지문 생성은 품질 편차가 있을 수 있어 검증 결과 확인이 필요하다.
