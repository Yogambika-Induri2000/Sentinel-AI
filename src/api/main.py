import sys
import os
import warnings
warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.genai.agent import search_vectors_direct, execute_sql_direct, build_sentinel_agent

app = FastAPI(
    title="Sentinel-AI API",
    description="Real-Time TikTok Trend & Misinformation Intelligence Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------
class VectorSearchRequest(BaseModel):
    query: str

class SQLQueryRequest(BaseModel):
    sql: str

class AgentQueryRequest(BaseModel):
    prompt: str
    openai_api_key: Optional[str] = None


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/")
def health_check():
    """Health check endpoint to verify API operation."""
    return {"status": "online", "service": "Sentinel-AI Intelligence Engine", "version": "1.0.0"}


@app.post("/api/v1/search/vector")
def vector_search_endpoint(request: VectorSearchRequest):
    """Executes HNSW Cosine Similarity Vector Search against transcript embeddings in pgvector."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty.")
    
    result = search_vectors_direct(request.query)
    return {"query": request.query, "results": result}


@app.post("/api/v1/search/sql")
def sql_query_endpoint(request: SQLQueryRequest):
    """Executes structured analytical queries against the PostgreSQL 'videos' table."""
    if not request.sql.strip():
        raise HTTPException(status_code=400, detail="SQL statement cannot be empty.")
    
    result = execute_sql_direct(request.sql)
    return {"sql": request.sql, "results": result}


@app.post("/api/v1/agent/query")
def agent_query_endpoint(request: AgentQueryRequest):
    """Routes natural language queries through the LangChain Agentic RAG Router (Text-to-SQL + Vector Search)."""
    api_key = request.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400, 
            detail="OPENAI_API_KEY must be provided in request payload or set in server environment."
        )
    
    try:
        agent = build_sentinel_agent(api_key)
        response = agent.invoke({"input": request.prompt})
        return {"prompt": request.prompt, "response": response["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")