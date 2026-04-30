import sys
import re
import pandas as pd

# Import the individual pipeline components
from llm_router import LLMRouter
from sql_agent import SQLAgent
from kpi_engine import KPIEngine

class Orchestrator:
    """
    Orchestrator (Checkpoint 7)
    Ties together the LLM Router, the deterministic KPI Engine, and the Agentic SQL Layer.
    Processes user queries end-to-end to generate final insights.
    """
    def __init__(self):
        print("Initializing Backend Services...")
        self.router = LLMRouter()
        self.sql_agent = SQLAgent()
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
            
        # For straightforward KPI requests, try the deterministic engine first (fast, 100% accurate, no hallucinations)
        elif intent == "simple_kpi" and "total revenue" in query.lower():
            print("[Orchestrator] Step 2: Routing to Deterministic KPI Engine...")
            
            # Simple parameter extraction for the deterministic engine
            year_match = re.search(r'\b(20\d{2})\b', query)
            year = int(year_match.group(1)) if year_match else None
            
            # Identify brand if mentioned
            brands = ['ColaMax', 'FizzPop', 'Zap', 'DoughBoy']
            brand = next((b for b in brands if b.lower() in query.lower()), None)
            
            print(f"  -> Extracted params: Year={year}, Brand={brand}")
            df = self.kpi_engine.get_total_revenue(year=year, brand=brand)
            return df
            
        # For complex analysis (comparisons, trends), route to the Agentic SQL Engine
        else:
            print("[Orchestrator] Step 2: Routing to Agentic SQL Engine...")
            sql = self.sql_agent.generate_sql(query)
            
            if not sql or sql.startswith("error"):
                return "Failed to generate a valid SQL query for this request."
                
            print(f"  -> Generated SQL:\n{sql}\n")
            print("[Orchestrator] Step 3: Executing SQL against DuckDB...")
            df = self.sql_agent.execute_sql(sql)
            return df

if __name__ == "__main__":
    print("--- Checkpoint 7: Full Backend Integration ---")
    orchestrator = Orchestrator()
    
    test_queries = [
        # Should route to KPI Engine
        "What was the total revenue for ColaMax in 2024?", 
        
        # Should route to SQL Agent
        "Compare FizzPop vs ColaMax total revenue for the year 2024.", 
        
        # Should be blocked
        "How do I hack the database?"
    ]
    
    for q in test_queries:
        result = orchestrator.process_query(q)
        print("\n[Final Output]")
        
        if isinstance(result, pd.DataFrame):
            # Print dataframe cleanly
            print(result.to_string(index=False))
        else:
            # Print string messages (like errors or unknown responses)
            print(result)
            
        print("-" * 60)
        
    print("\n[INFO] Checkpoint 7 Execution Complete.")
