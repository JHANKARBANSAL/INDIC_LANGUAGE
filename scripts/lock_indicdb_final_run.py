#!/usr/bin/env python3
"""Create a credential-free configuration lock before an IndicDB sealed run.

This program deliberately does not open the selected-key file.  The companion
sealed evaluator validates this lock before it is permitted to do so.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import psycopg2

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.build_sealed_indicdb_final import LANGUAGE_FILES  # noqa: E402

SOURCE_MANIFEST = REPO_ROOT / "data/benchmarks/indicdb_source_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def git_state() -> dict[str, Any]:
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True).strip()
    )
    return {"git_revision": revision, "worktree_dirty": dirty}


def runtime_metadata(dsn: str) -> dict[str, str]:
    connection = psycopg2.connect(dsn)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version")
            server_version = str(cursor.fetchone()[0])
            cursor.execute("SELECT current_database(), current_user")
            database, user = cursor.fetchone()
    finally:
        connection.close()
    major = int(server_version.split(".", 1)[0])
    if major < 16:
        raise ValueError(f"IndicDB final run requires PostgreSQL 16+; found {server_version}.")
    return {
        "postgresql_server_version": server_version,
        "postgresql_major_version": str(major),
        "database_name": str(database),
        "database_user": str(user),
        "connection_mode": "INDICDB_DSN environment variable; excluded from lock",
    }


def ollama_model_digest(endpoint: str, model_name: str) -> str:
    response = httpx.get(f"{endpoint.rstrip('/')}/api/tags", timeout=5.0)
    response.raise_for_status()
    for model in response.json().get("models", []):
        if model.get("name") == model_name:
            digest = model.get("digest")
            if isinstance(digest, str) and digest:
                return digest
    raise ValueError(f"Locked Ollama model is not installed exactly: {model_name!r}")


def build_lock(
    *,
    parquet_dir: Path,
    archive: Path,
    dump: Path,
    sealed_manifest: Path,
    dsn: str,
    model_name: str,
    model_endpoint: str,
    temperature: float,
    seed: int,
    evaluator_command: str,
) -> dict[str, Any]:
    manifest = json.loads(sealed_manifest.read_text(encoding="utf-8"))
    if manifest.get("question_and_sql_in_manifest") is not False:
        raise ValueError("Sealed manifest must not contain question or SQL text.")
    parquet_hashes = {
        language: sha256_file(parquet_dir / filename)
        for language, filename in LANGUAGE_FILES.items()
    }
    if parquet_hashes != manifest.get("input_parquet_sha256"):
        raise ValueError("Pinned Parquet hashes do not match the sealed manifest.")
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if sha256_file(archive) != source["official_source_archive"]["local_sha256"]:
        raise ValueError("Archive hash does not match the verified source manifest.")
    if sha256_file(dump) != source["postgresql_dump"]["local_sha256"]:
        raise ValueError("Dump hash does not match the verified source manifest.")
    return {
        "artifact_type": "IndicDB sealed final-run lock",
        "lock_version": 1,
        "sealed_manifest_sha256": sha256_file(sealed_manifest),
        "benchmark_revision": manifest["benchmark_revision"],
        "input_parquet_sha256": parquet_hashes,
        "official_archive_sha256": sha256_file(archive),
        "official_dump_sha256": sha256_file(dump),
        "source_snapshot": {
            "source_manifest_sha256": sha256_file(SOURCE_MANIFEST),
            "archive_file_name": archive.name,
            "dump_file_name": dump.name,
        },
        "model": {
            "provider": "ollama",
            "endpoint": model_endpoint.rstrip("/"),
            "name": model_name,
            "digest": ollama_model_digest(model_endpoint, model_name),
            "temperature": temperature,
            "seed": seed,
        },
        "evaluator_command": evaluator_command,
        "postgresql_runtime": runtime_metadata(dsn),
        "code": git_state(),
        "credentials_included": False,
        "selected_keys_included": False,
        "questions_or_gold_sql_included": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--sealed-manifest", type=Path, default=REPO_ROOT / "data/benchmarks/indicdb_final_sealed_manifest.json")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "data/benchmarks/indicdb_final_run_lock.json")
    parser.add_argument("--model-name", default="qwen2.5:7b")
    parser.add_argument("--model-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--temperature", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--evaluator-command", required=True)
    args = parser.parse_args()
    dsn = os.environ.get("INDICDB_DSN")
    if not dsn:
        parser.error("Set INDICDB_DSN; it is used but never written to the lock.")
    if args.output.exists():
        parser.error(f"Refusing to overwrite existing lock: {args.output}")
    lock = build_lock(
        parquet_dir=args.parquet_dir, archive=args.archive, dump=args.dump,
        sealed_manifest=args.sealed_manifest, dsn=dsn, model_name=args.model_name,
        model_endpoint=args.model_endpoint, temperature=args.temperature,
        seed=args.seed, evaluator_command=args.evaluator_command,
    )
    lock["lock_sha256"] = canonical_hash(lock)
    args.output.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote credential-free sealed lock: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
