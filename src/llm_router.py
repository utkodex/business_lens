import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from config import (
    LLM_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL,
    OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL,
)


class LLMRouter:
    """
    LLM Router (Checkpoint 5)
    Acts as the entry point for user queries.  Classifies intent so the system
    can route the query to the correct execution path (deterministic SQL vs.
    agentic generation).

    Supports two backends selectable at construction time:
      - "groq"   → ChatGroq  (langchain-groq,   cloud, llama-3.3-70b-versatile)
      - "ollama" → ChatOllama (langchain-ollama, cloud, ollama.com endpoint)
    """

    def __init__(self, llm_provider: str = None):
        load_dotenv()
        self.llm_provider = (llm_provider or LLM_PROVIDER).lower()
        self.llm = self._build_llm()

        self.prompt = PromptTemplate.from_template("""
You are an intelligent router for an FMCG retail analytics AI assistant.
Your job is to classify the user's query into one of the following exact categories:

- "simple_kpi": The user is asking for straightforward metrics like Total Revenue, Market Share, or YoY Growth for a specific brand, category, or time period.
- "comparison": The user is comparing two or more entities (e.g., comparing brands, categories, or retailers).
- "trend_analysis": The user is asking about trends, forecasting, or patterns over time.
- "unknown": The query is unrelated to retail analytics, or is too vague/complex to classify.

Return ONLY the exact category name (e.g., simple_kpi) without any other text, punctuation, or explanation.

User Query: {query}
Category:""")

        self.chain = self.prompt | self.llm | StrOutputParser()

    # ------------------------------------------------------------------
    def _build_llm(self):
        """Instantiate the correct LangChain LLM based on the chosen provider."""
        if self.llm_provider == "groq":
            print(f"[LLMRouter] Using ChatGroq  → model: {GROQ_MODEL}")
            return ChatGroq(
                api_key=GROQ_API_KEY,
                model=GROQ_MODEL,
                temperature=0,
            )
        else:  # "ollama"
            print(f"[LLMRouter] Using ChatOllama → {OLLAMA_BASE_URL} / model: {OLLAMA_MODEL}")
            return ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {},
                temperature=0,
            )

    # ------------------------------------------------------------------
    def classify(self, query: str) -> str:
        """Classifies a given query into a routing intent."""
        try:
            response = self.chain.invoke({"query": query})
            return response.strip().lower()
        except Exception as e:
            return f"error: {str(e)}"


# ── Quick smoke-test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("--- Checkpoint 5: Intent Classification ---")
    router = LLMRouter()

    test_queries = [
        "What was the total revenue for ColaMax in 2024?",
        "How does the market share of FizzPop compare to Zap in Beverages?",
        "What are the sales trends for Snacks over the last 3 quarters?",
        "Show me the YoY growth for DoughBoy.",
        "Can you write a python script to hack the database?"
    ]

    print(f"Initializing router with provider: {router.llm_provider}\n")
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: '{query}'")
        classification = router.classify(query)
        print(f"Predicted Route: [{classification}]\n")

    print("[INFO] Checkpoint 5 Execution Complete.")
