from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
import random
from statistics import mean
from typing import Dict, Iterable, List, Sequence

from .learners import build_learners
from .metrics import MetricsRecorder
from .models import RewardArms, RewardConfig


@dataclass
class SimulationConfig:
    arms: int
    players: int
    steps: int
    seed: int = 123
    learner: str = "epsilon-greedy"
    mean_profile: str = "linear"
    std_profile: str = "constant"
    reward_means: Sequence[float] | None = None
    reward_stds: Sequence[float] | None = None
    mean_low: float = 0.1
    mean_high: float = 1.0
    std_value: float = 0.15
    top_offset: float = 0.35
    reward_distribution: str = "gamma"
    collision_rule: str = "split"
    init_value: float = 0.5
    epsilon: float = 0.1
    epsilon_decay: float = 0.0
    epsilon_min: float = 0.01
    exploration_bonus: float = 2.0
    repeats: int = 1

    @property
    def rho(self) -> float:
        return self.players / self.arms


@dataclass
class SimulationResult:
    config: SimulationConfig
    arm_means: List[float]
    arm_stds: List[float]
    summary: Dict[str, float]
    time_series: List[Dict[str, float]]


def _build_time_series(metrics: MetricsRecorder) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for step in range(len(metrics.mean_reward)):
        rows.append(
            {
                "step": float(step),
                "mean_reward": metrics.mean_reward[step],
                "system_reward": metrics.system_reward[step],
                "oracle_reward": metrics.oracle_reward[step],
                "efficiency": metrics.efficiency[step],
                "occupancy_variance": metrics.occupancy_variance[step],
                "player_reward_variance": metrics.player_reward_variance[step],
                "unique_arm_fraction": metrics.unique_arm_fraction[step],
                "cumulative_regret": metrics.cumulative_regret[step],
            }
        )
    return rows


def _oracle_reward(raw_rewards: Sequence[float], players: int, arms: int) -> float:
    usable = min(players, arms)
    return sum(sorted(raw_rewards, reverse=True)[:usable])


def _player_rewards(
    raw_rewards: Sequence[float],
    occupancies: Sequence[int],
    choices: Sequence[int],
    collision_rule: str,
) -> tuple[List[float], float]:
    rewards: List[float] = []
    if collision_rule == "split":
        for arm in choices:
            occupancy = occupancies[arm]
            rewards.append(raw_rewards[arm] / occupancy)
        system_reward = sum(raw_rewards[arm_idx] for arm_idx, occupancy in enumerate(occupancies) if occupancy > 0)
        return rewards, system_reward

    if collision_rule == "hard":
        for arm in choices:
            occupancy = occupancies[arm]
            rewards.append(raw_rewards[arm] if occupancy == 1 else 0.0)
        system_reward = sum(raw_rewards[arm_idx] for arm_idx, occupancy in enumerate(occupancies) if occupancy == 1)
        return rewards, system_reward

    raise ValueError(f"Unknown collision rule: {collision_rule}")


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
    env = RewardArms(arm_means, arm_stds, config.reward_distribution, base_rng)
    learners = build_learners(
        learner_kind=config.learner,
        players=config.players,
        arms=config.arms,
        seed=config.seed,
        init_value=config.init_value,
        epsilon=config.epsilon,
        epsilon_decay=config.epsilon_decay,
        epsilon_min=config.epsilon_min,
        exploration_bonus=config.exploration_bonus,
    )
    metrics = MetricsRecorder(players=config.players, arms=config.arms)

    for step in range(config.steps):
        choices = [learner.select_arm(step) for learner in learners]
        occupancies = [0 for _ in range(config.arms)]
        for arm in choices:
            occupancies[arm] += 1

        raw_rewards = env.sample_rewards()
        player_rewards, system_reward = _player_rewards(raw_rewards, occupancies, choices, config.collision_rule)
        oracle_reward = _oracle_reward(raw_rewards, config.players, config.arms)

        for learner, arm, reward in zip(learners, choices, player_rewards):
            learner.update(arm, reward)

        metrics.record(
            rewards=player_rewards,
            occupancies=occupancies,
            system_reward=system_reward,
            oracle_reward=oracle_reward,
        )

    summary = metrics.final_summary()
    summary.update(
        {
            "arms": float(config.arms),
            "players": float(config.players),
            "steps": float(config.steps),
            "rho": config.rho,
            "mean_arm_mean": mean(arm_means),
            "best_arm_mean": max(arm_means),
            "worst_arm_mean": min(arm_means),
            "mean_arm_std": mean(arm_stds),
        }
    )
    return SimulationResult(
        config=config,
        arm_means=arm_means,
        arm_stds=arm_stds,
        summary=summary,
        time_series=_build_time_series(metrics),
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


def write_time_series_csv(path: Path, time_series: Sequence[Dict[str, float]]) -> None:
    ensure_parent_dir(path)
    if not time_series:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(time_series[0].keys()))
        writer.writeheader()
        writer.writerows(time_series)


def write_sweep_csv(path: Path, rows: Sequence[Dict[str, float]]) -> None:
    ensure_parent_dir(path)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def expand_rho_grid(rho_values: Sequence[float]) -> Iterable[float]:
    for rho in rho_values:
        yield rho
