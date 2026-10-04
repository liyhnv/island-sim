# Results

Eight runs, four weeks each, on simulator v6.2 / v7 (see [`04-experiment-design.md`](04-experiment-design.md)):

| | Group A (individualist) | Group B (reputation) |
|---|---|---|
| Scores hidden | `A-hidden-1` (seed 43), `A-hidden-2` (seed 44) | `B-hidden-1`, `B-hidden-2` |
| Scores shown | `A-shown-1` (seed 43), `A-shown-2` (seed 44) | `B-shown-1`, `B-shown-2` |

Runs are labelled *group-condition-replication*. Runs with the same replication number share a seed, so A and B face the same luck. (Log folders keep the names given by `run.py`. Replication 1 is `--run 2`, e.g. `logs/B_r2_fb`, and replication 2 is `--run 3`. `--run 1` was the v6 pilot.)

Every run passed all rule checks in [`06-validation.md`](06-validation.md). With two runs per cell, I report results as **directions that hold in both replications** and their size, not as significance tests. I treat a difference that appears in only one replication as noise.

Interactive dashboard: [Tableau Public](https://public.tableau.com/app/profile/yihan.li4388/viz/IslandSurvivalIncentives/IslandSurvivalOverview).
All numbers below can be reproduced with `analysis/export_tables.py` and the queries in `analysis/sql/`.

![Dashboard, scores hidden](../results/figures/dashboard_scores_hidden.png)
![Dashboard, scores shown](../results/figures/dashboard_scores_shown.png)

## Summary

| Question | Answer | Holds in |
|---|---|---|
| H1a: Does B share more? | Yes, modestly: 4.5 vs 1.75 units given across households per run on average | 3 of 4 pairs |
| H1b: Is B less unequal? | Yes, slightly: run-average Gini lower by 0.02-0.07 | 4 of 4 pairs |
| H1c: Do B's weakest go hungry less? | **Only when scores are shown** (both replications), mixed when hidden | 2 of 2 shown, 1 of 2 hidden |
| H2: Does the food-rich agent gain bargaining power in the typhoon? | Not testable, since only 5 loans were made in 8 runs | - |
| H4: Does cross-family liking grow faster in B? | No. Cross-family liking is the same in A and B (about 54-57 of 100) | - |
| Exploratory: incentive vs persona (Pete) | The least generous persona gave food only under the reputation rule, and more when he saw his score | gifts in 3 of 4 B runs, 0 of 4 A runs |

## H1: Sharing, inequality and hunger

| Run | Units given across households | Run-average Gini | Starving days, weak members (Lucky + Alice + Bob) |
|---|---|---|---|
| A-hidden-1 / B-hidden-1 | 0.5 / 2.0 | 0.557 / 0.505 | 9 / **21** |
| A-hidden-2 / B-hidden-2 | 0.0 / 6.0 | 0.666 / 0.636 | 25 / 20 |
| A-shown-1 / B-shown-1 | 3.5 / 2.0 | 0.579 / 0.505 | 15 / **10** |
| A-shown-2 / B-shown-2 | 3.0 / 8.0 | 0.652 / 0.632 | 16 / **9** |

- **Inequality** rose in every run, from about 0.2 on day 1 to 0.7-0.8 on day 20 (the maximum possible with six agents is about 0.83; why I use the Gini is explained in [`04-experiment-design.md`](04-experiment-design.md)). This was mostly because the agent with fishing gear (Pete) accumulated food while the elderly couple ran down theirs. B was less unequal than A in every pair, but the gap is small compared with how much runs differ from each other (the two replications differ by about 0.1).
- **Hunger.** With scores hidden, the two replications point in opposite directions (B worse in replication 1, better in replication 2). With scores shown, B's weak members starved less in both replications, by 5-7 days out of 60 possible. Averaged per run: hidden A 17.0 / B 20.5, shown A 15.5 / B 9.5.
- **Typhoon (difference-in-differences, `07_typhoon_did.sql`).** I measured the change in the weak members' average fullness from weeks 1-2 to weeks 3-4, B minus A. It was -20.1 (seed 43) and +12.0 (seed 44) with scores hidden, and -10.1 (seed 43) and +13.6 (seed 44) with scores shown. The sign follows the seed, not the condition, so I do not claim a typhoon-specific incentive effect.

## H2: Bargaining power during the typhoon

Agents proposed 68 loans across the eight runs. 5 were made, all with Pete as the lender (four to Alice, one to Kurt), at 11-29% interest. Three were in group A (20%, 25%, 29%) and two in group B (25%, 11%). Pete agreed to 6 of 36 requests to lend or trade food. With so few transactions, H2 cannot be evaluated. One contrast matters for the exploratory question below. In A, the only way food moved from Pete to the elderly couple was an interest-bearing loan. In B it was mostly a gift.

## H4: Family lines

In every run, agents rated their own family about 87-93 out of 100 and members of other families about 53-57. The gap (34-39 points) was slightly smaller in B in three of four pairs. In the hidden replication-1 pair, however, this came from B agents rating **their own family** lower, not from rating other families higher. Cross-family liking did not differ between A and B. H4 is not supported.

## Exploratory: incentive versus persona

Pete's written persona is self-reliant and ungenerous (starting generosity 25 of 100), and he is the richest agent. The reputation rule therefore pulls directly against his persona.

| | Scores hidden | Scores shown |
|---|---|---|
| Units Pete gave, group A (rep. 1, 2) | 0, 0 | 0, 0 |
| Units Pete gave, group B (rep. 1, 2) | 0, 5.0 | 1.0, 8.0 |
| "Like" Pete received from other families, A (rep. 1, 2) | 35.5, 43.8 | 50.8, 42.0 |
| "Like" Pete received from other families, B (rep. 1, 2) | 45.3, 59.3 | 49.8, 60.8 |

- Pete **never** gave food in group A. In group B he gave food in three of four runs.
- With the same seed, he gave more when he could see his score. For seed 43 his gifts went from 0 to 1 unit. For seed 44 they went from 5 to 8 units, and his gifts to the elderly couple started in the typhoon week instead of the last week.
- His gifts came with conditions ("only if you promise to help me with some work later", "I need to know you'll use it wisely"), and his stated reasons almost never mention reputation or his score. His behaviour moved toward the incentive, but his explanations stayed in persona.
- Other families liked him more in B in three of four pairs.

**Same-seed check.** Runs with the same seed see identical prompts until the first score is shown at the end of week 1. For seed 44, both pairs (`A-hidden-2`/`A-shown-2` and `B-hidden-2`/`B-shown-2`) have identical food holdings for every agent on days 1-5 (in B, Pete gave Stella 1 unit on days 4 and 5 in both), and they diverge only from week 2. So the simulator and model are reproducible for a given seed, and the differences between hidden and shown runs arise after feedback starts. (`A-hidden-1` and `B-hidden-1` ran on v6.2 and do not match their v7 counterparts in week 1, so this check is only available for seed 44.)

## Mechanism checks

- **What agents say.** Reputation-type words in weekly plans (per 100 plans) were more frequent in B only in the hidden replication-1 pair (33 vs 17). In the other three pairs B was lower (0 vs 29, 4 vs 8, 4 vs 13). Being told the reputation rule did not produce a stable shift in how agents justify their plans, even where it changed what they did. (This is a keyword proxy only. The flagged passages still need to be read.)
- **Say-do gap.** I counted promise-like lines ("I can share...", "I'll give...") that were followed by an actual gift within a day. A had 0-4 per run. B had 0-1 in replication 1 but 10 of 20-23 in replication 2. Where B agents gave, they mostly did what they said. Where they did not give, they talked about sharing anyway.
- **Persona drift** at the season end was nearly identical in A and B for every agent. For example, Pete's generosity went from 25 to 30 or 35 in all runs. The bounded persona update follows the persona and the events, not the incentive.

## Data quality

| | A-hidden-1 | B-hidden-1 | A-hidden-2 | B-hidden-2 | A-shown-1 | B-shown-1 | A-shown-2 | B-shown-2 |
|---|---|---|---|---|---|---|---|---|
| Fallbacks (default answer after 3 invalid tries) | 0 | 0 | 8 | 2 | 3 | 0 | 5 | 0 |

Fallbacks are more frequent in A (16) than in B (2). Most are borrowers mis-filling loan amounts, or agents trying to give more than their safe surplus allows. In both cases the agent's message is kept and only the invalid proposal is dropped. Because A households were short more often, they tried to borrow more often and so had more chances to fail. This slightly suppresses credit requests in A, and it is listed in [`07-limitations.md`](07-limitations.md).

## What this does and does not show

- The most robust result is about **one agent**. A persona that conflicts with the scoring rule kept its voice but changed its behaviour under the reputation rule, and more so when it saw its score. Because Pete is both the least generous persona and the richest agent, this cannot be separated into "persona" and "position".
- At the group level, score feedback is what made the reputation rule protect the weakest members. Being told the rule alone did not do so consistently. This rests on two replications per cell.
- Inequality differences between A and B are consistent in sign but small relative to run-to-run variation. Credit and family-line hypotheses could not be supported.

The gap between what agents say and what they do, and what I would try next, is discussed in [`10-discussion.md`](10-discussion.md).
