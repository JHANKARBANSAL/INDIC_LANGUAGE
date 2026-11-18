# IndicSQL: Schema-Grounded Multilingual Text-to-SQL for Indic Languages

## Abstract

IndicSQL investigates schema-grounded Text-to-SQL across English, Hinglish,
Hindi, Marathi, Bengali, Tamil, and Telugu. The system combines multilingual
schema routing, metric planning, entity grounding, and read-only SQL execution.
Final numerical results will be populated only from the locked official
IndicDB PostgreSQL evaluation.

## Method

The pipeline routes a question to released schema metadata, identifies metric,
aggregation, ranking, grouping, and entity constraints, then executes generated
read-only SQL with timeouts. Invalid routing is recorded as failure; the gold
benchmark schema is not supplied to the predictor.

## Data and protocol

We pin IndicDB to revision `f57b0fb75d672114ae2d6e6be1a78d64056ce8af`.
Parquet inputs, archive, and PostgreSQL dump are SHA-256 verified. The final
evaluation is a deterministic sealed multilingual set evaluated on restored
official PostgreSQL, with model digest, seed, temperature, runtime, and source
hashes locked beforehand.

## Results

Insert only sanitized final-report aggregates here: per-language schema-route
rate, SQL execution success, execution equivalence, latency, errors, empty
results, mapped-schema denominator, and UDISE exclusion count.

## Limitations

UDISE is excluded pending source-level schema identity proof. SQL execution
equivalence is not semantic correctness. Native-speaker review remains required
before claims about naturalness, translation quality, or gold-SQL semantics.
