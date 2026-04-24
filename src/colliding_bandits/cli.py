from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from statistics import mean
from typing import Dict, List

from .models import parse_float_list
from .plotting import plot_experiment, plot_sweep_lines
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


def add_common_args(parser: argparse.ArgumentParser, *, require_players: bool) -> None:
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


def _average_rows(rows: List[Dict[str, float]]) -> Dict[str, float]:
    return {key: mean(row[key] for row in rows) for key in rows[0]}


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
