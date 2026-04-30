import sys
import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

class QueryResponse(BaseModel):
    type: str          # "dataframe" or "text"
    data: object       # list[dict] for dataframe, str for text

# --- Singleton Orchestrator ---
orchestrator = None

@app.on_event("startup")
def startup_event():
    """Initialize the orchestrator (LLM + DB connections) once at server start."""
    global orchestrator
    print("[API] Initializing Backend Services...")
    orchestrator = Orchestrator()
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
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Backend services are still initializing.")
    
    try:
        result = orchestrator.process_query(request.query)
        
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
