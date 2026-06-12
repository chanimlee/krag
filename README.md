# KRAG: Korean RAG-based Item Generation

KRAG is a research project for building a RAG dataset and pipeline for automatic Korean proficiency and reading assessment item generation.

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

Current record counts:

- `textbook.jsonl`: 144
- `vocab.jsonl`: 549
- `grammar.jsonl`: 35
- `textbook_knowledge.jsonl`: 728
- `sample_question.jsonl`: 119

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

## Next Steps

- Human review of `reports/retrieval_review_sheet.tsv` or `.csv`.
- Design item generation experiments across RAG conditions.
