import json
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from prompts.templates import SYSTEM_PROMPT, QUESTION_GENERATION_PROMPT


def _format_grammar_context(grammar_items: list[dict]) -> str:
    if not grammar_items:
        return "관련 문법 자료 없음"
    return "\n\n".join(item["content"] for item in grammar_items)


def _format_vocabulary_context(vocab_items: list[dict]) -> str:
    if not vocab_items:
        return "관련 어휘 자료 없음"
    return "\n".join(item["content"] for item in vocab_items)


def _format_reading_context(reading_items: list[dict]) -> str:
    if not reading_items:
        return "참고 지문 없음"
    texts = []
    for item in reading_items:
        meta = item["metadata"]
        texts.append(
            f"[{meta.get('title', '제목 없음')} / {meta.get('text_type', '')} / "
            f"{meta.get('difficulty', '')}]\n{item['content']}"
        )
    return "\n\n---\n\n".join(texts)


def _format_qtype_context(qtype_items: list[dict]) -> str:
    if not qtype_items:
        return "문항 유형 정보 없음"
    return qtype_items[0]["content"]


def generate_questions(params: dict, context: dict) -> list[dict]:
    """Claude API를 사용하여 4지선다 문항을 생성한다."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = QUESTION_GENERATION_PROMPT.format(
        unit=params.get("unit", "미지정"),
        grammar=params.get("grammar", "미지정"),
        topic=params.get("topic", "일반"),
        question_type=params.get("question_type", "세부내용"),
        text_type=params.get("text_type", "설명문"),
        difficulty=params.get("difficulty", "보통"),
        num_questions=params.get("num_questions", 1),
        grammar_context=_format_grammar_context(context.get("grammar", [])),
        vocabulary_context=_format_vocabulary_context(context.get("vocabulary", [])),
        reading_context=_format_reading_context(context.get("reading_texts", [])),
        question_type_info=_format_qtype_context(context.get("question_type_info", [])),
    )

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()

    # JSON 파싱
    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_text:
        raw_text = raw_text.split("```")[1].split("```")[0].strip()

    result = json.loads(raw_text)
    return result.get("questions", [])
