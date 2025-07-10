import time
from typing import List, Union
from fastapi import FastAPI, HTTPException
import uvicorn

from inferline.schemas.openai import (
    Model,
    ModelsResponse,
    CompletionRequest,
    CompletionResponse,
    CompletionResponseChoice,
    Pricing
)


app = FastAPI(
    title="InferLine API",
    description="OpenAI-compatible API server for LLM inference routing",
    version="0.1.0"
)


# Mock models for demonstration
AVAILABLE_MODELS = [
    Model(
        id="gpt-3.5-turbo",
        object="model",
        created=int(time.time()),
        owned_by="openai",
        pricing=Pricing(),
        description="GPT-3.5 Turbo model",
        context_length=4096,
        max_output_length=4096
    ),
    Model(
        id="gpt-4",
        object="model",
        created=int(time.time()),
        owned_by="openai",
        pricing=Pricing(),
        description="GPT-4 model",
        context_length=8192,
        max_output_length=8192
    ),
    Model(
        id="claude-3-sonnet",
        object="model",
        created=int(time.time()),
        owned_by="anthropic",
        pricing=Pricing(),
        description="Claude 3 Sonnet model",
        context_length=200000,
        max_output_length=4096
    ),
    Model(
        id="llama-2-70b",
        object="model",
        created=int(time.time()),
        owned_by="meta",
        pricing=Pricing(),
        description="LLaMA 2 70B model",
        context_length=4096,
        max_output_length=4096
    ),
]


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List all available models"""
    return ModelsResponse(data=AVAILABLE_MODELS)


@app.post("/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """Create a text completion"""
    # Validate model exists
    model_ids = [model.id for model in AVAILABLE_MODELS]
    if request.model not in model_ids:
        raise HTTPException(status_code=404, detail=f"Model '{request.model}' not found")
    
    # Mock completion response
    prompt = request.prompt
    completion_text = f"This is a mock completion for prompt: '{prompt[:50]}...'"
    
    choices = [
        CompletionResponseChoice(
            text=completion_text,
            index=i,
            logprobs=None,
            finish_reason="stop"
        )
        for i in range(request.n or 1)
    ]
    
    # Mock usage statistics
    prompt_tokens = len(prompt.split())
    completion_tokens = len(completion_text.split())
    
    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }
    
    return CompletionResponse(
        model=request.model,
        choices=choices,
        usage=usage
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": int(time.time())}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
