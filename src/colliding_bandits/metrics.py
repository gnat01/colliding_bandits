from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List, Sequence


def _variance(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    avg = sum(values) / len(values)
    return sum((value - avg) ** 2 for value in values) / len(values)


@dataclass
class MetricsRecorder:
    players: int
    arms: int
    mean_reward: List[float] = field(default_factory=list)
    system_reward: List[float] = field(default_factory=list)
    oracle_reward: List[float] = field(default_factory=list)
    efficiency: List[float] = field(default_factory=list)
    occupancy_variance: List[float] = field(default_factory=list)
    player_reward_variance: List[float] = field(default_factory=list)
    unique_arm_fraction: List[float] = field(default_factory=list)
    cumulative_regret: List[float] = field(default_factory=list)
    _regret_total: float = 0.0

    def record(
        self,
        rewards: Sequence[float],
        occupancies: Sequence[int],
        system_reward: float,
        oracle_reward: float,
    ) -> None:
        self._regret_total += max(0.0, oracle_reward - system_reward)
        unique_arms = sum(1 for occupancy in occupancies if occupancy > 0)

        self.mean_reward.append(mean(rewards) if rewards else 0.0)
        self.system_reward.append(system_reward)
        self.oracle_reward.append(oracle_reward)
        self.efficiency.append(0.0 if oracle_reward <= 0 else system_reward / oracle_reward)
        self.occupancy_variance.append(_variance([float(value) for value in occupancies]))
        self.player_reward_variance.append(_variance([float(value) for value in rewards]))
        self.unique_arm_fraction.append(unique_arms / self.arms)
        self.cumulative_regret.append(self._regret_total)

    def final_summary(self) -> Dict[str, float]:
        late_start = max(0, len(self.cumulative_regret) * 4 // 5)
        if len(self.cumulative_regret) >= 2 and late_start < len(self.cumulative_regret) - 1:
            regret_rate = (
                self.cumulative_regret[-1] - self.cumulative_regret[late_start]
            ) / (len(self.cumulative_regret) - 1 - late_start)
        else:
            regret_rate = self.cumulative_regret[-1] if self.cumulative_regret else 0.0

        return {
            "mean_reward_final": self.mean_reward[-1] if self.mean_reward else 0.0,
            "mean_reward_average": mean(self.mean_reward) if self.mean_reward else 0.0,
            "system_reward_final": self.system_reward[-1] if self.system_reward else 0.0,
            "system_reward_average": mean(self.system_reward) if self.system_reward else 0.0,
            "oracle_reward_final": self.oracle_reward[-1] if self.oracle_reward else 0.0,
            "oracle_reward_average": mean(self.oracle_reward) if self.oracle_reward else 0.0,
            "efficiency_final": self.efficiency[-1] if self.efficiency else 0.0,
            "efficiency_average": mean(self.efficiency) if self.efficiency else 0.0,
            "occupancy_variance_final": self.occupancy_variance[-1] if self.occupancy_variance else 0.0,
            "occupancy_variance_average": mean(self.occupancy_variance) if self.occupancy_variance else 0.0,
            "player_reward_variance_final": self.player_reward_variance[-1] if self.player_reward_variance else 0.0,
            "player_reward_variance_average": mean(self.player_reward_variance)
            if self.player_reward_variance
            else 0.0,
            "unique_arm_fraction_final": self.unique_arm_fraction[-1] if self.unique_arm_fraction else 0.0,
            "unique_arm_fraction_average": mean(self.unique_arm_fraction) if self.unique_arm_fraction else 0.0,
            "cumulative_regret_final": self.cumulative_regret[-1] if self.cumulative_regret else 0.0,
            "late_regret_rate": regret_rate,
        }
