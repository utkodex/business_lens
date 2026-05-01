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

# ── LLM Provider ────────────────────────────────────────────────────────────
# Switch between "groq" (cloud, ChatGroq) and "ollama" (cloud, ChatOllama)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Groq Cloud – langchain-groq / ChatGroq
# .strip('\'"') safely removes accidental quotes from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip('\'"')
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip('\'"')

# Ollama Cloud – langchain-ollama / ChatOllama (pointing to ollama.com)
OLLAMA_API_KEY  = os.getenv("OLLAMA_API_KEY", "").strip('\'"')
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com").strip('\'"')
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "deepseek-v3.1:671b-cloud").strip('\'"')


if __name__ == "__main__":
    print(f"--- Configuration Checkpoint ---")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")

    files_to_check = [
        ("Internal Sales CSV", INTERNAL_SALES_FILE),
        ("Competitor Market CSV", COMPETITOR_MARKET_FILE),
        ("Data Dictionary", DATA_DICTIONARY_FILE),
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
    print(f"LLM Provider : {LLM_PROVIDER}")
    if LLM_PROVIDER == "groq":
        print(f"Groq Model   : {GROQ_MODEL}")
        print(f"Groq API Key : {'Set' if GROQ_API_KEY else 'MISSING'}")
    else:
        print(f"Ollama Model   : {OLLAMA_MODEL}")
        print(f"Ollama Base URL: {OLLAMA_BASE_URL}")
        print(f"Ollama API Key : {'Set' if OLLAMA_API_KEY else 'MISSING'}")

    if all_files_exist:
        print("\n[SUCCESS] Checkpoint 1 passed: All configuration and data paths are valid.")
    else:
        print("\n[ERROR] Checkpoint 1 failed: Some data files are missing.")
