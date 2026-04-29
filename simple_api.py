"""
Simple Production API - No Prometheus, No Complex Dependencies
Just FastAPI + Groq + Basic Security + Caching
"""

import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# === Configuration ===
class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "simple-api")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    MAX_TOKENS_PER_REQUEST = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4000"))

# === Cache ===
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            if time.time() - self.timestamps[key] < Config.CACHE_TTL:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: str):
        self.cache[key] = value
        self.timestamps[key] = time.time()

cache = SimpleCache()

# === Security ===
class InputSanitizer:
    def __init__(self):
        self.suspicious_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"forget\s+(all\s+)?previous",
            r"new\s+instructions:",
            r"system\s*prompt",
            r"---\s*end\s*(of)?\s*prompt",
            r"pretend\s+you\s+are",
            r"act\s+as\s+(if\s+)?you",
            r"bypass\s+(all\s+)?restrictions",
        ]
    
    def is_suspicious(self, text: str) -> tuple[bool, Optional[str]]:
        import re
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True, f"Suspicious pattern detected: {pattern}"
        return False, None
    
    def sanitize(self, text: str) -> str:
        import re
        text = re.sub(r"[-]{3,}", "", text)
        text = re.sub(r"[=]{3,}", "", text)
        text = text.replace("{{", "{ {").replace("}}", "} }")
        return text.strip()

sanitizer = InputSanitizer()

# === Cost Optimization ===
class ModelRouter:
    def __init__(self):
        self.cheap_model = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        self.expensive_model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        self.classifier = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    def classify_complexity(self, query: str) -> str:
        prompt = ChatPromptTemplate.from_template(
            """Classify this query's complexity as 'simple' or 'complex'.

Simple: Basic facts, short answers, simple calculations
Complex: Analysis, reasoning, creative tasks, multi-step problems

Query: {query}

Respond with only: simple or complex"""
        )
        response = self.classifier.invoke(prompt.format(query=query))
        return response.content.strip().lower()
    
    def invoke(self, query: str) -> tuple[str, str]:
        complexity = self.classify_complexity(query)
        model = self.cheap_model if complexity == "simple" else self.expensive_model
        model_name = "llama-3.1-8b-instant" if complexity == "simple" else "llama-3.3-70b-versatile"
        
        response = model.invoke(query)
        return response.content, model_name

router = ModelRouter()

# === API Models ===
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    cached: bool
    tokens_used: int
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float

# === FastAPI App ===
app = FastAPI(
    title="Simple Production AI API",
    description="Production-ready AI API with security and cost optimization",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple metrics storage
metrics = {
    "requests_total": 0,
    "cache_hits": 0,
    "errors_total": 0,
    "total_tokens": 0
}

start_time = time.time()

# === Routes ===
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        uptime_seconds=time.time() - start_time
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Simple Production AI API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "metrics": "/metrics"
        },
        "metrics": metrics
    }

@app.get("/metrics")
async def get_metrics():
    """Simple metrics endpoint."""
    return metrics

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with production patterns."""
    start_time = time.time()
    metrics["requests_total"] += 1
    
    try:
        # 1. Input Security
        is_suspicious, reason = sanitizer.is_suspicious(request.message)
        if is_suspicious:
            metrics["errors_total"] += 1
            raise HTTPException(status_code=400, detail="Input contains suspicious content")
        
        sanitized_message = sanitizer.sanitize(request.message)
        
        # 2. Token Budget Check
        estimated_tokens = len(sanitized_message.split()) * 4 // 3
        if estimated_tokens > Config.MAX_TOKENS_PER_REQUEST:
            metrics["errors_total"] += 1
            raise HTTPException(
                status_code=413,
                detail=f"Message too long: {estimated_tokens} > {Config.MAX_TOKENS_PER_REQUEST} tokens"
            )
        
        # 3. Caching
        cache_key = hashlib.md5(sanitized_message.encode()).hexdigest()
        cached_response = cache.get(cache_key)
        
        if cached_response:
            processing_time = (time.time() - start_time) * 1000
            metrics["cache_hits"] += 1
            
            return ChatResponse(
                response=cached_response,
                model_used="cache",
                cached=True,
                tokens_used=0,
                processing_time_ms=processing_time
            )
        
        # 4. Model Routing & Processing
        response_content, model_used = router.invoke(sanitized_message)
        
        # 5. Cache the result
        cache.set(cache_key, response_content)
        
        # 6. Metrics
        processing_time = (time.time() - start_time) * 1000
        output_tokens = len(response_content.split()) * 4 // 3
        total_tokens = estimated_tokens + output_tokens
        metrics["total_tokens"] += total_tokens
        
        return ChatResponse(
            response=response_content,
            model_used=model_used,
            cached=False,
            tokens_used=total_tokens,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        metrics["errors_total"] += 1
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple Production AI API...")
    print("📍 Available at: http://localhost:8000")
    print("📊 Health check: http://localhost:8000/health")
    print("💬 Chat endpoint: http://localhost:8000/chat")
    print("📈 Metrics: http://localhost:8000/metrics")
    
    uvicorn.run(
        "simple_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
