# Production AI API

Enterprise-ready AI API combining all production patterns: security, testing, cost optimization, and monitoring.

## Features

### 🛡️ Security
- Input sanitization and validation
- Prompt injection detection
- Token budget enforcement
- CORS protection

### 💰 Cost Optimization
- Intelligent model routing (simple vs complex queries)
- Response caching with TTL
- Token usage tracking
- Performance metrics

### 📊 Monitoring
- Structured logging with structlog
- Prometheus metrics
- LangSmith tracing
- Request latency tracking

### 🚀 Performance
- FastAPI async framework
- Response caching
- Model selection optimization
- Health check endpoints

## Quick Start

1. **Install dependencies**
```bash
uv sync
```

2. **Configure environment**
```bash
# Copy .env file and update with your API keys
cp .env.example .env
```

3. **Run the API**
```bash
uv run python main.py
```

4. **Test the API**
```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2 + 2?"}'

# Metrics
curl http://localhost:8000/metrics
```

## API Endpoints

### GET `/health`
Health check endpoint with system status.

### POST `/chat`
Main chat endpoint with production patterns.

**Request:**
```json
{
  "message": "What is the capital of France?",
  "user_id": "optional-user-id",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "The capital of France is Paris.",
  "model_used": "llama-3.1-8b-instant",
  "cached": false,
  "tokens_used": 15,
  "processing_time_ms": 1234.56
}
```

### GET `/metrics`
Prometheus metrics endpoint for monitoring.

## Architecture

### Production Patterns Implemented

1. **Security Layer**
   - Input sanitization removes dangerous patterns
   - Suspicious content detection
   - Token budget enforcement

2. **Cost Optimization Layer**
   - Model routing based on query complexity
   - Response caching with TTL
   - Token usage tracking

3. **Monitoring Layer**
   - Structured logging
   - Prometheus metrics
   - LangSmith tracing

4. **API Layer**
   - FastAPI async framework
   - CORS middleware
   - Error handling

### Model Routing

- **Simple queries** → `llama-3.1-8b-instant` (faster, cheaper)
- **Complex queries** → `llama-3.3-70b-versatile` (more capable)

## Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here

# Optional
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=production-api
SECRET_KEY=your_secret_key_here
CACHE_TTL=3600
MAX_TOKENS_PER_REQUEST=4000
LOG_LEVEL=INFO
```

## Monitoring

### Metrics Available
- `api_requests_total` - Total API requests
- `api_request_duration_seconds` - Request latency
- `token_usage_total` - Token usage by type
- `cache_hits_total` - Cache hit count

### Structured Logging
All requests are logged with:
- Request details
- Model used
- Token counts
- Processing time
- Cache status

### LangSmith Tracing
All AI operations are traced in LangSmith for:
- Performance monitoring
- Error debugging
- Usage analytics

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
- Use HTTPS in production
- Configure proper CORS origins
- Set strong SECRET_KEY
- Monitor token usage and costs
- Set up log aggregation
- Configure alerting

## Development

### Running Tests
```bash
uv run pytest
```

### Code Quality
```bash
uv run black .
uv run ruff check .
```

## License

MIT License - see LICENSE file for details.