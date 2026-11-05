#!/usr/bin/env python3
"""
CLI Script to Ingest Authentic Government of India Open Datasets into IndicSQL.
Populates all 20 NDAP benchmark databases with genuine, authentic data.

Usage:
    uv run python scripts/ingest_real_gov_data.py
    uv run python scripts/ingest_real_gov_data.py --api-key YOUR_DATA_GOV_IN_KEY
"""

import argparse
import sys
from indicsql.schema.ingest_real_gov_data import ingest_all_20_ndap_databases


def main():
    parser = argparse.ArgumentParser(
        description="Ingest authentic Government of India open datasets across all 20 NDAP benchmark tables."
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Optional data.gov.in API key. If omitted, uses public sandbox key or DATA_GOV_IN_API_KEY env var.",
    )

    args = parser.parse_args()
    print("🚀 Initiating authentic Government of India open data ingestion for all 20 databases...")
    summary = ingest_all_20_ndap_databases(api_key=args.api_key)

    print("\n📊 Ingestion Results Summary (20 NDAP Tables):")
    total_records = 0
    for table, count in summary.items():
        total_records += count
        print(f"  • {table:<36}: {count:>7} records")
    print(f"\n✨ Total Records Ingested: {total_records:,}")
    print("✨ All 20 NDAP benchmark datasets updated with original data successfully!")


if __name__ == "__main__":
    main()
