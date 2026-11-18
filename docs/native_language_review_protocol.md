# Native-language review protocol

This protocol is required before any seven-language benchmark result is used in
a paper claim. Machine-generated or developer-authored translations are not
native-speaker validation.

## Review unit

Review each benchmark item independently in Hindi, Marathi, Bengali, Tamil,
Telugu, Hinglish, and English. A reviewer must record:

- whether the question is natural and unambiguous in its declared language;
- whether every state, district, commodity, sector, and programme mention has
  the intended meaning;
- whether the stated aggregation, ranking, grouping, and time scope are
  explicit in the question;
- whether the gold SQL expresses that meaning against the documented schema;
- whether the result is meaningful (including intentional empty results).

## Required reviewers and decisions

- One fluent native speaker per native language; two independent reviewers for
  items marked ambiguous or changed after review.
- Reviewers must not see model predictions before approving question meaning
  and gold SQL intent.
- Record `approved`, `rewrite_required`, or `gold_sql_correction_required`,
  with a brief rationale and reviewer/date identifier.

## Publication gate

Do not report multilingual accuracy, language rankings, or semantic correctness
until every reported item is approved or excluded with a recorded reason.
The current local development and frozen suites remain `review_pending`.
