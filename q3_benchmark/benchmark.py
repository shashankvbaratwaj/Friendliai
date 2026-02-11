"""
LLM Inference Benchmark: vLLM vs Friendli Engine

This script benchmarks two inference engines and generates a comparison report.
"""

import asyncio
import time
from config import (
    VLLM_ENDPOINT,
    FRIENDLI_ENDPOINT,
    MODEL_NAME,
    CONCURRENCY_LEVELS,
    REQUESTS_PER_LEVEL,
    WARMUP_REQUESTS,
    GENERATION_CONFIG,
    TEST_PROMPTS,
)
from metrics import (
    run_concurrent_requests,
    calculate_aggregated_metrics,
    AggregatedMetrics,
)


async def benchmark_engine(
    name: str,
    endpoint: str,
    concurrency_levels: list[int],
    requests_per_level: int,
    warmup_requests: int,
) -> dict[int, AggregatedMetrics]:
    """
    Benchmark a single engine across multiple concurrency levels.

    Args:
        name: Engine name (for logging)
        endpoint: API endpoint URL
        concurrency_levels: List of concurrency levels to test
        requests_per_level: Number of requests at each level
        warmup_requests: Number of warmup requests to discard

    Returns:
        Dictionary mapping concurrency level to aggregated metrics
    """
    results = {}

    print(f"\n{'='*50}")
    print(f"Benchmarking: {name}")
    print(f"Endpoint: {endpoint}")
    print(f"{'='*50}")

    # Warmup phase
    print(f"\nWarmup: Sending {warmup_requests} requests...")
    await run_concurrent_requests(
        endpoint=endpoint,
        model=MODEL_NAME,
        prompts=TEST_PROMPTS,
        generation_config=GENERATION_CONFIG,
        concurrency=1,
        num_requests=warmup_requests,
    )
    print("Warmup complete.")

    # Benchmark each concurrency level
    for concurrency in concurrency_levels:
        print(f"\nTesting concurrency={concurrency}...")

        start_time = time.perf_counter()

        metrics_list = await run_concurrent_requests(
            endpoint=endpoint,
            model=MODEL_NAME,
            prompts=TEST_PROMPTS,
            generation_config=GENERATION_CONFIG,
            concurrency=concurrency,
            num_requests=requests_per_level,
        )

        total_duration = time.perf_counter() - start_time

        # Calculate aggregated metrics
        aggregated = calculate_aggregated_metrics(
            metrics_list=metrics_list,
            concurrency=concurrency,
            total_duration=total_duration,
        )

        results[concurrency] = aggregated

        # Print summary for this level
        print(f"  Avg TTFT:     {aggregated.avg_ttft:.3f}s")
        print(f"  Avg Latency:  {aggregated.avg_latency:.3f}s")
        print(f"  Throughput:   {aggregated.throughput:.2f} req/s")
        print(f"  Success Rate: {aggregated.success_rate:.1f}%")

    return results


async def run_benchmark():
    """Run the full benchmark comparing both engines."""

    print("\n" + "=" * 60)
    print("LLM INFERENCE BENCHMARK")
    print("vLLM vs Friendli Engine")
    print("=" * 60)
    print(f"\nModel: {MODEL_NAME}")
    print(f"Concurrency levels: {CONCURRENCY_LEVELS}")
    print(f"Requests per level: {REQUESTS_PER_LEVEL}")
    print(f"Warmup requests: {WARMUP_REQUESTS}")

    # Benchmark vLLM
    vllm_results = await benchmark_engine(
        name="vLLM",
        endpoint=VLLM_ENDPOINT,
        concurrency_levels=CONCURRENCY_LEVELS,
        requests_per_level=REQUESTS_PER_LEVEL,
        warmup_requests=WARMUP_REQUESTS,
    )

    # Benchmark Friendli
    friendli_results = await benchmark_engine(
        name="Friendli Engine",
        endpoint=FRIENDLI_ENDPOINT,
        concurrency_levels=CONCURRENCY_LEVELS,
        requests_per_level=REQUESTS_PER_LEVEL,
        warmup_requests=WARMUP_REQUESTS,
    )

    return vllm_results, friendli_results


def main():
    """Main entry point."""
    # Run the async benchmark
    vllm_results, friendli_results = asyncio.run(run_benchmark())

    # Generate visualization
    print("\n" + "=" * 60)
    print("Generating visualization...")
    print("=" * 60)

    from visualize import generate_comparison_chart
    generate_comparison_chart(vllm_results, friendli_results)

    print("\nBenchmark complete! Results saved to 'benchmark_results.png'")


if __name__ == "__main__":
    main()
