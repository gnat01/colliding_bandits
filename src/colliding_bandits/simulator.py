from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
import random
from statistics import mean
from typing import Dict, Iterable, List, Sequence

from .models import RewardArms, RewardConfig


class RunningStats:
    def __init__(self) -> None:
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        if self.count < 2:
            return 0.0
        return self.m2 / (self.count - 1)

    @property
    def std(self) -> float:
        return self.variance ** 0.5


@dataclass
class SimulationConfig:
    arms: int
    players: int
    exploration_cycles: int
    strategy_steps: int
    seed: int = 123
    learner: str = "epsilon-greedy"
    mean_profile: str = "two-tier"
    std_profile: str = "constant"
    reward_means: Sequence[float] | None = None
    reward_stds: Sequence[float] | None = None
    mean_low: float = 0.1
    mean_high: float = 1.0
    std_value: float = 0.15
    top_offset: float = 0.35
    randomise_arms: bool = False
    reward_distribution: str = "gamma"
    collision_rule: str = "split"
    init_value: float = 0.0
    epsilon: float = 0.1
    epsilon_decay: float = 0.0
    epsilon_min: float = 0.01
    exploration_bonus: float = 2.0

    @property
    def rho(self) -> float:
        return self.players / self.arms

    @property
    def exploration_steps(self) -> int:
        return self.exploration_cycles * self.arms

    @property
    def total_steps(self) -> int:
        return self.exploration_steps + self.strategy_steps


@dataclass
class SimulationResult:
    config: SimulationConfig
    arm_means: List[float]
    arm_stds: List[float]
    summary: Dict[str, float]
    player_total_reward_rows: List[Dict[str, float]]
    player_regret_rows: List[Dict[str, float]]
    arm_plays_rows: List[Dict[str, float]]
    arm_collision_rows: List[Dict[str, float]]
    player_choice_rows: List[Dict[str, float]]
    final_estimate_rows: List[Dict[str, float]]
    metric_rows: List[Dict[str, float]]
    player_instant_reward_rows: List[Dict[str, float]]
    arm_realized_reward_rows: List[Dict[str, float]]
    arm_occupancy_rows: List[Dict[str, float]]
    arm_system_reward_rows: List[Dict[str, float]]
    arm_oracle_shortfall_rows: List[Dict[str, float]]
    oracle_trace_rows: List[Dict[str, float]]


def _uniform_choice_among_best(values: Sequence[float], rng: random.Random) -> int:
    best = max(values)
    candidates = [idx for idx, value in enumerate(values) if value == best]
    return rng.choice(candidates)


def _epsilon_greedy_choice(
    stats: Sequence[RunningStats],
    step: int,
    epsilon: float,
    epsilon_decay: float,
    epsilon_min: float,
    rng: random.Random,
) -> int:
    unseen = [idx for idx, stat in enumerate(stats) if stat.count == 0]
    if unseen:
        return rng.choice(unseen)
    current_epsilon = max(epsilon_min, epsilon / ((step + 1) ** epsilon_decay))
    if rng.random() < current_epsilon:
        return rng.randrange(len(stats))
    return _uniform_choice_among_best([stat.mean for stat in stats], rng)


def _ucb1_choice(
    stats: Sequence[RunningStats],
    step: int,
    exploration_bonus: float,
    rng: random.Random,
) -> int:
    unseen = [idx for idx, stat in enumerate(stats) if stat.count == 0]
    if unseen:
        return rng.choice(unseen)
    import math

    log_term = math.log(max(2, step + 1))
    values = []
    for stat in stats:
        bonus = (exploration_bonus * log_term / stat.count) ** 0.5
        values.append(stat.mean + bonus)
    return _uniform_choice_among_best(values, rng)


def _player_choice(
    config: SimulationConfig,
    player_index: int,
    global_step: int,
    stats: Sequence[RunningStats],
    rng: random.Random,
) -> int:
    if global_step < config.exploration_steps:
        return (player_index + global_step) % config.arms
    strategy_step = global_step - config.exploration_steps
    if config.learner == "epsilon-greedy":
        return _epsilon_greedy_choice(
            stats,
            strategy_step,
            config.epsilon,
            config.epsilon_decay,
            config.epsilon_min,
            rng,
        )
    if config.learner == "ucb1":
        return _ucb1_choice(stats, strategy_step, config.exploration_bonus, rng)
    raise ValueError(f"Unknown learner: {config.learner}")


