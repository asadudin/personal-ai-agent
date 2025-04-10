from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import asyncio
from agent_service import service

# Initialize FastAPI app
app = FastAPI(
    title="MCP Agent Army API",
    description="API for interacting with the MCP Agent Army system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class QueryResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Health Check Endpoint
@app.get("/status")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

# Main Query Endpoint
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        result = await service.process_query(request.query)
        # Transform agent service response to match our API model
        if isinstance(result, dict):
            return {
                "status": "success",
                "data": result.get("result", result)
            }
        return {
            "status": "success",
            "data": {"result": result} if result else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "data": None
        }

# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
