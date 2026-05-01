"""
build_db.py — Rebuilds the DuckDB star-schema from CSV sources.
Called at container startup so the app works even when the .duckdb file
is not committed to git.
"""

import sys
import os

# Ensure src/ is on the path so config / data_pipeline / db_manager resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
from config import DUCKDB_FILE, INTERNAL_SALES_FILE, COMPETITOR_MARKET_FILE
from data_pipeline import clean_internal_sales, clean_competitor_market
from db_manager import setup_database, create_schema_and_load_data


def build():
    """Build (or rebuild) the DuckDB database from CSV data files."""
    if DUCKDB_FILE.exists():
        print(f"[build_db] Database already exists at {DUCKDB_FILE}, rebuilding...")
        os.remove(DUCKDB_FILE)

    print("[build_db] Loading & cleaning internal sales data...")
    df_internal = clean_internal_sales(pd.read_csv(INTERNAL_SALES_FILE))

    print("[build_db] Loading & cleaning competitor market data...")
    df_comp = clean_competitor_market(pd.read_csv(COMPETITOR_MARKET_FILE))

    print("[build_db] Connecting to DuckDB & building star schema...")
    conn = setup_database()
    create_schema_and_load_data(conn, df_internal, df_comp)
    conn.close()

    print("[build_db] ✅ Database built successfully.")


if __name__ == "__main__":
    build()
