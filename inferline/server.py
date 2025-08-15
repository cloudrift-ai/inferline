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
    QueuedInferenceRequest,
    InferenceResult,
    InferenceStatus,
    QueueStats,
    ProviderModelRegistration,
    ProviderRegistrationResponse,
    ProviderCapabilities,
    QueueRequestWithCapabilities
)


app = FastAPI(
    title="InferLine API",
    description="OpenAI-compatible API server for LLM inference routing",
    version="0.1.0"
)

# In-memory storage for queue and results
inference_queue: Dict[str, QueuedInferenceRequest] = {}
results_storage: Dict[str, Union[CompletionResponse, dict]] = {}

# Provider-registered models tracking (deprecated - kept for backward compatibility)
provider_models: Dict[str, Dict[str, Model]] = {}  # provider_id -> {model_id -> Model}

# Dynamic model tracking based on active requests
available_models: Dict[str, Model] = {}

# Active provider capabilities tracking
active_providers: Dict[str, ProviderCapabilities] = {}  # provider_id -> capabilities
provider_last_seen: Dict[str, float] = {}  # provider_id -> timestamp


def register_model_from_request(model_id: str):
    """Register a model as available when it's requested by a provider"""
    if model_id not in available_models:
        # Create a basic model entry for the requested model
        # In a real implementation, this could fetch model details from a registry
        available_models[model_id] = Model(
            id=model_id,
            object="model",
            created=int(time.time()),
            owned_by="dynamic",
            description=f"Dynamically registered model: {model_id}",
            context_length=4096,  # Default values - could be configured
            max_output_length=4096
        )

def cleanup_inactive_models():
    """Remove models that are no longer being used in active requests"""
    active_model_ids = set()
    
    # Collect model IDs from active requests
    for request in inference_queue.values():
        if request.status in [InferenceStatus.PENDING, InferenceStatus.PROCESSING]:
            if request.request_type == "completion":
                model_id = request.request_data.get("model")
                if model_id:
                    active_model_ids.add(model_id)
    
    # Keep only models that are in active use
    models_to_remove = [model_id for model_id in available_models.keys() if model_id not in active_model_ids]
    for model_id in models_to_remove:
        del available_models[model_id]


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List all available models from active providers"""
    all_models = {}
    
    # Clean up inactive providers (older than 5 minutes)
    current_time = time.time()
    inactive_providers = [
        provider_id for provider_id, last_seen in provider_last_seen.items()
        if current_time - last_seen > 300  # 5 minutes
    ]
    for provider_id in inactive_providers:
        active_providers.pop(provider_id, None)
        provider_last_seen.pop(provider_id, None)
    
    # Add models from active providers
    for provider_id, capabilities in active_providers.items():
        for model_id in capabilities.supported_models:
            if model_id not in all_models:
                # Create a basic model entry for each supported model
                all_models[model_id] = Model(
                    id=model_id,
                    object="model",
                    created=int(time.time()),
                    owned_by=provider_id,
                    description=f"Model served by provider: {provider_id}",
                    provider_name=provider_id,
                    context_length=4096,  # Default values
                    max_output_length=4096
                )
    
    # Add models from legacy registered providers (backward compatibility)
    for provider_id, models in provider_models.items():
        for model_id, model in models.items():
            if model_id not in all_models:
                all_models[model_id] = model
    
    # Also include dynamically registered models from requests
    for model_id, model in available_models.items():
        if model_id not in all_models:
            all_models[model_id] = model
    
    return ModelsResponse(data=list(all_models.values()))


@app.post("/providers/register", response_model=ProviderRegistrationResponse)
async def register_provider_models(registration: ProviderModelRegistration):
    """Register models available from a provider"""
    provider_id = registration.provider_id
    models = registration.models
    
    # Store provider models
    provider_models[provider_id] = {}
    for model in models:
        provider_models[provider_id][model.id] = model
    
    return ProviderRegistrationResponse(
        success=True,
        message=f"Successfully registered {len(models)} models for provider {provider_id}",
        registered_models=len(models)
    )


@app.post("/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """Create a text completion (synchronous with queue processing)"""
    # Register the requested model as available
    register_model_from_request(request.model)
    
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


@app.post("/queue/next", response_model=QueuedInferenceRequest)
async def get_next_inference_request(provider_info: QueueRequestWithCapabilities):
    """Get the next pending inference request that this provider can handle"""
    capabilities = provider_info.provider_capabilities
    provider_id = capabilities.provider_id
    
    # Update provider tracking
    active_providers[provider_id] = capabilities
    provider_last_seen[provider_id] = time.time()
    
    # Find pending requests that this provider can handle
    pending_requests = []
    for req in inference_queue.values():
        if req.status == InferenceStatus.PENDING:
            # Check if provider supports the requested model
            requested_model = req.request_data.get('model')
            request_type = req.request_type
            
            if (requested_model in capabilities.supported_models and 
                request_type in capabilities.request_types):
                pending_requests.append(req)
    
    if not pending_requests:
        raise HTTPException(status_code=204, detail="No pending requests for this provider")

    # Get the oldest request this provider can handle
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
