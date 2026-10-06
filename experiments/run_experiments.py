"""
experiments/run_experiments.py - Large-Scale Simulation Experiment Runner.

Executes a full factorial sweep:
- 4 Strategies: lone_entry, blind_follow, shared_map, split_exit
- 3 Difficulties: low, medium, high
- 2 Communication Ranges: 4.0 (low/local), 15.0 (high/broad)
- 500 Random Seeds per configuration (12,000 total episodes)

Saves all raw empirical data to `logs/results.csv` and generates analysis figures in `logs/figures/`.
"""

import os
import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure root package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sim.environment import Config
from sim.engine import run_episode


def run_all_experiments(
    num_episodes_per_config: int = 500,
    output_csv: str = "logs/results.csv",
    figures_dir: str = "logs/figures",
) -> pd.DataFrame:
    """Executes the complete experimental matrix and generates telemetry and figures."""
    strategies = ["lone_entry", "blind_follow", "shared_map", "split_exit"]
    difficulties = ["low", "medium", "high"]
    comm_ranges = [4.0, 15.0]

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    records = []
    total_runs = len(strategies) * len(difficulties) * len(comm_ranges) * num_episodes_per_config
    print(f"Starting experimental sweep: {total_runs} total episodes across 4 strategies...")

    start_time = time.time()
    counter = 0

    for diff in difficulties:
        for cr in comm_ranges:
            for strat in strategies:
                for episode_idx in range(num_episodes_per_config):
                    seed = 10000 + episode_idx
                    config = Config(
                        seed=seed,
                        difficulty=diff,
                        comm_range=cr,
                        max_steps=120,
                    )
                    res = run_episode(config, strat, record_history=False)
                    
                    records.append({
                        "strategy": strat,
                        "difficulty": diff,
                        "comm_range": cr,
                        "seed": seed,
                        "outcome": res["outcome"],
                        "success": 1 if res["outcome"] == "success" else 0,
                        "wipeout": 1 if res["outcome"] == "wipeout" else 0,
                        "timeout": 1 if res["outcome"] == "timeout" else 0,
                        "steps": res["steps"],
                        "survivors": res["survivors"],
                        "rings_breached": res["rings_breached"],
                        "messages_sent": res["messages_sent"],
                    })

                    counter += 1
                    if counter % 2000 == 0:
                        elapsed = time.time() - start_time
                        print(f"Progress: {counter}/{total_runs} episodes ({counter/total_runs*100:.1f}%) in {elapsed:.2f}s")

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"Successfully saved raw experimental data ({len(df)} rows) to '{output_csv}'")

    # Generate figures
    generate_analysis_charts(df, figures_dir)
    return df


