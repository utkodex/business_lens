import sys
import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal

# Add src to python path so imports work seamlessly
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from orchestrator import Orchestrator

# --- FastAPI App ---
app = FastAPI(
    title="Business Lens AI API",
    description="FMCG Category Intelligence API — routes queries through deterministic KPI engine or agentic SQL layer.",
    version="1.0.0"
)

# --- CORS (allow Streamlit frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request / Response Models ---
class QueryRequest(BaseModel):
    query: str
    llm_provider: Literal["groq", "ollama"] = "groq"   # UI toggle

class QueryResponse(BaseModel):
    type: str          # "dataframe" or "text"
    data: object       # list[dict] for dataframe, str for text

# --- Lazy Orchestrator cache (one instance per provider) ---
_orchestrators: dict[str, Orchestrator] = {}

def get_orchestrator(provider: str) -> Orchestrator:
    """Return (and lazily create) the orchestrator for the given provider."""
    if provider not in _orchestrators:
        print(f"[API] Creating Orchestrator for provider='{provider}'...")
        _orchestrators[provider] = Orchestrator(provider)
        print(f"[API] Orchestrator ready for provider='{provider}'.")
    return _orchestrators[provider]

@app.on_event("startup")
def startup_event():
    """Pre-warm the default Groq orchestrator at server start."""
    get_orchestrator("groq")
    print("[API] Backend ready.")

# --- Endpoints ---

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Business Lens AI API"}

@app.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest):
    """
    Process a natural-language analytics query.
    Routes through the Orchestrator pipeline (LLM Router → KPI Engine / SQL Agent).
    The llm_provider field selects the backend: 'groq' or 'ollama'.
    """
    try:
        orch = get_orchestrator(request.llm_provider)
        result = orch.process_query(request.query)

        if isinstance(result, pd.DataFrame):
            return QueryResponse(
                type="dataframe",
                data=result.to_dict(orient="records")
            )
        else:
            return QueryResponse(
                type="text",
                data=str(result)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
