import asyncio
import logging
import time
from typing import Optional, Dict, List
import aiohttp
import os

from inferline.schemas.openai import (
    QueuedInferenceRequest,
    InferenceResult
)

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """Service that wraps OpenAI endpoint and processes inferline requests"""
    
    def __init__(
        self,
        openai_base_url: str = "http://localhost:8000",
        openai_api_key: Optional[str] = None,
        inferline_base_url: str = "http://localhost:8000",
        poll_interval: float = 1.0,
        model_refresh_interval: float = 60.0
    ):
        self.openai_base_url = openai_base_url.rstrip('/')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY', '')
        self.inferline_base_url = inferline_base_url.rstrip('/')
        self.poll_interval = poll_interval
        self.model_refresh_interval = model_refresh_interval
        
        self.available_models: List[str] = []
        self.last_model_refresh = 0
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        
    async def start(self):
        """Start the provider service"""
        self.session = aiohttp.ClientSession()
        self.running = True
        logger.info("OpenAI Provider started")
        
        # Start background tasks
        await asyncio.gather(
            self._model_refresh_loop(),
            self._request_processing_loop()
        )
    
    async def stop(self):
        """Stop the provider service"""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("OpenAI Provider stopped")
    
    async def _model_refresh_loop(self):
        """Periodically refresh available models from OpenAI endpoint"""
        while self.running:
            try:
                await self._refresh_models()
                await asyncio.sleep(self.model_refresh_interval)
            except Exception as e:
                logger.error(f"Error refreshing models: {e}")
                await asyncio.sleep(self.model_refresh_interval)
    
    async def _refresh_models(self):
        """Fetch available models from OpenAI endpoint"""
        try:
            headers = {}
            if self.openai_api_key:
                headers['Authorization'] = f'Bearer {self.openai_api_key}'
            
            async with self.session.get(
                f"{self.openai_base_url}/models",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Extract model IDs from OpenAI format
                    models = data.get('data', [])
                    self.available_models = [model['id'] for model in models]
                    self.last_model_refresh = time.time()
                    logger.info(f"Refreshed models: {self.available_models}")
                else:
                    logger.warning(f"Failed to fetch models: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error fetching models from OpenAI: {e}")
    
    async def _request_processing_loop(self):
        """Main loop to poll for and process inference requests"""
        while self.running:
            try:
                request = await self._get_next_request()
                if request:
                    await self._process_request(request)
                else:
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in request processing loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _get_next_request(self) -> Optional[QueuedInferenceRequest]:
        """Get the next pending request from inferline queue"""
        try:
            async with self.session.get(
                f"{self.inferline_base_url}/queue/next"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return QueuedInferenceRequest(**data)
                elif response.status == 204:
                    # No pending requests
                    return None
                else:
                    logger.warning(f"Failed to get next request: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting next request: {e}")
            return None
    
    async def _process_request(self, request: QueuedInferenceRequest):
        """Process an inference request by forwarding to OpenAI"""
        try:
            model = request.request_data.get('model')
            
            # Check if we can handle this model
            if model not in self.available_models:
                await self._submit_error_result(
                    request.request_id,
                    f"Model '{model}' not available on OpenAI endpoint"
                )
                return
            
            # Process based on request type
            if request.request_type == "completion":
                result = await self._process_completion_request(request)
            else:
                await self._submit_error_result(
                    request.request_id,
                    f"Unsupported request type: {request.request_type}"
                )
                return
            
            # Submit successful result
            await self._submit_result(request.request_id, result)
            
        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {e}")
            await self._submit_error_result(request.request_id, str(e))
    
    async def _process_completion_request(self, request: QueuedInferenceRequest) -> Dict:
        """Process a completion request by calling OpenAI"""
        headers = {
            'Content-Type': 'application/json'
        }
        if self.openai_api_key:
            headers['Authorization'] = f'Bearer {self.openai_api_key}'
        
        # Prepare request data for OpenAI
        openai_request = request.request_data.copy()
        
        async with self.session.post(
            f"{self.openai_base_url}/completions",
            json=openai_request,
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"OpenAI API error {response.status}: {error_text}")
    
    async def _submit_result(self, request_id: str, result_data: Dict):
        """Submit successful result back to inferline"""
        try:
            result = InferenceResult(
                request_id=request_id,
                result_data=result_data,
                usage=result_data.get('usage'),
                error_message=None
            )
            
            async with self.session.post(
                f"{self.inferline_base_url}/queue/result",
                json=result.dict()
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully submitted result for request {request_id}")
                else:
                    logger.error(f"Failed to submit result: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error submitting result for {request_id}: {e}")
    
    async def _submit_error_result(self, request_id: str, error_message: str):
        """Submit error result back to inferline"""
        try:
            result = InferenceResult(
                request_id=request_id,
                result_data={},
                usage=None,
                error_message=error_message
            )
            
            async with self.session.post(
                f"{self.inferline_base_url}/queue/result",
                json=result.dict()
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully submitted error for request {request_id}")
                else:
                    logger.error(f"Failed to submit error: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error submitting error for {request_id}: {e}")


async def main():
    """Main function to run the OpenAI provider service"""
    logging.basicConfig(level=logging.INFO)
    
    # Configuration from environment variables
    openai_base_url = os.getenv('OPENAI_BASE_URL', 'http://localhost:8000')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    inferline_base_url = os.getenv('INFERLINE_BASE_URL', 'http://localhost:8000')
    poll_interval = float(os.getenv('POLL_INTERVAL', '1.0'))
    model_refresh_interval = float(os.getenv('MODEL_REFRESH_INTERVAL', '60.0'))
    
    provider = OpenAIProvider(
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        inferline_base_url=inferline_base_url,
        poll_interval=poll_interval,
        model_refresh_interval=model_refresh_interval
    )
    
    try:
        await provider.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await provider.stop()


if __name__ == "__main__":
    asyncio.run(main())