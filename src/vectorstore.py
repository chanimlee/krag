import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from config import (
    OPENAI_API_KEY,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL,
    COLLECTION_NAMES,
    DATA_FILES,
)


def _load_jsonl(filepath: str) -> list[dict]:
    records = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _get_embeddings():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)


def build_vectorstores(data_dir: str = "data") -> dict[str, Chroma]:
    """데이터 파일을 읽어 ChromaDB 컬렉션을 생성한다."""
    embeddings = _get_embeddings()
    stores: dict[str, Chroma] = {}

    # 문법 컬렉션
    grammar_records = _load_jsonl(os.path.join(data_dir, "grammar.jsonl"))
    grammar_texts = [
        f"문법: {r['grammar']}\n의미: {r['meaning']}\n예문: {' / '.join(r['examples'])}\n"
        f"용법: {r['usage_note']}\n단원: {r['unit']}단원"
        for r in grammar_records
    ]
    grammar_meta = [
        {"id": r["id"], "unit": r["unit"], "grammar": r["grammar"],
         "type": r["type"], "level": r["level"], "tags": ",".join(r.get("tags", []))}
        for r in grammar_records
    ]
    stores["grammar"] = Chroma.from_texts(
        texts=grammar_texts,
        embedding=embeddings,
        metadatas=grammar_meta,
        collection_name=COLLECTION_NAMES["grammar"],
        persist_directory=CHROMA_PERSIST_DIR,
    )

    # 어휘 컬렉션
    vocab_records = _load_jsonl(os.path.join(data_dir, "vocabulary.jsonl"))
    vocab_texts = [
        f"어휘: {r['word']}\n품사: {r['pos']}\n의미(영): {r['meaning']}\n"
        f"의미(한): {r['meaning_ko']}\n예문: {r['example']}\n단원: {r['unit']}단원"
        for r in vocab_records
    ]
    vocab_meta = [
        {"id": r["id"], "unit": r["unit"], "word": r["word"],
         "pos": r["pos"], "difficulty": r["difficulty"], "tags": ",".join(r.get("tags", []))}
        for r in vocab_records
    ]
    stores["vocabulary"] = Chroma.from_texts(
        texts=vocab_texts,
        embedding=embeddings,
        metadatas=vocab_meta,
        collection_name=COLLECTION_NAMES["vocabulary"],
        persist_directory=CHROMA_PERSIST_DIR,
    )

    # 읽기 지문 컬렉션
    reading_records = _load_jsonl(os.path.join(data_dir, "reading_texts.jsonl"))
    reading_texts = [
        f"제목: {r['title']}\n주제: {r['topic']}\n지문유형: {r['text_type']}\n"
        f"난이도: {r['difficulty']}\n단원: {r['unit']}단원\n\n지문:\n{r['text']}"
        for r in reading_records
    ]
    reading_meta = [
        {"id": r["id"], "unit": r["unit"], "title": r["title"],
         "topic": r["topic"], "difficulty": r["difficulty"],
         "text_type": r["text_type"], "word_count": r["word_count"],
         "grammar_points": ",".join(r.get("grammar_points", []))}
        for r in reading_records
    ]
    stores["reading"] = Chroma.from_texts(
        texts=reading_texts,
        embedding=embeddings,
        metadatas=reading_meta,
        collection_name=COLLECTION_NAMES["reading"],
        persist_directory=CHROMA_PERSIST_DIR,
    )

    # 문항 유형 컬렉션
    qtype_records = _load_jsonl(os.path.join(data_dir, "question_types.jsonl"))
    qtype_texts = [
        f"문항 유형: {r['name']}\n설명: {r['description']}\n"
        f"문제 형식 예시: {' / '.join(r['stem_patterns'])}\n"
        f"오답 전략: {' / '.join(r['distractor_strategies'])}"
        for r in qtype_records
    ]
    qtype_meta = [
        {"id": r["id"], "type": r["type"], "name": r["name"],
         "focus": r["focus"], "difficulty_range": ",".join(r.get("difficulty_range", []))}
        for r in qtype_records
    ]
    stores["question_types"] = Chroma.from_texts(
        texts=qtype_texts,
        embedding=embeddings,
        metadatas=qtype_meta,
        collection_name=COLLECTION_NAMES["question_types"],
        persist_directory=CHROMA_PERSIST_DIR,
    )

    return stores


def load_vectorstores() -> dict[str, Chroma]:
    """기존에 저장된 ChromaDB 컬렉션을 로드한다."""
    embeddings = _get_embeddings()
    stores: dict[str, Chroma] = {}
    for key, collection_name in COLLECTION_NAMES.items():
        stores[key] = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )
    return stores


def vectorstore_exists() -> bool:
    return Path(CHROMA_PERSIST_DIR).exists()
