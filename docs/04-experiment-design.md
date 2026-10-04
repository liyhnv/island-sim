# Experiment Design

## Research question

Under resource scarcity, does the scoring rule that LLM agents are *told* they will be judged by change how their small economy behaves? I look at sharing, lending, inequality, who goes hungry, and how the agents treat each other. I also ask whether it matters that agents can *see* how they are scoring. And when behaviour changes, I want to know whether it changes through the expected mechanism (for example, B agents giving *because* they care about reputation).

The claims this design can support are about **societies of LLM agents**, not about humans (see [`07-limitations.md`](07-limitations.md)). I still think this is a meaningful question, because LLM agents are more and more often placed in economic roles where their objectives are written in natural language.

## Conditions

There are two factors: the scoring rule (A vs B) and score feedback (off vs on).

| | Group A: individualist | Group B: reputation |
|---|---|---|
| Weights (economic / social / subjective) | 0.6 / 0.2 / 0.2 | 0.2 / 0.6 / 0.2 |
| Sentence added to the scoring rule | "Your evaluation depends mainly on how much food you personally hold." | "Your evaluation depends mainly on how much the others trust and like you." |

| Feedback | What the agent sees |
|---|---|
| Off | The scoring rule only. Scores are still computed and logged every week. |
| On (`--feedback`) | After every weekly review, in every prompt of the following week: its own season total, its rank among the six, the previous week's total, and the three parts (food, reputation, well-being). It never sees the individual ratings it received or anyone else's score. |

Everything else is the same: world, personas, rules, prompts, model, and the random seed.

I added feedback because without it the reputation incentive had no visible consequence for the agents. An agent could be rated poorly week after week and never know it (see [`05-development-log.md`](05-development-log.md), v7). Showing only the agent's own aggregate keeps the ratings secret, as in Agentopia, but still lets the agent react to its standing.

## Timeline of a run

| Weeks | Role |
|---|---|
| 1-2 | Baseline |
| 3 | Typhoon on days 1-3 (only clam gathering possible), forecast at the start of the week |
| 4 | Recovery; the season is settled at the end of the week |

## Replications

Each replication is a **pair** of runs (A and B) that share one seed. As long as the two groups take the same actions, they face the same production luck, injuries and theft-detection draws. The seed is used for both the simulator and the model's sampling.

| Condition | Replication | Seed | Runs | Status |
|---|---|---|---|---|
| Scores hidden | 1 | 43 | A-hidden-1, B-hidden-1 | complete (weeks 1-4, see note) |
| Scores hidden | 2 | 44 | A-hidden-2, B-hidden-2 | complete |
| Scores shown | 1 | 43 | A-shown-1, B-shown-1 | complete |
| Scores shown | 2 | 44 | A-shown-2, B-shown-2 | complete |

Run labels follow the pattern *group-condition-replication*. On the command line, replication *k* is `run.py --run k+1` (seed 42 + *k*), because `--run 1` was used for the v6 pilot. Log folders keep those names (`logs/A_r2`, `logs/A_r2_fb`, ...).

A note on replication 1 with scores hidden. It was run on v6.2 as part of the earlier 8-week plan and stopped after week 5, and I use weeks 1-4. In weeks 1-4, v6.2 and v7 show the same world and prompts to agents without feedback. The only changes in v7 were removing the week-5 radio event and adding score logging. So this run serves as the no-feedback comparison for seed 43.

With two pairs per main condition, I report results as consistent directions across replications with effect sizes, not as significance tests. I treat a difference that appears in only one replication as noise.

## Hypotheses and measures

| | Hypothesis | Measures |
|---|---|---|
| H1 | B shares more, ends less unequal, and its weakest members go hungry less | units given and lent across households per week; "who gives to whom" matrix; daily Gini coefficient of food holdings; starving days and average fullness of Lucky, Alice and Bob |
| H2 | During the typhoon the agent with the most food gains bargaining power | interest rate of each loan by week; share of the cooperative-fishing catch each partner receives relative to what it caught; acceptance rate of requests made to Pete |
| H4 | Liking across families grows faster in B, while A divides along family lines | weekly secret like/respect ratings: within-family minus between-family average; 6x6 heatmaps for weeks 1 and 4 |
| F | Seeing one's score strengthens the A/B difference, especially in transfers by agents with a low reputation score | A-B differences in H1 and H4 measures with vs without feedback; change in behaviour in the week after an agent's score or rank drops |

H3 (an end-game effect after a rescue announcement) belonged to the original 8-week plan and is left for future work (see [`05-development-log.md`](05-development-log.md), v7). I kept the numbering so that H1, H2 and H4 match my earlier notes.

H2 was first framed in terms of barter prices. During development almost no barter happened and credit became the main market. So loan interest and catch splits are now the main price measures.

### Why the Gini coefficient

