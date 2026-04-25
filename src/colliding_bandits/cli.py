from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from statistics import mean, stdev
import subprocess
from typing import Dict, List

from .models import parse_float_list
from .plotting import plot_collapse_panels, plot_experiment, plot_sweep_lines
from .simulator import (
    SimulationConfig,
    expand_rho_grid,
    run_simulation,
    write_summary_json,
    write_sweep_csv,
    write_tables,
)

DEFAULT_CONFIG_PATH = Path("config/default.json")


def _reward_vectors(args: argparse.Namespace) -> tuple[List[float] | None, List[float] | None]:
    means = parse_float_list(args.reward_means) if args.reward_means else None
    stds = parse_float_list(args.reward_stds) if args.reward_stds else None
    if means is None and stds is None:
        return None, None
    if means is None or stds is None:
        raise ValueError("Provide both --reward-means and --reward-stds, or provide neither.")
    if len(means) != len(stds):
        raise ValueError("reward-means and reward-stds must have the same length")
    if args.arms != len(means):
        raise ValueError(f"--arms={args.arms} does not match len(reward-means)={len(means)}")
    if any(mean <= 0 for mean in means) and args.reward_distribution == "gamma":
        raise ValueError("gamma rewards require all means to be strictly positive")
    return means, stds


def add_common_args(parser: argparse.ArgumentParser, *, require_players: bool, require_arms: bool = True) -> None:
    if require_arms:
        parser.add_argument("--arms", type=int, required=True, help="Number of arms K.")
    parser.add_argument("--players", type=int, required=require_players, help="Number of players N.")
    parser.add_argument("--exploration-cycles", type=int, required=True, help="How many full offset cycles each player executes in exploration.")
    parser.add_argument("--strategy-steps", type=int, required=True, help="Number of strategy-phase steps after exploration.")
    parser.add_argument("--seed", type=int, default=123, help="Base random seed.")
    parser.add_argument(
        "--learner",
        choices=["epsilon-greedy", "ucb1"],
        required=True,
        help="Bandit learner used by each player.",
    )
    parser.add_argument(
        "--reward-distribution",
        choices=["gamma", "uniform"],
        required=True,
        help="Per-arm reward distribution parameterized by mu_k and sd_k.",
    )
    parser.add_argument(
        "--reward-means",
        type=str,
        default=None,
        help="Optional comma-separated arm means mu_k. If omitted, means are generated internally.",
    )
    parser.add_argument(
        "--reward-stds",
        type=str,
        default=None,
        help="Optional comma-separated arm standard deviations sd_k. If omitted, stds are generated internally.",
    )
    parser.add_argument(
        "--mean-profile",
        choices=["linear", "uniform", "two-tier"],
        default="two-tier",
        help="Internal mean generator used when reward-means are omitted.",
    )
    parser.add_argument("--mean-low", type=float, default=0.1, help="Minimum internally generated mean.")
    parser.add_argument("--mean-high", type=float, default=1.0, help="Maximum internally generated mean.")
    parser.add_argument(
        "--std-profile",
        choices=["constant", "linear"],
        default="constant",
        help="Internal std generator used when reward-stds are omitted.",
    )
    parser.add_argument("--std-value", type=float, default=0.15, help="Internal standard deviation scale.")
    parser.add_argument("--top-offset", type=float, default=0.35, help="Top-band offset for two-tier means.")
    parser.add_argument(
        "--randomise-arms",
        action="store_true",
        help="Shuffle the internally generated arms so higher indices do not systematically get higher means.",
    )
    parser.add_argument("--init-value", type=float, default=0.5, help="Initial per-arm estimate.")
    parser.add_argument("--epsilon", type=float, default=0.1, help="Base epsilon for epsilon-greedy.")
    parser.add_argument("--epsilon-decay", type=float, default=0.0, help="Power-law epsilon decay.")
    parser.add_argument("--epsilon-min", type=float, default=0.01, help="Minimum epsilon.")
    parser.add_argument("--exploration-bonus", type=float, default=2.0, help="UCB exploration multiplier.")


def build_config(args: argparse.Namespace) -> SimulationConfig:
    means, stds = _reward_vectors(args)
    return SimulationConfig(
        arms=args.arms,
        players=args.players,
        exploration_cycles=args.exploration_cycles,
        strategy_steps=args.strategy_steps,
        seed=args.seed,
        learner=args.learner,
        mean_profile="explicit" if means is not None else args.mean_profile,
        std_profile="explicit" if stds is not None else args.std_profile,
        reward_means=means,
        reward_stds=stds,
        mean_low=args.mean_low,
        mean_high=args.mean_high,
        std_value=args.std_value,
        top_offset=args.top_offset,
        randomise_arms=args.randomise_arms,
        reward_distribution=args.reward_distribution,
        collision_rule="split",
        init_value=args.init_value,
        epsilon=args.epsilon,
        epsilon_decay=args.epsilon_decay,
        epsilon_min=args.epsilon_min,
        exploration_bonus=args.exploration_bonus,
    )


