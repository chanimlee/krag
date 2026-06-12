# Item Generation Prompt Packages

## prompt_passage_u05_reading_010_detail_info_2items

- unit: 5
- passage_id: `passage_u05_reading_010`
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

## prompt_passage_u05_reading_010_main_idea_1items

- unit: 5
- passage_id: `passage_u05_reading_010`
- skill: reading
- source_activity: reading
- candidate_type: recipe
- priority: high
- item_types: main_idea
- item_count: 1

### Prompt

```text
You are an assistant for Korean language teachers.

Task:
- Generate 1 Korean proficiency assessment item(s) for the selected existing textbook passage.
- Item type: main_idea
- Generate only question stems and answer options.
- Do not create a new passage.
- Do not modify the selected passage.

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
