# Codex RAG 작업 인수인계

## 1. 프로젝트 목적

이 프로젝트는 한국어 숙달도 평가, 특히 한국어 읽기 평가 문항 자동 생성을 위한 RAG 기반 데이터셋과 생성 파이프라인을 구축하는 연구이다. 현재 단계의 목표는 한국어 교재 지식과 TOPIK 예시 문항을 재현 가능한 JSONL 데이터 기반으로 정리하고, 이후 Prompt-only, Knowledge-RAG, Example-RAG, Hybrid-RAG 조건을 비교할 수 있도록 검증 가능한 출발점을 마련하는 것이다.

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

## 10. 다음 단계 제안

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

## 11. 다음 단계 제안

아직 구현하지 않은 다음 단계 후보는 아래와 같다.

- FAISS 또는 Chroma 기반 검색 인덱스 구축
- 검색 품질 테스트
- `textbook_knowledge.jsonl`을 지식 DB로 사용하는 Knowledge-RAG
- `sample_question.jsonl`을 문항 유형 예시 DB로 사용하는 Example-RAG
- 두 DB를 결합하는 Hybrid-RAG
- Prompt-only / Knowledge-RAG / Example-RAG / Hybrid-RAG 비교 실험 설계
- 사람 검토용 문항 평가 양식 설계
- smoke test 결과 사람 검토
- semantic embedding retriever 추가 여부 결정
- 또는 문항 생성 파이프라인 설계