def print_summary(summary: Dict[str, float]) -> None:
    for key in [
        "rho",
        "mean_reward_average",
        "efficiency_average",
        "occupancy_variance_average",
        "player_reward_variance_average",
        "cumulative_regret_final",
        "late_regret_rate",
    ]:
        print(f"{key:>28}: {summary[key]:.6f}")


def _default_run_log_path(args: argparse.Namespace) -> Path | None:
    if getattr(args, "run_log", None):
        return Path(args.run_log)
    if getattr(args, "plot_prefix", None):
        return Path(f"{args.plot_prefix}_run.log")
    if getattr(args, "summary_json", None):
        return Path(args.summary_json).with_suffix(".log")
    return None


def write_run_log(path: Path, result) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best_idx = max(range(len(result.arm_means)), key=lambda idx: result.arm_means[idx])
    worst_idx = min(range(len(result.arm_means)), key=lambda idx: result.arm_means[idx])
    lines = [
        f"arms={result.config.arms}",
        f"players={result.config.players}",
        f"exploration_cycles={result.config.exploration_cycles}",
        f"exploration_steps={result.config.exploration_steps}",
        f"strategy_steps={result.config.strategy_steps}",
        f"total_steps={result.config.total_steps}",
        f"seed={result.config.seed}",
        f"learner={result.config.learner}",
        f"reward_distribution={result.config.reward_distribution}",
        f"rho={result.config.rho:.6f}",
        "",
        f"best_arm_index={best_idx}",
        f"best_arm_mean={result.arm_means[best_idx]:.6f}",
        f"best_arm_std={result.arm_stds[best_idx]:.6f}",
        f"worst_arm_index={worst_idx}",
        f"worst_arm_mean={result.arm_means[worst_idx]:.6f}",
        f"worst_arm_std={result.arm_stds[worst_idx]:.6f}",
        "",
        "arm_table:",
    ]
    for idx, (mean_value, std_value) in enumerate(zip(result.arm_means, result.arm_stds)):
        lines.append(f"  arm={idx:02d} mean={mean_value:.6f} std={std_value:.6f}")
    lines.extend(["", "summary:"])
    lines.extend(f"  {key}={value}" for key, value in result.summary.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_run(args: argparse.Namespace) -> int:
    result = run_simulation(build_config(args))
    print_summary(result.summary)
    if args.summary_json:
        write_summary_json(Path(args.summary_json), result)
    if args.table_prefix:
        for path in write_tables(Path(args.table_prefix), result):
            print(f"wrote table: {path}")
    if args.plot_prefix:
        for path in plot_experiment(Path(args.plot_prefix), result):
            print(f"wrote plot: {path}")
    run_log_path = _default_run_log_path(args)
    if run_log_path is not None:
        write_run_log(run_log_path, result)
        print(f"wrote log: {run_log_path}")
    return 0


def _parse_rho_values(raw: str) -> List[float]:
    return parse_float_list(raw)


def _parse_int_values(raw: str) -> List[int]:
    return [int(value) for value in parse_float_list(raw)]


def _average_rows(rows: List[Dict[str, float]]) -> Dict[str, float]:
    return {key: mean(row[key] for row in rows) for key in rows[0]}


def _collapse_rows_from_result(result, *, epsilon: float, repeat_idx: int) -> List[Dict[str, float]]:
    grouped_estimates: Dict[int, List[Dict[str, float]]] = {}
    for row in result.final_estimate_rows:
        grouped_estimates.setdefault(int(row["player"]), []).append(row)

    arm_to_payoffs: Dict[int, List[float]] = {}
    for player_idx, rows in grouped_estimates.items():
        cumulative_rows = []
        for row in rows:
            cumulative_reward = row["estimated_mean"] * row["samples"]
            cumulative_rows.append((int(row["arm"]), cumulative_reward))
        best_arm, best_payoff = max(cumulative_rows, key=lambda item: (item[1], -item[0]))
        arm_to_payoffs.setdefault(best_arm, []).append(best_payoff)

    collapse_rows: List[Dict[str, float]] = []
    for arm_index, payoffs in sorted(arm_to_payoffs.items()):
        cluster_size = len(payoffs)
        avg_payoff = mean(payoffs)
        sd_payoff = stdev(payoffs) if len(payoffs) >= 2 else 0.0
        collapse_rows.append(
            {
                "value": float(arm_index),
                "m": avg_payoff,
                "s": sd_payoff,
                "n": float(cluster_size),
                "arms": float(result.config.arms),
                "epsilon": epsilon,
                "scaled_1": result.config.arms / epsilon,
                "scaled_2": result.config.arms * epsilon,
                "rho": result.config.players / result.config.arms,
                "arms_over_players": result.config.arms / result.config.players,
                "players_over_epsilon": result.config.players / epsilon,
                "rho_over_epsilon": (result.config.players / result.config.arms) / epsilon,
                "arms_over_players_epsilon": result.config.arms / (result.config.players * epsilon),
                "players": float(result.config.players),
                "repeat": float(repeat_idx),
                "m_per_player": avg_payoff / result.config.players,
                "best_arm_mean": result.summary["best_arm_mean"],
            }
        )
    return collapse_rows


def command_sweep(args: argparse.Namespace) -> int:
    base = build_config(args)
    rho_values = _parse_rho_values(args.rho_values)
    output_rows: List[Dict[str, float]] = []

    for run_index, rho in enumerate(expand_rho_grid(rho_values)):
        players = max(1, round(rho * base.arms))
        repeat_rows: List[Dict[str, float]] = []
        for repeat_idx in range(args.repeats):
            config = replace(base, players=players, seed=base.seed + 10_000 * run_index + repeat_idx)
            result = run_simulation(config)
            row = {"rho_target": rho, "rho_realized": config.rho}
            row.update(result.summary)
            repeat_rows.append(row)
        averaged = _average_rows(repeat_rows)
        output_rows.append(averaged)
        print(
            f"rho={averaged['rho_realized']:.3f} "
            f"reward={averaged['mean_reward_average']:.4f} "
            f"eff={averaged['efficiency_average']:.4f} "
            f"regret_rate={averaged['late_regret_rate']:.4f}"
        )

    if args.sweep_csv:
        write_sweep_csv(Path(args.sweep_csv), output_rows)
    if args.plot_prefix:
        for path in plot_sweep_lines(Path(args.plot_prefix), output_rows):
            print(f"wrote plot: {path}")
    return 0


def command_collapse(args: argparse.Namespace) -> int:
    if args.learner != "epsilon-greedy":
        raise ValueError("collapse is currently defined only for epsilon-greedy, since the scaling variable is arms / epsilon")
    if args.reward_means or args.reward_stds:
        raise ValueError("collapse currently expects internally generated arms; do not pass reward_means or reward_stds")
    arms_values = _parse_int_values(args.arms_values)
    epsilon_values = _parse_rho_values(args.epsilon_values)
    collapse_rows: List[Dict[str, float]] = []

    for arm_index, arms in enumerate(arms_values):
        for epsilon_index, epsilon in enumerate(epsilon_values):
            for repeat_idx in range(args.repeats):
                seed = args.seed + 10_000 * arm_index + 1_000 * epsilon_index + repeat_idx
                config = SimulationConfig(
                    arms=arms,
                    players=args.players,
                    exploration_cycles=args.exploration_cycles,
                    strategy_steps=args.strategy_steps,
                    seed=seed,
                    learner=args.learner,
                    mean_profile=args.mean_profile,
                    std_profile=args.std_profile,
                    reward_means=None,
                    reward_stds=None,
                    mean_low=args.mean_low,
                    mean_high=args.mean_high,
                    std_value=args.std_value,
                    top_offset=args.top_offset,
                    randomise_arms=args.randomise_arms,
                    reward_distribution=args.reward_distribution,
                    collision_rule="split",
                    init_value=args.init_value,
                    epsilon=epsilon,
                    epsilon_decay=args.epsilon_decay,
                    epsilon_min=args.epsilon_min,
                    exploration_bonus=args.exploration_bonus,
                )
                result = run_simulation(config)
                collapse_rows.extend(_collapse_rows_from_result(result, epsilon=epsilon, repeat_idx=repeat_idx))
                print(
                    f"arms={arms:>4} eps={epsilon:>6.3f} repeat={repeat_idx} "
                    f"mean_reward={result.summary['mean_reward_average']:.4f}"
                )

    if args.collapse_csv:
        write_sweep_csv(Path(args.collapse_csv), collapse_rows)
    if args.plot_prefix:
        for path in plot_collapse_panels(Path(args.plot_prefix), collapse_rows):
            print(f"wrote plot: {path}")
    return 0


def command_collapse_ggplot(args: argparse.Namespace) -> int:
    script_path = Path(__file__).with_name("collapse_ggplot.R")
    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Collapse CSV not found: {input_csv}")
    output_prefix = Path(args.output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["Rscript", str(script_path), str(input_csv), str(output_prefix)],
        check=True,
    )
    print(f"wrote ggplot bundle: {output_prefix}_ggplot_bundle.pdf")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="colliding-bandits",
        description="Minimal equal-split colliding bandit simulator.",
        epilog=(
            "By default the arm means/stds are generated internally from --arms and --seed.\n"
            "Run with no arguments to load config/default.json."
        ),
    )
    parser.add_argument("--config", type=str, default=None, help="Optional JSON config file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one simulation.")
    add_common_args(run_parser, require_players=True)
    run_parser.add_argument("--summary-json", type=str, default=None, help="Optional JSON summary output.")
    run_parser.add_argument("--run-log", type=str, default=None, help="Optional plain-text run log.")
    run_parser.add_argument(
        "--table-prefix",
        type=str,
        default=None,
        help="Prefix for CSV tables, e.g. outputs/run gives outputs/run_player_total_reward.csv.",
    )
    run_parser.add_argument(
        "--plot-prefix",
        type=str,
        default=None,
        help="Prefix for experiment PNGs, e.g. outputs/run gives outputs/run_player_total_reward.png.",
    )
    run_parser.set_defaults(func=command_run)

    sweep_parser = subparsers.add_parser("sweep", help="Sweep over rho and save line plots.")
    add_common_args(sweep_parser, require_players=False)
    sweep_parser.add_argument("--rho-values", type=str, required=True, help="Comma-separated rho values with rho = N / K.")
    sweep_parser.add_argument("--repeats", type=int, default=3, help="Number of seeds to average per rho.")
    sweep_parser.add_argument("--sweep-csv", type=str, default=None, help="CSV summary output for the sweep.")
    sweep_parser.add_argument(
        "--plot-prefix",
        type=str,
        default=None,
        help="Prefix for rho-line PNGs, e.g. outputs/sweep gives outputs/sweep_mean_reward_vs_rho.png.",
    )
    sweep_parser.set_defaults(func=command_sweep)

    collapse_parser = subparsers.add_parser("collapse", help="Sweep over arms and epsilon and save scaling-collapse plots.")
    add_common_args(collapse_parser, require_players=True, require_arms=False)
    collapse_parser.add_argument("--arms-values", type=str, required=True, help="Comma-separated K values for the collapse sweep.")
    collapse_parser.add_argument("--epsilon-values", type=str, required=True, help="Comma-separated epsilon values for the collapse sweep.")
    collapse_parser.add_argument("--repeats", type=int, default=3, help="Number of seeds to average per (arms, epsilon) pair.")
    collapse_parser.add_argument("--collapse-csv", type=str, default=None, help="CSV output for the collapse table.")
    collapse_parser.add_argument(
        "--plot-prefix",
        type=str,
        default=None,
        help="Prefix for collapse PNG/PDF plots, e.g. outputs/collapse gives outputs/collapse_scaled.pdf.",
    )
    collapse_parser.set_defaults(func=command_collapse)

    collapse_ggplot_parser = subparsers.add_parser("collapse-ggplot", help="Render collapse CSV with ggplot2.")
    collapse_ggplot_parser.add_argument("--input-csv", type=str, required=True, help="Collapse CSV produced by the collapse command.")
    collapse_ggplot_parser.add_argument("--output-prefix", type=str, required=True, help="Prefix for ggplot outputs.")
    collapse_ggplot_parser.set_defaults(func=command_collapse_ggplot)
    return parser


def _namespace_from_config(parser: argparse.ArgumentParser, config_path: Path) -> argparse.Namespace:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    command = payload.get("command", "run")
    arguments = payload.get("args", {})
    argv: List[str] = [command]
    for key, value in arguments.items():
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                argv.append(flag)
            continue
        argv.extend([flag, str(value)])
    namespace = parser.parse_args(argv)
    namespace.config = str(config_path)
    return namespace


def main() -> int:
    parser = build_parser()
    import sys

    argv = sys.argv[1:]
    if not argv:
        if not DEFAULT_CONFIG_PATH.exists():
            parser.error(f"No CLI args given and default config not found: {DEFAULT_CONFIG_PATH}")
        args = _namespace_from_config(parser, DEFAULT_CONFIG_PATH)
        return args.func(args)

    if argv[0] == "--config":
        if len(argv) < 2:
            parser.error("--config requires a file path")
        config_path = Path(argv[1])
        if not config_path.exists():
            parser.error(f"Config file not found: {config_path}")
        args = _namespace_from_config(parser, config_path)
        return args.func(args)

    args = parser.parse_args(argv)
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            parser.error(f"Config file not found: {config_path}")
        args = _namespace_from_config(parser, config_path)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
