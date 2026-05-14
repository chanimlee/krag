import json
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from prompts.templates import SYSTEM_PROMPT, REVIEW_PROMPT


def review_questions(questions: list[dict], params: dict) -> dict:
    """생성된 문항을 Claude API로 자동 검토한다."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = REVIEW_PROMPT.format(
        question_json=json.dumps(questions, ensure_ascii=False, indent=2),
        difficulty=params.get("difficulty", "보통"),
    )

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()

    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_text:
        raw_text = raw_text.split("```")[1].split("```")[0].strip()

    return json.loads(raw_text)


def apply_review_feedback(questions: list[dict], review: dict) -> list[dict]:
    """검토 결과를 바탕으로 문항에 검토 정보를 추가한다."""
    review_map = {
        r["question_number"]: r
        for r in review.get("review_results", [])
    }

    annotated = []
    for q in questions:
        num = q.get("question_number", 0)
        rv = review_map.get(num, {})
        q["review"] = {
            "scores": rv.get("scores", {}),
            "total_score": rv.get("total_score", 0),
            "issues": rv.get("issues", []),
            "corrections": rv.get("corrections", []),
            "approved": rv.get("approved", False),
        }
        annotated.append(q)

    return annotated
