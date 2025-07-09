# InferLine

InferLine is an innovative LLM router designed to maximize utilization of inference infrastructure.
Unlike traditional routers that push requests, InferLine operates like a computational conveyor belt,
enabling LLM providers to pull inference tasks when ready.

## Pull-based Architecture Advantage

This pull-based architecture offers significant benefits:

- **Natural Backpressure**: Providers only pull tasks they can handle, preventing overload.
- **Simplified Scaling**: New providers can join and immediately pull work without complex router configuration.
- **Efficient Resource Use**: Tasks are distributed based on real-time provider capacity, maximizing throughput.

## How It Works

Imagine LLM inference requests moving along a digital conveyor belt. Instead of the router pushing requests,
your LLM providers (workers) act like assembly line operators, reaching out to pull the next available task when they have capacity.
This ensures optimal workflow and resource utilization.
