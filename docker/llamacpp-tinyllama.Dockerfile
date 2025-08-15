FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential curl

RUN pip install --upgrade pip && \
    pip install llama-cpp-python[server] --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

WORKDIR /models

RUN curl -L -o /models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

EXPOSE 8000

CMD ["python", "-m", "llama_cpp.server", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--model", "/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", \
     "--n_ctx", "2048", \
     "--n_threads", "4"]