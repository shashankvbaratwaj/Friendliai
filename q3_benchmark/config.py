"""
Configuration for LLM inference benchmark.

This file contains all configurable parameters for the benchmark.
Modify the endpoint URLs to match your deployment.
"""

# Engine endpoints (both should expose OpenAI-compatible API)
VLLM_ENDPOINT = "http://localhost:8000/v1/chat/completions"
FRIENDLI_ENDPOINT = "http://localhost:8001/v1/chat/completions"

# Model name (must be the same model deployed on both engines)
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"

# Benchmark parameters
CONCURRENCY_LEVELS = [1, 2, 4, 8, 16, 32]  # Number of concurrent requests
REQUESTS_PER_LEVEL = 20                      # Requests to send at each concurrency level
WARMUP_REQUESTS = 5                          # Requests to discard (cold start)

# Generation parameters (keep consistent across both engines)
GENERATION_CONFIG = {
    "max_tokens": 256,
    "temperature": 0.7,
    "top_p": 0.9,
}

# Test prompts (varied lengths and complexities for realistic benchmark)
TEST_PROMPTS = [
    "Explain the concept of recursion in programming.",
    "What are the main differences between Python and JavaScript?",
    "Write a short poem about the ocean.",
    "Summarize the key principles of machine learning.",
    "What is the capital of France and what is it known for?",
    "Explain how a neural network learns.",
    "Describe the water cycle in simple terms.",
    "What are the benefits of exercise?",
    "How does photosynthesis work?",
    "Explain the theory of relativity briefly.",
]
