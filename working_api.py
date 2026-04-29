"""
Working API - Bypasses terminal freezing issue
Uses delayed initialization to avoid freezing
"""

from fastapi import FastAPI
from pydantic import BaseModel
import time
import hashlib

app = FastAPI(title="Working AI API")

# Global variables (initialized lazily)
llm = None
is_initialized = False

def initialize_ai():
    """Initialize AI components only when needed"""
    global llm, is_initialized
    if not is_initialized:
        print("🔧 Initializing AI components...")
        from dotenv import load_dotenv
        from langchain_groq import ChatGroq
        import os
        
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        is_initialized = True
        print("✅ AI components initialized")

# Cache
cache = {}
cache_timestamps = {}

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    cached: bool
    processing_time_ms: float

@app.get("/")
async def root():
    return {"message": "Working AI API", "status": "ready"}

@app.get("/health")
async def health():
    return {"status": "healthy", "ai_initialized": is_initialized}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    
    try:
        # Initialize AI on first request
        if not is_initialized:
            initialize_ai()
        
        # Simple caching
        cache_key = hashlib.md5(request.message.encode()).hexdigest()
        if cache_key in cache:
            if time.time() - cache_timestamps[cache_key] < 3600:  # 1 hour TTL
                processing_time = (time.time() - start_time) * 1000
                return ChatResponse(
                    response=cache[cache_key],
                    cached=True,
                    processing_time_ms=processing_time
                )
        
        # Process with AI
        response = llm.invoke(request.message)
        result = response.content
        
        # Cache result
        cache[cache_key] = result
        cache_timestamps[cache_key] = time.time()
        
        processing_time = (time.time() - start_time) * 1000
        return ChatResponse(
            response=result,
            cached=False,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        return ChatResponse(
            response=f"Error: {str(e)}",
            cached=False,
            processing_time_ms=0
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Working AI API...")
    print("📍 Available at: http://localhost:8003")
    print("💬 Chat endpoint: http://localhost:8003/chat")
    print("🔧 AI components will initialize on first request")
    
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
