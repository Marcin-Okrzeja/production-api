"""
AI Agent module for Production AI API
Model routing and AI processing logic
"""

from typing import Tuple, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config import get_settings
from models import ModelType


class ModelRouter:
    """Intelligent model routing based on query complexity"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cheap_model = None
        self.expensive_model = None
        self.classifier = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Initialize models only when needed"""
        if not self._initialized:
            self.cheap_model = ChatGroq(model=self.settings.cheap_model, temperature=0)
            self.expensive_model = ChatGroq(model=self.settings.expensive_model, temperature=0)
            self.classifier = ChatGroq(model=self.settings.classifier_model, temperature=0)
            self._initialized = True
        
        self.classification_prompt = ChatPromptTemplate.from_template(
            """Classify this query's complexity as 'simple' or 'complex'.

Simple: Basic facts, short answers, simple calculations, definitions
Complex: Analysis, reasoning, creative tasks, multi-step problems, comparisons

Query: {query}

Respond with only: simple or complex"""
        )
    
    def classify_complexity(self, query: str) -> str:
        """Classify query complexity"""
        self._ensure_initialized()
        try:
            response = self.classifier.invoke(self.classification_prompt.format(query=query))
            result = response.content.strip().lower()
            return result if result in ["simple", "complex"] else "simple"
        except Exception:
            return "simple"  # Default to simple on error
    
    def get_model(self, complexity: str) -> ChatGroq:
        """Get appropriate model for complexity"""
        self._ensure_initialized()
        if complexity == "simple":
            return self.cheap_model
        else:
            return self.expensive_model
    
    def invoke(self, query: str, specified_model: Optional[ModelType] = None) -> Tuple[str, str]:
        """Process query with intelligent routing"""
        self._ensure_initialized()
        if specified_model:
            # Use specified model
            if specified_model == ModelType.CHEAP:
                model = self.cheap_model
                model_name = self.settings.cheap_model
            else:
                model = self.expensive_model
                model_name = self.settings.expensive_model
        else:
            # Use intelligent routing
            complexity = self.classify_complexity(query)
            model = self.get_model(complexity)
            model_name = self.settings.cheap_model if complexity == "simple" else self.settings.expensive_model
        
        try:
            response = model.invoke(query)
            return response.content, model_name
        except Exception as e:
            # Fallback to simple model on error
            try:
                response = self.cheap_model.invoke(query)
                return response.content, self.settings.cheap_model
            except Exception:
                raise e


class AIAgent:
    """Main AI agent with error handling and fallbacks"""
    
    def __init__(self):
        self.router = ModelRouter()
        self.is_initialized = False
    
    def initialize(self):
        """Initialize AI components"""
        if not self.is_initialized:
            # Test model connections
            try:
                self.router._ensure_initialized()
                self.router.classifier.invoke("test")
                self.is_initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize AI agent: {e}")
    
    def process_query(self, query: str, model: Optional[ModelType] = None) -> Tuple[str, str]:
        """Process a query and return response with model used"""
        if not self.is_initialized:
            self.initialize()
        
        return self.router.invoke(query, model)
    
    def health_check(self) -> dict:
        """Check AI agent health"""
        try:
            if not self.is_initialized:
                return {"status": "not_initialized", "details": "AI components not loaded"}
            
            # Test with simple query
            response, model = self.router.invoke("test")
            return {
                "status": "healthy",
                "model_used": model,
                "test_response": response[:50] + "..." if len(response) > 50 else response
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global agent instance
agent = AIAgent()


def get_agent() -> AIAgent:
    """Get global agent instance"""
    return agent


if __name__ == "__main__":
    # Test agent
    print("🤖 Testing AI agent...")
    
    try:
        agent.initialize()
        print("✅ Agent initialized successfully")
        
        # Test simple query
        response, model = agent.process_query("What is 2 + 2?")
        print(f"✅ Simple query: {response[:30]}... (model: {model})")
        
        # Test complex query
        response, model = agent.process_query("Explain the economic impact of AI")
        print(f"✅ Complex query: {response[:30]}... (model: {model})")
        
        # Test health check
        health = agent.health_check()
        print(f"✅ Health check: {health['status']}")
        
        print("🎉 AI agent working!")
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
