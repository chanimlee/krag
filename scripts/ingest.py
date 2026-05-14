"""데이터를 ChromaDB에 인제스트하는 스크립트."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.krag_system import KRAGSystem


if __name__ == "__main__":
    system = KRAGSystem()
    system.ingest()
    print("\n모든 데이터가 ChromaDB에 저장되었습니다.")
    print("이제 'python main.py'를 실행하여 문항을 생성할 수 있습니다.")
