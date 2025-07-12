import time
import asyncio
from typing import List, Union, Dict
from fastapi import FastAPI, HTTPException
import uvicorn
from datetime import datetime

from inferline.schemas.openai import (
    Model,
    ModelsResponse,
    CompletionRequest,
    CompletionResponse,
    CompletionResponseChoice,
    Pricing,
    QueuedInferenceRequest,
    InferenceResult,
    InferenceStatus,
    QueueStats,
    InferenceRequestResponse
)


app = FastAPI(
    title="InferLine API",
    description="OpenAI-compatible API server for LLM inference routing",
    version="0.1.0"
)

# In-memory storage for queue and results
inference_queue: Dict[str, QueuedInferenceRequest] = {}
results_storage: Dict[str, Union[CompletionResponse, dict]] = {}


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
    """Create a text completion (synchronous with queue processing)"""
    # Validate model exists
    model_ids = [model.id for model in AVAILABLE_MODELS]
    if request.model not in model_ids:
        raise HTTPException(status_code=404, detail=f"Model '{request.model}' not found")
    
    # Create queued request
    queued_request = QueuedInferenceRequest(
        request_type="completion",
        request_data=request.dict()
    )
    
    # Store in queue
    inference_queue[queued_request.request_id] = queued_request
    
    # Wait for completion with timeout
    timeout = 300  # 5 minutes timeout
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        queued_request = inference_queue[queued_request.request_id]
        
        if queued_request.status == InferenceStatus.COMPLETED:
            if queued_request.request_id in results_storage:
                result = results_storage[queued_request.request_id]
                del inference_queue[queued_request.request_id]
                del results_storage[queued_request.request_id]
                return result
            else:
                raise HTTPException(status_code=500, detail="Result not found")
        elif queued_request.status == InferenceStatus.FAILED:
            error_msg = queued_request.error_message or "Unknown error"
            del inference_queue[queued_request.request_id]
            raise HTTPException(status_code=500, detail=f"Processing failed: {error_msg}")
        
        # Wait briefly before checking again
        await asyncio.sleep(0.1)
    
    # Timeout occurred
    raise HTTPException(status_code=408, detail="Request timeout - processing took too long")


@app.get("/queue/next", response_model=QueuedInferenceRequest)
async def get_next_inference_request():
    """Get the next pending inference request from the queue"""
    # Find the oldest pending request
    pending_requests = [
        req for req in inference_queue.values() 
        if req.status == InferenceStatus.PENDING
    ]
    
    if not pending_requests:
        raise HTTPException(status_code=404, detail="No pending requests in queue")
    
    # Get the oldest request
    oldest_request = min(pending_requests, key=lambda x: x.created_at)
    
    # Mark as processing
    oldest_request.status = InferenceStatus.PROCESSING
    oldest_request.started_at = datetime.now()
    
    return oldest_request


@app.post("/queue/result")
async def submit_inference_result(result: InferenceResult):
    """Submit the result of an inference request"""
    request_id = result.request_id
    
    if request_id not in inference_queue:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    queued_request = inference_queue[request_id]
    
    if result.error_message:
        queued_request.status = InferenceStatus.FAILED
        queued_request.error_message = result.error_message
    else:
        queued_request.status = InferenceStatus.COMPLETED
        # Store the result
        results_storage[request_id] = result.result_data
    
    queued_request.completed_at = datetime.now()
    
    return {"message": "Result submitted successfully", "request_id": request_id}


@app.get("/completions/{request_id}")
async def get_completion_result(request_id: str):
    """Get the result of a completion request"""
    if request_id not in inference_queue:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    queued_request = inference_queue[request_id]
    
    if queued_request.status == InferenceStatus.PENDING:
        return {"status": "pending", "message": "Request is still in queue"}
    elif queued_request.status == InferenceStatus.PROCESSING:
        return {"status": "processing", "message": "Request is being processed"}
    elif queued_request.status == InferenceStatus.FAILED:
        return {"status": "failed", "message": queued_request.error_message}
    elif queued_request.status == InferenceStatus.COMPLETED:
        if request_id in results_storage:
            return results_storage[request_id]
        else:
            raise HTTPException(status_code=500, detail="Result not found")
    else:
        raise HTTPException(status_code=500, detail="Unknown status")


@app.get("/queue/stats", response_model=QueueStats)
async def get_queue_stats():
    """Get queue statistics"""
    stats = QueueStats()
    
    for request in inference_queue.values():
        if request.status == InferenceStatus.PENDING:
            stats.pending_requests += 1
        elif request.status == InferenceStatus.PROCESSING:
            stats.processing_requests += 1
        elif request.status == InferenceStatus.COMPLETED:
            stats.completed_requests += 1
        elif request.status == InferenceStatus.FAILED:
            stats.failed_requests += 1
    
    return stats


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": int(time.time())}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
