from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import List, Sequence


def _argmax_with_random_tiebreak(values: Sequence[float], rng: random.Random) -> int:
    max_value = max(values)
    indices = [idx for idx, value in enumerate(values) if value == max_value]
    return rng.choice(indices)


@dataclass
class BaseLearner:
    arms: int
    rng: random.Random
    init_value: float = 0.5
    counts: List[int] = field(init=False)
    estimates: List[float] = field(init=False)
    last_choice: int | None = field(default=None, init=False)
    streak_length: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.counts = [0 for _ in range(self.arms)]
        self.estimates = [float(self.init_value) for _ in range(self.arms)]

    def select_arm(self, step: int) -> int:
        raise NotImplementedError

    def update(self, arm: int, observation: float) -> None:
        self.counts[arm] += 1
        count = self.counts[arm]
        estimate = self.estimates[arm]
        self.estimates[arm] = estimate + (observation - estimate) / count
        if self.last_choice == arm:
            self.streak_length += 1
        else:
            self.last_choice = arm
            self.streak_length = 1


@dataclass
class EpsilonGreedyLearner(BaseLearner):
    epsilon: float = 0.1
    epsilon_decay: float = 0.0
    epsilon_min: float = 0.0

    def select_arm(self, step: int) -> int:
        epsilon = max(self.epsilon_min, self.epsilon / ((step + 1) ** self.epsilon_decay))
        unseen = [idx for idx, count in enumerate(self.counts) if count == 0]
        if unseen:
            return self.rng.choice(unseen)
        if self.rng.random() < epsilon:
            return self.rng.randrange(self.arms)
        return _argmax_with_random_tiebreak(self.estimates, self.rng)


@dataclass
class UCB1Learner(BaseLearner):
    exploration_bonus: float = 2.0

    def select_arm(self, step: int) -> int:
        unseen = [idx for idx, count in enumerate(self.counts) if count == 0]
        if unseen:
            return self.rng.choice(unseen)
        log_term = math.log(max(2, step + 1))
        scores = []
        for idx, estimate in enumerate(self.estimates):
            bonus = math.sqrt(self.exploration_bonus * log_term / self.counts[idx])
            scores.append(estimate + bonus)
        return _argmax_with_random_tiebreak(scores, self.rng)


def build_learners(
    learner_kind: str,
    players: int,
    arms: int,
    seed: int,
    init_value: float,
    epsilon: float,
    epsilon_decay: float,
    epsilon_min: float,
    exploration_bonus: float,
) -> List[BaseLearner]:
    learners: List[BaseLearner] = []
    for player_idx in range(players):
        rng = random.Random(seed + 10_000 * (player_idx + 1))
        if learner_kind == "epsilon-greedy":
            learner = EpsilonGreedyLearner(
                arms=arms,
                rng=rng,
                init_value=init_value,
                epsilon=epsilon,
                epsilon_decay=epsilon_decay,
                epsilon_min=epsilon_min,
            )
        elif learner_kind == "ucb1":
            learner = UCB1Learner(
                arms=arms,
                rng=rng,
                init_value=init_value,
                exploration_bonus=exploration_bonus,
            )
        else:
            raise ValueError(f"Unknown learner kind: {learner_kind}")
        learners.append(learner)
    return learners
