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

## Next Steps

- Human review of `reports/retrieval_review_sheet.tsv` or `.csv`.
- Implement a selected-passage-based item draft pipeline.
- Design generated item validation scripts.
