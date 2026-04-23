# Colliding Bandits as Statistical Physics

## Starting Point

The usual multiplayer multi-armed bandit literature asks for regret bounds under decentralized learning with collisions. That is not the main angle here.

The more interesting object is the collective dynamics: many noisy learners competing for a finite set of arms, with collisions acting as an interaction. Players are particles, arms are sites or energy wells, rewards are quenched disorder, and the learning rule creates a time-dependent effective potential landscape. The goal is to study ordering, jamming, freezing, metastability, and scaling rather than only regret.

In this view, multiplayer bandits are a disordered interacting particle system with adaptive microscopic rules.

## Physical Picture

At each time step:

- `N` players choose among `K` arms.
- Each arm has an intrinsic quality or reward parameter `mu_k`.
- Multiple players choosing the same arm experience congestion or collision.
- Players update their beliefs using only local observations.
- Exploration noise, memory, and reward ambiguity determine whether the system settles, wanders, or jams.

The central question is not only whether players learn the top arms, but whether the system self-organizes into a low-collision ordered allocation, and how that transition depends on load, reward disorder, information, and learning temperature.

## Candidate Phases

The natural phase diagram should include at least:

- **Fluid / wandering phase:** players continue exploring, switching, and colliding; no stable allocation persists.
- **Ordered / orthogonal phase:** players settle onto distinct high-reward arms with low collision density.
- **Jammed phase:** too many players, too little information, or weak repulsion creates persistent collisions.
- **Glassy / metastable phase:** many near-stable allocations exist; dynamics shows history dependence, long relaxation times, aging, and hysteresis.
- **Condensed phase:** many players cluster around a small number of high-reward arms despite collision costs.
- **Critical boundary:** the transition region between search and locking, where relaxation times and fluctuations may show scaling laws.

The classic Musical Chairs algorithm is an engineered absorbing-state process. More interesting physical dynamics appear when collision avoidance is not hard-coded, but emerges from noisy local reward learning.

## Collision Channel

The collision rule should be parameterized rather than fixed to the standard bandit convention.

A useful general model is:

```text
r_i(t) = X_a(t) * g(n_a(t)) + noise
```

where:

- `a` is the arm chosen by player `i`,
- `X_a(t)` is the arm's stochastic reward,
- `n_a(t)` is the number of players choosing arm `a`,
- `g(n)` is a congestion kernel.

Important kernels:

- **Hard exclusion:** `g(1) = 1`, `g(n >= 2) = 0`. This is the classic collision bandit.
- **Shared reward:** `g(n) = 1 / n`. Total site reward is conserved and split among occupants.
- **Power-law congestion:** `g(n) = n^(-alpha)`. This interpolates between weak congestion and hard exclusion.
- **Exponential congestion:** `g(n) = exp(-beta * (n - 1))`. This gives a smooth interaction-strength parameter.
- **Threshold capacity:** `g(n) = 1` for `n <= q`, then decays or drops for `n > q`.

For phase-transition work, `alpha`, `beta`, or `q` become control parameters.

## Observation Channel

Reward loss and collision observability should be separate. The true payoff may depend on occupancy, but the player should not necessarily observe that occupancy.

Useful feedback classes:

- **Full occupancy:** player observes `n_a(t)`.
- **Binary collision:** player observes only whether `n_a(t) > 1`.
- **Censored reward only:** player observes only their realized reward, so they cannot distinguish a bad arm from a crowded arm.
- **Noisy aggregate:** player receives a degraded signal statistically related to congestion but not exactly revealing it.

The richest starting point is likely hidden or partially shaded congestion:

```text
r_i(t) ~ Bernoulli(mu_a / n_a(t)^alpha)
```

or:

```text
r_i(t) ~ Bernoulli(mu_a * exp(-beta * (n_a(t) - 1)))
```

with players observing only their own reward. This creates the key ambiguity: "is this arm bad, or am I sharing it?" That ambiguity is likely where metastability and nontrivial scaling appear.

## Control Parameters

The likely relevant variables are:

