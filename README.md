# KRAG: Korean RAG-based Item Generation

KRAG is a research project for building a RAG-based assistant that helps Korean language teachers draft end-of-semester assessment items after teaching a specific textbook for one semester.

The current generation goal is not to create new passages. The system uses existing reading and listening passages from the textbook, then drafts only question stems and answer options grounded in those passages.

The current repository focuses on a reproducible data foundation: structured Markdown sources, JSONL conversion, and validation reports. Local PDF files are reference materials and are intentionally excluded from GitHub.

## Project Structure

- `source_md/`: source Markdown files
- `scripts/`: conversion and validation scripts
- `rag_jsonl_output/`: generated JSONL files
- `docs/`: handoff notes and research records
- `reports/`: validation reports

## Python Environment

On this Windows workstation, use the fixed Python executable below:

```text
C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe
```

The plain `python` command may point to PsychoPy Python and may not have all required packages. See `docs/python_environment.md`.

## Current Status

- Markdown to JSONL conversion is complete.
- JSONL validation is complete.
- Record counts have been checked.
- TF-IDF baseline retrieval is complete.
- Textbook passage inventory and unit constraints are available.

Current record counts:

- `textbook.jsonl`: 144
- `vocab.jsonl`: 549
- `grammar.jsonl`: 35
- `textbook_knowledge.jsonl`: 728
- `sample_question.jsonl`: 119

Additional generated data:

- `rag_jsonl_output/passage_bank.jsonl`: existing textbook passage candidates for item drafting
- `rag_jsonl_output/chapter_constraints.jsonl`: unit-level grammar and vocabulary constraints

## Rebuild JSONL

Run from the project root:

```powershell
python .\scripts\build_rag_jsonl.py
```

## Validate JSONL

Run from the project root:

```powershell
python .\scripts\validate_rag_jsonl.py
```

The validation report is written to:

```text
reports/validation_report.json
```

## Build TF-IDF Retrieval Index

Run from the project root:

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\build_tfidf_index.py
```

The generated `rag_index/` directory is local-only and excluded from Git.

## Export Retrieval Review Sheet

Run from the project root:

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\export_retrieval_review_sheet.py
```

Review files:

- `reports/retrieval_review_sheet.tsv`
- `reports/retrieval_review_sheet.csv`

Evaluation guide:

- `docs/retrieval_evaluation_guide.md`

## Build Textbook Inventory

Run from the project root:

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\build_textbook_inventory.py
```

Outputs:

- `rag_jsonl_output/passage_bank.jsonl`
- `rag_jsonl_output/chapter_constraints.jsonl`
- `reports/textbook_inventory.json`
- `reports/textbook_inventory.md`

`passage_bank.jsonl` includes explicit reading/listening passages and reusable textbook texts such as complete dialogues, culture texts, task texts, notices, ads, articles, blog-like posts, and guide texts. Each record includes `source_activity`, `candidate_type`, `usable_for_exam`, `priority`, and `extraction_reason`.

## Propose Exam Blueprint

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\propose_exam_blueprint.py --units 1-9 --total-items 30
```

By default, the blueprint uses passage candidates where `usable_for_exam=true` and `priority` is `high` or `medium`.

## Build Item Generation Prompt Packages

Prompt packages combine a selected passage, unit grammar/vocabulary constraints, question type requests, and the expected output schema.

The question type system is derived from `sample_question.md` and organized as:

- `factual`: 사실적 문항
- `inferential`: 추론적 문항
- `evaluative`: 평가적 문항

Schema files:

- `docs/question_type_schema.json`
- `docs/question_type_schema.md`

Each stem type includes suitability rules, generation policy, and fallback recommendations. Prompt packages include `requested_questions`, `suitability_hints`, `allow_skip`, and `skip_policy` so the generator does not force unsuitable requests.

Examples:

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\build_item_generation_prompts.py --passage-id passage_u05_reading_008 --item-count 4 --question-plan reports/item_generation_prompt_samples/question_plan_u05_bulgogi_suitability.json --output-dir reports/item_generation_prompt_samples

& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\build_item_generation_prompts.py --unit 3 --skill reading --item-count 6 --comprehension-type factual --stem-type "내용 일치" --output-dir reports/item_generation_prompt_samples
```

Outputs are saved as JSONL and Markdown under:

- `reports/item_generation_prompt_samples/`

The old `--item-types` option is retained only as a compatibility shim for earlier prompt experiments. New work should use `--question-plan`, `--comprehension-type`, and `--stem-type`.

## Generate Item Drafts From Prompt Packages

OpenAI is the only implemented provider in the current script. The code is structured so additional providers can be added later, but Anthropic is not implemented in this commit.

The API key must be provided through the `OPENAI_API_KEY` environment variable. Do not put API keys in code, documents, sample files, or logs.

Check the run plan before making an API call:

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\generate_items_from_prompts.py --input reports/item_generation_prompt_samples/prompts_passage_u05_reading_008.jsonl --output-dir reports/generated_item_samples --dry-run --limit 1 --overwrite
```

Generate a small sample:

```powershell
& "C:\Users\chani\AppData\Local\Programs\Python\Python313\python.exe" .\scripts\generate_items_from_prompts.py --input reports/item_generation_prompt_samples/prompts_passage_u05_reading_008.jsonl --output-dir reports/generated_item_samples --limit 1 --overwrite
```

Outputs:

- `reports/generated_item_samples/generated_items_*.jsonl`
- `reports/generated_item_samples/skipped_requests_*.jsonl`
- `reports/generated_item_samples/generated_items_*.md`
- `reports/generated_item_samples/generation_errors_*.jsonl`
- `reports/generated_item_samples/raw_responses/` for raw responses that failed JSON parsing

Generated item records now use `comprehension_type`, `comprehension_type_label`, `stem_type`, `stem_template`, `difficulty_rationale`, and `teacher_edit_suggestions` instead of the earlier temporary `item_type` field. Model responses may contain both `items` and `skipped_requests`; at least one must be non-empty.

`skipped_requests` is used when a requested question type is not suitable for the passage. This is especially important for evaluative questions, which require passage-internal evidence such as author attitude, viewpoint, purpose, advice, evaluation, persuasion, or feeling.

## Next Steps

- Human review of `reports/retrieval_review_sheet.tsv` or `.csv`.
- Run small OpenAI item generation samples after setting `OPENAI_API_KEY`.
- Design generated item validation scripts.
