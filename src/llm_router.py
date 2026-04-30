import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

class LLMRouter:
    """
    LLM Router (Checkpoint 5)
    Acts as the entry point for user queries. Classifies intent so the system
    can route the query to the correct execution path (deterministic SQL vs. agentic generation).
    """
    def __init__(self):
        load_dotenv()
        
        # Read API key explicitly from OLLAMA_API_KEY
        api_key = os.getenv("OLLAMA_API_KEY", "")
        
        # Using exact parameters from working test.py
        base_url = "https://ollama.com"
        model = "deepseek-v3.1:671b-cloud"
        
        # We are using Langchain Ollama as requested.
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}"
            } if api_key else {},
            temperature=0,
        )
        
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
        
    def classify(self, query: str) -> str:
        """
        Classifies a given query into a routing intent.
        """
        try:
            # Clean up the response to ensure strict routing labels
            response = self.chain.invoke({"query": query})
            return response.strip().lower()
        except Exception as e:
            # Provide a fallback error route if the LLM is unreachable or fails
            return f"error: {str(e)}"

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
    
    print("Initializing Langchain Ollama router...\n")
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: '{query}'")
        classification = router.classify(query)
        print(f"Predicted Route: [{classification}]\n")
    
    print("[INFO] Checkpoint 5 Execution Complete.")
