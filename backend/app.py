"""
app.py — FastAPI chatbot serving the RAG + Persona system.

Endpoints:
  GET  /          → Chat UI (inline HTML/CSS/JS)
  POST /chat      → RAG or persona query
  GET  /persona   → Full persona.json
  GET  /topics    → All topic segments
  GET  /health    → {"status": "ok", "ready": bool}
"""

import json
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_engine import RAGEngine, is_persona_query, format_persona_answer

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
TOPICS_PATH  = BASE_DIR / "data" / "processed" / "topic_segments.json"
PERSONA_PATH = BASE_DIR / "data" / "processed" / "persona.json"

# ── Global engine ─────────────────────────────────────────────────────────────
engine = RAGEngine()


# ── Frontend Serving ────────────────────────────────────────────────────────
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import re

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG engine on startup."""
    print("[APP] Initializing RAG engine...")
    engine.initialize()
    print("[APP] Ready!")
    yield
    print("[APP] Shutting down.")


app = FastAPI(
    title="Kastack Conversation RAG Chatbot",
    description="RAG-powered chatbot over 11K conversation days",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

if frontend_dist.exists():
    if (frontend_dist / "client" / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "client" / "assets")), name="assets")
    elif (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


# ── Request/Response models ───────────────────────────────────────────────────

from typing import Optional

def extract_jobs_from_messages(messages: dict, target_user: str) -> list:
    """Fallback extraction if not provided by rag_engine."""
    jobs = []
    job_pattern = re.compile(r"i (?:am|work as) a(?:n)? ([a-z\s]+)", re.IGNORECASE)
    for msg in messages.values():
        if msg.get("sender") == target_user:
            text = msg.get("message_text", "")
            match = job_pattern.search(text)
            if match:
                jobs.append({"job": match.group(1).strip()})
    return jobs

class ChatRequest(BaseModel):
    message: str
    target_user: Optional[str] = None
    target_topic: Optional[str] = None



@app.post("/chat")
async def chat(req: ChatRequest):
    query = req.message.strip()
    if not query:
        return JSONResponse({"error": "Empty query"}, status_code=400)

    if not engine.ready:
        return JSONResponse({"error": "RAG engine still initializing. Try again in a moment."}, status_code=503)

    # Detect job queries
    job_keywords = ['job', 'work', 'career', 'profession', 'occupation', 'what do you do']
    is_job_query = any(kw in query.lower() for kw in job_keywords)
    
    if is_job_query:
        target = req.target_user or "User 1"  # fallback if needed
        jobs = extract_jobs_from_messages(engine.messages, target)
        
        if jobs:
            # Deduplicate and count
            from collections import Counter
            job_counts = Counter([j['job'] for j in jobs])
            top_jobs = job_counts.most_common(5)
            
            answer = f"{target} mentioned these jobs across conversations:\n"
            for job, count in top_jobs:
                answer += f"• {job.title()} ({count} mention{'s' if count > 1 else ''})\n"
            answer += "\nNote: These are from different conversations with different people."
            
            return JSONResponse({
                "query": query,
                "answer": answer,
                "sources": {"jobs_found": jobs[:15]}, # cap at 15 for UI
                "is_persona_query": False,
                "is_job_query": True
            })
        else:
            return JSONResponse({
                "query": query,
                "answer": f"I couldn't find any job mentions from {target} in the conversations.",
                "sources": {"no_results": True},
                "is_persona_query": False,
                "is_job_query": True
            })

    # Route: persona query vs RAG query
    if is_persona_query(query):
        answer = format_persona_answer(query, engine.persona)
        return JSONResponse({
            "query": query,
            "answer": answer,
            "sources": {"topics_used": [], "messages_used": []},
            "is_persona_query": True
        })

    # RAG pipeline
    result = engine.query(query, target_user=req.target_user, target_topic=req.target_topic)
    result["is_persona_query"] = False
    return JSONResponse(result)

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "ok",
        "ready": engine.ready,
        "total_topics": len(engine.topics) if engine.ready else 0,
        "total_messages": len(engine.messages) if engine.ready else 0,
        "checkpoints_loaded": len(engine.checkpoints) if engine.ready and hasattr(engine, 'checkpoints') and engine.checkpoints else 0
    })

@app.get("/persona")
async def get_persona():
    if not engine.ready:
        return JSONResponse({"error": "Engine initializing"}, status_code=503)
    return JSONResponse(engine.persona)

@app.get("/topics")
async def get_topics():
    if not engine.ready:
        return JSONResponse({"error": "Engine initializing"}, status_code=503)
    topics_list = []
    for v in engine.topics:
        v_dict = dict(v)
        topics_list.append(v_dict)
    return JSONResponse({"total": len(topics_list), "topics": topics_list})

# ── Frontend Proxy ────────────────────────────────────────────────────────────
import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse

# The Node.js SSR server will run on port 3000
client = httpx.AsyncClient(base_url="http://127.0.0.1:3000")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_frontend(request: Request, path: str):
    url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
    req = client.build_request(
        request.method,
        url,
        headers=request.headers.raw,
        content=request.stream()
    )
    resp = await client.send(req, stream=True)
    return StreamingResponse(
        resp.aiter_raw(),
        status_code=resp.status_code,
        headers=resp.headers,
    )

# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
