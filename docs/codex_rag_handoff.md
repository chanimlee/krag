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

아직 구현하지 않은 다음 단계 후보는 아래와 같다.

- FAISS 또는 Chroma 기반 검색 인덱스 구축
- 검색 품질 테스트
- `textbook_knowledge.jsonl`을 지식 DB로 사용하는 Knowledge-RAG
- `sample_question.jsonl`을 문항 유형 예시 DB로 사용하는 Example-RAG
- 두 DB를 결합하는 Hybrid-RAG
- Prompt-only / Knowledge-RAG / Example-RAG / Hybrid-RAG 비교 실험 설계
- 사람 검토용 문항 평가 양식 설계
