from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from src.agents.super_agents import SuperAgent
from src.database.weaviate_client import weaviate_manager
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Sanjeevani Multi-Agent API",
    version="0.1.0",
    description="FastAPI interface for querying the Sanjeevani multi-agent system"
)

# ---------- Request Model ----------
class QueryRequest(BaseModel):
    question: str
    limit: Optional[int] = 3
    session_id: Optional[str] = None

# ---------- Response Models ----------
class AgentResult(BaseModel):
    agent: str
    results: List[Any]
    summary: str
    confidence: float

class QueryResponse(BaseModel):
    answer: str
    details: List[AgentResult]

# ---------- Startup ----------
@app.on_event("startup")
async def startup_event():
    logging.info("🚀 Starting API and connecting to Weaviate...")
    if weaviate_manager.connect():
        if weaviate_manager.create_collections():
            logging.info("✅ Weaviate connected and collections ready.")
        else:
            logging.error(" Failed to create collections in Weaviate.")
    else:
        logging.error(" Could not connect to Weaviate at startup.")

# ---------- Shutdown ----------
@app.on_event("shutdown")
async def shutdown_event():
    logging.info(" Shutting down API and closing Weaviate connection...")
    weaviate_manager.close()

# ---------- Root Endpoint ----------
@app.get("/")
async def root():
    return {"message": "Sanjeevani Multi-Agent API is running"}

# ---------- Query Endpoint ----------
@app.post("/query", response_model=QueryResponse)
async def query_api(request: QueryRequest):
    try:
        sa = SuperAgent()
        response = sa.query(
            question=request.question,
            limit=request.limit,
            session_id=request.session_id
        )
        return response
    except Exception as e:
        logging.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
