from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import List, Sequence


def parse_float_list(raw: str) -> List[float]:
    return [float(part.strip()) for part in raw.split(",") if part.strip()]


def linspace(start: float, stop: float, count: int) -> List[float]:
    if count <= 1:
        return [float(start)]
    step = (stop - start) / (count - 1)
    return [start + idx * step for idx in range(count)]


@dataclass
class RewardConfig:
    arms: int
    mean_profile: str
    std_profile: str
    means: Sequence[float] | None = None
    stds: Sequence[float] | None = None
    mean_low: float = 0.1
    mean_high: float = 1.0
    std_value: float = 0.15
    top_offset: float = 0.35
    seed: int | None = None

    def build_means(self) -> List[float]:
        rng = random.Random(self.seed)
        if self.means is not None:
            if len(self.means) != self.arms:
                raise ValueError(f"Explicit means length {len(self.means)} does not match arms={self.arms}")
            return [float(value) for value in self.means]
        if self.mean_profile == "explicit":
            raise ValueError("Explicit means were requested but not provided.")

        if self.mean_profile == "linear":
            return linspace(self.mean_low, self.mean_high, self.arms)
        if self.mean_profile == "uniform":
            values = [rng.uniform(self.mean_low, self.mean_high) for _ in range(self.arms)]
            values.sort()
            return values
        if self.mean_profile == "two-tier":
            midpoint = max(1, self.arms // 2)
            low_band = linspace(self.mean_low, max(self.mean_low, self.mean_high - self.top_offset), midpoint)
            top_count = self.arms - midpoint
            top_start = min(self.mean_high, max(self.mean_low, self.mean_high - self.top_offset / 2.0))
            top_band = linspace(top_start, self.mean_high, max(1, top_count))
            return (low_band + top_band)[: self.arms]
        raise ValueError(f"Unknown mean profile: {self.mean_profile}")

    def build_stds(self) -> List[float]:
        if self.stds is not None:
            if len(self.stds) != self.arms:
                raise ValueError(f"Explicit stds length {len(self.stds)} does not match arms={self.arms}")
            return [max(0.0, float(value)) for value in self.stds]
        if self.std_profile == "explicit":
            raise ValueError("Explicit stds were requested but not provided.")

        if self.std_profile == "constant":
            return [max(0.0, self.std_value) for _ in range(self.arms)]
        if self.std_profile == "linear":
            start = max(0.0, self.std_value / 2.0)
            stop = max(start, self.std_value * 1.5)
            return linspace(start, stop, self.arms)
        raise ValueError(f"Unknown std profile: {self.std_profile}")


class RewardArms:
    def __init__(
        self,
        means: Sequence[float],
        stds: Sequence[float],
        distribution: str,
        rng: random.Random,
    ) -> None:
        self.means = list(means)
        self.stds = list(stds)
        self.distribution = distribution
        self.rng = rng

    def sample_rewards(self) -> List[float]:
        rewards: List[float] = []
        for mean, std in zip(self.means, self.stds):
            if std <= 0:
                rewards.append(mean)
                continue

            if self.distribution == "gamma":
                if mean <= 0:
                    raise ValueError("Gamma rewards require mu_k > 0 for all arms.")
                shape = (mean / std) ** 2
                scale = (std**2) / mean
                rewards.append(self.rng.gammavariate(shape, scale))
                continue

            if self.distribution == "uniform":
                half_width = math.sqrt(3.0) * std
                low = mean - half_width
                high = mean + half_width
                rewards.append(self.rng.uniform(low, high))
                continue

            raise ValueError(f"Unknown reward distribution: {self.distribution}")
        return rewards
