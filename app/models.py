"""
Pydantic models for Production AI API
Request/response models and data validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """Available AI models"""
    CHEAP = "llama-3.1-8b-instant"
    EXPENSIVE = "llama-3.3-70b-versatile"
    CLASSIFIER = "llama-3.1-8b-instant"


class RequestStatus(str, Enum):
    """Request status types"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=10000, description="Chat message")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    model: Optional[ModelType] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(0.0, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Maximum tokens to generate")
    
    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        """Validate message content"""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="AI response")
    model_used: str = Field(..., description="Model that generated the response")
    cached: bool = Field(default=False, description="Whether response was cached")
    tokens_used: int = Field(..., ge=0, description="Total tokens used")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    status: RequestStatus = Field(RequestStatus.COMPLETED, description="Request status")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., ge=0, description="Service uptime in seconds")
    ai_initialized: bool = Field(default=False, description="Whether AI components are initialized")
    environment: str = Field(..., description="Running environment")


class MetricsResponse(BaseModel):
    """Metrics response model"""
    requests_total: int = Field(..., ge=0, description="Total requests processed")
    cache_hits: int = Field(..., ge=0, description="Number of cache hits")
    errors_total: int = Field(..., ge=0, description="Total errors encountered")
    total_tokens: int = Field(..., ge=0, description="Total tokens processed")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate")
    average_processing_time_ms: float = Field(..., ge=0, description="Average processing time")


class SecurityCheck(BaseModel):
    """Security check result model"""
    is_safe: bool = Field(..., description="Whether input is safe")
    risk_level: str = Field(..., description="Risk level assessment")
    blocked_patterns: List[str] = Field(default_factory=list, description="Blocked patterns found")
    sanitized_input: Optional[str] = Field(None, description="Sanitized input")


class CacheEntry(BaseModel):
    """Cache entry model"""
    key: str = Field(..., description="Cache key")
    value: str = Field(..., description="Cached value")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    access_count: int = Field(default=0, ge=0, description="Number of times accessed")
    size_bytes: int = Field(..., ge=0, description="Size in bytes")


class ModelMetrics(BaseModel):
    """Model performance metrics"""
    model_name: str = Field(..., description="Model name")
    requests_count: int = Field(..., ge=0, description="Number of requests")
    total_tokens: int = Field(..., ge=0, description="Total tokens processed")
    average_latency_ms: float = Field(..., ge=0, description="Average latency")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")


class UserInfo(BaseModel):
    """User information model"""
    user_id: str = Field(..., description="User identifier")
    email: Optional[str] = Field(None, description="User email")
    created_at: datetime = Field(..., description="Account creation date")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")
    request_count: int = Field(default=0, ge=0, description="Total requests made")
    is_active: bool = Field(default=True, description="Account status")


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    request_count: int = Field(default=0, ge=0, description="Requests in session")
    is_active: bool = Field(default=True, description="Session status")


class APIInfo(BaseModel):
    """API information model"""
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")
    models: List[str] = Field(..., description="Available models")
    features: List[str] = Field(..., description="Available features")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")


class ValidationError(BaseModel):
    """Validation error model"""
    field: str = Field(..., description="Field with validation error")
    message: str = Field(..., description="Error message")
    value: Any = Field(..., description="Invalid value")


class BulkRequest(BaseModel):
    """Bulk request model for multiple chat requests"""
    requests: List[ChatRequest] = Field(..., min_items=1, max_items=10, description="Chat requests")
    parallel: bool = Field(default=True, description="Process requests in parallel")


class BulkResponse(BaseModel):
    """Bulk response model"""
    responses: List[ChatResponse] = Field(..., description="Chat responses")
    total_processing_time_ms: float = Field(..., ge=0, description="Total processing time")
    successful_requests: int = Field(..., ge=0, description="Number of successful requests")
    failed_requests: int = Field(..., ge=0, description="Number of failed requests")


# Model validation helpers
def validate_chat_request(request: ChatRequest) -> List[ValidationError]:
    """Validate chat request and return list of errors"""
    errors = []
    
    if len(request.message) > 10000:
        errors.append(ValidationError(
            field="message",
            message="Message too long (max 10000 characters)",
            value=len(request.message)
        ))
    
    if request.temperature is not None and (request.temperature < 0 or request.temperature > 2):
        errors.append(ValidationError(
            field="temperature",
            message="Temperature must be between 0 and 2",
            value=request.temperature
        ))
    
    if request.max_tokens is not None and (request.max_tokens < 1 or request.max_tokens > 4000):
        errors.append(ValidationError(
            field="max_tokens",
            message="Max tokens must be between 1 and 4000",
            value=request.max_tokens
        ))
    
    return errors


# Model creation helpers
def create_error_response(error_message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict] = None) -> ErrorResponse:
    """Create standardized error response"""
    return ErrorResponse(
        error=error_message,
        error_code=error_code,
        details=details,
        timestamp=datetime.utcnow(),
        request_id=None
    )


def create_chat_response(response: str, model: str, tokens: int, processing_time: float, cached: bool = False) -> ChatResponse:
    """Create standardized chat response"""
    return ChatResponse(
        response=response,
        model_used=model,
        cached=cached,
        tokens_used=tokens,
        processing_time_ms=processing_time,
        status=RequestStatus.CACHED if cached else RequestStatus.COMPLETED
    )


if __name__ == "__main__":
    # Test model creation
    print("🔧 Testing Pydantic models...")
    
    # Test chat request
    request = ChatRequest(message="Hello, how are you?")
    print(f"✅ ChatRequest created: {request.message[:20]}...")
    
    # Test chat response
    response = create_chat_response(
        response="I'm doing well, thank you!",
        model="llama-3.1-8b-instant",
        tokens=25,
        processing_time=1234.56
    )
    print(f"✅ ChatResponse created: {response.response[:20]}...")
    
    # Test error response
    error = create_error_response("Test error", "TEST_ERROR")
    print(f"✅ ErrorResponse created: {error.error}")
    
    print("🎉 All models working correctly!")
