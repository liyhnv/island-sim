# Experiment Design

## Research question

Under resource scarcity, does the scoring rule that LLM agents are *told* they will be judged by
change how their small economy behaves: sharing, lending, inequality, who goes hungry, and how
they treat each other? And when it does, do the changes come about through the mechanism we
would expect (for example, B agents giving *because* they care about reputation)?

The claim this design can support is about **societies of LLM agents**, not about humans
(see [`07-limitations.md`](07-limitations.md)). That is still a meaningful question: LLM agents are
increasingly placed in economic roles where their objectives are specified in natural language.

## Conditions

| | Group A: individualist | Group B: reputation |
|---|---|---|
| Weights (economic / social / subjective) | 0.6 / 0.2 / 0.2 | 0.2 / 0.6 / 0.2 |
| Sentence added to the scoring rule | "Your evaluation depends mainly on how much food you personally hold." | "Your evaluation depends mainly on how much the others trust and like you." |

Everything else is identical: world, personas, rules, prompts, model, and the random seed.

## Replications

Each replication is a **pair** of runs (A and B) sharing one seed, so both groups face the same
production luck, injuries and theft detection draws as long as they take the same actions.
Replication *n* uses seed 41 + *n* for the simulator and for the model's sampling.

| Replication | Seed | Role |
|---|---|---|
| 1 | 42 | complete; supplementary because of the caveats in [`08-status-and-next-steps.md`](08-status-and-next-steps.md) |
| 2 | 43 | main (running) |
| 3 | 44 | main (planned) |
| 4 | 45 | main, if time allows |

With 2-3 main pairs, results will be reported as consistent directions across replications with
effect sizes, not as significance tests. A difference that appears in only one replication will be
treated as noise.

## Hypotheses and measures

| | Hypothesis | Measures |
|---|---|---|
| H1 | B shares more, ends less unequal, and its weakest members go hungry less | units given and lent across households per week; "who gives to whom" matrix; daily Gini coefficient of food holdings; starving days and average fullness of Lucky, Alice and Bob |
| H2 | During the typhoon the food-rich agent gains bargaining power | interest rate of each loan by week; share of the cooperative-fishing catch each partner receives relative to what it caught; acceptance rate of requests made to Pete; any barter exchange ratios |
| H3 | After the radio news (week 5), effort and cooperation fall, more in A | share of productive actions; transfers and cooperative trips; weeks 1-4 vs 5-8 |
| H4 | Cross-family liking grows faster in B; A divides along families | weekly secret like/respect ratings: within-family minus between-family average; 6x6 heatmaps for week 1 and week 8 |

H2 was originally framed in terms of barter prices. During development, almost no barter
happened and credit became the main market (see [`05-development-log.md`](05-development-log.md)),
so loan interest and catch splits are now the primary price measures.

### Life reward (computed afterwards)

At the end of each season the three reward components are computed from the logs, standardised
and weighted as described to the agents: the social reward by PageRank on the like and respect
ratings with a reciprocity bonus; the subjective reward from fullness, stamina and belonging minus
5 points per starving day; the economic reward from the change in own food. This lets us check
whether agents ended up doing well *on the rule they were given*, and compare that across groups.

### Persona drift

Self-rated generosity and trust each week, the bounded season updates, and the rewritten mindset
texts at weeks 0, 4 and 8, compared between groups and against how the others rated each agent.

## Checking the mechanism, not just the outcome

An outcome that matches a hypothesis is not enough if it arose for a different reason. Every plan,
action, message and gift carries the agent's own stated reason, so we will also:

- **Code stated reasons.** For each gift, loan offer and refusal, classify the reason (own food
  security, reputation/how others see me, family, fairness/morality, reciprocity, persona-specific
  such as Pete's soft spot for Lucky). H1 is supported mechanistically only if B's extra transfers
  are disproportionately justified by reputation-type reasons.
- **Measure the say-do gap.** Count commitments made in messages ("I'll share", "I'll lend you 2")
  and check whether a matching transfer followed within the week; compare between groups.
- **Report behaviour quality as a control.** Share of loans consistent with the budget, fallback
  rate per agent and group, and irrational patterns found during development (for example, lending
  to the richest agent). If both groups are equally imperfect, imperfection cannot explain the
  difference between them.

## Planned figures

- Units shared per week, A vs B, per replication
- Daily Gini coefficient, A vs B, with the typhoon and the radio marked
- Loan interest and catch-split shares by week (typhoon marked)
- 6x6 like/respect heatmaps for weeks 1 and 8, A and B
- Weeks 1-4 vs 5-8: productive actions and transfers
- Season life-reward table
- Generosity drift per agent, A and B side by side
- 3-4 case studies quoted from the logs
