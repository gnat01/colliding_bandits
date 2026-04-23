# How To Run

## Model

This is now the stripped-down version:

- `K` arms
- each arm has internally generated `mu_k` and `sd_k`, unless you explicitly override them
- reward law is either `gamma` or `uniform`
- `N` players
- each player uses either `epsilon-greedy` or `ucb1`
- collision rule is equal split:
  - if `n` players choose the same arm and the arm reward is `r`, each gets `r / n`

Each player tracks only their own realized rewards over time.

Main observables:

- cumulative regret over time
- mean reward over time
- efficiency relative to the equal-split oracle
- occupancy variance across arms
- reward variance across players

Main sweep variable:

- `rho = N / K`

## Internal Generation

You do **not** need to type arm means by hand.

By default the simulator can generate arm means/stds internally from:

- `--arms`
- `--seed`
- `--mean-profile`
- `--mean-low`
- `--mean-high`
- `--std-profile`
- `--std-value`
- `--top-offset`

It also writes a plain-text run log with:

- every arm's generated mean and std
- best arm index/mean/std
- worst arm index/mean/std
- summary metrics

If you pass `--plot-prefix outputs/foo`, the log is written automatically to:

- `outputs/foo_run.log`

## Config-First Workflow

This is now the intended way to run things.

Default medium run:

```bash
python src/cli.py
```

This loads:

- [config/default.json](/Users/gn/work/learn/python/colliding_bandits/config/default.json)

Phase-transition sweep:

```bash
python src/cli.py --config config/rho_sweep.json
```

This loads:

- [config/rho_sweep.json](/Users/gn/work/learn/python/colliding_bandits/config/rho_sweep.json)

If you want a custom run, copy one of those JSON files, edit it, and point `--config` at it.

There is a short companion note here:

- [docs/configs.md](/Users/gn/work/learn/python/colliding_bandits/docs/configs.md)

That file explains the config format and the available keys.

## Defaults Worth Remembering

If you do not override them in the config, the internal generator defaults are:

- `mean-profile = two-tier`
- `mean-low = 0.1`
- `mean-high = 1.0`
- `std-profile = constant`
- `std-value = 0.15`
- `top-offset = 0.35`

Sweep default:

- `repeats = 3`

These defaults matter only when you do not pass explicit `reward-means` and `reward-stds`.

## Medium Run

This is the exact medium run command for the simplified idea:

```bash
python src/cli.py run \
  --arms 32 \
  --players 40 \
  --steps 10000 \
  --seed 123 \
  --learner epsilon-greedy \
  --reward-distribution gamma \
  --mean-profile two-tier \
  --mean-low 0.1 \
  --mean-high 1.0 \
  --std-profile constant \
  --std-value 0.15 \
  --top-offset 0.35 \
  --init-value 0.5 \
  --epsilon 0.1 \
  --epsilon-decay 0.05 \
  --epsilon-min 0.01 \
  --summary-json outputs/medium_run_summary.json \
  --time-series-csv outputs/medium_run_timeseries.csv \
  --plot-prefix outputs/medium_run
```

This writes:

- `outputs/medium_run_summary.json`
- `outputs/medium_run_timeseries.csv`
- `outputs/medium_run_run.log`
- `outputs/medium_run_cumulative_regret.png`
- `outputs/medium_run_mean_reward.png`
- `outputs/medium_run_efficiency.png`
- `outputs/medium_run_occupancy_variance.png`
- `outputs/medium_run_player_reward_variance.png`

The run log is important. It records:

- every arm's generated `mu_k`
- every arm's generated `sd_k`
- the best arm
- the worst arm
- the end-of-run summary metrics

## Same Medium Run With UCB

```bash
python src/cli.py run \
  --arms 32 \
  --players 40 \
  --steps 10000 \
  --seed 123 \
  --learner ucb1 \
  --reward-distribution gamma \
  --mean-profile two-tier \
  --mean-low 0.1 \
  --mean-high 1.0 \
  --std-profile constant \
  --std-value 0.15 \
  --top-offset 0.35 \
  --init-value 0.5 \
  --exploration-bonus 2.0 \
  --summary-json outputs/medium_run_ucb_summary.json \
  --time-series-csv outputs/medium_run_ucb_timeseries.csv \
  --plot-prefix outputs/medium_run_ucb
```

