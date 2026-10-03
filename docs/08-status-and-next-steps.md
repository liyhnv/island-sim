# Status and Next Steps (as of 2026-10-03)

## Runs

| Run | Simulator | Seed | Status | Use |
|---|---|---|---|---|
| `logs_trial_A`, `logs_A_v1`, `logs_A_broken`, `logs_A_v3_noloans` | v1-v3 | 42 | done | development only |
| `logs_A_v4`, `logs_B_v4` | v4 | 42 | A: 8 weeks; B: stopped in week 7 | pilot; found the v5 bugs |
| `*_v5_partial` | v5 | 42 | stopped at weeks 4 / 3 | development only |
| v6 pilot | v6 | 42 | done | pilot; found the v6.1 and v6.2 bugs |
| `A_r2`, `B_r2` | v6.2 | 43 | stopped after week 5; weeks 1-4 used | main, no feedback |
| `A_r2_fb`, `B_r2_fb` | v7 | 43 | running | main, feedback |
| `A_r3_fb`, `B_r3_fb` | v7 | 44 | planned | main, feedback |
| `A_r3`, `B_r3` | v7 | 44 | if time allows | main, no feedback |

`A_r2` and `B_r2` passed every check in [`06-validation.md`](06-validation.md) with no fallbacks.

## Next steps

1. Finish the feedback runs (replications 2 and 3), checking each with `analysis/check_run.py`
   after the first two weeks and at the end.
2. If time allows, a second no-feedback pair (seed 44).
3. Analysis with `analysis/analyze.py` plus coding of stated reasons; figures as listed in
   [`04-experiment-design.md`](04-experiment-design.md).
4. Case studies from the logs (3-4).
5. Write-up: background (AI Town -> island -> Agentopia), design, results by hypothesis,
   mechanism checks, limitations.
6. Publish the logs of all runs, including development runs, with a data dictionary.

## Possible extensions

- Repeat one replication pair with a larger or different model to test how much of the observed
  behaviour depends on the model.
- An 8-week, two-season version with a rescue announcement, to test the end-game hypothesis (H3)
  once the typhoon's after-effects can be separated from it.
- An information treatment: food holdings public versus private.
- A public-goods task (for example, building a boat for rescue) to study free-riding.
