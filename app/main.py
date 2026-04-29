"""
Main FastAPI application for Production AI API
Complete production-ready API with all patterns
"""

import time
import hashlib
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from models import (
    ChatRequest, ChatResponse, HealthResponse, 
    MetricsResponse, ErrorResponse, APIInfo, RequestStatus
)
from security import get_sanitizer
from cache import get_cache
from agent import get_agent
from monitoring import get_metrics, create_tracker


# Get settings and components
settings = get_settings()
sanitizer = get_sanitizer()
cache = get_cache()
agent = get_agent()
metrics = get_metrics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    print(f"🚀 Starting {settings.api_host}:{settings.api_port}")
    yield
    print("🛑 Shutting down")


# Create FastAPI app
app = FastAPI(
    title="Production AI API",
    description="Enterprise-ready AI API with security, monitoring, and cost optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for monitoring
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Monitor all requests"""
    tracker = create_tracker()
    tracker.start()
    
    try:
        response = await call_next(request)
        processing_time = tracker.stop()
        
        metrics.record_request()
        metrics.record_processing_time(processing_time)
        
        response.headers["X-Process-Time"] = str(processing_time)
        return response
        
    except Exception as e:
        processing_time = tracker.stop()
        metrics.record_error()
        metrics.record_processing_time(processing_time)
        raise


# Routes
@app.get("/", response_model=APIInfo)
async def root():
    """API information"""
    return APIInfo(
        name="Production AI API",
        version="1.0.0",
        description="Enterprise-ready AI API with security, monitoring, and cost optimization",
        endpoints={
            "health": "/health",
            "chat": "/chat",
            "metrics": "/metrics"
        },
        models=[settings.cheap_model, settings.expensive_model],
        features=["Security", "Caching", "Model Routing", "Monitoring", "Error Handling"],
        documentation_url="/docs"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - time.time()  # Will be updated with proper uptime tracking
    
    # Check AI agent health
    agent_health = agent.health_check()
    ai_initialized = agent_health["status"] == "healthy"
    
    return HealthResponse(
        status="healthy" if ai_initialized else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        uptime_seconds=uptime,
        ai_initialized=ai_initialized,
        environment="production" if settings.is_production else "development"
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics_endpoint():
    """Get application metrics"""
    return metrics.get_summary()


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with all production patterns"""
    tracker = create_tracker()
    tracker.start()
    
    try:
        # 1. Security validation
        security_check = sanitizer.validate_input(request.message)
        if not security_check.is_safe:
            metrics.record_error()
            raise HTTPException(
                status_code=400,
                detail=f"Input validation failed: {', '.join(security_check.blocked_patterns)}"
            )
        
        sanitized_message = security_check.sanitized_input
        
        # 2. Token budget check
        estimated_tokens = len(sanitized_message.split()) * 4 // 3
        if estimated_tokens > settings.max_tokens_per_request:
            metrics.record_error()
            raise HTTPException(
                status_code=413,
                detail=f"Message too long: {estimated_tokens} > {settings.max_tokens_per_request} tokens"
            )
        
        # 3. Check cache
        cache_key = hashlib.md5(sanitized_message.encode()).hexdigest()
        cached_response = cache.get(cache_key)
        
        if cached_response:
            processing_time = tracker.stop()
            metrics.record_cache_hit()
            metrics.record_processing_time(processing_time)
            
            return ChatResponse(
                response=cached_response,
                model_used="cache",
                cached=True,
                tokens_used=0,
                processing_time_ms=processing_time,
                status=RequestStatus.CACHED
            )
        
        # 4. Process with AI
        response_content, model_used = agent.process_query(
            sanitized_message, 
            request.model
        )
        
        # 5. Cache the result
        cache.set(cache_key, response_content)
        
        # 6. Record metrics
        processing_time = tracker.stop()
        output_tokens = len(response_content.split()) * 4 // 3
        total_tokens = estimated_tokens + output_tokens
        
        metrics.record_tokens(total_tokens)
        metrics.record_processing_time(processing_time)
        metrics.record_model_usage(model_used, total_tokens, processing_time, True)
        
        return ChatResponse(
            response=response_content,
            model_used=model_used,
            cached=False,
            tokens_used=total_tokens,
            processing_time_ms=processing_time,
            status=RequestStatus.COMPLETED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = tracker.stop()
        metrics.record_error()
        metrics.record_processing_time(processing_time)
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    metrics.record_error()
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=str(exc),
            error_code="INTERNAL_ERROR",
            timestamp=datetime.utcnow(),
            request_id=None
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Production AI API...")
    print(f"📍 Environment: {'Production' if settings.is_production else 'Development'}")
    print(f"📍 Available at: http://{settings.api_host}:{settings.api_port}")
    print(f"📍 Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"📍 Health check: http://{settings.api_host}:{settings.api_port}/health")
    print(f"📍 Metrics: http://{settings.api_host}:{settings.api_port}/metrics")
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower()
    )
