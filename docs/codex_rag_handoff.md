# Codex RAG 작업 인수인계

## 1. 프로젝트 목적

이 프로젝트는 한국어 교사가 특정 한국어 교재를 한 학기 동안 수업한 뒤, 학기말 평가 문항을 쉽게 만들 수 있도록 돕는 RAG 기반 문항 생성 보조 시스템을 구축하는 연구이다.

현재 단계의 목표는 새로운 지문 생성이 아니다. 기존 교재에 있는 읽기 지문과 듣기 지문을 바탕으로, 문제와 선택지만 생성하는 것이다. 문항 생성 시 문법과 어휘는 해당 단원 범위 안으로 제한하고, 정답과 오답 선택지는 모두 기존 지문에 근거해야 한다.

## 2. 현재 기준 작업 폴더

```text
C:\Users\chani\OneDrive\OneDrive_cylee\연구\학회 발표\20260718_이중언어학회 국제학술대회\RAG workstation
```

## 3. 현재 폴더 구조

```text
RAG workstation/
├─ docs/
├─ rag_jsonl_output/
├─ reports/
├─ scripts/
├─ source_md/
├─ rag_jsonl_output_backup_20260612_231058/
├─ 서울대한국어+_3A.pdf
├─ 한국어이해교육론_읽기평가.pdf
└─ 한국어평가론.pdf
```

## 4. 원천 Markdown 파일 목록

원천 Markdown 파일은 수정하지 않는 것을 원칙으로 한다.

```text
source_md/textbook.md
source_md/vocab.md
source_md/grammar.md
source_md/sample_question.md
```

## 5. 생성 JSONL 파일 목록

```text
rag_jsonl_output/textbook.jsonl
rag_jsonl_output/vocab.jsonl
rag_jsonl_output/grammar.jsonl
rag_jsonl_output/textbook_knowledge.jsonl
rag_jsonl_output/sample_question.jsonl
rag_jsonl_output/passage_bank.jsonl
rag_jsonl_output/chapter_constraints.jsonl
```

## 6. JSONL 재생성 명령

프로젝트 루트인 `RAG workstation`에서 실행한다.

```powershell
python .\scripts\build_rag_jsonl.py
```

선택적으로 원천/출력 폴더를 명시할 수 있다.

```powershell
python .\scripts\build_rag_jsonl.py --source-dir .\source_md --output-dir .\rag_jsonl_output
```

## 7. JSONL 검증 명령

프로젝트 루트인 `RAG workstation`에서 실행한다.

```powershell
python .\scripts\validate_rag_jsonl.py
```

검증 결과 상세 보고서는 다음 파일로 저장된다.

```text
reports/validation_report.json
```

## 8. 현재 레코드 수

```text
textbook.jsonl: 144
vocab.jsonl: 549
grammar.jsonl: 35
textbook_knowledge.jsonl: 728
sample_question.jsonl: 119
```

`textbook_knowledge.jsonl`은 `textbook.jsonl + vocab.jsonl + grammar.jsonl`의 합과 일치한다.

## 9. 검증 결과 요약

최종 검증 결과는 통과이다.

```text
valid JSONL: 통과
id 필드 존재: 통과
파일별 id 중복 없음: 통과
빈 text 필드 없음: 통과
textbook_knowledge 합산: 통과
sample_question 필수 필드: 통과
sample_question options: 통과
vacab.md 잔존 없음: 통과
```

이번 점검에서 `vacab.md` 오타를 `vocab.md`로 수정했다. 또한 일부 단원 도입 레코드의 `text`가 비어 있어, 스키마와 id 규칙은 유지한 채 `text`가 비는 경우에만 단원명, 쪽수, 활동 영역을 최소 검색 텍스트로 채우도록 파서를 보강했다.

## 10. TF-IDF 검색 baseline

TF-IDF 기반 검색 인덱스 구축을 완료했다. LLM API 호출이나 문항 생성은 아직 수행하지 않았고, 현재 단계는 검색 baseline과 smoke test까지이다.

인덱스는 두 DB로 분리했다.

```text
rag_index/tfidf_knowledge/
rag_index/tfidf_examples/
```

`tfidf_knowledge`는 `rag_jsonl_output/textbook_knowledge.jsonl`을 사용하고, `tfidf_examples`는 `rag_jsonl_output/sample_question.jsonl`을 사용한다. `rag_index/`는 `.gitignore`에 의해 Git 추적에서 제외된다.

