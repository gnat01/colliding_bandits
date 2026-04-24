# Outputs

## Run Outputs

For `table_prefix = outputs/foo` and `plot_prefix = outputs/foo`:

### Summary

- `outputs/foo_summary.json`
- `outputs/foo_run.log`

### Tables

- `outputs/foo_player_total_reward.csv`
- `outputs/foo_player_instant_reward.csv`
- `outputs/foo_player_regret.csv`
- `outputs/foo_arm_realized_rewards.csv`
- `outputs/foo_arm_occupancy.csv`
- `outputs/foo_arm_system_reward.csv`
- `outputs/foo_arm_oracle_shortfall.csv`
- `outputs/foo_arm_plays.csv`
- `outputs/foo_arm_collisions.csv`
- `outputs/foo_player_choices.csv`
- `outputs/foo_final_estimates.csv`
- `outputs/foo_metrics.csv`
- `outputs/foo_oracle_trace.csv`

### Plots

- `outputs/foo_player_total_reward.png`
- `outputs/foo_player_regret.png`
- `outputs/foo_arm_plays.png`
- `outputs/foo_arm_collisions.png`
- `outputs/foo_player_choices_heatmap.png`
- `outputs/foo_mean_reward.png`
- `outputs/foo_mean_regret.png`

## Sweep Outputs

For `plot_prefix = outputs/rho_sweep`:

- `outputs/rho_sweep.csv`
- `outputs/rho_sweep_mean_reward_vs_rho.png`
- `outputs/rho_sweep_mean_regret_vs_rho.png`
- `outputs/rho_sweep_efficiency_vs_rho.png`
- `outputs/rho_sweep_occupancy_variance_vs_rho.png`
- `outputs/rho_sweep_late_regret_rate_vs_rho.png`

## What The Main Tables Mean

`player_total_reward.csv`
: cumulative reward of each player versus time

`player_instant_reward.csv`
: realized reward of each player at each timestep

`player_regret.csv`
: cumulative regret of each player against repeated pulls of the best arm

`arm_realized_rewards.csv`
: realized reward sample of each arm at each timestep

`arm_occupancy.csv`
: occupancy of each arm at each timestep

`arm_system_reward.csv`
: system reward contribution of each arm at each timestep

`arm_oracle_shortfall.csv`
: difference between best-arm mean and realized arm reward at each timestep

`arm_plays.csv`
: cumulative number of times each arm has been played up to time `t`

`arm_collisions.csv`
: cumulative number of timesteps on which each arm experienced a collision

`player_choices.csv`
: chosen arm of each player at each timestep

`final_estimates.csv`
: final per-player, per-arm estimated mean and estimated standard deviation

`metrics.csv`
: compact mean-level metrics over time

`oracle_trace.csv`
: per-time oracle/system aggregate trace using the best-arm oracle

## What The Main Plots Mean

The blue vertical line marks the end of exploration and the start of strategy.

`player_total_reward.png`
: all players' cumulative reward trajectories

`player_regret.png`
: all players' regret trajectories

`arm_plays.png`
: cumulative arm-play counts

`arm_collisions.png`
: cumulative arm-collision counts

`player_choices_heatmap.png`
: player-by-time choice map

`mean_reward.png`
: mean player reward over time with oracle mean reference

`mean_regret.png`
: mean player regret over time
