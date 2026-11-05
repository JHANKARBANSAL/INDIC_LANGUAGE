#!/usr/bin/env python3
"""
CLI Script to Curate Fine-Tuning Corpora Grounded in Authentic NDAP Government Data.
Regenerates:
- data/training/sarvam_partition.jsonl (Cross-lingual Indic-to-English translation & entity normalization)
- data/training/qwen_partition.jsonl (DDL-to-SQL aggregation & reasoning)
- data/training/val_sarvam.jsonl (Ground-truth validation)
- data/training/val_qwen.jsonl (Ground-truth validation)

Usage:
    uv run python scripts/curate_training_data.py
    uv run python scripts/curate_training_data.py --sarvam-count 6000 --qwen-count 6000
"""

import argparse
import json
import logging
from pathlib import Path
from indicsql.training.dataset_curator import DatasetCurator


def main():
    parser = argparse.ArgumentParser(
        description="Curate fine-tuning corpora grounded in authentic NDAP data."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/training",
        help="Target output directory (default: data/training)",
    )
    parser.add_argument(
        "--sarvam-count",
        type=int,
        default=6000,
        help="Number of transliteration records for Sarvam partition (default: 6000)",
    )
    parser.add_argument(
        "--qwen-count",
        type=int,
        default=6000,
        help="Number of SQL records for Qwen partition (default: 6000)",
    )
    parser.add_argument(
        "--sarvam-val-count",
        type=int,
        default=600,
        help="Number of validation records for Sarvam partition (default: 600)",
    )
    parser.add_argument(
        "--qwen-val-count",
        type=int,
        default=600,
        help="Number of validation records for Qwen partition (default: 600)",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("🚀 Initiating fine-tuning dataset curation grounded in real NDAP stores...")
    curator = DatasetCurator()
    summary = curator.curate_and_export(
        Path(args.output_dir),
        sarvam_count=args.sarvam_count,
        qwen_count=args.qwen_count,
        sarvam_val_count=args.sarvam_val_count,
        qwen_val_count=args.qwen_val_count,
    )

    print("\n📊 Curation Results Summary:")
    print(f"  • Sarvam Partition (Transliteration) : {summary['sarvam_training']['count']:,} pairs -> {summary['sarvam_training']['path']}")
    print(f"  • Qwen Partition (Text-to-SQL)       : {summary['qwen_training']['count']:,} pairs -> {summary['qwen_training']['path']}")
    print(f"  • Validation (Sarvam Held-Out)       : {summary['validation_split']['val_sarvam_count']:,} pairs -> {summary['validation_split']['val_sarvam_path']}")
    print(f"  • Validation (Qwen Held-Out)         : {summary['validation_split']['val_qwen_count']:,} pairs -> {summary['validation_split']['val_qwen_path']}")
    print(f"\n✨ Total Training Records   : {summary['total_train_records']:,}")
    print(f"✨ Total Validation Records : {summary['total_val_records']:,}")
    print("✨ Fine-tuning datasets successfully aligned with 10% held-out validation split!")


if __name__ == "__main__":
    main()
