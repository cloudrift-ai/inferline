# InferLine

InferLine is an innovative LLM router designed to maximize utilization of inference infrastructure.
Unlike traditional routers that push requests, InferLine operates like a computational conveyor belt,
enabling LLM providers to pull inference tasks when ready.

## How It Works

1. **User sends request** to InferLine API (OpenAI-compatible)
2. **InferLine Server** queues the request and waits for available providers
3. **OpenAI Provider** polls the queue for tasks it can handle
4. **LLM Container** processes the request and returns results
5. **Provider** submits results back to InferLine
6. **User receives** the completed response

```
┌─────────────────┐    ┌────────────────────┐    ┌─────────────────────┐
│   User Request  │───▶│  InferLine Server  │◀──▶│    Request Queue    │
│                 │    │   (API Endpoint)   │    │   (Task Storage)    │
└─────────────────┘    └────────────────────┘    └─────────────────────┘
                                 ▲                        ▲
                                 │                        │
                                 ▼                        │
┌─────────────────────┐    ┌───────────────────┐          │
│    LLM Container    │◀──▶│  OpenAI Provider  │──────────┘
│ (TinyLlama, Llama3) │    │   (Connector)     │
└─────────────────────┘    └───────────────────┘
```

## Pull-based Architecture Benefits

- **Natural Backpressure**: Providers only pull tasks they can handle, preventing overload
- **Simplified Scaling**: New providers can join and immediately pull work without complex router configuration  
- **Efficient Resource Use**: Tasks are distributed based on real-time provider capacity, maximizing throughput

## Quick Start with TinyLlama

Run a local TinyLlama model connected to the InferLine server at https://inferline.cloudrift.ai:

```bash
PROVIDER_ID=my-llama-server docker compose -f docker/docker-compose-tinyllama.yml up -d
```

This will:
1. **Download and run TinyLlama** (1.1B parameter model, ~640MB)
2. **Connect to InferLine** server automatically
3. **Register as available** for inference requests

The model will appear in the [InferLine dashboard](https://inferline.cloudrift.ai).

### Test the Connection

```bash
# Check available models
curl https://inferline.cloudrift.ai/api/models

# Send a completion request
curl -X POST "https://inferline.cloudrift.ai/api/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", "prompt": "Hello, how are you?"}'
```

InferLine provides an OpenAI-compatible API. You can use any OpenAI client library by changing the base URL to `https://inferline.cloudrift.ai/api`.

### Stop the Service

```bash
docker compose -f docker/docker-compose-tinyllama.yml down
```

## Run Complete Local Demo

To run the full InferLine stack locally (server, frontend, and TinyLlama):

```bash
# Start the complete local demo
docker compose -f docker/docker-compose-local-demo.yml up -d

# View logs
docker compose -f docker/docker-compose-local-demo.yml logs -f
```

This runs:
- **InferLine Server** on http://localhost:8000
- **Frontend Dashboard** on http://localhost:5000
- **TinyLlama Model** on http://localhost:8001
- **OpenAI Provider** connecting them together

### Test Local Setup

```bash
# Check the frontend dashboard
open http://localhost:5000

# Test API directly
curl -X POST "http://localhost:8000/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", "prompt": "Hello, how are you?"}'

# Check server health
curl http://localhost:8000/health
```

### Stop Local Demo

```bash
docker compose -f docker/docker-compose-local-demo.yml down
```
