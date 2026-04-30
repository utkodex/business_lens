import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Data files
INTERNAL_SALES_FILE = DATA_DIR / "weekly_internal_sales.csv"
COMPETITOR_MARKET_FILE = DATA_DIR / "weekly_competitor_market.csv"
DATA_DICTIONARY_FILE = DATA_DIR / "Data Dictionary.xlsx"

# Database
DB_DIR = BASE_DIR / "db"
DUCKDB_FILE = DB_DIR / "business_lens.duckdb"

# LLM Configuration (DeepSeek Cloud)
# Loaded from .env file
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1") 
LLM_MODEL = os.getenv("LLM_MODEL", "llmdeepseek-v3.1")

if __name__ == "__main__":
    print(f"--- Configuration Checkpoint ---")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    
    # Check data files
    files_to_check = [
        ("Internal Sales CSV", INTERNAL_SALES_FILE),
        ("Competitor Market CSV", COMPETITOR_MARKET_FILE),
        ("Data Dictionary", DATA_DICTIONARY_FILE)
    ]
    
    print("\nVerifying Data Files:")
    all_files_exist = True
    for name, path in files_to_check:
        exists = path.exists()
        status = "OK" if exists else "FAIL"
        print(f"  [{status}] {name}: {path}")
        if not exists:
            all_files_exist = False
            
    print(f"\nDatabase path: {DUCKDB_FILE}")
    print(f"LLM Model: {LLM_MODEL}")
    print(f"LLM API Key configured: {'Yes' if DEEPSEEK_API_KEY else 'No'}")
    
    if all_files_exist:
        print("\n[SUCCESS] Checkpoint 1 passed: All configuration and data paths are valid.")
    else:
        print("\n[ERROR] Checkpoint 1 failed: Some data files are missing.")
