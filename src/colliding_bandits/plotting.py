from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Dict, List, Sequence


def _ensure_matplotlib_env() -> None:
    if "MPLCONFIGDIR" not in os.environ:
        cache_dir = Path(tempfile.gettempdir()) / "colliding_bandits_mplconfig"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache_dir)


def _import_pyplot():
    _ensure_matplotlib_env()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _prepare_output_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def plot_time_series(prefix: Path, time_series: Sequence[Dict[str, float]]) -> List[Path]:
    if not time_series:
        return []
    plt = _import_pyplot()
    steps = [row["step"] for row in time_series]
    specs = [
        ("cumulative_regret", "Cumulative Regret", "cumulative_regret.png"),
        ("mean_reward", "Mean Reward Per Player", "mean_reward.png"),
        ("efficiency", "Efficiency", "efficiency.png"),
        ("occupancy_variance", "Occupancy Variance", "occupancy_variance.png"),
        ("player_reward_variance", "Player Reward Variance", "player_reward_variance.png"),
    ]

    written: List[Path] = []
    for metric_key, title, suffix in specs:
        output_path = Path(f"{prefix}_{suffix}")
        _prepare_output_path(output_path)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(steps, [row[metric_key] for row in time_series], linewidth=1.6)
        ax.set_title(title)
        ax.set_xlabel("Step")
        ax.set_ylabel(metric_key)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(output_path, dpi=170)
        plt.close(fig)
        written.append(output_path)
    return written


def plot_sweep_lines(prefix: Path, rows: Sequence[Dict[str, float]]) -> List[Path]:
    if not rows:
        return []
    plt = _import_pyplot()
    sorted_rows = sorted(rows, key=lambda row: row["rho_realized"])
    rho_values = [row["rho_realized"] for row in sorted_rows]

    specs = [
        ("mean_reward_average", "Mean Reward vs rho", "mean_reward_vs_rho.png"),
        ("efficiency_average", "Efficiency vs rho", "efficiency_vs_rho.png"),
        ("occupancy_variance_average", "Occupancy Variance vs rho", "occupancy_variance_vs_rho.png"),
        ("player_reward_variance_average", "Player Reward Variance vs rho", "player_reward_variance_vs_rho.png"),
        ("late_regret_rate", "Late Regret Rate vs rho", "late_regret_rate_vs_rho.png"),
    ]

    written: List[Path] = []
    for metric_key, title, suffix in specs:
        output_path = Path(f"{prefix}_{suffix}")
        _prepare_output_path(output_path)
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.plot(rho_values, [row[metric_key] for row in sorted_rows], marker="o", linewidth=1.8)
        ax.set_title(title)
        ax.set_xlabel("rho = N / K")
        ax.set_ylabel(metric_key)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(output_path, dpi=180)
        plt.close(fig)
        written.append(output_path)
    return written
