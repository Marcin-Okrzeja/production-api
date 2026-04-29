"""
Production-Ready AI API
Combining all patterns: security, testing, cost optimization, monitoring
"""

import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
from prometheus_client import Counter, Histogram, generate_latest

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

# === Configuration ===
class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "production-api")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    MAX_TOKENS_PER_REQUEST = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4000"))

# === Logging Setup ===
logger = structlog.get_logger()

# === Metrics ===
REQUEST_COUNT = Counter("production_api_requests_total", "Total API requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("production_api_request_duration_seconds", "API request latency")
TOKEN_USAGE = Counter("production_api_token_usage_total", "Token usage", ["type"])
CACHE_HITS = Counter("production_api_cache_hits_total", "Cache hits")

# === Cache ===
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            if time.time() - self.timestamps[key] < Config.CACHE_TTL:
                CACHE_HITS.inc()
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
    
    @traceable(name="routed_query")
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

# === Application Lifecycle ===
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Production API starting up")
    yield
    logger.info("Production API shutting down")

# === FastAPI App ===
app = FastAPI(
    title="Production AI API",
    description="Enterprise-ready AI API with security, monitoring, and cost optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Middleware for Monitoring ===
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    REQUEST_LATENCY.observe(process_time)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

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

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with all production patterns."""
    start_time = time.time()
    
    try:
        # 1. Input Security
        is_suspicious, reason = sanitizer.is_suspicious(request.message)
        if is_suspicious:
            logger.warning("Suspicious input detected", reason=reason, message=request.message[:100])
            raise HTTPException(status_code=400, detail="Input contains suspicious content")
        
        sanitized_message = sanitizer.sanitize(request.message)
        
        # 2. Token Budget Check
        estimated_tokens = len(sanitized_message.split()) * 4 // 3
        if estimated_tokens > Config.MAX_TOKENS_PER_REQUEST:
            raise HTTPException(
                status_code=413,
                detail=f"Message too long: {estimated_tokens} > {Config.MAX_TOKENS_PER_REQUEST} tokens"
            )
        
        # 3. Caching
        cache_key = hashlib.md5(sanitized_message.encode()).hexdigest()
        cached_response = cache.get(cache_key)
        
        if cached_response:
            processing_time = (time.time() - start_time) * 1000
            logger.info("Cache hit", cache_key=cache_key[:8], processing_time_ms=processing_time)
            
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
        TOKEN_USAGE.labels(type="input").inc(estimated_tokens)
        TOKEN_USAGE.labels(type="output").inc(output_tokens)
        
        logger.info(
            "Chat request completed",
            model=model_used,
            input_tokens=estimated_tokens,
            output_tokens=output_tokens,
            processing_time_ms=processing_time,
            cached=False
        )
        
        return ChatResponse(
            response=response_content,
            model_used=model_used,
            cached=False,
            tokens_used=estimated_tokens + output_tokens,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error", error=str(e), message=request.message[:100])
        REQUEST_COUNT.labels(
            method="POST",
            endpoint="/chat",
            status="500"
        ).inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Production AI API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "metrics": "/metrics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
