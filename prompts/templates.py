SYSTEM_PROMPT = """당신은 외국인을 위한 한국어 교육 전문가입니다.
서울대 한국어+ 3A 교재를 기반으로 한국어 읽기 평가 문항을 생성합니다.

문항 생성 원칙:
1. 지문은 해당 단원의 문법과 어휘 수준에 맞게 작성합니다.
2. 모든 선택지는 지문을 읽은 학생이 실제로 고민할 만한 수준으로 작성합니다.
3. 오답 선택지는 지문의 내용을 살짝 바꾸거나 반대로 하여 정교하게 만듭니다.
4. 정답과 해설은 명확하고 교육적으로 작성합니다.
5. 한국어 맞춤법과 문법에 맞게 작성합니다."""

QUESTION_GENERATION_PROMPT = """다음 교재 자료를 바탕으로 한국어 읽기 평가 문항을 생성해 주세요.

=== 교사 입력 정보 ===
단원: {unit}단원
목표 문법: {grammar}
주제/소재: {topic}
문항 유형: {question_type}
지문 유형: {text_type}
난이도: {difficulty}
문항 수: {num_questions}개

=== 검색된 문법 자료 ===
{grammar_context}

=== 검색된 어휘 자료 ===
{vocabulary_context}

=== 참고 지문 예시 ===
{reading_context}

=== 문항 유형 안내 ===
{question_type_info}

=== 생성 지침 ===
위 자료를 바탕으로 아래 형식에 맞춰 {num_questions}개의 4지선다 읽기 문항을 생성해 주세요.

**반드시 아래 JSON 형식으로만 출력하세요. 다른 설명은 넣지 마세요.**

{{
  "questions": [
    {{
      "question_number": 1,
      "passage": "지문 내용 (150~200자 분량, {text_type} 형식, {difficulty} 난이도)",
      "question": "문제 발문",
      "choices": {{
        "①": "선택지 1",
        "②": "선택지 2",
        "③": "선택지 3",
        "④": "선택지 4"
      }},
      "answer": "①",
      "explanation": "정답 해설: 왜 이 선택지가 정답인지, 왜 나머지 선택지가 오답인지 설명",
      "grammar_used": ["사용된 문법1", "사용된 문법2"],
      "vocabulary_used": ["사용된 어휘1", "어휘2"]
    }}
  ]
}}"""

REVIEW_PROMPT = """다음 한국어 읽기 평가 문항을 검토하고 품질 평가를 해 주세요.

=== 검토할 문항 ===
{question_json}

=== 검토 기준 ===
1. 언어 정확성: 맞춤법, 문법, 자연스러운 표현
2. 난이도 적절성: 목표 난이도({difficulty})에 맞는지
3. 문항 타당성: 정답이 명확하고 오답이 적절한지
4. 지문 완성도: 지문이 자연스럽고 교육적 가치가 있는지
5. 선택지 균형: 선택지 길이와 형식이 균형 잡혔는지

**반드시 아래 JSON 형식으로만 출력하세요.**

{{
  "review_results": [
    {{
      "question_number": 1,
      "scores": {{
        "language_accuracy": 5,
        "difficulty_appropriateness": 5,
        "question_validity": 5,
        "passage_quality": 5,
        "choice_balance": 5
      }},
      "total_score": 25,
      "issues": ["발견된 문제점 목록 (없으면 빈 배열)"],
      "corrections": ["수정 제안 (없으면 빈 배열)"],
      "approved": true
    }}
  ],
  "overall_feedback": "전체 문항에 대한 종합 의견"
}}"""