I measure inequality with the Gini coefficient of the six agents' food holdings, computed every day. With holdings sorted from poorest (i = 1) to richest (i = n), G = sum of (2i - n - 1) x food_i, divided by n x total food. It is 0 when everyone holds the same. When one agent holds everything it reaches (n - 1) / n, which is about 0.83 with six agents, so values near 0.8 at the end of a run mean that almost all food sits with one or two agents.

I chose it for four reasons:

- It is the standard single-number measure of inequality, and Agentopia also reports it, so the result can be read without explaining a new measure.
- It uses all six agents, not only the richest and the poorest, so it changes when food moves between any two people.
- It does not depend on how much food there is in total. Total food on the island rises and falls with production, spoilage and the typhoon, so a measure in units (such as the gap between richest and poorest) would mostly track those swings. The Gini can be compared across days and across runs.
- It is easy to compute for every day and every run, in Python and in SQL (`analysis/sql/02_gini_daily.sql`, using window functions).

It also has limits, which is why it is never used alone:

- It does not say who is poor. The same Gini can come from a hungry child or from an adult who simply ate his food. So H1 also looks at the starving days and fullness of the weakest members.
- With six agents, one agent can move it a lot. In practice much of the rise comes from Pete, who has the fishing gear and keeps his catch.
- It measures holdings, not what people eat. Family members eat from each other's food, so uneven holdings inside a household do not mean anyone goes hungry.

## Incentive vs persona (exploratory)

I added this question after reading weeks 1-4 of the no-feedback run. For that reason I report it as exploratory, not as a hypothesis I specified in advance.

> When the scoring rule an agent is told about conflicts with its written persona, which one drives its behaviour, and does seeing its own score change that?

The personas differ in starting generosity (Pete 25, Bob 30, Stella 45, Kurt 60, Lucky 70, Alice 80). Rule B pulls against the low-generosity personas, and rule A pulls against the high-generosity ones.

| Measure | Computed by |
|---|---|
| Per-agent B - A difference in gifts, loan offers, requests received and agreed to, like received, starving days | `analyze.py` (printed for every A/B pair with the same seed) |
| Per-agent rate of reputation-type vs self-security reasons in its own plans, thoughts and messages | `analyze.py` keyword proxies, followed by manual reading of the flagged passages |
| Whether an agent changes behaviour in the week after seeing a low reputation score or rank | feedback runs: `scores.jsonl` joined with the following week's actions and reasons |

I look for three patterns. The first is an incentive effect that gets smaller as the conflict with the persona gets larger. The second is a change in *how* an agent talks with no change in what it gives (cheap talk). The third is an agent meeting the incentive through low-cost channels, such as agreeing to joint fishing or saying kind words, instead of giving food.

This analysis has limits. Each persona is a single agent, and persona is confounded with position. Pete is both the least generous persona and the agent with the most food and the fishing gear. The results are case studies, not evidence that personas in general outweigh incentives.

### Season score (life reward)

The score is computed after every weekly review and logged in `scores.jsonl` (the formula is in [`03-world-and-rules.md`](03-world-and-rules.md)). It lets me check whether agents ended up doing well *on the rule they were given* and compare that across groups. In the feedback condition it also lets me relate each agent's behaviour to the score it had just seen.

### Persona drift

I compare self-rated generosity and trust each week, the bounded season update at the end of week 4, and the rewritten mindset texts. I compare these between groups and against how the others rated each agent.

## Checking the mechanism as well as the outcome

An outcome that matches a hypothesis is not enough if it happened for a different reason. Every plan, action, message and gift carries the agent's own stated reason, so I also do the following:

- **Code stated reasons.** For each gift, loan offer and refusal, I classify the reason: own food security, reputation / how others see me, my score, family, fairness / morality, reciprocity, or something specific to the persona, such as Pete's soft spot for Lucky. I count H1 as supported at the level of mechanism only if B's extra transfers are disproportionately justified by reputation-type reasons.
- **Measure the gap between saying and doing.** I count commitments made in messages ("I'll share", "I'll lend you 2") and check whether a matching transfer followed. I compare this between groups and between feedback conditions.
- **Report behaviour quality as a control.** This covers the share of loans consistent with the budget, the fallback rate per agent and per group, and irrational patterns I found during development. If both groups are equally imperfect, imperfection cannot explain the difference between them.

`analysis/analyze.py` computes the quantitative measures and two keyword-based text proxies (mentions of reputation, and promise-like lines followed by a gift). The proxies only point me to passages to read. They do not replace reading them.

## Planned figures

- Units shared per week, A vs B, with and without feedback
- Daily Gini coefficient, A vs B, with the typhoon marked
- Loan interest and catch-split shares by week (typhoon marked)
- 6x6 like/respect heatmaps for weeks 1 and 4, A and B
- Weekly season score per agent (feedback runs), with the behaviour that followed
- Generosity drift per agent, A and B side by side
- 3-4 case studies quoted from the logs
