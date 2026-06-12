# Question Type Schema

이 문서는 `source_md/sample_question.md`와 `rag_jsonl_output/sample_question.jsonl`에 나타난 TOPIK 예시 문항의 발문 문구를 바탕으로 문항 유형 체계를 정리한 것이다.

이번 단계부터 문항 생성 prompt package와 생성 결과는 임시 `item_type` 중심 체계 대신 아래 세 범주를 사용한다.

- `factual`: 사실적 문항
- `inferential`: 추론적 문항
- `evaluative`: 평가적 문항

## 설계 원칙

- 발문 문구는 `sample_question.md`에 나타난 문구를 우선 사용한다.
- 사실적 문항은 지문에 명시된 정보 확인을 중심으로 한다.
- 추론적 문항은 지문에 직접 쓰이지 않았지만 지문 근거로 판단 가능한 내용을 묻는다.
- 평가적 문항은 적절성, 태도, 심정, 목적 등을 판단하되 지문 밖 배경지식을 요구하지 않는다.
- 모든 문항의 정답과 오답 판단 근거는 기존 지문 안에서 찾을 수 있어야 한다.

## 유형 목록

| comprehension_type | label | stem_type | default_difficulty | 대표 발문 |
|---|---|---|---|---|
| factual | 사실적 문항 | 내용 일치 | easy | 윗글의 내용과 같은 것을 고르십시오. |
| factual | 사실적 문항 | 세부 내용 파악 | easy | 무엇에 대한 내용인지 맞는 것을 고르십시오. |
| factual | 사실적 문항 | 순서 파악 | hard | 다음 문장이 들어갈 곳으로 가장 알맞은 것을 고르십시오. |
| factual | 사실적 문항 | 빈칸 내용 파악 | medium | ( )에 들어갈 말로 가장 알맞은 것을 고르십시오. |
| inferential | 추론적 문항 | 주제 파악 | medium | 다음을 읽고 글의 주제로 가장 알맞은 것을 고르십시오. |
| inferential | 추론적 문항 | 내용 추론 | medium | 윗글의 내용으로 알 수 있는 것을 고르십시오. |
| inferential | 추론적 문항 | 이유/근거 추론 | medium | 필자가 이 글을 쓴 목적을 고르십시오. |
| evaluative | 평가적 문항 | 필자 태도 평가 | hard | 밑줄 친 부분에 나타난 필자의 태도로 알맞은 것을 고르십시오. |
| evaluative | 평가적 문항 | 심정/기분 평가 | medium | 밑줄 친 부분에 나타난 나의 심정으로 알맞은 것을 고르십시오. |

자세한 기계 판독용 스키마는 다음 파일을 사용한다.

```text
docs/question_type_schema.json
```
