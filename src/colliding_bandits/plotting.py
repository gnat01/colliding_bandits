from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import List, Sequence


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


def _save_figure(fig, output_path: Path) -> List[Path]:
    _prepare_output_path(output_path)
    pdf_path = output_path.with_suffix(".pdf")
    fig.savefig(output_path, dpi=180)
    fig.savefig(pdf_path)
    return [output_path, pdf_path]


def _plot_multi_line(prefix: Path, suffix: str, title: str, x_label: str, y_label: str, rows, exploration_steps: int) -> Path:
    plt = _import_pyplot()
    output_path = Path(f"{prefix}_{suffix}")
    _prepare_output_path(output_path)
    fig, ax = plt.subplots(figsize=(9, 5))
    steps = [row["step"] for row in rows]
    series_keys = [key for key in rows[0].keys() if key != "step"]
    for key in series_keys:
        ax.plot(steps, [row[key] for row in rows], linewidth=1.0, alpha=0.9)
    ax.axvline(exploration_steps, color="blue", linestyle="--", linewidth=1.5)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    _save_figure(fig, output_path)
    plt.close(fig)
    return output_path


def _plot_choice_heatmap(prefix: Path, rows, exploration_steps: int) -> Path:
    plt = _import_pyplot()
    output_path = Path(f"{prefix}_player_choices_heatmap.png")
    _prepare_output_path(output_path)
    player_keys = [key for key in rows[0].keys() if key != "step"]
    matrix = [[row[key] for row in rows] for key in player_keys]
    fig, ax = plt.subplots(figsize=(10, 5))
    image = ax.imshow(matrix, aspect="auto", interpolation="nearest", origin="lower")
    ax.axvline(exploration_steps, color="blue", linestyle="--", linewidth=1.5)
    ax.set_title("Player Choices Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Player")
    ax.set_yticks(range(len(player_keys)))
    ax.set_yticklabels([key.replace("player_", "P") for key in player_keys])
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Arm Index")
    fig.tight_layout()
    _save_figure(fig, output_path)
    plt.close(fig)
    return output_path


def _plot_occupancy_heatmap(prefix: Path, rows, exploration_steps: int) -> Path:
    plt = _import_pyplot()
    output_path = Path(f"{prefix}_arm_occupancy_heatmap.png")
    _prepare_output_path(output_path)
    arm_keys = [key for key in rows[0].keys() if key != "step"]
    matrix = [[row[key] for row in rows] for key in arm_keys]
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    image = ax.imshow(matrix, aspect="auto", interpolation="nearest", origin="lower")
    ax.axvline(exploration_steps, color="blue", linestyle="--", linewidth=1.5)
    ax.set_title("Arm Occupancy Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Arm")
    ax.set_yticks(range(len(arm_keys)))
    ax.set_yticklabels([key.replace("arm_", "A") for key in arm_keys])
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Occupancy")
    fig.tight_layout()
    _save_figure(fig, output_path)
    plt.close(fig)
    return output_path


def _plot_occupancy_animation(prefix: Path, rows, reward_rows, exploration_steps: int, players: int) -> Path:
    _ensure_matplotlib_env()
    from PIL import Image
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from io import BytesIO

    output_path = Path(f"{prefix}_arm_occupancy_histogram.gif")
    _prepare_output_path(output_path)
    arm_keys = [key for key in rows[0].keys() if key != "step"]
    total_steps = len(rows)
    frame_stride = 100
    frame_indices = list(range(0, total_steps, frame_stride))
    if frame_indices[-1] != total_steps - 1:
        frame_indices.append(total_steps - 1)

    cumulative_reward = {key: 0.0 for key in arm_keys}
    cumulative_count = {key: 0 for key in arm_keys}
    frames: List[Image.Image] = []
    next_frame_set = set(frame_indices)
    for idx, (row, reward_row) in enumerate(zip(rows, reward_rows)):
        for key in arm_keys:
            cumulative_reward[key] += reward_row[key]
            cumulative_count[key] += 1

        if idx not in next_frame_set:
            continue

        row = rows[idx]
        values = [row[key] for key in arm_keys]
        avg_rewards = [
            (key, cumulative_reward[key] / cumulative_count[key] if cumulative_count[key] > 0 else 0.0)
            for key in arm_keys
        ]
        avg_rewards.sort(key=lambda item: item[1], reverse=True)
        best_key, best_value = avg_rewards[0]
        worst_key, worst_value = avg_rewards[-1]
        top_lines = [
            f"{rank+1}. {key.replace('arm_', 'A')} : {value:.3f}"
            for rank, (key, value) in enumerate(avg_rewards[:10])
        ]
        summary_lines = [
            "",
            f"Best  : {best_key.replace('arm_', 'A')} = {best_value:.3f}",
            f"Worst : {worst_key.replace('arm_', 'A')} = {worst_value:.3f}",
        ]

        fig, (ax, text_ax) = plt.subplots(
            1,
            2,
            figsize=(11.5, 4.8),
            gridspec_kw={"width_ratios": [3.0, 1.5]},
        )
        ax.bar(range(len(arm_keys)), values, color="#4c78a8")
        ax.set_ylim(0, max(4, max(values) + 1))
        ax.set_title(f"Arm Occupancy Histogram at step {int(row['step'])}")
        ax.set_xlabel("Arm")
        ax.set_ylabel("Occupancy")
        ax.text(
            0.98,
            0.95,
            "exploration" if row["step"] <= exploration_steps else "strategy",
            transform=ax.transAxes,
            ha="right",
            va="top",
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
        )
        text_ax.axis("off")
        text_ax.set_title("Top 10 Arms\nAvg Reward So Far")
        text_ax.text(
            0.0,
            1.0,
            "\n".join(top_lines + summary_lines),
            ha="left",
            va="top",
            family="monospace",
        )
        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=110)
        plt.close(fig)
        buffer.seek(0)
        frame = Image.open(buffer).convert("RGBA")
        palette_frame = frame.convert("P", palette=Image.Palette.ADAPTIVE)
        frames.append(palette_frame.copy())
        frame.close()
        buffer.close()

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=[1000] * len(frames),
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output_path


