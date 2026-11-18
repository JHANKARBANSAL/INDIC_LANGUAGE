# IndicDB Benchmark Partitions

This directory holds test harness fixtures and partitions for the **IndicDB Benchmark (April 2026)**:
- 15,617 natural language queries.
- 7 supported languages: Hindi (`hi`), Bengali (`bn`), Tamil (`ta`), Telugu (`te`), Marathi (`mr`), Hinglish (`hi-en`), and English (`en`).
- Complexity levels: Easy, Medium, and Hard (focus on nested aggregations, GROUP BY, and complex multi-table joins).

## Local NDAP partition protocol

`indicdb_eval_suite_pan_india_280.json` began as a frozen local evaluation
suite. Its SHA-256 is `e14c86e500efa61ed4d6689b20d2aed85d2841075f61dbc11e58887132f33e1a`.
Its failure analysis was subsequently used to guide vocabulary and planner
changes, so it is now an **iterative regression suite**, not an unbiased final
test set. Do not report its score as held-out research performance.

`indicdb_development_candidate.json` is a 75-item engineering development
candidate derived reproducibly from `indicdb_eval_suite_expanded.json` by
`scripts/build_development_partition.py`. It excludes every exact normalized
question and gold-SQL string from the frozen 280 suite. It spans all seven
languages, but its translations and gold semantics are **not native-speaker
reviewed**; it must not be presented as a paper-quality benchmark or used for
a multilingual accuracy claim.

`indicdb_unseen_suite_140.json` remains a legacy regression fixture only. Its
100% local result is not an independent performance measurement because its
historical cases informed the regression coverage.
