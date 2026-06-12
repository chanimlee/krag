# Item Generation Prompt Packages

## prompt_passage_u02_listening_006_detail_info_2items

- unit: 2
- passage_id: `passage_u02_listening_006`
- skill: listening
- source_activity: listening
- candidate_type: core_listening
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
  "unit_no": 2,
  "unit_title": "날씨와 여행",
  "passage_id": "passage_u02_listening_006",
  "skill": "listening",
  "source_activity": "listening",
  "candidate_type": "core_listening",
  "priority": "high",
  "passage_title": "여: 여보세요?",
  "passage_text": "여: 여보세요? 하루야, 우리 발리에 못 가게 됐어. 남: 아니,왜? 무슨 일이 생겼어? 여: 발리로 가는 비행기표가 하나도 안 남았대. 여행사에 알아 보니까 성수기에는 두 달 전에 예약을 해야 한대. 남: 그렇구나 할 수 없지 뭐. 그럼 제주도는 어때? 제주도 가는 비행기표는 있을 텐데... 여: 그래. 좋아. 내가 비행기표를 예약할 테니까 너는 숙소를 좀 알아봐. 공항 근처에 좋은 호텔이 많다고 들었어. 남: 공항 근처 호텔은 좀 복잡하고 시끄러울 텐데 바다가 보이는 조용한 펜션은 어때? 여: 펜션도 좋은데? 근데 일기 예보를 확인해 보니까 지금 제주도에 태풍이 올라오고 있대. 바람이 심하게 불면 비행기가 결항할 텐데... 남: 우리 휴가는 다음 주니까 괜찮을 거야. 제주도 가서 뭘 할까? 여: 내 친구가 제주도에서 고기국수를 먹었는데 정말 맛있었대. 우리도 먹어 보자. 남: 그러자. 나도 제주도 고기국수가 유명하다고 들었어. 우리 우도에도 갈까? 제주도 옆에 있는 섬인데 경치가 정말 아름답대. 여: 좋아 여행 갈 생각을 하니까 너무 설렌다."
}

