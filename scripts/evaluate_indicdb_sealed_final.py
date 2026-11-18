#!/usr/bin/env python3
"""Run the one-time IndicDB final audit without schema-oracle routing.

The lock is checked before this program opens the ignored selected-key file.
Results intentionally exclude final questions, gold SQL, benchmark schema names,
and selected keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any
from zipfile import ZipFile

import httpx
import pandas as pd
import psycopg2
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indicsql.agents.sql_synthesizer import _ollama_client
from indicsql.benchmark.indicdb import INDICDB_LANGUAGE_FILES, IndicDBQuery, enrich_schema_context
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.sandbox.postgres_engine import PostgresSandbox
from scripts.execute_indicdb_gold import build_schema_mapping
from scripts.lock_indicdb_final_run import canonical_hash, ollama_model_digest, sha256_file

REPO_ROOT = Path(__file__).resolve().parent.parent


def normalized_rows(rows: list[list[Any]]) -> list[str]:
    def normalize(value: Any) -> Any:
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, (int, float)):
            return round(float(value), 6)
        return value
    return sorted(json.dumps([normalize(value) for value in row], ensure_ascii=False) for row in rows)


def load_released_schema_configs(archive: Path) -> dict[str, dict[str, Any]]:
    configs: dict[str, dict[str, Any]] = {}
    with ZipFile(archive) as bundle:
        for name in bundle.namelist():
            if name.endswith('/schema_config.yaml'):
                config = yaml.safe_load(bundle.read(name))
                configs[config['database_name']] = config
    return configs


def validate_lock_before_keys(
    lock: dict[str, Any], manifest: Path, parquet_dir: Path, archive: Path, dump: Path, dsn: str
) -> None:
    unsigned = dict(lock)
    observed_lock_hash = unsigned.pop('lock_sha256', None)
    if observed_lock_hash != canonical_hash(unsigned):
        raise ValueError('Final-run lock integrity check failed.')
    if lock.get('credentials_included') or lock.get('selected_keys_included') or lock.get('questions_or_gold_sql_included'):
        raise ValueError('Final-run lock violates sealed-content policy.')
    if sha256_file(manifest) != lock.get('sealed_manifest_sha256'):
        raise ValueError('Sealed manifest differs from the locked manifest.')
    manifest_payload = json.loads(manifest.read_text(encoding='utf-8'))
    if manifest_payload.get('question_and_sql_in_manifest') is not False:
        raise ValueError('Manifest is not sealed.')
    hashes = {
        language: sha256_file(parquet_dir / filename)
        for language, filename in INDICDB_LANGUAGE_FILES.items()
    }
    if hashes != lock.get('input_parquet_sha256') or hashes != manifest_payload.get('input_parquet_sha256'):
        raise ValueError('Pinned Parquet verification failed.')
    if sha256_file(archive) != lock.get('official_archive_sha256'):
        raise ValueError('Official archive verification failed.')
    if sha256_file(dump) != lock.get('official_dump_sha256'):
        raise ValueError('Official dump verification failed.')
    connection = psycopg2.connect(dsn)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SHOW server_version')
            version = str(cursor.fetchone()[0])
            cursor.execute('SELECT current_database(), current_user')
            database, user = cursor.fetchone()
    finally:
        connection.close()
    runtime = lock.get('postgresql_runtime', {})
    if (version != runtime.get('postgresql_server_version') or str(database) != runtime.get('database_name')
            or str(user) != runtime.get('database_user') or int(version.split('.', 1)[0]) < 16):
        raise ValueError('PostgreSQL runtime differs from the locked PostgreSQL 16+ runtime.')
    model = lock.get('model', {})
    if ollama_model_digest(model['endpoint'], model['name']) != model.get('digest'):
        raise ValueError('Installed Ollama model digest differs from final-run lock.')


def load_selected_queries(parquet_dir: Path, selected_keys: set[tuple[str, str]]) -> list[IndicDBQuery]:
    """Read only rows whose pair IDs can belong to sealed keys, after validation."""
    pair_ids = sorted({pair_id for pair_id, _ in selected_keys})
    queries: list[IndicDBQuery] = []
    for language, filename in INDICDB_LANGUAGE_FILES.items():
        frame = pd.read_parquet(
            parquet_dir / filename,
            columns=['question', 'sql', 'pair_id', 'dataset_name'],
            filters=[('pair_id', 'in', pair_ids)],
        ).fillna('')
        for row in frame.itertuples(index=False):
            key = (str(row.pair_id).strip(), str(row.dataset_name).strip())
            if key in selected_keys and str(row.question).strip() and str(row.sql).strip():
                queries.append(IndicDBQuery(language, key[0], str(row.question).strip(), str(row.sql).strip(), key[1]))
    expected = len(selected_keys) * len(INDICDB_LANGUAGE_FILES)
    if len(queries) != expected:
        raise ValueError(f'Sealed key selection yielded {len(queries)} rows; expected {expected}.')
    return queries


def route_schema(question: str, model: dict[str, Any], candidates: list[str]) -> str | None:
    """Return only an exact released schema name; never use benchmark metadata."""
    prompt = (
        'Choose the one database schema that can answer the user question. '\
        'Return exactly one schema name from this list and nothing else. '\
        f'Schemas: {", ".join(candidates)}\nQuestion: {question}'
    )
    response = httpx.post(
        f"{model['endpoint']}/api/generate",
        json={'model': model['name'], 'prompt': prompt, 'stream': False,
              'options': {'temperature': model['temperature'], 'seed': model['seed']}},
        timeout=90.0,
    )
    response.raise_for_status()
    chosen = str(response.json().get('response', '')).strip().strip('`').strip()
    return chosen if chosen in candidates else None


def opaque_record_id(query: IndicDBQuery) -> str:
    return hashlib.sha256(f'{query.language}\0{query.pair_id}\0{query.dataset_name}'.encode()).hexdigest()[:16]


def selected_key_digest(payload: list[dict[str, str]]) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    ).hexdigest()


def write_checkpoint(path: Path, lock_hash: str, records: list[dict[str, Any]]) -> None:
    """Persist only sanitized completed records; never questions or gold SQL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        'artifact_type': 'IndicDB sealed evaluation checkpoint',
        'lock_sha256': lock_hash,
        'completed_records': len(records),
        'records': records,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parquet-dir', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--dump', type=Path, required=True)
    parser.add_argument('--sealed-manifest', type=Path, required=True)
    parser.add_argument('--lock', type=Path, required=True)
    parser.add_argument('--sealed-key-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--receipt', type=Path, default=REPO_ROOT / 'benchmark_results/sealed_final/indicdb_final_run_receipt.json')
    parser.add_argument('--statement-timeout-ms', type=int, default=5000)
    args = parser.parse_args()
    dsn = os.environ.get('INDICDB_DSN')
    if not dsn:
        parser.error('Set INDICDB_DSN; it is never written to outputs.')
    if args.output.exists():
        parser.error(f'Refusing to overwrite final result: {args.output}')
    if args.receipt.exists():
        parser.error(f'A sealed final run has already been recorded: {args.receipt}')
    checkpoint = args.checkpoint or args.output.with_suffix('.checkpoint.json')
    if checkpoint.exists():
        parser.error(f'Refusing to overwrite sealed checkpoint: {checkpoint}')
    lock = json.loads(args.lock.read_text(encoding='utf-8'))
    # This must precede all selected-key access.
    validate_lock_before_keys(lock, args.sealed_manifest, args.parquet_dir, args.archive, args.dump, dsn)
    manifest = json.loads(args.sealed_manifest.read_text(encoding='utf-8'))
    key_payload = json.loads(args.sealed_key_file.read_text(encoding='utf-8'))
    if selected_key_digest(key_payload) != manifest.get('selected_key_sha256'):
        raise ValueError('Selected-key file does not match the sealed manifest.')
    selected_keys = {(item['pair_id'], item['dataset_name']) for item in key_payload}
    queries = load_selected_queries(args.parquet_dir, selected_keys)
    configs = load_released_schema_configs(args.archive)
    mappings = build_schema_mapping(args.archive)
    unresolved = set(manifest.get('excluded_unresolved_schema_names', []))
    candidates = sorted(name for name in configs if name not in unresolved)
    model = lock['model']
    _ollama_client.base_url, _ollama_client.model_name, _ollama_client._is_active = model['endpoint'], model['name'], None
    if not _ollama_client.is_available or _ollama_client.model_name != model['name']:
        raise RuntimeError('Locked Ollama model unavailable; refusing fallback.')
    records: list[dict[str, Any]] = []
    metrics: dict[str, Counter[str]] = defaultdict(Counter)
    sandbox = PostgresSandbox(dsn, statement_timeout_ms=args.statement_timeout_ms)
    try:
        for query in queries:
            started = perf_counter()
            router_error = None
            try:
                chosen = route_schema(query.question, model, candidates)
            except Exception as exc:
                chosen = None
                router_error = f'{type(exc).__name__}: {exc}'
            prediction = None
            prediction_error = None
            generated_sql = ''
            if chosen is None:
                prediction_error = router_error or 'invalid_schema_router_output'
            else:
                postgres_schema = chosen.lower()
                try:
                    context = enrich_schema_context(sandbox.get_schema_context(postgres_schema), configs[chosen])
                    state = execute_indicsql_pipeline(
                        query.question, query_id=f'sealed-{opaque_record_id(query)}',
                        database_schema_name=postgres_schema, database_schema=context,
                        database_schema_source='released_metadata_router', language_override=query.language,
                        sandbox=sandbox,
                    )
                    prediction, generated_sql = state.get('execution_result'), state.get('generated_sql', '')
                    prediction_error = state.get('execution_error')
                except Exception as exc:
                    prediction_error = f'{type(exc).__name__}: {exc}'
            # Gold metadata is used only after prediction and only for the reference execution.
            gold = None
            gold_error = None
            gold_mapping = mappings.get(query.dataset_name)
            if gold_mapping is None:
                gold_error = 'unresolved_gold_schema_mapping'
            else:
                try:
                    gold = sandbox.execute_query(query.gold_sql, gold_mapping['postgres_schema_name'])
                except Exception as exc:
                    gold_error = f'{type(exc).__name__}: {exc}'
            match = None if gold is None or prediction is None else normalized_rows(gold['rows']) == normalized_rows(prediction['rows'])
            metrics[query.language]['queries'] += 1
            metrics[query.language]['valid_schema_routes'] += chosen is not None
            metrics[query.language]['prediction_errors'] += bool(prediction_error)
            metrics[query.language]['gold_errors'] += bool(gold_error)
            metrics[query.language]['execution_matches'] += match is True
            records.append({'record_id': opaque_record_id(query), 'language': query.language,
                            'routed_schema': chosen, 'generated_sql': generated_sql,
                            'prediction_error': prediction_error, 'gold_error': gold_error,
                            'prediction_row_count': None if prediction is None else prediction['row_count'],
                            'gold_row_count': None if gold is None else gold['row_count'],
                            'execution_match': match, 'latency_ms': round((perf_counter()-started)*1000, 3)})
            write_checkpoint(checkpoint, lock['lock_sha256'], records)
    finally:
        sandbox.close()
    result = {'artifact_type': 'IndicDB sealed final evaluation', 'official_postgresql_required': True,
              'semantic_correctness_verified': False, 'native_language_review_verified': False,
              'lock_sha256': lock['lock_sha256'], 'selected_question_count': len(records),
              'mapped_schema_denominator': len(records),
              'udise_identity_unresolved': 'INDIA_UDISE_SCHOOL_PROFILES' in manifest.get('excluded_unresolved_schema_names', []),
              'udise_excluded_benchmark_schema_names': ['INDIA_UDISE_SCHOOL_PROFILES'],
              'per_language': {key: dict(value) for key, value in sorted(metrics.items())}, 'records': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({
        'artifact_type': 'IndicDB sealed final-run receipt',
        'lock_sha256': lock['lock_sha256'],
        'result_sha256': sha256_file(args.output),
        'selected_question_count': len(records),
        'contains_questions_or_gold_sql': False,
    }, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote sealed result without questions/gold SQL: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
