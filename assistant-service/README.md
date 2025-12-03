# Cartographer Assistant Service

AI-powered assistant microservice for the Cartographer network mapping application.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic (Claude), Google Gemini, and Ollama (local models)
- **Network Context**: Automatically fetches network topology from the metrics service
- **Streaming Responses**: Real-time response streaming via Server-Sent Events (SSE)
- **Conversation History**: Maintains context across messages

## Configuration

Set the following environment variables:

### Required (at least one provider)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | Google Gemini API key |
| `OLLAMA_HOST` or `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `METRICS_SERVICE_URL` | `http://localhost:8003` | Metrics service URL |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## API Endpoints

### Chat

- `POST /api/assistant/chat` - Non-streaming chat
- `POST /api/assistant/chat/stream` - Streaming chat (SSE)

### Configuration

- `GET /api/assistant/config` - Get provider configuration
- `GET /api/assistant/providers` - List all providers
- `GET /api/assistant/models/{provider}` - List models for a provider

### Context

- `GET /api/assistant/context` - Get network context summary
- `POST /api/assistant/context/refresh` - Refresh cached context

## Example Request

```bash
curl -X POST http://localhost:8004/api/assistant/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What devices are unhealthy on my network?",
    "provider": "openai",
    "include_network_context": true
  }'
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

## Docker

```bash
# Build
docker build -t cartographer-assistant .

# Run
docker run -p 8004:8004 \
  -e OPENAI_API_KEY=your-key \
  -e METRICS_SERVICE_URL=http://localhost:8003 \
  cartographer-assistant
```
