"""
Minimal working API - Just FastAPI + Groq
"""

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

app = FastAPI(title="Minimal API")

# Initialize Groq once, not at module level
llm = None

def get_llm():
    global llm
    if llm is None:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    return llm

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Minimal API is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "api": "minimal"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        llm = get_llm()
        response = llm.invoke(request.message)
        return ChatResponse(response=response.content)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal API...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