def _best_arm_expected(arm_means: Sequence[float]) -> tuple[int, float]:
    best_idx = max(range(len(arm_means)), key=lambda idx: arm_means[idx])
    return best_idx, arm_means[best_idx]


def _player_rewards(
    raw_rewards: Sequence[float],
    occupancies: Sequence[int],
    choices: Sequence[int],
) -> tuple[List[float], float, List[int]]:
    rewards: List[float] = []
    collision_events = [0 for _ in occupancies]
    for arm_index, occupancy in enumerate(occupancies):
        if occupancy > 1:
            collision_events[arm_index] = 1
    for arm in choices:
        rewards.append(raw_rewards[arm] / occupancies[arm])
    system_reward = sum(raw_rewards[arm_index] for arm_index, occupancy in enumerate(occupancies) if occupancy > 0)
    return rewards, system_reward, collision_events


def run_simulation(config: SimulationConfig) -> SimulationResult:
    base_rng = random.Random(config.seed)
    reward_config = RewardConfig(
        arms=config.arms,
        mean_profile=config.mean_profile,
        std_profile=config.std_profile,
        means=config.reward_means,
        stds=config.reward_stds,
        mean_low=config.mean_low,
        mean_high=config.mean_high,
        std_value=config.std_value,
        top_offset=config.top_offset,
        seed=config.seed,
    )
    arm_means = reward_config.build_means()
    arm_stds = reward_config.build_stds()
    if config.randomise_arms:
        permutation = list(range(config.arms))
        base_rng.shuffle(permutation)
        arm_means = [arm_means[idx] for idx in permutation]
        arm_stds = [arm_stds[idx] for idx in permutation]
    env = RewardArms(arm_means, arm_stds, config.reward_distribution, base_rng)
    player_rngs = [random.Random(config.seed + 10_000 * (idx + 1)) for idx in range(config.players)]
    player_stats = [[RunningStats() for _ in range(config.arms)] for _ in range(config.players)]

    best_arm_index, best_arm_mean = _best_arm_expected(arm_means)
    oracle_mean_expected = best_arm_mean

    player_totals = [0.0 for _ in range(config.players)]
    arm_play_counts = [0 for _ in range(config.arms)]
    arm_collision_counts = [0 for _ in range(config.arms)]
    oracle_player_total = 0.0

    player_total_reward_rows: List[Dict[str, float]] = []
    player_regret_rows: List[Dict[str, float]] = []
    arm_plays_rows: List[Dict[str, float]] = []
    arm_collision_rows: List[Dict[str, float]] = []
    player_choice_rows: List[Dict[str, float]] = []
    metric_rows: List[Dict[str, float]] = []
    player_instant_reward_rows: List[Dict[str, float]] = []
    arm_realized_reward_rows: List[Dict[str, float]] = []
    arm_occupancy_rows: List[Dict[str, float]] = []
    arm_system_reward_rows: List[Dict[str, float]] = []
    arm_oracle_shortfall_rows: List[Dict[str, float]] = []
    oracle_trace_rows: List[Dict[str, float]] = []

    system_rewards: List[float] = []
    mean_player_rewards: List[float] = []
    mean_player_regrets: List[float] = []
    occupancy_variances: List[float] = []
    player_reward_variances: List[float] = []
    efficiencies: List[float] = []
    cumulative_system_regret = 0.0
    cumulative_regret_series: List[float] = []

    for step in range(config.total_steps):
        choices = [
            _player_choice(config, player_idx, step, player_stats[player_idx], player_rngs[player_idx])
            for player_idx in range(config.players)
        ]
        occupancies = [0 for _ in range(config.arms)]
        for arm in choices:
            occupancies[arm] += 1

        raw_rewards = env.sample_rewards()
        oracle_reward_t = raw_rewards[best_arm_index]
        player_rewards, system_reward, collision_events = _player_rewards(raw_rewards, occupancies, choices)
        oracle_player_total += oracle_reward_t
        oracle_total_t = oracle_reward_t * config.players
        cumulative_system_regret += max(0.0, oracle_total_t - system_reward)
        cumulative_regret_series.append(cumulative_system_regret)

        for player_idx, (arm, reward) in enumerate(zip(choices, player_rewards)):
            player_stats[player_idx][arm].update(reward)
            player_totals[player_idx] += reward
            arm_play_counts[arm] += 1

        for arm_index, event in enumerate(collision_events):
            arm_collision_counts[arm_index] += event

        step_index = step + 1
        player_total_row: Dict[str, float] = {"step": float(step_index)}
        player_regret_row: Dict[str, float] = {"step": float(step_index)}
        arm_plays_row: Dict[str, float] = {"step": float(step_index)}
        arm_collision_row: Dict[str, float] = {"step": float(step_index)}
        player_choice_row: Dict[str, float] = {"step": float(step_index)}
        player_instant_reward_row: Dict[str, float] = {"step": float(step_index)}
        arm_realized_reward_row: Dict[str, float] = {"step": float(step_index)}
        arm_occupancy_row: Dict[str, float] = {"step": float(step_index)}
        arm_system_reward_row: Dict[str, float] = {"step": float(step_index)}
        arm_oracle_shortfall_row: Dict[str, float] = {"step": float(step_index)}

        for player_idx, total in enumerate(player_totals):
            player_total_row[f"player_{player_idx}"] = total
            player_regret_row[f"player_{player_idx}"] = oracle_player_total - total
            player_choice_row[f"player_{player_idx}"] = float(choices[player_idx])
            player_instant_reward_row[f"player_{player_idx}"] = player_rewards[player_idx]

        for arm_index in range(config.arms):
            arm_plays_row[f"arm_{arm_index}"] = float(arm_play_counts[arm_index])
            arm_collision_row[f"arm_{arm_index}"] = float(arm_collision_counts[arm_index])
            arm_realized_reward_row[f"arm_{arm_index}"] = raw_rewards[arm_index]
            arm_occupancy_row[f"arm_{arm_index}"] = float(occupancies[arm_index])
            arm_system_reward_row[f"arm_{arm_index}"] = raw_rewards[arm_index] if occupancies[arm_index] > 0 else 0.0
            arm_oracle_shortfall_row[f"arm_{arm_index}"] = oracle_reward_t - raw_rewards[arm_index]

        current_mean_reward = mean(player_rewards)
        current_mean_regret = mean(player_regret_row[f"player_{idx}"] for idx in range(config.players))
        occup_mean = mean(float(value) for value in occupancies)
        current_occupancy_variance = mean((value - occup_mean) ** 2 for value in occupancies)
        rewards_mean = mean(player_rewards)
        current_player_reward_variance = mean((value - rewards_mean) ** 2 for value in player_rewards)
        current_efficiency = 0.0 if oracle_reward_t <= 0 else current_mean_reward / oracle_reward_t

        player_total_reward_rows.append(player_total_row)
        player_regret_rows.append(player_regret_row)
        arm_plays_rows.append(arm_plays_row)
        arm_collision_rows.append(arm_collision_row)
        player_choice_rows.append(player_choice_row)
        player_instant_reward_rows.append(player_instant_reward_row)
        arm_realized_reward_rows.append(arm_realized_reward_row)
        arm_occupancy_rows.append(arm_occupancy_row)
        arm_system_reward_rows.append(arm_system_reward_row)
        arm_oracle_shortfall_rows.append(arm_oracle_shortfall_row)
        metric_rows.append(
            {
                "step": float(step_index),
                "mean_player_reward": current_mean_reward,
                "mean_player_regret": current_mean_regret,
                "system_reward": system_reward,
                "oracle_reward": oracle_reward_t,
                "oracle_mean_expected": oracle_mean_expected,
                "best_arm_index": float(best_arm_index),
                "efficiency": current_efficiency,
                "occupancy_variance": current_occupancy_variance,
                "player_reward_variance": current_player_reward_variance,
                "cumulative_system_regret": cumulative_regret_series[-1],
            }
        )
        oracle_trace_rows.append(
            {
                "step": float(step_index),
                "oracle_reward": oracle_reward_t,
                "oracle_mean_expected": oracle_mean_expected,
                "system_reward": system_reward,
                "system_mean_reward": current_mean_reward,
                "efficiency": current_efficiency,
                "cumulative_system_regret": cumulative_regret_series[-1],
            }
        )

        system_rewards.append(system_reward)
        mean_player_rewards.append(current_mean_reward)
        mean_player_regrets.append(current_mean_regret)
        occupancy_variances.append(current_occupancy_variance)
        player_reward_variances.append(current_player_reward_variance)
        efficiencies.append(current_efficiency)

    final_estimate_rows: List[Dict[str, float]] = []
    for player_idx in range(config.players):
        for arm_index in range(config.arms):
            stat = player_stats[player_idx][arm_index]
            final_estimate_rows.append(
                {
                    "player": float(player_idx),
                    "arm": float(arm_index),
                    "samples": float(stat.count),
                    "estimated_mean": stat.mean,
                    "estimated_std": stat.std,
                }
            )

    late_start = max(0, config.total_steps * 4 // 5)
    late_regret_rate = (
        (cumulative_regret_series[-1] - cumulative_regret_series[late_start]) / (config.total_steps - 1 - late_start)
        if config.total_steps >= 2 and late_start < config.total_steps - 1
        else cumulative_regret_series[-1]
    )

    summary = {
        "rho": config.rho,
        "exploration_steps": float(config.exploration_steps),
        "strategy_steps": float(config.strategy_steps),
        "oracle_mean_expected": oracle_mean_expected,
        "mean_reward_final": mean_player_rewards[-1],
        "mean_reward_average": mean(mean_player_rewards),
        "mean_regret_final": mean_player_regrets[-1],
        "mean_regret_average": mean(mean_player_regrets),
        "system_reward_final": system_rewards[-1],
        "system_reward_average": mean(system_rewards),
        "efficiency_final": efficiencies[-1],
        "efficiency_average": mean(efficiencies),
        "occupancy_variance_final": occupancy_variances[-1],
        "occupancy_variance_average": mean(occupancy_variances),
        "player_reward_variance_final": player_reward_variances[-1],
        "player_reward_variance_average": mean(player_reward_variances),
        "cumulative_regret_final": cumulative_regret_series[-1],
        "late_regret_rate": late_regret_rate,
        "best_arm_index": float(best_arm_index),
        "best_arm_mean": best_arm_mean,
        "worst_arm_index": float(min(range(config.arms), key=lambda idx: arm_means[idx])),
        "worst_arm_mean": min(arm_means),
    }

    return SimulationResult(
        config=config,
        arm_means=arm_means,
        arm_stds=arm_stds,
        summary=summary,
        player_total_reward_rows=player_total_reward_rows,
        player_regret_rows=player_regret_rows,
        arm_plays_rows=arm_plays_rows,
        arm_collision_rows=arm_collision_rows,
        player_choice_rows=player_choice_rows,
        final_estimate_rows=final_estimate_rows,
        metric_rows=metric_rows,
        player_instant_reward_rows=player_instant_reward_rows,
        arm_realized_reward_rows=arm_realized_reward_rows,
        arm_occupancy_rows=arm_occupancy_rows,
        arm_system_reward_rows=arm_system_reward_rows,
        arm_oracle_shortfall_rows=arm_oracle_shortfall_rows,
        oracle_trace_rows=oracle_trace_rows,
    )


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_summary_json(path: Path, result: SimulationResult) -> None:
    ensure_parent_dir(path)
    payload = {
        "config": result.config.__dict__,
        "arm_means": result.arm_means,
        "arm_stds": result.arm_stds,
        "summary": result.summary,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _write_rows_csv(path: Path, rows: Sequence[Dict[str, float]]) -> None:
    ensure_parent_dir(path)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_tables(prefix: Path, result: SimulationResult) -> List[Path]:
    table_specs = [
        ("player_total_reward.csv", result.player_total_reward_rows),
        ("player_instant_reward.csv", result.player_instant_reward_rows),
        ("player_regret.csv", result.player_regret_rows),
        ("arm_realized_rewards.csv", result.arm_realized_reward_rows),
        ("arm_occupancy.csv", result.arm_occupancy_rows),
        ("arm_system_reward.csv", result.arm_system_reward_rows),
        ("arm_oracle_shortfall.csv", result.arm_oracle_shortfall_rows),
        ("arm_plays.csv", result.arm_plays_rows),
        ("arm_collisions.csv", result.arm_collision_rows),
        ("player_choices.csv", result.player_choice_rows),
        ("final_estimates.csv", result.final_estimate_rows),
        ("metrics.csv", result.metric_rows),
        ("oracle_trace.csv", result.oracle_trace_rows),
    ]
    written: List[Path] = []
    for suffix, rows in table_specs:
        path = Path(f"{prefix}_{suffix}")
        _write_rows_csv(path, rows)
        written.append(path)
    return written


def write_sweep_csv(path: Path, rows: Sequence[Dict[str, float]]) -> None:
    _write_rows_csv(path, rows)


def expand_rho_grid(rho_values: Sequence[float]) -> Iterable[float]:
    for rho in rho_values:
        yield rho