- `rho = N / K`, the player-to-arm load.
- Reward disorder, especially the gap distribution near the best arms.
- Collision interaction strength, e.g. `alpha` or `beta`.
- Exploration temperature or exploration decay schedule.
- Memory depth or learning rate.
- Feedback class: full collision information, binary collision, or reward-only censoring.
- Arm capacity or degeneracy.

Likely less relevant variables, at least away from criticality:

- Exact reward distribution far below the top arms.
- Precise implementation details of UCB versus Thompson sampling, once reduced to an effective exploration temperature.
- Microscopic tie-breaking rules.

The conjecture is that multiplayer bandit learning has universality classes classified by feedback model, collision kernel, and exploration cooling schedule, not by the exact algorithm.

## Renormalization View

The natural Wilsonian question is whether a coarse-graining map exists:

```text
(K, N, reward gaps, learning rate, exploration noise, horizon)
        -> R_b
(K / b, N / b, renormalized disorder, renormalized noise, renormalized interaction)
```

Arms can be grouped into blocks, agents into effective densities, and fast collision-learning dynamics integrated out. Fixed points would correspond to phases: diffusive exploration, ordered orthogonal occupation, jammed collision, and glassy metastability.

The Feigenbaumian question is whether there are universal scaling ratios near bifurcations or cascade-like transitions in the learning dynamics. Potential examples:

- Periodic collision cycles as exploration decay is tuned.
- Abrupt changes in settling behavior as load crosses a threshold.
- Repeated splitting of basins of attraction in deterministic or low-noise limits.
- Universal ratios in relaxation-time peaks under parameter refinement.

The Wilsonian route is probably the broader first target; the Feigenbaumian route becomes attractive if simulations reveal bifurcation cascades or discrete scale invariance.

## Observables

Regret can be recorded, but it should not be the primary observable.

Primary observables:

- Collision density `c(t)`.
- Occupation entropy across arms.
- Fraction of frozen or persistent players.
- Mean residence time on an arm.
- Cluster-size distribution of arm occupancies.
- Settling time or relaxation time `tau`.
- Autocorrelation of player choices.
- Hysteresis under slow sweeps of `rho`, `alpha`, `beta`, or exploration temperature.
- Distribution of lifetimes of metastable states.

Derived observables:

- Regret density.
- Reward inequality across players.
- Fraction of optimal arms occupied.
- Distance from an ideal orthogonal allocation.

## First Simulation Program

Start with the minimal model:

- `K` arms with fixed Bernoulli means `mu_k`.
- `N` players.
- Reward-only feedback.
- Congestion kernel `g(n) = n^(-alpha)` or `g(n) = exp(-beta * (n - 1))`.
- Simple learner: epsilon-greedy or softmax over empirical reward estimates.
- Exploration schedule controlled by temperature or decay exponent.

Sweep:

- `rho = N / K`.
- `alpha` or `beta`.
- reward gap scale.
- exploration temperature / cooling exponent.
- memory depth.

Measure:

- collision density over time,
- final occupation entropy,
- relaxation time,
- frozen fraction,
- cluster-size distribution.

Look for:

- curve collapse under rescaling of `K` and `N`,
- critical slowing down near ordering/jamming boundaries,
- hysteresis under parameter sweeps,
- sensitivity to initial conditions,
- bifurcation-like collision cycles.

## Coding Priorities

The first code should be a simulator, not an algorithm benchmark.

Recommended first modules:

- Environment with pluggable reward distribution and congestion kernel.
- Player policies: epsilon-greedy, softmax, UCB-like, Thompson-like.
- Observation channels: reward-only, binary collision, full occupancy.
- Metrics recorder for collision density, entropy, residence times, and occupancy histograms.
- Sweep runner for phase diagrams.
- Plotting utilities for time series and heatmaps.

The first concrete experiment should be:

```text
fixed K, vary rho and alpha, reward-only feedback, softmax learners
```

and plot collision density, frozen fraction, and occupation entropy. If there is a sharp boundary, the next step is finite-size scaling over `K`.
