"""KRAG - Korean RAG-based Assessment Generator CLI."""
import sys
import json
import argparse

from src.krag_system import KRAGSystem
from config import DIFFICULTY_LEVELS, QUESTION_TYPES, TEXT_TYPES


def parse_args():
    parser = argparse.ArgumentParser(
        description="KRAG: 서울대 한국어+ 3A 기반 읽기 평가 문항 자동 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py --unit 3 --grammar "-아/어야 하다" --topic 건강 --question-type 세부내용_일치 --difficulty 보통 --num 2
  python main.py --unit 5 --grammar "-다고 하다" --topic SNS --question-type 주제_제목 --difficulty 어려움
  python main.py --ingest
        """,
    )
    parser.add_argument("--ingest", action="store_true", help="데이터를 ChromaDB에 인제스트합니다")
    parser.add_argument("--unit", type=int, choices=range(1, 11), metavar="1-10", help="단원 번호 (1~10)")
    parser.add_argument("--grammar", type=str, default="", help='목표 문법 (예: "-아/어야 하다")')
    parser.add_argument("--topic", type=str, default="", help="주제/소재 (예: 건강, 여행)")
    parser.add_argument(
        "--question-type",
        type=str,
        default="세부내용_일치",
        choices=["세부내용_일치", "세부내용_불일치", "주제_제목", "추론", "어휘", "빈칸채우기"],
        help="문항 유형",
    )
    parser.add_argument(
        "--text-type",
        type=str,
        default="설명문",
        choices=["설명문", "안내문", "대화문", "기사문", "광고문", "이메일"],
        help="지문 유형",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="보통",
        choices=["쉬움", "보통", "어려움"],
        help="난이도",
    )
    parser.add_argument("--num", type=int, default=1, choices=range(1, 6), metavar="1-5", help="생성할 문항 수 (1~5)")
    parser.add_argument("--no-review", action="store_true", help="자동 검토 건너뛰기")
    parser.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    parser.add_argument("--interactive", action="store_true", help="대화형 입력 모드")
    return parser.parse_args()


def interactive_mode(system: KRAGSystem):
    print("\n" + "=" * 60)
    print("KRAG 대화형 문항 생성 모드")
    print("=" * 60)

    def prompt(msg, default="", choices=None):
        if choices:
            print(f"\n{msg}")
            for i, c in enumerate(choices, 1):
                print(f"  {i}. {c}")
            while True:
                val = input(f"선택 (기본값: {default}): ").strip()
                if not val and default:
                    return default
                try:
                    idx = int(val) - 1
                    if 0 <= idx < len(choices):
                        return choices[idx]
                except ValueError:
                    if val in choices:
                        return val
                print("올바른 번호를 입력하세요.")
        else:
            val = input(f"\n{msg} (기본값: {default}): ").strip()
            return val if val else default

    unit_str = prompt("단원 번호를 입력하세요 (1~10)", default="3")
    grammar = prompt('목표 문법을 입력하세요 (예: -아/어야 하다)', default="-아/어야 하다")
    topic = prompt("주제/소재를 입력하세요 (예: 건강)", default="건강")
    question_type = prompt("문항 유형을 선택하세요", default="세부내용_일치",
                           choices=["세부내용_일치", "세부내용_불일치", "주제_제목", "추론", "어휘", "빈칸채우기"])
    text_type = prompt("지문 유형을 선택하세요", default="설명문",
                       choices=["설명문", "안내문", "대화문", "기사문", "광고문", "이메일"])
    difficulty = prompt("난이도를 선택하세요", default="보통",
                        choices=["쉬움", "보통", "어려움"])
    num_str = prompt("생성할 문항 수를 입력하세요 (1~5)", default="1")

    params = {
        "unit": int(unit_str),
        "grammar": grammar,
        "topic": topic,
        "question_type": question_type,
        "text_type": text_type,
        "difficulty": difficulty,
        "num_questions": max(1, min(5, int(num_str))),
    }

    review_choice = prompt("자동 검토를 수행할까요? (y/n)", default="y")
    auto_review = review_choice.lower() != "n"

    result = system.generate(params, auto_review=auto_review)
    print("\n" + system.format_for_print(result))


def main():
    args = parse_args()
    system = KRAGSystem()

    if args.ingest:
        system.ingest()
        return

    if args.interactive:
        interactive_mode(system)
        return

    if not args.unit:
        print("오류: --unit 옵션이 필요합니다. '--interactive' 모드를 사용하거나 --unit을 지정하세요.")
        print("도움말: python main.py --help")
        sys.exit(1)

    params = {
        "unit": args.unit,
        "grammar": args.grammar,
        "topic": args.topic,
        "question_type": args.question_type,
        "text_type": args.text_type,
        "difficulty": args.difficulty,
        "num_questions": args.num,
    }

    result = system.generate(params, auto_review=not args.no_review)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n" + system.format_for_print(result))


if __name__ == "__main__":
    main()
