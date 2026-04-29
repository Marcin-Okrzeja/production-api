"""
Test FastAPI without any AI dependencies
"""

from fastapi import FastAPI
import time

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "Hello World", "timestamp": time.time()}

@app.get("/health")
async def health():
    return {"status": "healthy", "test": "basic_fastapi"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Testing FastAPI without AI dependencies...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
