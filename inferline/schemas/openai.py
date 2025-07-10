from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime


class Pricing(BaseModel):
    prompt: str = Field("0", description="pricing per 1 token in USD")
    completion: str = Field("0", description="pricing per 1 token in USD")
    image: str = Field("0", description="pricing per 1 image")
    request: str = Field("0", description="pricing per 1 request")
    input_cache_reads: str = Field("0", description="pricing per 1 token")
    input_cache_writes: str = Field("0", description="pricing per 1 token")


class Model(BaseModel):
    id: str = Field(..., description="Model ID")
    object: str = Field(..., description="Object type")
    created: int = Field(..., description="Timestamp of model creation")

    input_modalities: List[str] = Field(["text"], description="Input modalities")
    output_modalities: List[str] = Field(["text"], description="Output modalities")
    owned_by: str = Field(..., description="Owner of the model")
    pricing: Pricing = Field(Pricing(), description="Pricing information")
    description: Optional[str] = Field(None, description="Description of the model's capabilities")
    icon_url: Optional[str] = Field(None, description="URL to the model's icon image")
    instructions_url: Optional[str] = Field(None, description="URL to the model's usage instructions")
    input_price: Optional[float] = Field(None, description="Price per input token in microdollars")
    output_price: Optional[float] = Field(None, description="Price per output token in microdollars")
    context_length: Optional[int] = Field(None, description="Maximum context length in tokens")
    max_output_length: Optional[int] = Field(None, description="Maximum output length in tokens")
    parameters: Optional[str] = Field(None, description="Number of parameters")
    quantization: Optional[str] = Field(None, description="Quantization type")
    provider_name: Optional[str] = Field(None, description="Name of the provider")
    supported_sampling_parameters: Optional[List[str]] = Field(
        ["temperature", "top_p", "top_k", "repetition_penalty", "frequency_penalty", "presence_penalty", "stop",
         "seed"], description="List of supported sampling parameters")
    supported_features: Optional[List[str]] = Field([], description="List of supported features")


class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[Model]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field("llama4:maverick", description="The model to use for the chat completion")
    messages: List[ChatMessage] = Field(..., description="The messages to generate chat completions for")
    temperature: Optional[float] = Field(1.0, description="What sampling temperature to use")
    max_tokens: Optional[int] = Field(100, description="The maximum number of tokens to generate")
    stream: Optional[bool] = Field(False, description="If true, partial message deltas will be sent")
    top_p: Optional[float] = Field(1.0, description="Alternative to sampling with temperature")
    top_k: Optional[int] = Field(None, description="Top-k sampling value (range: [1, Infinity)).")
    n: Optional[int] = Field(1, description="How many chat completion choices to generate")
    stop: Optional[List[str]] = Field(None, description="Sequences where the API will stop generating further tokens")
    presence_penalty: Optional[float] = Field(0.0,
                                              description="Positive values penalize new tokens based on their existing frequency")
    frequency_penalty: Optional[float] = Field(0.0,
                                               description="Positive values penalize new tokens based on their existing frequency")
    repetition_penalty: Optional[float] = Field(None, description="Repetition penalty")
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user")
    logprobs: Optional[int] = Field(None, description="Number of log probabilities to return per output token.")
    seed: Optional[int] = Field(None, description="Seed for deterministic outputs.")
    min_p: Optional[float] = Field(0.0,
                                   description="Float that represents the minimum probability for a token to be considered, relative to the probability of the most likely token.")
    logit_bias: Optional[dict[int, float]] = Field(None,
                                                   description="If provided, the engine will construct a logits processor that applies these logit biases")
    stream_options: Optional[dict[str, str]] = Field(None, description="Stream options")

    class Config:
        extra = "allow"


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


class CompletionRequest(BaseModel):
    model: str = Field("llama4:maverick", description="The model to use for the completion")
    prompt: str = Field(..., description="The prompt to generate completions for")
    max_tokens: Optional[int] = Field(100, description="The maximum number of tokens to generate")
    temperature: Optional[float] = Field(1.0, description="What sampling temperature to use")
    top_p: Optional[float] = Field(1.0, description="Alternative to sampling with temperature")
    top_k: Optional[int] = Field(None, description="Top-k sampling value (range: [1, Infinity)).")
    n: Optional[int] = Field(1, description="How many completions to generate")
    stream: Optional[bool] = Field(False, description="If true, partial message deltas will be sent")
    # logprobs: Optional[bool] = Field(False, description="Include the log probabilities on the logprobs most likely tokens")
    echo: Optional[bool] = Field(False, description="Echo back the prompt in addition to the completion")
    stop: Optional[List[str]] = Field(None, description="Sequences where the API will stop generating further tokens")
    presence_penalty: Optional[float] = Field(0.0,
                                              description="Positive values penalize new tokens based on their existing frequency")
    frequency_penalty: Optional[float] = Field(0.0,
                                               description="Positive values penalize new tokens based on their existing frequency")
    best_of: Optional[int] = Field(1,
                                   description="Generates best_of completions server-side and returns the \"best\" (the one with the highest log probability per token)")
    repetition_penalty: Optional[float] = Field(None, description="Repetition penalty")
    # logit_bias: Optional[dict] = Field(None, description="Modify the likelihood of specified tokens appearing in the completion")
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user")
    logprobs: Optional[int] = Field(None, description="Number of log probabilities to return per output token.")
    seed: Optional[int] = Field(None, description="Seed for deterministic outputs.")
    min_p: Optional[float] = Field(0.0,
                                   description="Float that represents the minimum probability for a token to be considered, relative to the probability of the most likely token.")
    logit_bias: Optional[dict[int, float]] = Field(None,
                                                   description="If provided, the engine will construct a logits processor that applies these logit biases")
    stream_options: Optional[dict[str, Any]] = Field(None, description="Stream options")
    ignore_eos: Optional[bool] = Field(False, description="If true, the end of string token will be ignored")

    class Config:
        extra = "allow"


class CompletionResponseChoice(BaseModel):
    text: str
    index: int
    logprobs: Optional[dict]
    finish_reason: str

    class Config:
        extra = "allow"


class CompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"cmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    object: str = "text.completion"
    created: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    model: str
    choices: List[CompletionResponseChoice]
    usage: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"