## Phase Transition Sweep

The first sweep to look at is mean reward versus `rho`.

Exact command:

```bash
python src/cli.py sweep \
  --arms 20 \
  --steps 4000 \
  --seed 123 \
  --learner epsilon-greedy \
  --reward-distribution gamma \
  --mean-profile two-tier \
  --mean-low 0.1 \
  --mean-high 1.0 \
  --std-profile constant \
  --std-value 0.12 \
  --top-offset 0.35 \
  --init-value 0.5 \
  --epsilon 0.1 \
  --epsilon-decay 0.05 \
  --epsilon-min 0.01 \
  --rho-values 0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0 \
  --repeats 4 \
  --sweep-csv outputs/rho_sweep.csv \
  --plot-prefix outputs/rho_sweep
```

This writes:

- `outputs/rho_sweep.csv`
- `outputs/rho_sweep_mean_reward_vs_rho.png`
- `outputs/rho_sweep_efficiency_vs_rho.png`
- `outputs/rho_sweep_occupancy_variance_vs_rho.png`
- `outputs/rho_sweep_player_reward_variance_vs_rho.png`
- `outputs/rho_sweep_late_regret_rate_vs_rho.png`

These are the first transition/crossover plots to inspect.

Interpretation:

- `mean_reward_vs_rho`: main performance curve
- `efficiency_vs_rho`: how close the system is to the equal-split oracle
- `occupancy_variance_vs_rho`: how unevenly players are distributed over arms
- `player_reward_variance_vs_rho`: inequality across players
- `late_regret_rate_vs_rho`: whether regret is still accumulating significantly late in the run

## Smoke Test Outputs

There are already smoke-test outputs in `outputs/` generated from the simplified model.

Internal-generation single run:

- `outputs/internal_gen_summary.json`
- `outputs/internal_gen_timeseries.csv`
- `outputs/internal_gen_run.log`
- `outputs/internal_gen_cumulative_regret.png`
- `outputs/internal_gen_mean_reward.png`
- `outputs/internal_gen_efficiency.png`
- `outputs/internal_gen_occupancy_variance.png`
- `outputs/internal_gen_player_reward_variance.png`

Config-driven medium run:

- `outputs/medium_run_summary.json`
- `outputs/medium_run_timeseries.csv`
- `outputs/medium_run_run.log`
- `outputs/medium_run_cumulative_regret.png`
- `outputs/medium_run_mean_reward.png`
- `outputs/medium_run_efficiency.png`
- `outputs/medium_run_occupancy_variance.png`
- `outputs/medium_run_player_reward_variance.png`

Config-driven `rho` sweep:

- `outputs/rho_sweep.csv`
- `outputs/rho_sweep_mean_reward_vs_rho.png`
- `outputs/rho_sweep_efficiency_vs_rho.png`
- `outputs/rho_sweep_occupancy_variance_vs_rho.png`
- `outputs/rho_sweep_player_reward_variance_vs_rho.png`
- `outputs/rho_sweep_late_regret_rate_vs_rho.png`

The verified command that produced them:

```bash
python src/cli.py run \
  --arms 20 \
  --players 25 \
  --steps 1000 \
  --seed 123 \
  --learner epsilon-greedy \
  --reward-distribution gamma \
  --mean-profile two-tier \
  --std-profile constant \
  --std-value 0.12 \
  --init-value 0.5 \
  --epsilon 0.1 \
  --epsilon-decay 0.05 \
  --epsilon-min 0.01 \
  --summary-json outputs/internal_gen_summary.json \
  --time-series-csv outputs/internal_gen_timeseries.csv \
  --plot-prefix outputs/internal_gen
```

## What To Look At First

For the `rho` sweep, start with:

1. `mean_reward_vs_rho`
2. `efficiency_vs_rho`
3. `occupancy_variance_vs_rho`
4. `player_reward_variance_vs_rho`
5. `late_regret_rate_vs_rho`

That gives you:

- system performance
- performance relative to oracle
- load-balancing structure
- inequality across players
- whether regret keeps accumulating quickly in the late regime
