import os
import sys
import pandas as pd

# Add src to python path so imports work seamlessly
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.orchestrator import Orchestrator

# Create report folder
os.makedirs('report', exist_ok=True)

# 20 diverse business/analytical questions
questions = [
    "What was the total revenue for ColaMax in 2024?",
    "Compare FizzPop vs ColaMax total revenue for the year 2024.",
    "What is the total revenue for DoughBoy in 2024?",
    "How does Zap's revenue compare to FizzPop in 2024?",
    "What was the total sales volume across all categories in 2024?",
    "Which brand had the highest revenue in the Beverages category in 2024?",
    "What is the YoY growth of ColaMax from 2023 to 2024?",
    "List all competitor brands in the Snacks category.",
    "Which category generated more revenue in 2024: Beverages or Snacks?",
    "What was the revenue for Zap in 2024?",
    "Compare our internal sales volume vs competitor sales volume for Beverages in 2024.",
    "What was the revenue for ColaMax in week 10 of 2024?",
    "What is the total market share of DoughBoy in the Snacks category?",
    "What was the total revenue for FizzPop in 2023?",
    "What was the total revenue for ColaMax in 2023?",
    "What was the total revenue for DoughBoy in 2023?",
    "What was the total revenue for Zap in 2023?",
    "Show me the overall total revenue for all internal brands combined.",
    "Which internal brand had the lowest total revenue overall?",
    "Tell me a recipe for a chocolate cake."
]

print("Initializing Orchestrator with Groq backend...")
orchestrator = Orchestrator("groq")

output_path = 'report/query_logs_report.md'

print(f"Generating report at {output_path}...")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("# Business Lens AI - Query Execution Logs\n\n")
    f.write("This document contains the execution logs for 20 sample queries processed by the AI pipeline.\n\n")

    for i, q in enumerate(questions, 1):
        f.write(f"## Query {i}: {q}\n")
        print(f"Processing Query {i}/20...")
        
        # Manually trace orchestrator steps for logging
        intent = orchestrator.router.classify(q)
        f.write(f"- **Intent Predicted:** `{intent}`\n")
        
        if intent == "unknown":
            response = "I'm sorry, I can only answer questions related to FMCG retail analytics."
            f.write(f"- **Route Taken:** Fallback\n")
            f.write(f"- **Final Response:** {response}\n\n")
            continue
            
        if intent == "simple_kpi" and "total revenue" in q.lower():
            f.write(f"- **Route Taken:** Deterministic KPI Engine\n")
            # We let orchestrator run it so we get the exact string/df
            response = orchestrator.process_query(q)
            f.write(f"- **Final Response:** \n```\n{response}\n```\n\n")
            continue
            
        # Agentic Flow
        f.write(f"- **Route Taken:** Agentic SQL Engine\n")
        sql = orchestrator.sql_agent.generate_sql(q)
        f.write(f"- **Generated SQL:** \n```sql\n{sql}\n```\n")
        
        if not sql or sql.startswith("error"):
            f.write(f"- **Execution Result:** Failed to generate valid SQL.\n\n")
            continue
            
        result = orchestrator.sql_agent.execute_sql(sql)
        f.write(f"- **Execution Result:**\n")
        if isinstance(result, pd.DataFrame):
            f.write(f"```text\n{result.to_string(index=False)}\n```\n\n")
        else:
            f.write(f"```text\n{result}\n```\n\n")

print("Report generation complete!")
