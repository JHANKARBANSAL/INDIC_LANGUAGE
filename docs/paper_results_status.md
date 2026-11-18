# Paper-results status

## Permitted now

Use local NDAP results only as **development/regression diagnostics**. Label
every chart with the benchmark path, local DuckDB database variant, fallback
inference mode, dirty-worktree state, and the warning that the suite informed
engineering changes.

Recommended diagnostic figures:

- execution accuracy by language with Wilson intervals;
- failure taxonomy: routing, entity grounding, SQL semantics, and no-SQL;
- ablation timeline: baseline, routing, metric planner, vocabulary, entity,
  and ranking changes.

## Not permitted yet

- held-out multilingual accuracy claims;
- official IndicDB parity claims;
- semantic-correctness claims;
- license-subtype claims.

These require sealed official evaluation, native-language/gold review, UDISE
resolution or stated exclusion, and exact license evidence.
