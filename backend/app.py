"""
app.py - FastAPI chatbot serving the RAG + Persona system.

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

# Round 2 modules (intent / affect / conflict-RAG)
ROUND2_STATUS = {}
try:
    from round2.intent import classify as r2_intent
    ROUND2_STATUS["intent"] = True
except Exception as e:
    r2_intent = None
    ROUND2_STATUS["intent"] = f"error: {e}"
try:
    from round2.affect import emotion as r2_emotion
    ROUND2_STATUS["affect"] = True
except Exception as e:
    r2_emotion = None
    ROUND2_STATUS["affect"] = f"error: {e}"
try:
    from round2.rag import conflict_resolver as r2_conflict
    ROUND2_STATUS["conflict"] = True
except Exception as e:
    r2_conflict = None
    ROUND2_STATUS["conflict"] = f"error: {e}"
try:
    from round2.paths import ROUND2_DIR
    ROUND2_STATUS["paths"] = True
except Exception as e:
    ROUND2_DIR = None
    ROUND2_STATUS["paths"] = f"error: {e}"

# Lazy cache for the heavy conflict-RAG assets (MiniLM + ~294MB embeddings).
# TODO: reuse engine.embeddings instead of loading a second copy.
_conflict_assets = None
def get_conflict_assets():
    global _conflict_assets
    if _conflict_assets is None:
        _conflict_assets = r2_conflict.load_assets()
    return _conflict_assets

# Paths
BASE_DIR = Path(__file__).parent.parent
TOPICS_PATH  = BASE_DIR / "data" / "processed" / "topic_segments.json"
PERSONA_PATH = BASE_DIR / "data" / "processed" / "persona.json"

# Global engine
engine = RAGEngine()


# Frontend Serving
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


# Request/Response models

from typing import Optional

NOT_JOBS = {"nervous", "tired", "scared", "worried", "hungry", "happy",
            "sad", "excited", "bored", "sorry", "sure", "glad", "fine",
            "good", "great", "well", "okay", "ok", "sick", "busy",
            "interested", "curious", "afraid", "ready", "able",
            "home", "here", "there", "back", "away", "alone",
            "big fan", "huge fan", "new", "old", "young",
            "jealous", "lucky", "close", "impressed", "terrible",
            "awful", "horrible", "amazing", "wonderful", "fantastic",
            "proud", "grateful", "thankful", "blessed", "pleased",
            "certain", "confident", "comfortable", "uncomfortable",
            "confused", "lost", "stuck", "frustrated", "annoyed",
            "careful", "serious", "kidding", "joking", "telling",
            "open", "honest", "kind", "nice", "mean", "sweet",
            "right", "wrong", "crazy", "insane", "mad", "angry",
            "thinking about", "talking about", "looking forward",
            "managing", "coping", "surviving", "thriving",
            "free", "available", "late", "early",
            "different", "similar", "same", "like", "unlike",
            "stay"
           }

def extract_jobs_from_messages(messages: dict, target_user: str) -> list:
    """Fallback extraction if not provided by rag_engine."""
    jobs = []
    
    # Updated to ignore "at" if followed by "home"
    job_patterns = [
        re.compile(r"(?i)\bi['’]?m\s+an?\s+([a-z][a-z\s\-]+?)(?:\.|,|\!|\?|\s+and\s|\s+who\s|\s+that\s|\s+at\s+(?!home)|\s+for\s|\s+with\s|\s+so\s|$)", re.IGNORECASE),
        re.compile(r"(?i)\bi\s+work\s+as\s+an?\s+([a-z][a-z\s\-]+?)(?:\.|,|\!|\?|\s+and\s|\s+who\s|\s+that\s|\s+at\s+(?!home)|\s+for\s|\s+with\s|\s+so\s|$)", re.IGNORECASE)
    ]
    
    # Bulletproof target_user normalization
    user_str = str(target_user).lower().replace("_", "").replace(" ", "")
    if "1" in user_str:
        normalized_user = "User 1"
    elif "2" in user_str:
        normalized_user = "User 2"
    else:
        normalized_user = str(target_user).title()

    for msg in messages.values():
        if msg.get("sender") == normalized_user:
            text = msg.get("message_text", "")
            for pattern in job_patterns:
                match = pattern.search(text)
                if match:
                    job_str = match.group(1).strip().lower()
                    if job_str and job_str not in NOT_JOBS and len(job_str) > 2:
                        jobs.append({
                            "job": job_str,
                            "text": text,
                            "day": msg.get("day", 0),
                            "sender": msg.get("sender"),
                            "msg_id": msg.get("msg_id")
                        })
                        break # Only extract one job per message to avoid duplicates
    return jobs

class ChatRequest(BaseModel):
    message: str
    target_user: Optional[str] = None
    target_topic: Optional[str] = None


class TextRequest(BaseModel):
    text: str


class ConflictRequest(BaseModel):
    query: str
    subject: Optional[str] = None



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
        "checkpoints_loaded": len(engine.checkpoints) if engine.ready and hasattr(engine, 'checkpoints') and engine.checkpoints else 0,
        "round2_ready": all(v is True for v in ROUND2_STATUS.values()),
        "round2_modules": ROUND2_STATUS
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

# Round 2 endpoints (MUST stay above the catch-all frontend proxy)

@app.post("/intent")
async def intent(req: TextRequest):
    if r2_intent is None:
        return JSONResponse({"error": "intent module unavailable"}, status_code=503)
    return JSONResponse(r2_intent.classify(req.text))


@app.post("/affect")
async def affect(req: TextRequest):
    if r2_emotion is None:
        return JSONResponse({"error": "affect module unavailable"}, status_code=503)
    return JSONResponse(r2_emotion.score(req.text))


@app.get("/drift")
async def drift(view: Optional[str] = None):
    if ROUND2_DIR is None:
        return JSONResponse({"error": "round2 paths unavailable"}, status_code=503)
    path = ROUND2_DIR / "drift" / "timeline_with_triggers.json"
    if not path.exists():
        return JSONResponse({"error": "timeline_with_triggers.json not found"}, status_code=404)
    data = json.loads(path.read_text(encoding="utf-8"))
    if view == "real":
        return JSONResponse({"data_caveat": data.get("data_caveat"), "segments": data.get("real_data_segments", [])})
    if view == "demo":
        return JSONResponse({"segments": data.get("demo_arc_segments", [])})
    return JSONResponse(data)


@app.get("/drift/chart")
async def drift_chart(view: str = "demo"):
    if ROUND2_DIR is None:
        return JSONResponse({"error": "round2 paths unavailable"}, status_code=503)
    fname = "real_drift_chart.png" if view == "real" else "drift_chart.png"
    path = ROUND2_DIR / "drift" / fname
    if not path.exists():
        return JSONResponse({"error": f"{fname} not found"}, status_code=404)
    return FileResponse(str(path), media_type="image/png")


@app.post("/conflict")
async def conflict(req: ConflictRequest):
    if r2_conflict is None:
        return JSONResponse({"error": "conflict module unavailable"}, status_code=503)
    assets = get_conflict_assets()
    result = r2_conflict.retrieve_and_rerank_data(req.query, assets, subject_term=req.subject, top_k=10)
    return JSONResponse(result)

# Frontend Proxy
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

# Dev runner
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
