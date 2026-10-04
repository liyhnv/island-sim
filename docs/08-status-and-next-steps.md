# Status and Next Steps (as of 2026-10-04)

## Runs

| Run (log folder) | Simulator | Seed | Status | Use |
|---|---|---|---|---|
| `logs_trial_A`, `logs_A_v1`, `logs_A_broken`, `logs_A_v3_noloans` | v1-v3 | 42 | done | development only |
| `logs_A_v4`, `logs_B_v4` | v4 | 42 | A: 8 weeks. B: stopped in week 7 | pilot, found the v5 bugs |
| `*_v5_partial` | v5 | 42 | stopped at weeks 4 / 3 | development only |
| v6 pilot | v6 | 42 | done | pilot, found the v6.1 and v6.2 bugs |
| A/B-hidden-1 (`A_r2`, `B_r2`) | v6.2 | 43 | stopped after week 5, weeks 1-4 used | main, scores hidden |
| A/B-shown-1 (`A_r2_fb`, `B_r2_fb`) | v7 | 43 | complete | main, scores shown |
| A/B-hidden-2 (`A_r3`, `B_r3`) | v7 | 44 | complete | main, scores hidden |
| A/B-shown-2 (`A_r3_fb`, `B_r3_fb`) | v7 | 44 | complete | main, scores shown |

All eight main runs passed every rule check in [`06-validation.md`](06-validation.md). Fallback counts per run are in [`09-results.md`](09-results.md).

## Next steps

1. Read the passages flagged by the keyword proxies and code the stated reasons for every gift, loan offer and refusal. The text measures in `09-results.md` are keyword-based.
2. Run a third replication per cell, to check whether the feedback effect on hunger holds.
3. Publish the raw logs with a data dictionary.
4. Test ways of making talk costly (action before words, reminders of past promises, formal pledges). See [`10-discussion.md`](10-discussion.md).

## Possible extensions

- Repeat one replication pair with a larger or different model, to test how much of the observed behaviour depends on the model.
- An 8-week, two-season version with a rescue announcement, to test the end-game hypothesis (H3) once the typhoon's after-effects can be separated from it.
- An information treatment where food holdings are public versus private.
- A public-goods task (for example, building a boat for rescue) to study free-riding.
