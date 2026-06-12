# KRAG: Korean RAG-based Item Generation

KRAG is a research project for building a RAG dataset and pipeline for automatic Korean proficiency and reading assessment item generation.

The current repository focuses on a reproducible data foundation: structured Markdown sources, JSONL conversion, and validation reports. Local PDF files are reference materials and are intentionally excluded from GitHub.

## Project Structure

- `source_md/`: source Markdown files
- `scripts/`: conversion and validation scripts
- `rag_jsonl_output/`: generated JSONL files
- `docs/`: handoff notes and research records
- `reports/`: validation reports

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

## Next Steps

- Build a retrieval index.
- Test retrieval quality.
- Design item generation experiments across RAG conditions.