인덱스 구성 파일은 각 폴더에 다음과 같이 저장된다.

```text
vectorizer.joblib
matrix.joblib
docstore.json
```

빌드 결과는 다음과 같다.

```text
knowledge documents: 728
example documents: 119
knowledge vocabulary size: 24872
example vocabulary size: 13018
```

현재 Windows 환경에서는 기본 `python`이 PsychoPy Python을 가리킬 수 있다. `scikit-learn`과 `joblib`이 설치된 Python 3.13을 사용할 경우 다음처럼 실행했다.

```powershell
& 'C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe' .\scripts\check_env.py
& 'C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe' .\scripts\build_tfidf_index.py
```

일반 Python 환경에서 requirements가 설치되어 있으면 다음 명령으로도 실행 가능하다.

```powershell
python .\scripts\check_env.py
python .\scripts\build_tfidf_index.py
python .\scripts\test_retrieval.py --query "-는다고 하다를 활용한 읽기 문항" --top-k 5 --target both
python .\scripts\run_retrieval_smoke_test.py
```

검색 테스트 질의 목록은 다음 문서에 있다.

```text
docs/retrieval_test_queries.md
```

Smoke test 리포트는 다음 위치에 저장했다.

```text
reports/retrieval_smoke_test.json
reports/retrieval_smoke_test.md
```

TF-IDF 검색기는 임베딩 모델이나 외부 API 없이 실행할 수 있고, 토큰/어절 단위 매칭 결과를 설명하기 쉬우며, 이후 semantic retriever의 성능을 비교할 기준선으로 쓰기 좋기 때문에 baseline retriever로 둔다.

## 11. Python 실행 환경

현재 Windows 환경에서는 앞으로 다음 Python 실행 파일을 프로젝트 기본값으로 사용한다.

```text
C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe
```

일반 `python` 명령은 PsychoPy Python을 가리킬 수 있고, 해당 환경에는 `scikit-learn`과 `joblib`이 없을 수 있다. 자세한 실행 명령은 다음 문서에 정리했다.

```text
docs/python_environment.md
```

## 12. Retrieval review sheet

Smoke test 결과를 사람이 평가할 수 있도록 TSV/CSV 파일로 변환했다.

생성 명령은 다음과 같다.

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\export_retrieval_review_sheet.py
```

평가 파일 위치:

```text
reports/retrieval_review_sheet.tsv
reports/retrieval_review_sheet.csv
```

평가 기준 문서:

```text
docs/retrieval_evaluation_guide.md
```

평가 파일은 15개 질의에 대해 knowledge top-5와 examples top-5를 포함하므로 총 150개 평가 행을 가진다. 다음 단계에서는 사람이 `relevance`, `usefulness_for_item_generation`, `error_type`, `reviewer_note` 열을 채우면 된다.

## 13. Textbook passage inventory and exam blueprint

기존 교재 지문 기반 문항 생성을 위해 교재 인벤토리를 추가했다.

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\build_textbook_inventory.py
```

주요 출력:

```text
rag_jsonl_output/passage_bank.jsonl
rag_jsonl_output/chapter_constraints.jsonl
reports/textbook_inventory.json
reports/textbook_inventory.md
```

`passage_bank.jsonl`은 기존 교재의 읽기/듣기 지문을 문항 생성 대상으로 정리한다. `chapter_constraints.jsonl`은 단원별 문법·어휘 제약으로 사용한다.

시험 구성안 예시는 다음 명령으로 생성한다.

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\propose_exam_blueprint.py --units 1-9 --total-items 30 --output reports/exam_blueprint_u01_u09_30items.json
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\propose_exam_blueprint.py --units 3 --total-items 6 --reading-ratio 1.0 --listening-ratio 0.0 --output reports/exam_blueprint_u03_6items_reading.json
```

문항 생성 프롬프트 설계 초안은 다음 문서에 있다. 아직 LLM API 호출은 구현하지 않았다.

```text
docs/item_generation_prompt_template.md
```

## 14. 다음 단계 제안

현재 목표에 맞춘 다음 단계 후보는 아래와 같다.

- 사용자가 단원과 총 문항 수를 지정하는 설정 파일 설계
- `passage_bank.jsonl`에서 사용할 기존 읽기/듣기 지문을 선택하는 스크립트 구현
- 선택 지문 기반 문항 생성 draft pipeline 구현
- 생성 문항 검증 스크립트 설계
- 교사용 출력 형식 설계
- 이후 필요 시 semantic retriever 추가 여부 결정
