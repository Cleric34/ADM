"""
experiments/run_experiments.py - Large-Scale Simulation Experiment Runner.

Executes a full factorial sweep:
- 5 Strategies: oracle, lone_entry, blind_follow, shared_map, split_exit
- 3 Difficulties: low, medium, high
- 2 Communication Ranges: 4.0 (low/local), 15.0 (high/broad)
- 500 Random Seeds per configuration (15,000 total episodes)

Saves all raw empirical data to `logs/results.csv` and generates analysis figures
with 95% confidence intervals in `logs/figures/`.
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
    strategies = ["oracle", "lone_entry", "blind_follow", "shared_map", "split_exit"]
    difficulties = ["low", "medium", "high"]
    comm_ranges = [4.0, 15.0]

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    records = []
    total_runs = len(strategies) * len(difficulties) * len(comm_ranges) * num_episodes_per_config
    print(f"Starting experimental sweep: {total_runs} total episodes across {len(strategies)} strategies...")

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
                        max_steps=400,
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
                    if counter % 2500 == 0:
                        elapsed = time.time() - start_time
                        print(f"Progress: {counter}/{total_runs} episodes ({counter/total_runs*100:.1f}%) in {elapsed:.2f}s")

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"Successfully saved raw experimental data ({len(df)} rows) to '{output_csv}'")

    # Generate figures with 95% confidence intervals
    generate_analysis_charts(df, figures_dir)
    return df


def generate_analysis_charts(df: pd.DataFrame, figures_dir: str) -> None:
    """Generates standard publication-grade matplotlib figures with 95% confidence intervals."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    colors = {
        "oracle": "#805AD5",
        "lone_entry": "#E53E3E",
        "blind_follow": "#DD6B20",
        "shared_map": "#3182CE",
        "split_exit": "#38A169",
    }
    strategy_order = ["oracle", "lone_entry", "blind_follow", "shared_map", "split_exit"]
    strategy_labels = {
        "oracle": "Oracle (Full Knowledge)",
        "lone_entry": "Lone Entry (Abhimanyu)",
        "blind_follow": "Blind Follow",
        "shared_map": "Shared Map",
        "split_exit": "Split Exit",
    }
    diff_order = ["low", "medium", "high"]

    # Figure 1: Success Rate per Strategy by Difficulty with 95% CI
    fig, ax = plt.subplots(figsize=(9, 5.5))
    grouped_mean = df.groupby(["difficulty", "strategy"])["success"].mean().unstack()[strategy_order].reindex(diff_order) * 100
    grouped_n = df.groupby(["difficulty", "strategy"])["success"].count().unstack()[strategy_order].reindex(diff_order)
    # Wilson / Wald 95% CI for proportion = 1.96 * sqrt(p * (1 - p) / n)
    p = grouped_mean / 100.0
    grouped_ci = 1.96 * np.sqrt(np.maximum(0, p * (1 - p)) / grouped_n) * 100

    x = np.arange(len(diff_order))
    width = 0.16
    for i, strat in enumerate(strategy_order):
        means = grouped_mean[strat].values
        cis = grouped_ci[strat].values
        ax.bar(
            x + (i - 2) * width,
            means,
            width=width,
            yerr=cis,
            capsize=4,
            label=strategy_labels[strat],
            color=colors[strat],
            edgecolor="black",
            alpha=0.88,
        )

    ax.set_title("Mission Success Rate by Strategy and Difficulty (with 95% CI)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Formation Defense Difficulty", fontsize=11, fontweight="bold")
    ax.set_ylabel("Success Rate (%)", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(["Low", "Medium", "High"], fontsize=10)
    ax.legend(title="Strategy", frameon=True, fontsize=9)
    plt.tight_layout()
    fig1_path = os.path.join(figures_dir, "success_rate_by_strategy.png")
    fig.savefig(fig1_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig1_path}")

    # Figure 2: Average Rings Breached with 95% CI
    fig, ax = plt.subplots(figsize=(9, 5.5))
    grouped_rings_mean = df.groupby(["difficulty", "strategy"])["rings_breached"].mean().unstack()[strategy_order].reindex(diff_order)
    grouped_rings_std = df.groupby(["difficulty", "strategy"])["rings_breached"].std().unstack()[strategy_order].reindex(diff_order)
    grouped_rings_ci = 1.96 * (grouped_rings_std / np.sqrt(grouped_n))

    for i, strat in enumerate(strategy_order):
        means = grouped_rings_mean[strat].values
        cis = grouped_rings_ci[strat].values
        ax.bar(
            x + (i - 2) * width,
            means,
            width=width,
            yerr=cis,
            capsize=4,
            label=strategy_labels[strat],
            color=colors[strat],
            edgecolor="black",
            alpha=0.88,
        )

    ax.set_title("Average Rings Breached by Strategy and Difficulty (with 95% CI)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Formation Defense Difficulty", fontsize=11, fontweight="bold")
    ax.set_ylabel("Mean Rings Breached (0 to 7)", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 7.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Low", "Medium", "High"], fontsize=10)
    ax.legend(title="Strategy", frameon=True, fontsize=9)
    plt.tight_layout()
    fig2_path = os.path.join(figures_dir, "average_rings_breached.png")
    fig.savefig(fig2_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig2_path}")

    # Figure 3: Average Survivors with 95% CI
    fig, ax = plt.subplots(figsize=(9, 5.5))
    grouped_surv_mean = df.groupby(["difficulty", "strategy"])["survivors"].mean().unstack()[strategy_order].reindex(diff_order)
    grouped_surv_std = df.groupby(["difficulty", "strategy"])["survivors"].std().unstack()[strategy_order].reindex(diff_order)
    grouped_surv_ci = 1.96 * (grouped_surv_std / np.sqrt(grouped_n))

    for i, strat in enumerate(strategy_order):
        means = grouped_surv_mean[strat].values
        cis = grouped_surv_ci[strat].values
        ax.bar(
            x + (i - 2) * width,
            means,
            width=width,
            yerr=cis,
            capsize=4,
            label=strategy_labels[strat],
            color=colors[strat],
            edgecolor="black",
            alpha=0.88,
        )

    ax.set_title("Mean Surviving Units at Episode End (with 95% CI)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Formation Defense Difficulty", fontsize=11, fontweight="bold")
    ax.set_ylabel("Average Survivors", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(["Low", "Medium", "High"], fontsize=10)
    ax.legend(title="Strategy", frameon=True, fontsize=9)
    plt.tight_layout()
    fig3_path = os.path.join(figures_dir, "survival_rate.png")
    fig.savefig(fig3_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig3_path}")

    # Figure 4: Effect of Communication Range (Low vs High) on Shared Map and Split Exit
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    comm_df = df[df["strategy"].isin(["shared_map", "split_exit"])]
    comm_strats = ["shared_map", "split_exit"]
    
    # 4A: Success Rate vs Comm Range with 95% CI
    comm_succ_mean = comm_df.groupby(["comm_range", "strategy"])["success"].mean().unstack()[comm_strats] * 100
    comm_succ_n = comm_df.groupby(["comm_range", "strategy"])["success"].count().unstack()[comm_strats]
    p_comm = comm_succ_mean / 100.0
    comm_succ_ci = 1.96 * np.sqrt(np.maximum(0, p_comm * (1 - p_comm)) / comm_succ_n) * 100

    x_c = np.arange(2)
    w_c = 0.35
    for i, strat in enumerate(comm_strats):
        ax1.bar(
            x_c + (i - 0.5) * w_c,
            comm_succ_mean[strat].values,
            width=w_c,
            yerr=comm_succ_ci[strat].values,
            capsize=4,
            label=strategy_labels[strat],
            color=colors[strat],
            edgecolor="black",
            alpha=0.88,
        )
    ax1.set_title("Success Rate vs Comm Range (95% CI)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Communication Range (Grid Units)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Success Rate (%)", fontsize=10, fontweight="bold")
    ax1.set_xticks(x_c)
    ax1.set_xticklabels(["Low (4.0)", "High (15.0)"])
    ax1.legend(frameon=True)

    # 4B: Messages Sent vs Comm Range with 95% CI
    comm_msgs_mean = comm_df.groupby(["comm_range", "strategy"])["messages_sent"].mean().unstack()[comm_strats]
    comm_msgs_std = comm_df.groupby(["comm_range", "strategy"])["messages_sent"].std().unstack()[comm_strats]
    comm_msgs_ci = 1.96 * (comm_msgs_std / np.sqrt(comm_succ_n))

    for i, strat in enumerate(comm_strats):
        ax2.bar(
            x_c + (i - 0.5) * w_c,
            comm_msgs_mean[strat].values,
            width=w_c,
            yerr=comm_msgs_ci[strat].values,
            capsize=4,
            label=strategy_labels[strat],
            color=colors[strat],
            edgecolor="black",
            alpha=0.88,
        )
    ax2.set_title("Messages Delivered vs Comm Range (95% CI)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Communication Range (Grid Units)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Mean Delivered Messages", fontsize=10, fontweight="bold")
    ax2.set_xticks(x_c)
    ax2.set_xticklabels(["Low (4.0)", "High (15.0)"])
    ax2.legend(frameon=True)

    plt.tight_layout()
    fig4_path = os.path.join(figures_dir, "comm_range_effect.png")
    fig.savefig(fig4_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure: {fig4_path}")


if __name__ == "__main__":
    run_all_experiments()
