"""
Metrics collection utilities for LLM inference benchmark.
"""

import time
import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Optional
from dataclasses import field


@dataclass
class RequestMetrics:
    """Metrics collected for a single request."""
    ttft: float              # Time to first token (seconds)
    latency: float           # Total request time (seconds)
    tokens_generated: int    # Number of tokens in response
    success: bool            # Whether request completed successfully
    error: Optional[str]     # Error message if failed


async def send_single_request(
    session: aiohttp.ClientSession,
    endpoint: str,
    model: str,
    prompt: str,
    generation_config: dict
) -> RequestMetrics:
    """
    Send a single request and measure TTFT, latency, and tokens.

    Uses streaming to accurately measure time-to-first-token.
    """
    # Build the request payload (OpenAI-compatible format)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,  # Enable streaming to measure TTFT
        **generation_config
    }

    start_time = time.perf_counter()
    first_token_time = None
    tokens_generated = 0

    try:
        async with session.post(endpoint, json=payload) as response:
            # Check for HTTP errors
            if response.status != 200:
                error_text = await response.text()
                return RequestMetrics(
                    ttft=0, latency=0, tokens_generated=0,
                    success=False, error=f"HTTP {response.status}: {error_text}"
                )

            # Read streaming response line by line
            async for line in response.content:
                line = line.decode("utf-8").strip()

                # Skip empty lines and SSE prefixes
                if not line or line.startswith(":"):
                    continue

                # Parse SSE data format: "data: {...}"
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix

                    # End of stream marker
                    if data == "[DONE]":
                        break

                    # Record first token time
                    if first_token_time is None:
                        first_token_time = time.perf_counter()

                    tokens_generated += 1

        end_time = time.perf_counter()

        # Calculate metrics
        ttft = (first_token_time - start_time) if first_token_time else 0
        latency = end_time - start_time

        return RequestMetrics(
            ttft=ttft,
            latency=latency,
            tokens_generated=tokens_generated,
            success=True,
            error=None
        )

    except Exception as e:
        return RequestMetrics(
            ttft=0, latency=0, tokens_generated=0,
            success=False, error=str(e)
        )


async def run_concurrent_requests(
    endpoint: str,
    model: str,
    prompts: list[str],
    generation_config: dict,
    concurrency: int,
    num_requests: int
) -> list[RequestMetrics]:
    """
    Run multiple requests at a specified concurrency level.

    Args:
        endpoint: API endpoint URL
        model: Model name
        prompts: List of prompts to randomly select from
        generation_config: Generation parameters
        concurrency: Number of simultaneous requests
        num_requests: Total number of requests to send

    Returns:
        List of RequestMetrics for all completed requests
    """
    import random

    all_metrics = []

    # Create a session with connection pooling
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:

        # Process requests in batches of 'concurrency' size
        for batch_start in range(0, num_requests, concurrency):
            batch_size = min(concurrency, num_requests - batch_start)

            # Create concurrent tasks for this batch
            tasks = []
            for _ in range(batch_size):
                prompt = random.choice(prompts)
                task = send_single_request(
                    session=session,
                    endpoint=endpoint,
                    model=model,
                    prompt=prompt,
                    generation_config=generation_config
                )
                tasks.append(task)

            # Run all tasks in this batch concurrently
            batch_metrics = await asyncio.gather(*tasks)
            all_metrics.extend(batch_metrics)

    return all_metrics


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a benchmark run."""
    concurrency: int
    avg_ttft: float           # Average time to first token (seconds)
    avg_latency: float        # Average total latency (seconds)
    throughput: float         # Requests per second
    total_tokens: int         # Total tokens generated
    token_throughput: float   # Tokens per second
    success_rate: float       # Percentage of successful requests
    num_requests: int         # Total requests attempted


def calculate_aggregated_metrics(
    metrics_list: list[RequestMetrics],
    concurrency: int,
    total_duration: float
) -> AggregatedMetrics:
    """
    Calculate aggregated metrics from a list of request metrics.

    Args:
        metrics_list: List of individual request metrics
        concurrency: Concurrency level used
        total_duration: Total time taken for all requests (seconds)

    Returns:
        AggregatedMetrics with averages and throughput
    """
    # Filter successful requests for averaging
    successful = [m for m in metrics_list if m.success]

    if not successful:
        return AggregatedMetrics(
            concurrency=concurrency,
            avg_ttft=0,
            avg_latency=0,
            throughput=0,
            total_tokens=0,
            token_throughput=0,
            success_rate=0,
            num_requests=len(metrics_list)
        )

    # Calculate averages
    avg_ttft = sum(m.ttft for m in successful) / len(successful)
    avg_latency = sum(m.latency for m in successful) / len(successful)
    total_tokens = sum(m.tokens_generated for m in successful)

    # Calculate throughput
    throughput = len(successful) / total_duration
    token_throughput = total_tokens / total_duration

    # Calculate success rate
    success_rate = len(successful) / len(metrics_list) * 100

    return AggregatedMetrics(
        concurrency=concurrency,
        avg_ttft=avg_ttft,
        avg_latency=avg_latency,
        throughput=throughput,
        total_tokens=total_tokens,
        token_throughput=token_throughput,
        success_rate=success_rate,
        num_requests=len(metrics_list)
    )
