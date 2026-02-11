"""
Visualization module for benchmark results.

Generates a comparison chart showing performance metrics
for vLLM vs Friendli Engine across concurrency levels.
"""

import matplotlib.pyplot as plt
from metrics import AggregatedMetrics


def generate_comparison_chart(
    vllm_results: dict[int, AggregatedMetrics],
    friendli_results: dict[int, AggregatedMetrics],
    output_file: str = "benchmark_results.png"
) -> None:
    """
    Generate a comparison chart with three subplots:
    1. Throughput vs Concurrency
    2. Latency vs Concurrency
    3. Time to First Token vs Concurrency

    Args:
        vllm_results: vLLM metrics by concurrency level
        friendli_results: Friendli metrics by concurrency level
        output_file: Path to save the chart
    """
    # Extract data for plotting
    concurrency_levels = sorted(vllm_results.keys())

    vllm_throughput = [vllm_results[c].throughput for c in concurrency_levels]
    friendli_throughput = [friendli_results[c].throughput for c in concurrency_levels]

    vllm_latency = [vllm_results[c].avg_latency for c in concurrency_levels]
    friendli_latency = [friendli_results[c].avg_latency for c in concurrency_levels]

    vllm_ttft = [vllm_results[c].avg_ttft for c in concurrency_levels]
    friendli_ttft = [friendli_results[c].avg_ttft for c in concurrency_levels]

    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("LLM Inference Benchmark: vLLM vs Friendli Engine", fontsize=14, fontweight="bold")

    # Subplot 1: Throughput
    ax1 = axes[0]
    ax1.plot(concurrency_levels, vllm_throughput, marker="o", label="vLLM", linewidth=2)
    ax1.plot(concurrency_levels, friendli_throughput, marker="s", label="Friendli", linewidth=2)
    ax1.set_xlabel("Concurrency Level")
    ax1.set_ylabel("Throughput (requests/sec)")
    ax1.set_title("Throughput vs Concurrency")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(concurrency_levels)

    # Subplot 2: Latency
    ax2 = axes[1]
    ax2.plot(concurrency_levels, vllm_latency, marker="o", label="vLLM", linewidth=2)
    ax2.plot(concurrency_levels, friendli_latency, marker="s", label="Friendli", linewidth=2)
    ax2.set_xlabel("Concurrency Level")
    ax2.set_ylabel("Average Latency (seconds)")
    ax2.set_title("Latency vs Concurrency")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(concurrency_levels)

    # Subplot 3: Time to First Token
    ax3 = axes[2]
    ax3.plot(concurrency_levels, vllm_ttft, marker="o", label="vLLM", linewidth=2)
    ax3.plot(concurrency_levels, friendli_ttft, marker="s", label="Friendli", linewidth=2)
    ax3.set_xlabel("Concurrency Level")
    ax3.set_ylabel("Avg Time to First Token (seconds)")
    ax3.set_title("TTFT vs Concurrency")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(concurrency_levels)

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to: {output_file}")
