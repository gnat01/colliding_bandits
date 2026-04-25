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

## Scaling Collapse

Run the old-style scaling-collapse sweep:

```bash
python src/cli.py --config config/collapse_sweep.json
```

This loads:

- [config/collapse_sweep.json](/Users/gn/work/learn/python/colliding_bandits/config/collapse_sweep.json)

and sweeps over:

- `arms_values`
- `epsilon_values`
- multiple seeds per pair

then groups players by their learned best arm at the end of the run and writes the collapse table plus faceted PNG/PDF plots.

To render the same collapse table with `ggplot2` instead of `matplotlib`:

```bash
python src/cli.py --config config/collapse_ggplot.json
```

This reads:

- `outputs/collapse_sweep.csv`

and writes `ggplot2` outputs with the same panel logic.

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
- `outputs/medium_run_player_instant_reward.csv`
- `outputs/medium_run_player_regret.csv`
- `outputs/medium_run_arm_realized_rewards.csv`
- `outputs/medium_run_arm_occupancy.csv`
- `outputs/medium_run_arm_system_reward.csv`
- `outputs/medium_run_arm_oracle_shortfall.csv`
- `outputs/medium_run_arm_plays.csv`
- `outputs/medium_run_arm_collisions.csv`
- `outputs/medium_run_player_choices.csv`
- `outputs/medium_run_final_estimates.csv`
- `outputs/medium_run_metrics.csv`
- `outputs/medium_run_oracle_trace.csv`

### Plots

- `outputs/medium_run_player_total_reward.png`
- `outputs/medium_run_player_total_reward.pdf`
- `outputs/medium_run_player_regret.png`
- `outputs/medium_run_player_regret.pdf`
- `outputs/medium_run_arm_plays.png`
- `outputs/medium_run_arm_plays.pdf`
- `outputs/medium_run_arm_collisions.png`
- `outputs/medium_run_arm_collisions.pdf`
- `outputs/medium_run_arm_occupancy.png`
- `outputs/medium_run_arm_occupancy.pdf`
- `outputs/medium_run_player_choices_heatmap.png`
- `outputs/medium_run_player_choices_heatmap.pdf`
- `outputs/medium_run_arm_occupancy_heatmap.png`
- `outputs/medium_run_arm_occupancy_heatmap.pdf`
- `outputs/medium_run_arm_occupancy_histogram.gif`
- `outputs/medium_run_mean_reward.png`
- `outputs/medium_run_mean_reward.pdf`
- `outputs/medium_run_mean_regret.png`
- `outputs/medium_run_mean_regret.pdf`
- `outputs/medium_run_oracle_trace_panel.png`
- `outputs/medium_run_oracle_trace_panel.pdf`

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

Collapse outputs already generated:

- [outputs/collapse_sweep.csv](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep.csv)
- [outputs/collapse_sweep_collapse_by_epsilon.png](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_by_epsilon.png)
- [outputs/collapse_sweep_collapse_by_epsilon.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_by_epsilon.pdf)
- [outputs/collapse_sweep_collapse_by_arms.png](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_by_arms.png)
- [outputs/collapse_sweep_collapse_by_arms.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_by_arms.pdf)
- [outputs/collapse_sweep_collapse_scaled.png](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled.png)
- [outputs/collapse_sweep_collapse_scaled.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled.pdf)
- [outputs/collapse_sweep_collapse_scaled_per_player.png](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled_per_player.png)
- [outputs/collapse_sweep_collapse_scaled_per_player.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled_per_player.pdf)

GGPlot collapse outputs:

- [outputs/collapse_sweep_collapse_by_epsilon_ggplot.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_by_epsilon_ggplot.pdf)
- [outputs/collapse_sweep_collapse_by_arms_ggplot.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_by_arms_ggplot.pdf)
- [outputs/collapse_sweep_collapse_scaled_ggplot.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled_ggplot.pdf)
- [outputs/collapse_sweep_collapse_scaled_per_player_ggplot.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled_per_player_ggplot.pdf)
- [outputs/collapse_sweep_collapse_scaled_binned_ggplot.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled_binned_ggplot.pdf)
- [outputs/collapse_sweep_collapse_scaled_per_player_binned_ggplot.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_collapse_scaled_per_player_binned_ggplot.pdf)
- [outputs/collapse_sweep_ggplot_bundle.pdf](/Users/gn/work/learn/python/colliding_bandits/outputs/collapse_sweep_ggplot_bundle.pdf)

## If You Want Your Own Config

Copy one of the config files, edit it, then run:

```bash
python src/cli.py --config your_config.json
```

Config format is documented in:

- [docs/configs.md](/Users/gn/work/learn/python/colliding_bandits/docs/configs.md)
- [docs/outputs.md](/Users/gn/work/learn/python/colliding_bandits/docs/outputs.md)
