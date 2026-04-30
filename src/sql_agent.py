import os
import re
import duckdb
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

from config import DUCKDB_FILE

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
    """
    def __init__(self):
        load_dotenv()
        
        api_key = os.getenv("OLLAMA_API_KEY", "")
        base_url = "https://ollama.com"
        model = "deepseek-v3.1:671b-cloud"
        
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            temperature=0,
        )
        
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

    def generate_sql(self, question: str) -> str:
        """
        Takes a natural language question and generates a SQL query string.
        """
        try:
            response = self.chain.invoke({"schema": SCHEMA, "question": question})
            
            # Use regex to perfectly extract the SQL block if it exists
            match = re.search(r"```(?:sql)?\n(.*?)\n```", response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
            # If no markdown block is found, strip whitespace and return
            return response.strip()
        except Exception as e:
            print(f"[Error] SQL Generation failed: {e}")
            return ""

    def execute_sql(self, query: str):
        """
        Executes a generated SQL query against the DuckDB instance.
        """
        if not query:
            return None
            
        with duckdb.connect(self.db_path, read_only=True) as conn:
            try:
                return conn.execute(query).df()
            except Exception as e:
                print(f"[DuckDB Execution Error]: {e}")
                return None

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
