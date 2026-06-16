import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger


def load_latest_results(results_dir: str = "data/evaluation/results") -> dict:
    results_path = Path(results_dir)
    json_files = sorted(results_path.glob("run_*.json"), reverse=True)
    if not json_files:
        raise FileNotFoundError(f"No result files found in {results_dir}")
    with open(json_files[0]) as f:
        return json.load(f)


def plot_grouped_bar(data: dict, output_path: str):
    summary = data["summary"]
    modes = list(summary.keys())
    metrics = ["ndcg_at_10", "mrr_at_10", "precision_at_5", "recall_at_5"]
    metric_labels = ["NDCG@10", "MRR@10", "P@5", "R@5"]

    x = np.arange(len(metrics))
    width = 0.25
    colors = {"sparse": "#2563eb", "dense": "#9333ea", "hybrid": "#059669"}

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, mode in enumerate(modes):
        values = [summary[mode].get(m, 0) for m in metrics]
        ax.bar(x + i * width, values, width, label=mode.capitalize(), color=colors.get(mode, "#666"))

    ax.set_xlabel("Metric")
    ax.set_ylabel("Score")
    ax.set_title("Retrieval Metrics by Mode")
    ax.set_xticks(x + width)
    ax.set_xticklabels(metric_labels)
    ax.legend()
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved grouped bar chart to {output_path}")


def plot_heatmap(data: dict, output_path: str):
    per_query = data["per_query"]
    query_types = sorted(set(q["query_type"] for q in per_query))
    modes = list(data["summary"].keys())
    metric = "ndcg_at_10"

    grid = np.zeros((len(query_types), len(modes)))
    counts = np.zeros((len(query_types), len(modes)))

    for q in per_query:
        row = query_types.index(q["query_type"])
        for col, mode in enumerate(modes):
            if mode in q["modes"]:
                grid[row, col] += q["modes"][mode].get(metric, 0)
                counts[row, col] += 1

    counts[counts == 0] = 1
    grid = grid / counts

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(grid, cmap="YlGn", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(modes)))
    ax.set_xticklabels([m.capitalize() for m in modes])
    ax.set_yticks(range(len(query_types)))
    ax.set_yticklabels([qt.capitalize() for qt in query_types])

    for i in range(len(query_types)):
        for j in range(len(modes)):
            ax.text(j, i, f"{grid[i, j]:.2f}", ha="center", va="center", fontsize=12)

    ax.set_title(f"NDCG@10: Query Type x Retrieval Mode")
    plt.colorbar(im)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved heatmap to {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", action="store_true", default=True)
    parser.add_argument("--results-dir", default="data/evaluation/results")
    args = parser.parse_args()

    data = load_latest_results(args.results_dir)
    results_dir = Path(args.results_dir)

    plot_grouped_bar(data, str(results_dir / "metrics_by_mode.png"))
    plot_heatmap(data, str(results_dir / "heatmap_querytype_mode.png"))


if __name__ == "__main__":
    main()
