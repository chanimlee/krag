# Item Generation Prompt Packages

## prompt_passage_u05_reading_010_content_match_sequence_content_inference_4items

- unit: 5
- passage_id: `passage_u05_reading_010`
- skill: reading
- source_activity: reading
- candidate_type: recipe
- priority: high
- item_count: 4

### Question Requests

1. 사실적 문항 / 내용 일치 / medium
2. 사실적 문항 / 순서 파악 / hard
3. 추론적 문항 / 내용 추론 / medium
4. 평가적 문항 / 필자 태도 평가 / hard

### Suitability Hints

1. factual / 내용 일치 / likely_suitable=True / detected relevant text features: 절차
2. factual / 순서 파악 / likely_suitable=True / detected relevant text features: 순서, 절차
3. inferential / 내용 추론 / likely_suitable=True / detected relevant text features: 목적
4. evaluative / 필자 태도 평가 / likely_suitable=True / candidate_type 'recipe' is listed as unsuitable for '필자 태도 평가'.; detected relevant text features: 추천/조언, 평가 표현, 설득 의도, 태도 단서, 감정 표현; evaluative text features were detected, so the text may be suitable despite the passage type warning.

### Prompt

```text
You are an assistant for Korean language teachers.

Task:
- Generate 4 Korean proficiency assessment item(s) for the selected existing textbook passage.
- Generate only question stems and answer options.
- Do not create a new passage.
- Do not modify the selected passage.
- Follow the question type system derived from sample_question.md.

Requested questions:
[
  {
    "comprehension_type": "factual",
    "comprehension_type_label": "사실적 문항",
    "stem_type": "내용 일치",
    "stem_templates": [
      "윗글의 내용과 같은 것을 고르십시오.",
      "다음을 읽고 글의 내용과 같은 것을 고르십시오.",
      "다음 글의 내용과 같은 것을 고르십시오."
    ],
    "difficulty": "medium",
    "notes": "지문에 명시된 정보와 일치하는 선택지를 고르는 유형이다.",
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 3
    }
  },
  {
    "comprehension_type": "factual",
    "comprehension_type_label": "사실적 문항",
    "stem_type": "순서 파악",
    "stem_templates": [
      "다음 문장이 들어갈 곳으로 가장 알맞은 것을 고르십시오."
    ],
    "difficulty": "hard",
    "notes": "사건이나 절차의 흐름, 담화 연결 관계를 바탕으로 문장 위치를 판단한다.",
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 1
    }
  },
  {
    "comprehension_type": "inferential",
    "comprehension_type_label": "추론적 문항",
    "stem_type": "내용 추론",
    "stem_templates": [
      "윗글의 내용으로 알 수 있는 것을 고르십시오."
    ],
    "difficulty": "medium",
    "notes": "지문에 직접 쓰이지 않았지만 명시 정보들을 근거로 판단할 수 있는 내용을 묻는다.",
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 2
    }
  },
  {
    "comprehension_type": "evaluative",
    "comprehension_type_label": "평가적 문항",
    "stem_type": "필자 태도 평가",
    "stem_templates": [
      "밑줄 친 부분에 나타난 필자의 태도로 알맞은 것을 고르십시오.",
      "윗글에 나타난 필자의 태도로 가장 알맞은 것을 고르십시오.",
      "밑줄 친 부분에서 나타난 필자의 태도로 알맞은 것을 고르십시오."
    ],
    "difficulty": "hard",
    "notes": "지문 표현과 맥락에 근거해 필자의 태도나 관점을 판단한다. 지문 밖 배경지식은 요구하지 않는다.",
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 1
    }
  }
]

Suitability hints:
[
  {
    "comprehension_type": "factual",
    "stem_type": "내용 일치",
    "requested_difficulty": "medium",
    "candidate_type": "recipe",
    "likely_suitable": true,
    "reasons": [
      "detected relevant text features: 절차"
    ],
    "required_text_features": [
      "명시적 정보",
      "사건",
      "대상",
      "절차",
      "장소",
      "인물"
    ],
    "detected_text_features": [
      "추천/조언",
      "평가 표현",
      "설득 의도",
      "태도 단서",
      "감정 표현",
      "순서",
      "절차",
      "목적"
    ],
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 3
    },
    "fallback_recommendations": [
      {
        "comprehension_type": "factual",
        "stem_type": "세부 내용 파악"
      },
      {
        "comprehension_type": "inferential",
        "stem_type": "내용 추론"
      }
    ]
  },
  {
    "comprehension_type": "factual",
    "stem_type": "순서 파악",
    "requested_difficulty": "hard",
    "candidate_type": "recipe",
    "likely_suitable": true,
    "reasons": [
      "detected relevant text features: 순서, 절차"
    ],
    "required_text_features": [
      "순서",
      "절차",
      "시간 흐름",
      "담화 연결",
      "사건 전개"
    ],
    "detected_text_features": [
      "추천/조언",
      "평가 표현",
      "설득 의도",
      "태도 단서",
      "감정 표현",
      "순서",
      "절차",
      "목적"
    ],
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 1
    },
    "fallback_recommendations": [
      {
        "comprehension_type": "factual",
        "stem_type": "내용 일치"
      },
      {
        "comprehension_type": "factual",
        "stem_type": "세부 내용 파악"
      }
    ]
  },
  {
    "comprehension_type": "inferential",
    "stem_type": "내용 추론",
    "requested_difficulty": "medium",
    "candidate_type": "recipe",
    "likely_suitable": true,
    "reasons": [
      "detected relevant text features: 목적"
    ],
    "required_text_features": [
      "여러 정보의 결합",
      "암시",
      "원인",
      "결과",
      "목적",
      "상황"
    ],
    "detected_text_features": [
      "추천/조언",
      "평가 표현",
      "설득 의도",
      "태도 단서",
      "감정 표현",
      "순서",
      "절차",
      "목적"
    ],
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 2
    },
    "fallback_recommendations": [
      {
        "comprehension_type": "factual",
        "stem_type": "내용 일치"
      },
      {
        "comprehension_type": "factual",
        "stem_type": "세부 내용 파악"
      }
    ]
  },
  {
    "comprehension_type": "evaluative",
    "stem_type": "필자 태도 평가",
    "requested_difficulty": "hard",
    "candidate_type": "recipe",
    "likely_suitable": true,
    "reasons": [
      "candidate_type 'recipe' is listed as unsuitable for '필자 태도 평가'.",
      "detected relevant text features: 추천/조언, 평가 표현, 설득 의도, 태도 단서, 감정 표현",
      "evaluative text features were detected, so the text may be suitable despite the passage type warning."
    ],
    "required_text_features": [
      "필자의 의견",
      "추천/조언",
      "평가 표현",
      "설득 의도",
      "태도 단서",
      "감정 표현"
    ],
    "detected_text_features": [
      "추천/조언",
      "평가 표현",
      "설득 의도",
      "태도 단서",
      "감정 표현",
      "순서",
      "절차",
      "목적"
    ],
    "generation_policy": {
      "allow_generation": true,
      "require_suitability_check": true,
      "max_items_per_passage": 1
    },
    "fallback_recommendations": [
      {
        "comprehension_type": "factual",
        "stem_type": "내용 일치"
      },
      {
        "comprehension_type": "factual",
        "stem_type": "순서 파악"
      },
      {
        "comprehension_type": "inferential",
        "stem_type": "내용 추론"
      }
    ]
  }
]

Skip policy:
{
  "allow_skip": true,
  "do_not_force_generation": true,
  "skip_when": [
    "requested stem_type is not suitable for the passage type",
    "required text features are missing",
    "evidence cannot be found inside the passage",
    "evaluative request would require personal opinion or outside background knowledge"
  ],
  "skipped_request_required_fields": [
    "comprehension_type",
    "stem_type",
    "requested_difficulty",
    "reason",
    "suggested_alternatives"
  ]
}

Passage metadata and text:
{
  "unit_no": 5,
  "unit_title": "음식과 조리법",
  "passage_id": "passage_u05_reading_010",
  "skill": "reading",
  "source_activity": "reading",
  "candidate_type": "recipe",
  "priority": "high",
  "passage_title": "언제나 그리운 내 고향 음식, 쌀국수 제가 가장 먹고 싶은 고향 음식은 쌀국수예요.",
  "passage_text": "언제나 그리운 내 고향 음식, 쌀국수 제가 가장 먹고 싶은 고향 음식은 쌀국수예요. 한국에도 베트남 쌀국수를 파는 곳이 많이 있지만 고향에서 먹는 쌀국수가 언제나 그리워요. 베트남 사람들은 누구나 쌀국수를 좋아해요. 간편하게 먹을 수 있고 맛도 좋거든요. 오늘은 여러분에게 쌀국수 만드는 법을 소개해 드릴게요. 쌀국수를 만들려면 소고기, 쌀국수, 양파, 파, 고추 등이 필요해요. 소고기 대신 닭고기를 사용해도 돼요. 재료 준비가 끝나면 먼저 냄비에 물을 붓고 고기와 양파, 파를 넣고 끓여요. 그다음에 국수를 삶아요. 삶은 국수는 찬물에 씻어야 면이 쫄깃해져요. 마지막으로 미리 삶아 놓은 쌀국수에 국물을 붓고 썰어 놓은 고기를 올려요. 여기에 숙주나 양파, 고수를 넣으면 더 맛있어요. 조리법만 이야기했는데 벌써 입에 군침이 도는 것 같네요. 오늘 저녁에 직접 만든 쌀국수를 드셔 보는 건 어떠세요?"
}

Unit grammar and vocabulary constraints:
{
  "unit_no": 5,
  "unit_title": "음식과 조리법",
  "grammar_items": [
    "누구나,언제나, 어디나 무엇이나",
    "[동][형] -을 줄 모르다",
    "[동][형]-어야, [명]이어야",
    "[동][형] -거든요, [명]이거든(요)",
    "(1) 누구나, 언제나, 어디나 무엇이나",
    "(2) [동][형]-을 줄 모르다",
    "(3) [동][형]-어야, [명]이어야",
    "(4) [동][형]-거든(요), [명]이거든(요)",
    "(1) [동]-나보다, [형]-은가 보다, [명]인가 보다"
  ],
  "grammar_forms": [],
  "vocabulary": [
    "고소하다 to be toasty/nutty",
    "매콤하다 to be spicy",
    "싱겁다 to be bland",
    "느끼하다 to be oily",
    "쫄깃하다 to be chewy",
    "연하다 to be tender",
    "질기다 to be tough",
    "바삭하다 to be crispy",
    "입이 심심하다 to have the snacking urge",
    "출출하다 to be slightly hungry",
    "궁중떡볶이 royal court rice cakes",
    "튀김 friedfood",
    "새우 shrimp",
    "간단하다 to be simple",
    "국물이 시원하다 broth hits the spot",
    "기대를 하다 to anticipate",
    "잼 jam",
    "양념치킨 seasoned chicken",
    "프라이드치킨 fried chicken",
    "식사를 거르다 to skip a meal",
    "굶다 to starve honey",
    "간편하다 to be convenient",
    "달콤하다 to be sweet",
    "해물파전 seafood green onion pancake",
    "밀가루 flour",
    "해물 seafood",
    "파 green onion",
    "오징어 squid",
    "군침이 돌다 to be salivating",
    "하도 so",
    "일부러 deliberately",
    "맛보다 to taste",
    "다듬다 to trim",
    "썰다 to chop",
    "다지다 to mince",
    "섞다 to mix",
    "젓다 to stir",
    "볶다 to stir-fry",
    "찌다 to steam",
    "튀기다 to deep-fry",
    "삶다 to boil",
    "부치다 to fry",
    "굽다 to grill",
    "끓이다 to heat",
    "오믈렛 omelet",
    "달걀 egg",
    "대신 instead of",
    "간장 soy sauce",
    "양념 seasoning",
    "양파 onion",
    "버섯 mushroom",
    "후추 pepper",
    "양념장 marinade",
    "재우다 to marinate",
    "프라이팬 fry pan",
    "갈다 to grind",
    "쌀국수 pho",
    "고추 chili pepper",
    "냄비 pot",
    "붓다 to pour",
    "찬물 cold water",
    "숙주 bean sprouts",
    "고수 cilantro (coriander)",
    "조리법 recipe",
    "타코 taco",
    "토르티야 tortilla",
    "식단을 조절하다 to watch one's diet",
    "유제품 dairy product",
    "다이어트를 하다 to go on a diet",
    "근육 운동 muscle exercise",
    "채식주의자 vegetarian",
    "쌀가루 rice flour",
    "두부 tofu"
  ]
}

Constraints:
- Generate an item only when the requested question type is suitable for the passage.
- If a requested question type is unsuitable, do not force an item. Put it in skipped_requests.
- skipped_requests must include comprehension_type, stem_type, requested_difficulty, reason, and suggested_alternatives.
- Evaluative questions require enough passage-internal evidence such as author attitude, viewpoint, purpose, advice, evaluation, persuasion, or feeling.
- Evaluative questions must not ask for the learner's personal opinion or outside background knowledge.
- factual questions check information explicitly stated in the passage.
- inferential questions ask what can be judged from passage evidence even when not directly stated.
- evaluative questions judge appropriateness, validity, attitude, purpose, feeling, or stance, but must not require background knowledge outside the passage.
- Use one of the listed stem_templates for each requested stem_type, or a very close variant.
- The correct answer must be clearly grounded in the passage.
- Distractors must be plausible but inconsistent with, unsupported by, or different from the passage.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Avoid excessive use of advanced grammar not taught in this unit.
- evidence must be a non-empty passage-grounded string.
- Return only valid JSON.
- The top-level JSON must contain "items" and "skipped_requests" lists.
- At least one of "items" or "skipped_requests" must be non-empty.

Expected output JSON schema:
{
  "items": [
    {
      "passage_id": "string",
      "unit": "integer",
      "skill": "reading|listening",
      "comprehension_type": "factual|inferential|evaluative",
      "comprehension_type_label": "사실적 문항|추론적 문항|평가적 문항",
      "stem_type": "string from docs/question_type_schema.json",
      "stem_template": "string from the selected stem_type templates or close variant",
      "question": "string",
      "options": [
        "string",
        "string",
        "string",
        "string"
      ],
      "answer": "integer 1-4",
      "rationale": "string",
      "evidence": "string grounded in the passage",
      "grammar_constraints_used": [
        "string"
      ],
      "vocabulary_constraints_used": [
        "string"
      ],
      "difficulty": "easy|medium|hard",
      "difficulty_rationale": "string",
      "teacher_edit_suggestions": [
        "string"
      ]
    }
  ],
  "skipped_requests": [
    {
      "comprehension_type": "factual|inferential|evaluative",
      "stem_type": "string from docs/question_type_schema.json",
      "requested_difficulty": "easy|medium|hard",
      "reason": "string",
      "suggested_alternatives": [
        {
          "comprehension_type": "factual|inferential|evaluative",
          "stem_type": "string"
        }
      ]
    }
  ]
}
```