def _plot_mean_lines(prefix: Path, suffix: str, title: str, steps, values, oracle_line, exploration_steps: int) -> Path:
    plt = _import_pyplot()
    output_path = Path(f"{prefix}_{suffix}")
    _prepare_output_path(output_path)
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.plot(steps, values, linewidth=1.8, label="mean player")
    if oracle_line is not None:
        ax.axhline(oracle_line, color="black", linestyle=":", linewidth=1.3, label="oracle mean")
    ax.axvline(exploration_steps, color="blue", linestyle="--", linewidth=1.5, label="strategy boundary")
    ax.set_title(title)
    ax.set_xlabel("Step")
    ax.set_ylabel(title)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    _save_figure(fig, output_path)
    plt.close(fig)
    return output_path


def _plot_oracle_trace_panel(prefix: Path, result) -> Path:
    plt = _import_pyplot()
    output_path = Path(f"{prefix}_oracle_trace_panel.png")
    _prepare_output_path(output_path)

    steps = [row["step"] for row in result.oracle_trace_rows]
    oracle_rewards = [row["oracle_reward"] for row in result.oracle_trace_rows]
    system_mean_rewards = [row["system_mean_reward"] for row in result.oracle_trace_rows]
    efficiencies = [row["efficiency"] for row in result.oracle_trace_rows]
    cumulative_regrets = [row["cumulative_system_regret"] for row in result.oracle_trace_rows]
    exploration_steps = result.config.exploration_steps

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    panels = [
        (axes[0, 0], oracle_rewards, "Oracle Reward Each Step", "oracle_reward"),
        (axes[0, 1], system_mean_rewards, "System Mean Reward", "system_mean_reward"),
        (axes[1, 0], efficiencies, "Efficiency", "efficiency"),
        (axes[1, 1], cumulative_regrets, "Cumulative System Regret", "cumulative_system_regret"),
    ]

    for ax, values, title, y_label in panels:
        ax.plot(steps, values, linewidth=1.4)
        ax.axvline(exploration_steps, color="blue", linestyle="--", linewidth=1.3)
        ax.set_title(title)
        ax.set_xlabel("Step")
        ax.set_ylabel(y_label)
        ax.grid(alpha=0.25)

    fig.tight_layout()
    _save_figure(fig, output_path)
    plt.close(fig)
    return output_path


def plot_experiment(prefix: Path, result) -> List[Path]:
    written: List[Path] = []
    exploration_steps = result.config.exploration_steps
    written.append(
        _plot_multi_line(
            prefix,
            "player_total_reward.png",
            "Player Total Reward",
            "Step",
            "Cumulative Reward",
            result.player_total_reward_rows,
            exploration_steps,
        )
    )
    written.append(
        _plot_multi_line(
            prefix,
            "player_regret.png",
            "Player Regret Against Oracle Mean",
            "Step",
            "Cumulative Regret",
            result.player_regret_rows,
            exploration_steps,
        )
    )
    written.append(
        _plot_multi_line(
            prefix,
            "arm_plays.png",
            "Arm Plays Until Time t",
            "Step",
            "Cumulative Plays",
            result.arm_plays_rows,
            exploration_steps,
        )
    )
    written.append(
        _plot_multi_line(
            prefix,
            "arm_collisions.png",
            "Arm Collisions Until Time t",
            "Step",
            "Cumulative Collisions",
            result.arm_collision_rows,
            exploration_steps,
        )
    )
    written.append(
        _plot_multi_line(
            prefix,
            "arm_occupancy.png",
            "Arm Occupancy At Time t",
            "Step",
            "Occupancy",
            result.arm_occupancy_rows,
            exploration_steps,
        )
    )
    written.append(_plot_choice_heatmap(prefix, result.player_choice_rows, exploration_steps))
    written.append(_plot_occupancy_heatmap(prefix, result.arm_occupancy_rows, exploration_steps))
    written.append(
        _plot_occupancy_animation(
            prefix,
            result.arm_occupancy_rows,
            result.arm_realized_reward_rows,
            exploration_steps,
            result.config.players,
        )
    )

    steps = [row["step"] for row in result.metric_rows]
    written.append(
        _plot_mean_lines(
            prefix,
            "mean_reward.png",
            "Mean Player Reward",
            steps,
            [row["mean_player_reward"] for row in result.metric_rows],
            result.summary["oracle_mean_expected"],
            exploration_steps,
        )
    )
    written.append(
        _plot_mean_lines(
            prefix,
            "mean_regret.png",
            "Mean Player Regret",
            steps,
            [row["mean_player_regret"] for row in result.metric_rows],
            None,
            exploration_steps,
        )
    )
    written.append(_plot_oracle_trace_panel(prefix, result))
    return written


