# Retrieval Evaluation Guide

Use this guide when reviewing `reports/retrieval_review_sheet.tsv` or `reports/retrieval_review_sheet.csv`.

## relevance

Evaluate how relevant the retrieved result is to the query.

Scores:

- `2` = Directly relevant. The result clearly matches the grammar, topic, or item type in the query.
- `1` = Partially relevant. Only some keywords or topics match.
- `0` = Not relevant.

## usefulness_for_item_generation

Evaluate how useful the retrieved result is for generating a new assessment item.

Scores:

- `2` = Can be used directly as evidence or a format reference for item generation.
- `1` = Can be used after modification or as secondary support.
- `0` = Difficult to use for item generation.

## error_type

If relevance or usefulness is low, record the likely failure type.

Allowed values:

- `none`
- `lexical_match_only`
- `wrong_unit`
- `wrong_skill_area`
- `wrong_question_type`
- `too_general`
- `too_fragmentary`
- `metadata_issue`
- `other`

## reviewer_note

Use this field for free-form reviewer comments.
