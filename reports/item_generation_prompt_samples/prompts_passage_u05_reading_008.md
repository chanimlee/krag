# Item Generation Prompt Packages

## prompt_passage_u05_reading_008_detail_info_2items

- unit: 5
- passage_id: `passage_u05_reading_008`
- skill: reading
- source_activity: reading
- candidate_type: recipe
- priority: high
- item_types: detail_info
- item_count: 2

### Prompt

```text
You are an assistant for Korean language teachers.

Task:
- Generate 2 Korean proficiency assessment item(s) for the selected existing textbook passage.
- Item type: detail_info
- Generate only question stems and answer options.
- Do not create a new passage.
- Do not modify the selected passage.

Passage metadata and text:
{
  "unit_no": 5,
  "unit_title": "음식과 조리법",
  "passage_id": "passage_u05_reading_008",
  "skill": "reading",
  "source_activity": "reading",
  "candidate_type": "recipe",
  "priority": "high",
  "passage_title": "불고기 만들기 재료 소고기 600g, 양파 1개, 파 30g, 버섯 20g, 간장, 후추, 설탕, 다진 마늘, 참기름 만드는 방법 1) 채소와...",
  "passage_text": "불고기 만들기 재료 소고기 600g, 양파 1개, 파 30g, 버섯 20g, 간장, 후추, 설탕, 다진 마늘, 참기름 만드는 방법 1) 채소와 고기를 먹기 좋은 크기로 썰어 놓는다. 고기는 연한 부분을 사용하는 것이 좋다. 2) 간장에 후추, 설탕, 다진 마늘, 참기름을 넣고 섞어서 양념장을 만든다. 3) 양념장에 고기를 넣어 30분 정도 재운다. 고기를 재워야 더 연하고 맛있어진다. 4) 뜨거워진 프라이팬에 고기와 준비한 야채를 넣고 볶는다. 5) 완성된 불고기를 접시에 담는다. 요리 비법 양념장에 설탕 대신에 과일을 갈아서 넣어 보세요. 과일을 넣으면 더 맛있거든요."
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
- The correct answer must be clearly grounded in the passage.
- Distractors must be plausible but inconsistent with, unsupported by, or different from the passage.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Avoid excessive use of advanced grammar not taught in this unit.
- Return only valid JSON.

Expected output JSON schema:
{
  "passage_id": "string",
  "unit_no": "integer",
  "skill": "reading|listening",
  "item_type": "string",
  "stem": "string",
  "options": {
    "1": "string",
    "2": "string",
    "3": "string",
    "4": "string"
  },
  "answer": "1|2|3|4",
  "rationale": {
    "1": "string",
    "2": "string",
    "3": "string",
    "4": "string"
  },
  "used_grammar": [
    "string"
  ],
  "used_vocabulary": [
    "string"
  ],
  "constraint_check": {
    "within_unit_grammar": "boolean",
    "within_unit_vocabulary": "boolean",
    "answer_grounded_in_passage": "boolean"
  }
}
```

## prompt_passage_u05_reading_008_content_match_1items

- unit: 5
- passage_id: `passage_u05_reading_008`
- skill: reading
- source_activity: reading
- candidate_type: recipe
- priority: high
- item_types: content_match
- item_count: 1

### Prompt

```text
You are an assistant for Korean language teachers.

Task:
- Generate 1 Korean proficiency assessment item(s) for the selected existing textbook passage.
- Item type: content_match
- Generate only question stems and answer options.
- Do not create a new passage.
- Do not modify the selected passage.

Passage metadata and text:
{
  "unit_no": 5,
  "unit_title": "음식과 조리법",
  "passage_id": "passage_u05_reading_008",
  "skill": "reading",
  "source_activity": "reading",
  "candidate_type": "recipe",
  "priority": "high",
  "passage_title": "불고기 만들기 재료 소고기 600g, 양파 1개, 파 30g, 버섯 20g, 간장, 후추, 설탕, 다진 마늘, 참기름 만드는 방법 1) 채소와...",
  "passage_text": "불고기 만들기 재료 소고기 600g, 양파 1개, 파 30g, 버섯 20g, 간장, 후추, 설탕, 다진 마늘, 참기름 만드는 방법 1) 채소와 고기를 먹기 좋은 크기로 썰어 놓는다. 고기는 연한 부분을 사용하는 것이 좋다. 2) 간장에 후추, 설탕, 다진 마늘, 참기름을 넣고 섞어서 양념장을 만든다. 3) 양념장에 고기를 넣어 30분 정도 재운다. 고기를 재워야 더 연하고 맛있어진다. 4) 뜨거워진 프라이팬에 고기와 준비한 야채를 넣고 볶는다. 5) 완성된 불고기를 접시에 담는다. 요리 비법 양념장에 설탕 대신에 과일을 갈아서 넣어 보세요. 과일을 넣으면 더 맛있거든요."
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
- The correct answer must be clearly grounded in the passage.
- Distractors must be plausible but inconsistent with, unsupported by, or different from the passage.
- Keep grammar and vocabulary within the unit constraints as much as possible.
- Avoid excessive use of advanced grammar not taught in this unit.
- Return only valid JSON.

Expected output JSON schema:
{
  "passage_id": "string",
  "unit_no": "integer",
  "skill": "reading|listening",
  "item_type": "string",
  "stem": "string",
  "options": {
    "1": "string",
    "2": "string",
    "3": "string",
    "4": "string"
  },
  "answer": "1|2|3|4",
  "rationale": {
    "1": "string",
    "2": "string",
    "3": "string",
    "4": "string"
  },
  "used_grammar": [
    "string"
  ],
  "used_vocabulary": [
    "string"
  ],
  "constraint_check": {
    "within_unit_grammar": "boolean",
    "within_unit_vocabulary": "boolean",
    "answer_grounded_in_passage": "boolean"
  }
}
```
