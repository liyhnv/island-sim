# Status and Next Steps (as of 2026-10-03)

## Runs

| Run | Simulator | Seed | Status | Use |
|---|---|---|---|---|
| `logs_trial_A`, `logs_A_v1`, `logs_A_broken`, `logs_A_v3_noloans` | v1-v3 | 42 | done | development only |
| `logs_A_v4`, `logs_B_v4` | v4 | 42 | A: 8 weeks; B: stopped in week 7 | pilot; found the v5 bugs |
| `logs_A_r1_v5_partial`, `logs_B_r1_v5_partial` | v5 | 42 | stopped at weeks 4 / 3 | development only |
| `A_r1`, `B_r1` | v6 (+ v6.1 from A week 5 / B week 4) | 42 | complete, 8 weeks | supplementary (see caveats) |
| `A_r2`, `B_r2` | v6.2 | 43 | running | main |
| `A_r3`, `B_r3` | v6.2 | 44 | planned | main |
| `A_r4`, `B_r4` | v6.2 | 45 | if time allows | main |

### Caveats for replication 1

- One duplicate-deal incident (group B, week 3: one intended loan executed three times) before
  the v6.1 fix.
- 18 contact-phase fallbacks (A: 4, B: 14), mostly failed borrowing requests (v6.2 bug). This
  suppresses credit in B more than in A, so replication 1 is not used for the A/B comparison of
  credit and transfers. It can still be used, with care, for measures unaffected by messaging
  (for example, work choices during the typhoon).

## Next steps

1. Finish replications 2 and 3 (and 4 if time allows) on v6.2, checking each with
   `analysis/check_run.py` after the first two weeks and at the end.
2. Analysis code: Gini, transfer matrices, loan terms and catch splits, rating heatmaps,
   life reward per season, persona drift, the say-do gap, and coding of stated reasons.
3. Case studies from the logs (3-4).
4. Write-up: background (AI Town -> island -> Agentopia), design, results by hypothesis,
   mechanism checks, limitations.
5. Publish the logs of all runs, including development runs, with a data dictionary.

## Possible extensions

- Repeat one replication pair with a larger or different model to test how much of the observed
  behaviour depends on the model.
- An information treatment: food holdings public versus private.
- A public-goods task (for example, building a boat for rescue) to study free-riding.
- Information asymmetry: the radio is heard by only one agent.