def plot_sweep_lines(prefix: Path, rows: Sequence[dict]) -> List[Path]:
    if not rows:
        return []
    plt = _import_pyplot()
    sorted_rows = sorted(rows, key=lambda row: row["rho_realized"])
    rho_values = [row["rho_realized"] for row in sorted_rows]
    specs = [
        ("mean_reward_average", "Mean Reward vs rho", "mean_reward_vs_rho.png"),
        ("mean_regret_average", "Mean Regret vs rho", "mean_regret_vs_rho.png"),
        ("efficiency_average", "Efficiency vs rho", "efficiency_vs_rho.png"),
        ("occupancy_variance_average", "Occupancy Variance vs rho", "occupancy_variance_vs_rho.png"),
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
        _save_figure(fig, output_path)
        plt.close(fig)
        written.append(output_path)
    return written


def plot_collapse_panels(prefix: Path, rows: Sequence[dict]) -> List[Path]:
    if not rows:
        return []
    plt = _import_pyplot()
    valid_rows = [row for row in rows if row["n"] > 0 and row["m"] > 0]
    if not valid_rows:
        return []

    def _facet_plot(
        suffix: str,
        title: str,
        facet_key: str,
        color_key: str,
        y_key: str,
        y_label: str,
    ) -> List[Path]:
        facet_values = sorted({row[facet_key] for row in valid_rows})
        ncols = min(3, max(1, len(facet_values)))
        nrows = (len(facet_values) + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(5.2 * ncols, 4.3 * nrows), squeeze=False)
        color_values = sorted({row[color_key] for row in valid_rows})
        cmap = plt.get_cmap("viridis")
        color_map = {
            value: cmap(index / max(1, len(color_values) - 1))
            for index, value in enumerate(color_values)
        }

        for ax, facet_value in zip(axes.flat, facet_values):
            subset = [row for row in valid_rows if row[facet_key] == facet_value]
            for color_value in color_values:
                curve = [row for row in subset if row[color_key] == color_value and row[y_key] > 0]
                if not curve:
                    continue
                curve = sorted(curve, key=lambda row: row["n"])
                xs = [row["n"] for row in curve]
                ys = [row[y_key] for row in curve]
                ax.plot(xs, ys, marker="o", linewidth=1.2, markersize=4, alpha=0.9, color=color_map[color_value], label=str(color_value))
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_title(f"{facet_key} = {facet_value:g}")
            ax.set_xlabel("n")
            ax.set_ylabel(y_label)
            ax.grid(alpha=0.25)

        for ax in axes.flat[len(facet_values):]:
            ax.axis("off")

        handles, labels = axes.flat[0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, title=color_key, loc="upper center", ncol=min(5, len(labels)))
        fig.suptitle(title)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        output_path = Path(f"{prefix}_{suffix}.png")
        saved = _save_figure(fig, output_path)
        plt.close(fig)
        return saved

    written: List[Path] = []
    written.extend(
        _facet_plot(
            "collapse_by_epsilon",
            "Collapse View By epsilon",
            "epsilon",
            "arms",
            "m",
            "m",
        )
    )
    written.extend(
        _facet_plot(
            "collapse_by_arms",
            "Collapse View By arms",
            "arms",
            "epsilon",
            "m",
            "m",
        )
    )
    written.extend(
        _facet_plot(
            "collapse_scaled",
            "Scaled Collapse: arms / epsilon",
            "scaled_1",
            "epsilon",
            "m",
            "m",
        )
    )
    written.extend(
        _facet_plot(
            "collapse_scaled_per_player",
            "Scaled Collapse: arms / epsilon with m / players",
            "scaled_1",
            "epsilon",
            "m_per_player",
            "m / players",
        )
    )
    return written
