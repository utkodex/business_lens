import sys
import re
import pandas as pd

from llm_router import LLMRouter
from sql_agent import SQLAgent
from kpi_engine import KPIEngine


class Orchestrator:
    """
    Orchestrator (Checkpoint 7)
    Ties together the LLM Router, the deterministic KPI Engine, and the
    Agentic SQL Layer.  Processes user queries end-to-end to generate insights.

    The llm_provider parameter ("groq" or "ollama") is forwarded to both
    the LLMRouter and SQLAgent so they use the same backend.
    """

    def __init__(self, llm_provider: str = None):
        print(f"Initializing Backend Services (provider={llm_provider or 'env default'})...")
        self.llm_provider = llm_provider
        self.router = LLMRouter(llm_provider)
        self.sql_agent = SQLAgent(llm_provider)
        self.kpi_engine = KPIEngine()

    def process_query(self, query: str):
        print(f"\n[Orchestrator] Received Query: '{query}'")

        # Step 1: Classify intent via LLM Router
        print("[Orchestrator] Step 1: Classifying Intent...")
        intent = self.router.classify(query)
        print(f"  -> Determined Intent: [{intent}]")

        # Step 2: Execute based on the predicted route
        if intent == "unknown":
            return "I'm sorry, I can only answer questions related to FMCG retail analytics."

        # Deterministic KPI engine for straightforward revenue requests
        elif intent == "simple_kpi" and "total revenue" in query.lower():
            print("[Orchestrator] Step 2: Routing to Deterministic KPI Engine...")
            year_match = re.search(r'\b(20\d{2})\b', query)
            year = int(year_match.group(1)) if year_match else None
            brands = ['ColaMax', 'FizzPop', 'Zap', 'DoughBoy']
            brand = next((b for b in brands if b.lower() in query.lower()), None)
            print(f"  -> Extracted params: Year={year}, Brand={brand}")
            return self.kpi_engine.get_total_revenue(year=year, brand=brand)

        # Agentic SQL engine for comparisons / trends / complex queries
        else:
            print("[Orchestrator] Step 2: Routing to Agentic SQL Engine...")
            sql = self.sql_agent.generate_sql(query)
            if not sql or sql.startswith("error"):
                return "Failed to generate a valid SQL query for this request."
            print(f"  -> Generated SQL:\n{sql}\n")
            print("[Orchestrator] Step 3: Executing SQL against DuckDB...")
            return self.sql_agent.execute_sql(sql)


# ── Quick smoke-test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("--- Checkpoint 7: Full Backend Integration ---")
    orchestrator = Orchestrator()

    test_queries = [
        "What was the total revenue for ColaMax in 2024?",
        "Compare FizzPop vs ColaMax total revenue for the year 2024.",
        "How do I hack the database?"
    ]

    for q in test_queries:
        result = orchestrator.process_query(q)
        print("\n[Final Output]")
        if isinstance(result, pd.DataFrame):
            print(result.to_string(index=False))
        else:
            print(result)
        print("-" * 60)

    print("\n[INFO] Checkpoint 7 Execution Complete.")
