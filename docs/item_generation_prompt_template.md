# Item Generation Prompt Template

This document describes the prompt package format for generating Korean assessment item drafts from existing textbook passages. The prompt package itself does not call an LLM API.

The question type system is defined in:

```text
docs/question_type_schema.json
docs/question_type_schema.md
```

## System Role

You are an assistant for Korean language teachers. Your task is to help draft end-of-semester assessment items from existing textbook reading or listening passages.

You must not create a new passage. Use only the selected existing passage. Generate the question, four options, answer, and teacher-review rationale.

## Input Data Structure

```json
{
  "passage_record": {
    "id": "passage_u05_reading_008",
    "unit_no": 5,
    "unit_title": "...",
    "skill": "reading",
    "source_activity": "reading",
    "candidate_type": "recipe",
    "priority": "high",
    "passage": "..."
  },
  "chapter_constraints": {
    "unit_no": 5,
    "grammar_items": [],
    "grammar_forms": [],
    "vocabulary": []
  },
  "question_requests": [
    {
      "comprehension_type": "factual",
      "comprehension_type_label": "사실적 문항",
      "stem_type": "내용 일치",
      "stem_templates": ["윗글의 내용과 같은 것을 고르십시오."],
      "difficulty": "medium"
    }
  ]
  ,
  "suitability_hints": [
    {
      "comprehension_type": "evaluative",
      "stem_type": "필자 태도 평가",
      "requested_difficulty": "hard",
      "candidate_type": "recipe",
      "likely_suitable": false,
      "reasons": ["candidate_type 'recipe' is listed as unsuitable for '필자 태도 평가'."],
      "fallback_recommendations": [
        {"comprehension_type": "factual", "stem_type": "내용 일치"}
      ]
    }
  ],
  "allow_skip": true,
  "skip_policy": {
    "do_not_force_generation": true
  }
}
```

## Comprehension Types

- `factual`: 지문에 명시된 정보를 확인한다.
- `inferential`: 지문에 직접 쓰이지 않았지만 지문 근거를 통해 판단할 수 있는 내용을 묻는다.
- `evaluative`: 지문 내용에 근거하여 적절성, 타당성, 필자의 태도, 목적, 심정 등을 판단한다.

평가적 문항도 지문 밖 배경지식을 요구하면 안 된다. 모든 `evidence`는 지문 안에서 찾을 수 있어야 한다.

## Core Constraints

- Do not modify the existing passage.
- Do not generate a new passage.
- Generate only the question and options, plus teacher-facing answer/rationale metadata.
- Use the stem type and stem template defined in `docs/question_type_schema.json`.
- Generate an item only when the requested question type is suitable for the passage.
- If the passage is unsuitable for a requested question type, record it in `skipped_requests`.
- Do not force evaluative questions for passages without passage-internal attitude, viewpoint, purpose, advice, evaluation, persuasion, or feeling evidence.
- The correct answer must be clearly supported by the passage.
- Distractors must be plausible but inconsistent with, unsupported by, or different from the passage.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Avoid excessive use of advanced grammar that is not taught in the unit.
- Include `answer`, `rationale`, `evidence`, `difficulty_rationale`, and `teacher_edit_suggestions`.
- A teacher-facing student version may hide `answer`, `rationale`, and `evidence`.

## Output JSON Schema

```json
{
  "items": [
    {
      "passage_id": "...",
      "unit": 5,
      "skill": "reading",
      "comprehension_type": "factual",
      "comprehension_type_label": "사실적 문항",
      "stem_type": "내용 일치",
      "stem_template": "윗글의 내용과 같은 것을 고르십시오.",
      "question": "윗글의 내용과 같은 것을 고르십시오.",
      "options": ["...", "...", "...", "..."],
      "answer": 2,
      "rationale": "정답과 오답의 판단 근거를 설명한다.",
      "evidence": "지문 안의 근거 문장 또는 표현",
      "grammar_constraints_used": [],
      "vocabulary_constraints_used": [],
      "difficulty": "medium",
      "difficulty_rationale": "난이도 판단 이유",
      "teacher_edit_suggestions": []
    }
  ],
  "skipped_requests": [
    {
      "comprehension_type": "evaluative",
      "stem_type": "필자 태도 평가",
      "requested_difficulty": "hard",
      "reason": "지문이 절차 중심 조리법이라 필자의 태도나 관점을 판단할 근거가 부족함.",
      "suggested_alternatives": [
        {"comprehension_type": "factual", "stem_type": "내용 일치"}
      ]
    }
  ]
}
```

## Reading Item Prompt

```text
You are generating Korean reading assessment items for a teacher.

Use the selected textbook passage exactly as given. Do not rewrite, extend, shorten, or replace the passage.

Passage record:
{passage_record_json}

Unit constraints:
{chapter_constraints_json}

Question requests:
{question_requests_json}

Suitability hints:
{suitability_hints_json}

Requirements:
- Handle exactly the requested number of question requests across `items` and `skipped_requests`.
- Generate only suitable requests.
- If a request is unsuitable, add it to `skipped_requests` instead of forcing an item.
- Follow the requested comprehension_type, stem_type, stem_templates, and difficulty.
- factual questions must check information explicitly stated in the passage.
- inferential questions must be answerable from passage evidence.
- evaluative questions must judge attitude, purpose, feeling, appropriateness, or validity from passage evidence only.
- Generate four options.
- Make exactly one correct answer.
- The correct option must be grounded in the passage.
- Distractors must be plausible but contradicted by, unsupported by, or different from the passage.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Return only valid JSON matching the output schema.
```

## Listening Item Prompt

```text
You are generating Korean listening assessment items for a teacher.

Use the selected textbook listening script exactly as given. Do not rewrite, extend, shorten, or replace the script.

Listening passage record:
{passage_record_json}

Unit constraints:
{chapter_constraints_json}

Question requests:
{question_requests_json}

Suitability hints:
{suitability_hints_json}

Requirements:
- Handle exactly the requested number of question requests across `items` and `skipped_requests`.
- Generate only suitable requests.
- If a request is unsuitable, add it to `skipped_requests` instead of forcing an item.
- Follow the requested comprehension_type, stem_type, stem_templates, and difficulty.
- factual questions must check information explicitly stated in the script.
- inferential questions must be answerable from script evidence.
- evaluative questions must judge attitude, purpose, feeling, appropriateness, or validity from script evidence only.
- Generate four options.
- Make exactly one correct answer.
- The correct option must be clearly grounded in the script.
- Distractors must be plausible but contradicted by, unsupported by, or different from the script.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Return only valid JSON matching the output schema.
```

## Validation Prompt

```text
Validate the generated item against the selected existing passage, unit constraints, and question type schema.

Passage record:
{passage_record_json}

Question type schema:
{question_type_schema_json}

Unit constraints:
{chapter_constraints_json}

Generated item:
{generated_item_json}

Check:
1. The passage was not modified or newly generated.
2. comprehension_type is factual, inferential, or evaluative.
3. stem_type exists in docs/question_type_schema.json.
4. stem_template matches or closely follows a template for the selected stem_type.
5. The item has exactly one correct answer.
6. The correct answer is grounded in the passage.
7. Each distractor is plausible but not correct according to the passage.
8. The stem and options do not overuse grammar or vocabulary outside the unit constraints.
9. evidence, rationale, difficulty_rationale, and teacher_edit_suggestions are complete.
10. skipped_requests are used when a requested question type is unsuitable.
11. each skipped_request has comprehension_type, stem_type, requested_difficulty, reason, and suggested_alternatives.

Return validation results as JSON with fields:
- passed
- errors
- warnings
- suggested_revision
```
