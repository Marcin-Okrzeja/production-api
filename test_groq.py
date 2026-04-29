"""
Test Groq connection only
"""

from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

def test_groq():
    print("🔍 Testing Groq connection...")
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        print("❌ GROQ_API_KEY not configured")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        # Test basic Groq connection
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        print("✅ Groq client created")
        
        # Test simple query
        response = llm.invoke("What is 1 + 1?")
        print(f"✅ Groq response: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq error: {e}")
        return False

if __name__ == "__main__":
    success = test_groq()
    print(f"🎯 Test result: {'SUCCESS' if success else 'FAILED'}")
