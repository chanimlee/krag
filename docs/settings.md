# Settings

## Python

현재 실행 환경의 Python 버전은 `python --version`으로 확인한다.

## 주요 패키지

이번 단계 requirements:

- pandas
- openpyxl
- chromadb
- sentence-transformers
- rank-bm25
- pydantic
- tqdm
- python-dotenv
- openai

이번 단계에서 실제로 사용하는 패키지:

- pandas
- openpyxl

## 향후 ChromaDB 예정 설정

- persist_directory = `./chroma_db`
- embedding_model = `BAAI/bge-m3`
- vector_db = `ChromaDB`

이번 단계에서는 ChromaDB collection을 실제로 만들지 않는다.

## Stage 2 RAG Retrieval Settings

- vector_db = ChromaDB
- persist_directory = ./chroma_db
- embedding_model = BAAI/bge-m3
- embedding_library = sentence-transformers
- embedding_model_role = RAG 문서의 dense embedding 생성
- selection_reason = BAAI/bge-m3는 다국어 retrieval에 적합하고, 교재 지문·문법·어휘·문항 샘플처럼 길이와 성격이 다른 한국어 교육 자료를 의미 기반으로 검색하는 데 적합하기 때문에 사용한다.
- retrieval_mode = dense retrieval
- distance_metric = cosine
- metadata_filtering = true
- batch_size = 32
- top_k = 5
- embedding_dimension = 1024
- collection_names: snu3a_u2_passages, snu3a_u2_knowledge, snu3a_u2_sample_questions
- model_decision_note = 초기 후보였던 sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens 대신, 현 시점의 RAG 구축 및 향후 서비스 확장성을 고려하여 BAAI/bge-m3를 기본 임베딩 모델로 확정하였다.

## Stage 2.5 Manual Review Decisions

- retrieval test manual review를 수행함
- prompt package 생성 전에 검색 결과를 수동 검토함
- target passage는 검색이 아니라 processed passage에서 직접 선택하기로 함
- 문법/어휘는 dense retrieval보다 structured metadata와 exact/substring match를 우선하기로 함
- TOPIK sample question은 construct filter + balanced sampling을 사용하기로 함
- 검토용 preview에는 passage_preview, stem, options_preview를 별도 제공하기로 함

## Stage 3 Prompt Package Generation Settings

- target_passage_selection = processed JSONL direct selection
- vocabulary_selection = unit-level structured inclusion
- grammar_selection = chapter-level structured inclusion
- grammar_detail_selection = grammar_id linked inclusion
- topik_sample_selection = construct filter + balanced sampling
- source_question_selection = related_passage_id -> same chapter_id -> ChromaDB fallback
- llm_api_called = false

## Stage 4 LLM Generation Settings

- llm_generation_model = gpt-4.1-mini
- temperature = prompt package generation_config 값 사용
- response_format = json_object
- max_tokens = 3000
- timeout_seconds = 120
- max_retries = 2
- retry_delay_seconds = 3
- 이번 단계에서는 기본 형식 검증만 수행
- evidence_sentence, 정답 유일성, 복사 여부, 목표 어휘·문법 포함 여부 정밀 검증은 5단계 예정

## Stage 4 LLM Generation Settings

- llm_generation_model = gpt-4.1-mini
- temperature = prompt package generation_config 값 사용
- response_format = json_object
- max_tokens = 3000
- timeout_seconds = 120
- max_retries = 2
- retry_delay_seconds = 3
- 이번 단계에서는 기본 형식 검증만 수행
- evidence_sentence, 정답 유일성, 복사 여부, 목표 어휘·문법 포함 여부 정밀 검증은 5단계 예정

## Stage 4 LLM Generation Settings

- llm_generation_model = gpt-4.1-mini
- temperature = prompt package generation_config 값 사용
- response_format = json_object
- max_tokens = 3000
- timeout_seconds = 120
- max_retries = 2
- retry_delay_seconds = 3
- 이번 단계에서는 기본 형식 검증만 수행
- evidence_sentence, 정답 유일성, 복사 여부, 목표 어휘·문법 포함 여부 정밀 검증은 5단계 예정

## Stage 5 Validation Settings

- evidence_match = exact OR whitespace-normalized match
- generated_passage_length = 250~400 Korean characters without spaces
- vocabulary_inclusion = generated passage text contains at least required_vocab_count vocabulary items
- grammar_inclusion = simple core-string heuristic for grammar forms
- source_copy_similarity = 5-gram character Jaccard; fail >=0.80, warning >=0.50
- llm_api_called = false

## Stage 6 Final Candidate Selection Settings

- final candidate selection rule: validation 결과를 기준으로 문항을 accept/revise/reject 후보로 자동 분류한다.
- preliminary_decision: pass=accept_candidate, warning=revise_candidate, fail=reject_candidate.
- manual_decision 우선 규칙: accept/revise/reject 값이 있으면 preliminary_decision보다 우선한다.
- summary table 생성 기준: 5단계 검증 결과와 6단계 최종 후보 분류 결과를 발표문용 표 형태로 요약한다.

## Stage 5 Validation Settings

- evidence_match = exact OR whitespace-normalized match
- generated_passage_length = 250~400 Korean characters without spaces
- vocabulary_inclusion = generated passage text contains at least required_vocab_count vocabulary items
- grammar_inclusion = simple core-string heuristic for grammar forms
- source_copy_similarity = 5-gram character Jaccard; fail >=0.80, warning >=0.50
- llm_api_called = false


## Stage 6 Option Quality Revision Settings

- revise decision 기준: 정답과 기본 근거는 타당하지만 선택지, 근거 제시, 지문 길이, 목표 어휘·문법 반영 등 일부 수정이 필요한 경우 revise로 둔다.
- evidence exact match 실패만으로 reject하지 않는다. 복수 문장 또는 전체 지문을 통해 답을 추론할 수 있고 manual_decision/comment가 있으면 accept 또는 revise 후보로 분류한다.
- option copy warning 기준: 선택지 전체가 지문에 exact/normalized substring으로 포함되거나 문자 n-gram overlap score가 0.80 이상이면 warning으로 표시한다.
- option order rule: shortest_to_longest. 공백 제외 문자열 길이를 1차 기준, 공백 포함 길이를 2차 기준, 기존 순서를 3차 기준으로 한다.
- answer recalculation after option reordering: 정답 텍스트를 기준으로 새 answer 번호를 반드시 재계산한다.


## Webapp Settings

- webapp framework = Streamlit
- embedded input excel = data/raw/RAG_textbook_chapter_input_template.xlsx
- embedded processed data = data/processed/*.jsonl
- embedded prompt packages = prompts/*.jsonl
- sample mode = enabled
- API mode = optional, requires OPENAI_API_KEY environment variable
- API key display/logging = disabled
- option order rule = shortest_to_longest
- validation includes option_copy_check
- webapp run outputs = outputs/webapp_runs/{run_id}/


## Similar Passage API Mode Settings

- similar_passage_api_mode = enabled
- generated_passage_min_length_without_spaces = 120
- validation includes vocabulary_inclusion_check, grammar_inclusion_check, passage_copy_check
- prompt package selection priority = target.chapter_id match, prompt_id contains chapter_id, same unit fallback, first available package
- API key source = OPENAI_API_KEY environment variable
- API key is not displayed, logged, or saved
