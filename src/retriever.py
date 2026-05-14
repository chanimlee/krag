from langchain_chroma import Chroma


class KRAGRetriever:
    def __init__(self, stores: dict[str, Chroma]):
        self.stores = stores

    def retrieve_grammar(self, unit: int | None = None, grammar_name: str = "", k: int = 3) -> list[dict]:
        query = f"{grammar_name} 문법 단원 {unit}" if unit else grammar_name
        results = self.stores["grammar"].similarity_search_with_score(query, k=k)
        items = []
        for doc, score in results:
            if unit and doc.metadata.get("unit") != unit:
                continue
            items.append({"content": doc.page_content, "metadata": doc.metadata, "score": score})
        # 단원 필터로 결과가 없으면 필터 없이 재검색
        if not items:
            items = [{"content": d.page_content, "metadata": d.metadata, "score": s}
                     for d, s in results]
        return items[:k]

    def retrieve_vocabulary(self, unit: int | None = None, topic: str = "", k: int = 5) -> list[dict]:
        query = f"{topic} 어휘 단원 {unit}" if unit else f"{topic} 어휘"
        results = self.stores["vocabulary"].similarity_search_with_score(query, k=k * 2)
        items = []
        for doc, score in results:
            if unit and doc.metadata.get("unit") != unit:
                continue
            items.append({"content": doc.page_content, "metadata": doc.metadata, "score": score})
        if not items:
            items = [{"content": d.page_content, "metadata": d.metadata, "score": s}
                     for d, s in results]
        return items[:k]

    def retrieve_reading_texts(
        self,
        unit: int | None = None,
        topic: str = "",
        text_type: str = "",
        difficulty: str = "",
        k: int = 2,
    ) -> list[dict]:
        query_parts = [topic, text_type, difficulty]
        if unit:
            query_parts.append(f"단원 {unit}")
        query = " ".join(p for p in query_parts if p)
        results = self.stores["reading"].similarity_search_with_score(query, k=k * 3)
        items = []
        for doc, score in results:
            meta = doc.metadata
            if unit and meta.get("unit") != unit:
                continue
            if difficulty and meta.get("difficulty") != difficulty:
                continue
            if text_type and meta.get("text_type") != text_type:
                continue
            items.append({"content": doc.page_content, "metadata": meta, "score": score})
        if not items:
            items = [{"content": d.page_content, "metadata": d.metadata, "score": s}
                     for d, s in results]
        return items[:k]

    def retrieve_question_type(self, question_type: str, k: int = 1) -> list[dict]:
        results = self.stores["question_types"].similarity_search_with_score(question_type, k=k)
        return [{"content": d.page_content, "metadata": d.metadata, "score": s}
                for d, s in results]

    def retrieve_all_for_generation(self, params: dict) -> dict:
        """문항 생성에 필요한 모든 자료를 검색한다."""
        unit = params.get("unit")
        grammar = params.get("grammar", "")
        topic = params.get("topic", "")
        question_type = params.get("question_type", "세부내용")
        text_type = params.get("text_type", "설명문")
        difficulty = params.get("difficulty", "보통")

        return {
            "grammar": self.retrieve_grammar(unit=unit, grammar_name=grammar, k=3),
            "vocabulary": self.retrieve_vocabulary(unit=unit, topic=topic, k=8),
            "reading_texts": self.retrieve_reading_texts(
                unit=unit, topic=topic, text_type=text_type, difficulty=difficulty, k=2
            ),
            "question_type_info": self.retrieve_question_type(question_type, k=1),
        }
