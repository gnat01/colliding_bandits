# How To Run

## Default

Run the default experiment:

```bash
python src/cli.py
```

This loads:

- [config/default.json](/Users/gn/work/learn/python/colliding_bandits/config/default.json)

That config runs:

- `K = 32` arms
- `N = 40` players
- exploration phase: `3` full offset cycles
- strategy phase: `10000` steps
- learner: `epsilon-greedy`
- reward law: `gamma`
- internally generated arm means/stds

If you want the good arms scattered across indices instead of tending to sit at higher indices, set:

- `randomise_arms: true`

in the config, or pass:

```bash
python src/cli.py run ... --randomise-arms
```

## Sweep

Run the `rho = N / K` sweep:

```bash
python src/cli.py --config config/rho_sweep.json
```

This loads:

- [config/rho_sweep.json](/Users/gn/work/learn/python/colliding_bandits/config/rho_sweep.json)

and averages multiple runs at each `rho`.

## Experiment Structure

Each experiment has two phases.

### 1. Exploration phase

Every player cycles through the arms in order, but not all starting at the same arm.

Player `i` starts from offset `i mod K`.

This lasts:

```text
exploration_steps = exploration_cycles * K
```

### 2. Strategy phase

After exploration, each player switches to either:

- `epsilon-greedy`
- `ucb1`

using only their own reward history.

## Rewards

Per arm:

- mean `m_i`
- standard deviation `sd_i`

Reward law:

- `gamma`
- `uniform`

Collision rule:

- equal split only

If `p` players choose arm `a` and the arm reward sample is `r`, each gets:

```text
r / p
```

When means/stds are generated internally, `randomise_arms = false` keeps the current index ordering. `randomise_arms = true` applies one seed-controlled shuffle to the generated arms before the run starts.

## Oracle

The oracle is now the simple hindsight single-player benchmark:

```text
if I knew the best arm, I would always pull it
```

So:

- `best_arm_mean = max_k mu_k`
- oracle mean reward per player = `best_arm_mean`
- oracle total expected reward at time `t` = `N * best_arm_mean`

Per-player regret is measured against repeated pulls of that best arm.

## What Gets Written

For a run with `plot_prefix = outputs/medium_run` and `table_prefix = outputs/medium_run`:

### Summary

- `outputs/medium_run_summary.json`
- `outputs/medium_run_run.log`

### Tables

- `outputs/medium_run_player_total_reward.csv`
- `outputs/medium_run_player_regret.csv`
- `outputs/medium_run_arm_plays.csv`
- `outputs/medium_run_arm_collisions.csv`
- `outputs/medium_run_player_choices.csv`
- `outputs/medium_run_final_estimates.csv`
- `outputs/medium_run_metrics.csv`

### Plots

- `outputs/medium_run_player_total_reward.png`
- `outputs/medium_run_player_regret.png`
- `outputs/medium_run_arm_plays.png`
- `outputs/medium_run_arm_collisions.png`
- `outputs/medium_run_player_choices_heatmap.png`
- `outputs/medium_run_mean_reward.png`
- `outputs/medium_run_mean_regret.png`

All time-series plots include a blue vertical line marking the end of exploration and the start of strategy.

## Smoke-Test Outputs Already Present

Medium run outputs already generated:

- [outputs/medium_run_summary.json](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_summary.json)
- [outputs/medium_run_run.log](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_run.log)
- [outputs/medium_run_player_total_reward.png](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_player_total_reward.png)
- [outputs/medium_run_player_regret.png](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_player_regret.png)
- [outputs/medium_run_arm_plays.png](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_arm_plays.png)
- [outputs/medium_run_arm_collisions.png](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_arm_collisions.png)
- [outputs/medium_run_player_choices_heatmap.png](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_player_choices_heatmap.png)
- [outputs/medium_run_mean_reward.png](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_mean_reward.png)
- [outputs/medium_run_mean_regret.png](/Users/gn/work/learn/python/colliding_bandits/outputs/medium_run_mean_regret.png)

Sweep outputs already generated:

- [outputs/rho_sweep.csv](/Users/gn/work/learn/python/colliding_bandits/outputs/rho_sweep.csv)
- [outputs/rho_sweep_mean_reward_vs_rho.png](/Users/gn/work/learn/python/colliding_bandits/outputs/rho_sweep_mean_reward_vs_rho.png)
- [outputs/rho_sweep_mean_regret_vs_rho.png](/Users/gn/work/learn/python/colliding_bandits/outputs/rho_sweep_mean_regret_vs_rho.png)
- [outputs/rho_sweep_efficiency_vs_rho.png](/Users/gn/work/learn/python/colliding_bandits/outputs/rho_sweep_efficiency_vs_rho.png)
- [outputs/rho_sweep_occupancy_variance_vs_rho.png](/Users/gn/work/learn/python/colliding_bandits/outputs/rho_sweep_occupancy_variance_vs_rho.png)
- [outputs/rho_sweep_late_regret_rate_vs_rho.png](/Users/gn/work/learn/python/colliding_bandits/outputs/rho_sweep_late_regret_rate_vs_rho.png)

## If You Want Your Own Config

Copy one of the config files, edit it, then run:

```bash
python src/cli.py --config your_config.json
```

Config format is documented in:

- [docs/configs.md](/Users/gn/work/learn/python/colliding_bandits/docs/configs.md)
- [docs/outputs.md](/Users/gn/work/learn/python/colliding_bandits/docs/outputs.md)
