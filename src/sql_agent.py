import os
import re
import duckdb
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from config import (
    DUCKDB_FILE,
    LLM_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL,
    OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL,
)

SCHEMA = """
Tables and their columns:
1. dim_time (date_id BIGINT, week_start TIMESTAMP, year BIGINT, month BIGINT, quarter BIGINT, week_number BIGINT)
2. dim_product (product_id BIGINT, sku_id VARCHAR, brand VARCHAR, variant VARCHAR)
3. dim_category (category_id BIGINT, category VARCHAR)
4. dim_retailer (retailer_id BIGINT, retailer VARCHAR)
5. fact_internal_sales (date_id BIGINT, product_id BIGINT, category_id BIGINT, retailer_id BIGINT, volume DOUBLE, total_sales DOUBLE, is_imputed BOOLEAN)
6. fact_competitor_market (date_id BIGINT, category_id BIGINT, retailer_id BIGINT, competitor_volume BIGINT, competitor_sales DOUBLE)

Relationships:
- fact_internal_sales and fact_competitor_market both join to dim_time on date_id.
- fact_internal_sales and fact_competitor_market both join to dim_category on category_id and dim_retailer on retailer_id.
- fact_internal_sales joins to dim_product on product_id.
"""


class SQLAgent:
    """
    SQL Agent (Checkpoint 6)
    Acts as a Text-to-SQL engine for complex analytical queries.
    Uses the underlying LLM to generate DuckDB-compatible SQL based on the star schema.

    Supports two backends:
      - "groq"   → ChatGroq  (langchain-groq,   cloud, llama-3.3-70b-versatile)
      - "ollama" → ChatOllama (langchain-ollama, cloud, ollama.com endpoint)
    """

    def __init__(self, llm_provider: str = None):
        load_dotenv()
        self.llm_provider = (llm_provider or LLM_PROVIDER).lower()
        self.llm = self._build_llm()
        self.db_path = str(DUCKDB_FILE)

        self.prompt = PromptTemplate.from_template("""
You are an expert Data Analyst and DuckDB SQL developer.
Generate a valid, highly optimized DuckDB SQL query to answer the user's question based on the provided schema.

Schema Details:
{schema}

Rules:
1. Return ONLY the SQL code enclosed in ```sql and ``` blocks. Do not include any conversational text, pleasantries, or explanations.
2. Use standard SQL joins based on the Relationships provided.
3. Be mindful of null values and use standard aggregations.
4. When filtering by strings, pay attention to exact matches (e.g., 'ColaMax', 'FizzPop').

Question: {question}
SQL Query:
""")
        self.chain = self.prompt | self.llm | StrOutputParser()

    # ------------------------------------------------------------------
    def _build_llm(self):
        """Instantiate the correct LangChain LLM based on the chosen provider."""
        if self.llm_provider == "groq":
            print(f"[SQLAgent] Using ChatGroq  → model: {GROQ_MODEL}")
            key = GROQ_API_KEY if GROQ_API_KEY else "invalid_key_prevent_crash"
            return ChatGroq(
                api_key=key,
                model=GROQ_MODEL,
                temperature=0,
            )
        else:  # "ollama"
            print(f"[SQLAgent] Using ChatOllama → {OLLAMA_BASE_URL} / model: {OLLAMA_MODEL}")
            return ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {},
                temperature=0,
            )

    # ------------------------------------------------------------------
    def generate_sql(self, question: str) -> str:
        """Takes a natural language question and generates a SQL query string."""
        try:
            response = self.chain.invoke({"schema": SCHEMA, "question": question})
            match = re.search(r"```(?:sql)?\n(.*?)\n```", response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return response.strip()
        except Exception as e:
            print(f"[Error] SQL Generation failed: {e}")
            return ""

    def execute_sql(self, query: str):
        """Executes a generated SQL query against the DuckDB instance."""
        if not query:
            return None
        with duckdb.connect(self.db_path, read_only=True) as conn:
            try:
                return conn.execute(query).df()
            except Exception as e:
                print(f"[DuckDB Execution Error]: {e}")
                return None


# ── Quick smoke-test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("--- Checkpoint 6: Agentic SQL Layer ---")
    agent = SQLAgent()

    question = "Compare FizzPop vs ColaMax total revenue for the year 2024. Show the brand and total revenue, ordered by revenue descending."
    print(f"Question: '{question}'\n")

    print("Generating SQL via LLM...")
    sql_query = agent.generate_sql(question)

    if sql_query:
        print(f"\n[Generated SQL]\n{sql_query}\n")
        print("Executing SQL against DuckDB...")
        results = agent.execute_sql(sql_query)
        if results is not None:
            print("\n[Query Results]")
            print(results.to_string(index=False))
        else:
            print("Query execution failed.")
    else:
        print("Failed to generate SQL.")

    print("\n[INFO] Checkpoint 6 Execution Complete.")
