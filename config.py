import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

COLLECTION_NAMES = {
    "grammar": "krag_grammar",
    "vocabulary": "krag_vocabulary",
    "reading": "krag_reading",
    "question_types": "krag_question_types",
}

DATA_FILES = {
    "grammar": "data/grammar.jsonl",
    "vocabulary": "data/vocabulary.jsonl",
    "reading": "data/reading_texts.jsonl",
    "question_types": "data/question_types.jsonl",
    "units": "data/units.jsonl",
}

DIFFICULTY_LEVELS = ["쉬움", "보통", "어려움"]
QUESTION_TYPES = ["세부내용", "주제/제목", "추론", "어휘", "문법", "빈칸채우기"]
TEXT_TYPES = ["설명문", "안내문", "대화문", "기사문", "광고문", "이메일"]
