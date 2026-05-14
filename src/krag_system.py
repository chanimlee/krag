import json
import os
from datetime import datetime
from pathlib import Path

from src.vectorstore import build_vectorstores, load_vectorstores, vectorstore_exists
from src.retriever import KRAGRetriever
from src.generator import generate_questions
from src.reviewer import review_questions, apply_review_feedback


class KRAGSystem:
    def __init__(self, data_dir: str = "data", output_dir: str = "output"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        Path(output_dir).mkdir(exist_ok=True)
        self._stores = None
        self._retriever = None

    def _ensure_loaded(self):
        if self._retriever is not None:
            return
        if vectorstore_exists():
            self._stores = load_vectorstores()
        else:
            raise RuntimeError(
                "ChromaDB가 초기화되지 않았습니다. 먼저 'python scripts/ingest.py'를 실행하세요."
            )
        self._retriever = KRAGRetriever(self._stores)

    def ingest(self):
        """데이터를 ChromaDB에 인제스트한다."""
        print("데이터 인제스트 시작...")
        self._stores = build_vectorstores(self.data_dir)
        self._retriever = KRAGRetriever(self._stores)
        print("데이터 인제스트 완료!")

    def generate(self, params: dict, auto_review: bool = True) -> dict:
        """
        문항 생성 메인 함수.

        params 예시:
        {
            "unit": 3,
            "grammar": "-아/어야 하다",
            "topic": "건강",
            "question_type": "세부내용_일치",
            "text_type": "설명문",
            "difficulty": "보통",
            "num_questions": 2,
        }
        """
        self._ensure_loaded()

        print(f"\n[1/3] 관련 자료 검색 중...")
        context = self._retriever.retrieve_all_for_generation(params)
        print(f"  >> 문법 {len(context['grammar'])}개, 어휘 {len(context['vocabulary'])}개, "
              f"지문 {len(context['reading_texts'])}개 검색 완료")

        print(f"[2/3] 문항 생성 중 (Claude {params.get('num_questions', 1)}개)...")
        questions = generate_questions(params, context)
        print(f"  >> {len(questions)}개 문항 생성 완료")

        review_result = None
        if auto_review and questions:
            print(f"[3/3] 문항 자동 검토 중...")
            review_result = review_questions(questions, params)
            questions = apply_review_feedback(questions, review_result)
            approved = sum(1 for q in questions if q.get("review", {}).get("approved"))
            print(f"  >> 검토 완료 ({approved}/{len(questions)}개 승인)")

        result = {
            "generated_at": datetime.now().isoformat(),
            "params": params,
            "questions": questions,
            "overall_feedback": review_result.get("overall_feedback", "") if review_result else "",
        }

        # 결과 저장
        output_path = self._save_output(result, params)
        print(f"\n결과 저장: {output_path}")

        return result

    def _save_output(self, result: dict, params: dict) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unit = params.get("unit", "x")
        qtype = params.get("question_type", "unknown").replace("/", "_")
        filename = f"unit{unit}_{qtype}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return filepath

    def format_for_print(self, result: dict) -> str:
        """생성된 문항을 읽기 좋은 텍스트로 포맷한다."""
        lines = []
        params = result.get("params", {})
        lines.append("=" * 60)
        lines.append("KRAG - 한국어 읽기 평가 문항")
        lines.append(f"단원: {params.get('unit')}단원 | 난이도: {params.get('difficulty')} | "
                     f"유형: {params.get('question_type')}")
        lines.append("=" * 60)

        for q in result.get("questions", []):
            lines.append(f"\n【문제 {q.get('question_number', '')}】")
            lines.append("\n[지문]")
            lines.append(q.get("passage", ""))
            lines.append(f"\n{q.get('question', '')}")
            choices = q.get("choices", {})
            for key in ["①", "②", "③", "④"]:
                if key in choices:
                    lines.append(f"  {key} {choices[key]}")
            lines.append(f"\n정답: {q.get('answer', '')}")
            lines.append(f"해설: {q.get('explanation', '')}")

            review = q.get("review", {})
            if review:
                total = review.get("total_score", 0)
                approved = "[승인]" if review.get("approved") else "[검토 필요]"
                lines.append(f"검토: {approved} (점수: {total}/25)")
                if review.get("issues"):
                    lines.append(f"지적사항: {', '.join(review['issues'])}")
            lines.append("-" * 60)

        feedback = result.get("overall_feedback", "")
        if feedback:
            lines.append(f"\n[종합 피드백]\n{feedback}")

        return "\n".join(lines)