def generate_analysis_charts(df: pd.DataFrame, figures_dir: str) -> None:
    """Generates standard publication-grade matplotlib figures from empirical results."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    colors = {"lone_entry": "#E53E3E", "blind_follow": "#DD6B20", "shared_map": "#3182CE", "split_exit": "#38A169"}
    strategy_labels = {
        "lone_entry": "Lone Entry (Abhimanyu)",
        "blind_follow": "Blind Follow",
        "shared_map": "Shared Map",
        "split_exit": "Split Exit",
    }

    # Figure 1: Success Rate per Strategy by Difficulty
    fig, ax = plt.subplots(figsize=(8, 5))
    grouped_success = df.groupby(["difficulty", "strategy"])["success"].mean().unstack()[["lone_entry", "blind_follow", "shared_map", "split_exit"]]
    # Reorder difficulty index: low, medium, high
    grouped_success = grouped_success.reindex(["low", "medium", "high"]) * 100

    grouped_success.plot(kind="bar", ax=ax, color=[colors[s] for s in grouped_success.columns], width=0.75, edgecolor="black", alpha=0.85)
    ax.set_title("Mission Success Rate by Strategy and Difficulty", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Formation Defense Difficulty", fontsize=11, fontweight="bold")
    ax.set_ylabel("Success Rate (%)", fontsize=11, fontweight="bold")
    ax.set_xticklabels(["Low", "Medium", "High"], rotation=0)
    ax.legend([strategy_labels[s] for s in grouped_success.columns], title="Strategy", frameon=True)
    plt.tight_layout()
    fig1_path = os.path.join(figures_dir, "success_rate_by_strategy.png")
    fig.savefig(fig1_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig1_path}")

    # Figure 2: Average Rings Breached by Strategy
    fig, ax = plt.subplots(figsize=(8, 5))
    grouped_rings = df.groupby(["difficulty", "strategy"])["rings_breached"].mean().unstack()[["lone_entry", "blind_follow", "shared_map", "split_exit"]]
    grouped_rings = grouped_rings.reindex(["low", "medium", "high"])

    grouped_rings.plot(kind="bar", ax=ax, color=[colors[s] for s in grouped_rings.columns], width=0.75, edgecolor="black", alpha=0.85)
    ax.set_title("Average Rings Breached (Depth of Penetration)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Formation Defense Difficulty", fontsize=11, fontweight="bold")
    ax.set_ylabel("Mean Rings Breached (Out of 7)", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 7.5)
    ax.set_xticklabels(["Low", "Medium", "High"], rotation=0)
    ax.legend([strategy_labels[s] for s in grouped_rings.columns], title="Strategy", frameon=True)
    plt.tight_layout()
    fig2_path = os.path.join(figures_dir, "average_rings_breached.png")
    fig.savefig(fig2_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig2_path}")

    # Figure 3: Average Survivors Rate
    fig, ax = plt.subplots(figsize=(8, 5))
    grouped_surv = df.groupby(["difficulty", "strategy"])["survivors"].mean().unstack()[["lone_entry", "blind_follow", "shared_map", "split_exit"]]
    grouped_surv = grouped_surv.reindex(["low", "medium", "high"])

    grouped_surv.plot(kind="bar", ax=ax, color=[colors[s] for s in grouped_surv.columns], width=0.75, edgecolor="black", alpha=0.85)
    ax.set_title("Mean Survivors at Episode Termination", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Formation Defense Difficulty", fontsize=11, fontweight="bold")
    ax.set_ylabel("Average Surviving Units", fontsize=11, fontweight="bold")
    ax.set_xticklabels(["Low", "Medium", "High"], rotation=0)
    ax.legend([strategy_labels[s] for s in grouped_surv.columns], title="Strategy", frameon=True)
    plt.tight_layout()
    fig3_path = os.path.join(figures_dir, "survival_rate.png")
    fig.savefig(fig3_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig3_path}")

    # Figure 4: Effect of Communication Range (Low vs High) on Shared Map and Split Exit
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    comm_df = df[df["strategy"].isin(["shared_map", "split_exit"])]
    
    # 4A: Success Rate vs Comm Range
    comm_success = comm_df.groupby(["comm_range", "strategy"])["success"].mean().unstack() * 100
    comm_success.plot(kind="bar", ax=ax1, color=[colors["shared_map"], colors["split_exit"]], edgecolor="black", alpha=0.85)
    ax1.set_title("Success Rate vs Communication Range", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Communication Range (Grid Units)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Success Rate (%)", fontsize=10, fontweight="bold")
    ax1.set_xticklabels(["Low (4.0)", "High (15.0)"], rotation=0)
    ax1.legend(["Shared Map", "Split Exit"], frameon=True)

    # 4B: Messages Sent vs Comm Range
    comm_msgs = comm_df.groupby(["comm_range", "strategy"])["messages_sent"].mean().unstack()
    comm_msgs.plot(kind="bar", ax=ax2, color=[colors["shared_map"], colors["split_exit"]], edgecolor="black", alpha=0.85)
    ax2.set_title("Mean Messages Delivered vs Comm Range", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Communication Range (Grid Units)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Average Messages Delivered", fontsize=10, fontweight="bold")
    ax2.set_xticklabels(["Low (4.0)", "High (15.0)"], rotation=0)
    ax2.legend(["Shared Map", "Split Exit"], frameon=True)

    plt.tight_layout()
    fig4_path = os.path.join(figures_dir, "comm_range_effect.png")
    fig.savefig(fig4_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig4_path}")


if __name__ == "__main__":
    run_all_experiments()