Unit grammar and vocabulary constraints:
{
  "unit_no": 2,
  "unit_title": "날씨와 여행",
  "grammar_items": [
    "[동]-는대요",
    "[형]-대(요)",
    "[명]이래(요)",
    "[동][형]-을 텐데",
    "[명]일 텐데",
    "[명]으로 유명하다",
    "[동][형]-기로 유명하다",
    "[동]-자고 하다",
    "(1) [-동]-는대(요), [형]-대(요), [명]이래(요)",
    "(2) [동][형]-을 텐데, [명]일 텐데",
    "[명]으로 유명하다, [동][형]-기로 유명하다"
  ],
  "grammar_forms": [],
  "vocabulary": [
    "소나기가 내리다 sudden shower falls",
    "눈이 그치다 snowing stops",
    "날씨가 개다 weather clears up",
    "태풍이 올라오다 typhoon ascends",
    "천둥이 치다 thunder roars",
    "번개가 치다 lightning strikes",
    "안개가 끼다 to be foggy",
    "최고 기온/최저 기온 highest temperature/lowest temperature",
    "영상/영화 above O℃ / below O'C",
    "(나무가) 쓰러지다 (tree) to fall down",
    "(간판이) 떨어지다 (sign) to fall",
    "(창문이) 부서지다 (window) to shatter",
    "(건물이) 무너지다 (building) to collapse",
    "딸기를 따다 to pick strawberries",
    "눈썰매 snow sled",
    "전국적 national",
    "영향 influence",
    "피하다 to avoid",
    "가능하다 to be possible",
    "실내 indoors",
    "동창 alumnus/alumna(alum)",
    "발리 Bali",
    "활짝 fully",
    "풍경 scenery",
    "성수기 peak season",
    "펜션 vacation rental",
    "결항하다 to be canceled",
    "고기국수 pork noodle soup",
    "우도 Udo Island",
    "여행지 travel destination",
    "휴가를 떠나다 to go on a vacation",
    "국내 여행 domestic travel",
    "해외여행 international travel",
    "계획을 변경하다 to change plans",
    "패키지여행 package tour",
    "자유여행 independent travel",
    "유람선을 타다 to go on a cruise",
    "문화를 체험하다 to experience the culture",
    "전시를 관람하다 to see an exhibition",
    "그림을 감상하다 to admire a painting",
    "유적지 historic site",
    "추천하다 to recommend",
    "딱 맞다 to fit perfectly",
    "오로라 aurora",
    "카펫 carpet",
    "비상약 first-aid medicine",
    "탑승 boarding",
    "일정 Itinerary",
    "세계문화유산 World Heritage",
    "화성 Hwaseong Fortress",
    "활쏘기 archery",
    "전통 공예품 traditional craft",
    "둘러보다 to look around",
    "시티 투어 city tour",
    "당일 (여행) same day (travel)",
    "당장 immediately",
    "쌀쌀하다 to be chilly",
    "샘내다 to be jealous",
    "일교차 daily temperature difference"
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

## prompt_passage_u02_listening_006_content_match_1items

- unit: 2
- passage_id: `passage_u02_listening_006`
- skill: listening
- source_activity: listening
- candidate_type: core_listening
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
  "unit_no": 2,
  "unit_title": "날씨와 여행",
  "passage_id": "passage_u02_listening_006",
  "skill": "listening",
  "source_activity": "listening",
  "candidate_type": "core_listening",
  "priority": "high",
  "passage_title": "여: 여보세요?",
  "passage_text": "여: 여보세요? 하루야, 우리 발리에 못 가게 됐어. 남: 아니,왜? 무슨 일이 생겼어? 여: 발리로 가는 비행기표가 하나도 안 남았대. 여행사에 알아 보니까 성수기에는 두 달 전에 예약을 해야 한대. 남: 그렇구나 할 수 없지 뭐. 그럼 제주도는 어때? 제주도 가는 비행기표는 있을 텐데... 여: 그래. 좋아. 내가 비행기표를 예약할 테니까 너는 숙소를 좀 알아봐. 공항 근처에 좋은 호텔이 많다고 들었어. 남: 공항 근처 호텔은 좀 복잡하고 시끄러울 텐데 바다가 보이는 조용한 펜션은 어때? 여: 펜션도 좋은데? 근데 일기 예보를 확인해 보니까 지금 제주도에 태풍이 올라오고 있대. 바람이 심하게 불면 비행기가 결항할 텐데... 남: 우리 휴가는 다음 주니까 괜찮을 거야. 제주도 가서 뭘 할까? 여: 내 친구가 제주도에서 고기국수를 먹었는데 정말 맛있었대. 우리도 먹어 보자. 남: 그러자. 나도 제주도 고기국수가 유명하다고 들었어. 우리 우도에도 갈까? 제주도 옆에 있는 섬인데 경치가 정말 아름답대. 여: 좋아 여행 갈 생각을 하니까 너무 설렌다."
}

Unit grammar and vocabulary constraints:
{
  "unit_no": 2,
  "unit_title": "날씨와 여행",
  "grammar_items": [
    "[동]-는대요",
    "[형]-대(요)",
    "[명]이래(요)",
    "[동][형]-을 텐데",
    "[명]일 텐데",
    "[명]으로 유명하다",
    "[동][형]-기로 유명하다",
    "[동]-자고 하다",
    "(1) [-동]-는대(요), [형]-대(요), [명]이래(요)",
    "(2) [동][형]-을 텐데, [명]일 텐데",
    "[명]으로 유명하다, [동][형]-기로 유명하다"
  ],
  "grammar_forms": [],
  "vocabulary": [
    "소나기가 내리다 sudden shower falls",
    "눈이 그치다 snowing stops",
    "날씨가 개다 weather clears up",
    "태풍이 올라오다 typhoon ascends",
    "천둥이 치다 thunder roars",
    "번개가 치다 lightning strikes",
    "안개가 끼다 to be foggy",
    "최고 기온/최저 기온 highest temperature/lowest temperature",
    "영상/영화 above O℃ / below O'C",
    "(나무가) 쓰러지다 (tree) to fall down",
    "(간판이) 떨어지다 (sign) to fall",
    "(창문이) 부서지다 (window) to shatter",
    "(건물이) 무너지다 (building) to collapse",
    "딸기를 따다 to pick strawberries",
    "눈썰매 snow sled",
    "전국적 national",
    "영향 influence",
    "피하다 to avoid",
    "가능하다 to be possible",
    "실내 indoors",
    "동창 alumnus/alumna(alum)",
    "발리 Bali",
    "활짝 fully",
    "풍경 scenery",
    "성수기 peak season",
    "펜션 vacation rental",
    "결항하다 to be canceled",
    "고기국수 pork noodle soup",
    "우도 Udo Island",
    "여행지 travel destination",
    "휴가를 떠나다 to go on a vacation",
    "국내 여행 domestic travel",
    "해외여행 international travel",
    "계획을 변경하다 to change plans",
    "패키지여행 package tour",
    "자유여행 independent travel",
    "유람선을 타다 to go on a cruise",
    "문화를 체험하다 to experience the culture",
    "전시를 관람하다 to see an exhibition",
    "그림을 감상하다 to admire a painting",
    "유적지 historic site",
    "추천하다 to recommend",
    "딱 맞다 to fit perfectly",
    "오로라 aurora",
    "카펫 carpet",
    "비상약 first-aid medicine",
    "탑승 boarding",
    "일정 Itinerary",
    "세계문화유산 World Heritage",
    "화성 Hwaseong Fortress",
    "활쏘기 archery",
    "전통 공예품 traditional craft",
    "둘러보다 to look around",
    "시티 투어 city tour",
    "당일 (여행) same day (travel)",
    "당장 immediately",
    "쌀쌀하다 to be chilly",
    "샘내다 to be jealous",
    "일교차 daily temperature difference"
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
