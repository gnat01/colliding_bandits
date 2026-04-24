# Config Files

## Shape

Each config file is JSON:

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
- `collapse`

## Default Files

- [config/default.json](/Users/gn/work/learn/python/colliding_bandits/config/default.json)
- [config/rho_sweep.json](/Users/gn/work/learn/python/colliding_bandits/config/rho_sweep.json)
- [config/collapse_sweep.json](/Users/gn/work/learn/python/colliding_bandits/config/collapse_sweep.json)

## Keys For `run`

Core:

- `arms`
- `players`
- `exploration_cycles`
- `strategy_steps`
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
- `randomise_arms`

Optional explicit override:

- `reward_means`
- `reward_stds`

Learner controls:

- `epsilon`
- `epsilon_decay`
- `epsilon_min`
- `exploration_bonus`

Outputs:

- `summary_json`
- `table_prefix`
- `plot_prefix`
- `run_log`

## Keys For `sweep`

Same generator / learner keys as `run`, but:

- no fixed `players`
- use `rho_values`
- use `repeats`
- use `sweep_csv`
- use `plot_prefix`

For each `rho`:

```text
players = round(rho * arms)
```

## Keys For `collapse`

Same generator / learner keys as `run`, but:

- fixed `players`
- use `arms_values`
- use `epsilon_values`
- use `repeats`
- use `collapse_csv`
- use `plot_prefix`

This mode is currently intended for `epsilon-greedy`, because the scaling variable is:

```text
scaled_1 = arms / epsilon
```

## Intended Workflow

Medium run:

```bash
python src/cli.py
```

Sweep:

```bash
python src/cli.py --config config/rho_sweep.json
```

Scaling collapse:

```bash
python src/cli.py --config config/collapse_sweep.json
```

## `randomise_arms`

- `false`: keep the current generated ordering, so with profiles like `linear` or `two-tier` the higher-index arms can systematically have higher means
- `true`: apply a seed-controlled permutation to the generated arms before the run starts, so arm index no longer leaks that ordering
