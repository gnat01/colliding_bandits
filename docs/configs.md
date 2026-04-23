# Config Files

## Purpose

The intended workflow is config-first:

- `python src/cli.py` loads `config/default.json`
- `python src/cli.py --config config/rho_sweep.json` loads that sweep config

This avoids giant multi-line shell commands.

## Structure

Each config file is a JSON object with:

```json
{
  "command": "run",
  "args": {
    "...": "..."
  }
}
```

`command` is either:

- `run`
- `sweep`

`args` contains the CLI arguments, but written as JSON keys.

Example:

```json
{
  "command": "run",
  "args": {
    "arms": 32,
    "players": 40,
    "steps": 10000,
    "seed": 123,
    "learner": "epsilon-greedy",
    "reward_distribution": "gamma",
    "mean_profile": "two-tier",
    "plot_prefix": "outputs/medium_run"
  }
}
```

## Keys For `run`

Core:

- `arms`
- `players`
- `steps`
- `seed`
- `learner`
- `reward_distribution`

Internal arm generator:

- `mean_profile`
- `mean_low`
- `mean_high`
- `std_profile`
- `std_value`
- `top_offset`

Learner knobs:

- `init_value`
- `epsilon`
- `epsilon_decay`
- `epsilon_min`
- `exploration_bonus`

Optional explicit override:

- `reward_means`
- `reward_stds`

Outputs:

- `summary_json`
- `time_series_csv`
- `plot_prefix`
- `run_log`

## Keys For `sweep`

Everything above except `players`, plus:

- `rho_values`
- `repeats`
- `sweep_csv`
- `plot_prefix`

In a sweep, players are derived from:

```text
players = round(rho * arms)
```

for each `rho` value.

## Existing Configs

Default medium run:

- [config/default.json](/Users/gn/work/learn/python/colliding_bandits/config/default.json)

Load sweep:

- [config/rho_sweep.json](/Users/gn/work/learn/python/colliding_bandits/config/rho_sweep.json)

## Recommended Workflow

1. Copy one of the existing config files.
2. Edit just the values you care about.
3. Run with `python src/cli.py --config your_file.json`.

That is the intended way to operate this repo now.
