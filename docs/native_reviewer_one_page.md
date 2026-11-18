# IndicSQL reviewer instructions

Review only the development CSV packet assigned to your language. Do not view
model predictions. For every row, mark these fields `yes`, `no`, or
`unclear`:

1. `natural_and_unambiguous`: Is the question natural and clear?
2. `terms_correct`: Do scheme, entity, and metric terms carry the intended meaning?
3. `intent_explicit`: Are aggregation, ranking, grouping, and time scope clear?
4. `gold_sql_semantics`: Does the gold SQL answer that question?

Set `review_status` to `approved`, `rewrite_required`,
`gold_sql_correction_required`, or `needs_second_review`. Add a short reason,
your name/identifier, and date. Do not change the question or SQL cells.

Packets are development-only and do not contain sealed-final questions.
