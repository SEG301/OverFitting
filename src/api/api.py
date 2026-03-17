import os
import uvicorn
import time
import json
import redis
import asyncio
from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Assuming run target is root of SEG module
from src.api.services.search_service import SearchService

# Setup the app
app = FastAPI(
    title="Vietnamese Enterprise Search Engine API",
    description="High-performance backend utilizing Hybrid BM25/Vector retrieval and Cross-Encoder Re-Ranking.",
    version="1.0.0"
)

# 1. Enable CORS for Frontend React/Next.js/HTML access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In prod, specify ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Add Slow Query Logging Middleware
@app.middleware("http")
async def log_slow_queries(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    # Threshold for Slow Query Alert is 0.5s = 500ms
    if process_time > 0.5:
        print(f"⚠️ [SLOW QUERY ALERT] {request.method} {request.url} took {process_time:.4f}s")
    return response

# 3. Setup Redis Caching (Graceful Degradation)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1.0)
    redis_client.ping()
    CACHE_ENABLED = True
except Exception:
    redis_client = None
    CACHE_ENABLED = False

# Shared ML Component Engine Wrapper
search_service = SearchService()

# Automatically Boot Models on Startup
@app.on_event("startup")
async def startup_event():
    print(f"Redis Cache Service: {'ONLINE' if CACHE_ENABLED else 'OFFLINE (localhost:6379 down)'}")
    print("FastAPI System Boot: Mapping files & ML Models to GPU/RAM memory...")
    # NOTE: In test mode we fall back to samples, in prod it parses 6.2GB JSONL via RAM-safe FileStream 
    search_service.initialize()

# Pydantic Schema
class SearchResult(BaseModel):
    universal_id: str
    company_name: str
    description: str
    score: float

class SuggestResult(BaseModel):
    suggestion: str

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Search Engine API is actively running!"}


@app.get("/search", response_model=List[SearchResult], tags=["Search"])
async def do_search(
    q: str = Query(..., min_length=1, description="The search query text"),
    top_k: int = Query(10, ge=1, le=100, description="Number of final results"),
    use_rerank: bool = Query(True, description="Enable Cross-Encoder validation (Slower but 2x accurate)"),
    location: Optional[str] = Query(None, description="Filter by location address"),
    industry: Optional[str] = Query(None, description="Filter by industry tags")
):
    """
    Executes a high-performance Hybrid Search against 1.8M documents with Filters.
    """
    try:
        # Cache Look-Up
        cache_key = f"search:{q}:{top_k}:{use_rerank}:{location}:{industry}"
        if CACHE_ENABLED:
            try:
                cached_res = redis_client.get(cache_key)
                if cached_res:
                    return json.loads(cached_res)
            except Exception:
                pass
                
        filters = {}
        if location: filters["location"] = location
        if industry: filters["industry"] = industry
        
        # Async Execution: Prevents blocking the main FastAPI worker thread for heavy CPU tasks
        results = await asyncio.to_thread(
            search_service.search, raw_query=q, top_k=top_k, use_reranker=use_rerank, filters=filters
        )
        
        # Cache Writing
        if CACHE_ENABLED:
            try:
                # Cache frequent identical queries for 1 hour 
                redis_client.setex(cache_key, 3600, json.dumps(results))
            except Exception:
                pass
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suggest", response_model=List[SuggestResult], tags=["Search"])
async def autocomplete_suggest(
    q: str = Query(..., min_length=2, description="Partial search query")
):
    """
    Returns autocomplete suggestions using the incredibly fast Memory Trie.
    """
    try:
        # Trie query <1ms
        matches = search_service.suggester.suggest(q)
        
        # If trie brings no results (or not loaded), fallback to nlp token suggestion 
        if not matches:
             res = search_service.processor.process(q)
             tokens = res["tokens"]
             if not tokens: return []
             suggestions = [{"suggestion": q + " " + t} for t in tokens[:5]]
             return suggestions
             
        # Map trie matches
        suggestions = [{"suggestion": match} for match in matches]
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company/{id:path}", tags=["Entities"])
async def get_company(id: str):
    """
    Fetches the full JSON object context for a particular company.
    """
    try:
        metadata = search_service.get_company(id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Company not found.")
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Host standard dev server locally on port 8000
    uvicorn.run("src.api.api:app", host="0.0.0.0", port=8000, reload=True)
