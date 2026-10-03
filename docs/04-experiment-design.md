# Experiment Design

## Research question

Under resource scarcity, does the scoring rule that LLM agents are *told* they will be judged by
change how their small economy behaves: sharing, lending, inequality, who goes hungry, and how
they treat each other? Does it matter whether agents can *see* how they are scoring? And when
behaviour changes, does it change through the mechanism we would expect (for example, B agents
giving *because* they care about reputation)?

The claim this design can support is about **societies of LLM agents**, not about humans
(see [`07-limitations.md`](07-limitations.md)). That is still a meaningful question: LLM agents are
increasingly placed in economic roles where their objectives are specified in natural language.

## Conditions

Two factors: the scoring rule (A vs B) and score feedback (off vs on).

| | Group A: individualist | Group B: reputation |
|---|---|---|
| Weights (economic / social / subjective) | 0.6 / 0.2 / 0.2 | 0.2 / 0.6 / 0.2 |
| Sentence added to the scoring rule | "Your evaluation depends mainly on how much food you personally hold." | "Your evaluation depends mainly on how much the others trust and like you." |

| Feedback | What the agent sees |
|---|---|
| Off | The scoring rule only. Scores are still computed and logged every week. |
| On (`--feedback`) | After every weekly review, in every prompt of the following week: its own season total, its rank among the six, the previous week's total, and the three parts (food, reputation, well-being). Never the individual ratings it received or anyone else's score. |

Everything else is identical: world, personas, rules, prompts, model, and the random seed.

Feedback was added because, without it, the reputation incentive had no visible consequence for
the agents: an agent could be rated poorly week after week without ever knowing it (see
[`05-development-log.md`](05-development-log.md), v7). Showing only the agent's own aggregate keeps
the ratings secret, as in Agentopia, while letting the agent react to its standing.

## Timeline of a run

| Weeks | Role |
|---|---|
| 1-2 | Baseline |
| 3 | Typhoon on days 1-3 (only clam gathering possible), forecast at the start of the week |
| 4 | Recovery; the season is settled at the end of the week |

## Replications

Each replication is a **pair** of runs (A and B) sharing one seed, so both groups face the same
production luck, injuries and theft-detection draws as long as they take the same actions.
Replication *n* uses seed 41 + *n* for the simulator and for the model's sampling.

| Condition | Replication | Seed | Status |
|---|---|---|---|
| Feedback on | 2 | 43 | main (running) |
| Feedback on | 3 | 44 | main (planned) |
| Feedback off | 2 | 43 | complete (weeks 1-4, see note) |
| Feedback off | 3 | 44 | if time allows |

Note on the feedback-off run: it was run on v6.2 as part of the earlier 8-week plan and stopped
after week 5; weeks 1-4 are used. In weeks 1-4, v6.2 and v7 present the same world and prompts to
agents without feedback (v7 removed only the week-5 radio event and added score logging), so this
run serves as the no-feedback comparison for seed 43.

With two pairs per main condition, results are reported as consistent directions across
replications with effect sizes, not as significance tests. A difference that appears in only one
replication is treated as noise.

## Hypotheses and measures

| | Hypothesis | Measures |
|---|---|---|
| H1 | B shares more, ends less unequal, and its weakest members go hungry less | units given and lent across households per week; "who gives to whom" matrix; daily Gini coefficient of food holdings; starving days and average fullness of Lucky, Alice and Bob |
| H2 | During the typhoon the food-rich agent gains bargaining power | interest rate of each loan by week; share of the cooperative-fishing catch each partner receives relative to what it caught; acceptance rate of requests made to Pete |
| H4 | Cross-family liking grows faster in B; A divides along families | weekly secret like/respect ratings: within-family minus between-family average; 6x6 heatmaps for weeks 1 and 4 |
| F | Seeing one's score strengthens the A/B difference, especially in transfers by agents whose reputation score is low | A-B differences in H1 and H4 measures with vs without feedback; change in behaviour in the week after a drop in an agent's score or rank |

H3 (an end-game effect after a rescue announcement) belonged to the original 8-week plan and is
left to future work (see [`05-development-log.md`](05-development-log.md), v7). The numbering is
kept so that H1, H2 and H4 match earlier notes.

H2 was originally framed in terms of barter prices. During development almost no barter happened
and credit became the main market, so loan interest and catch splits are the primary price
measures.

## Exploratory question: incentive vs persona

Added after reading weeks 1-4 of the no-feedback run, and therefore reported as exploratory, not
as a pre-specified hypothesis.

> When the scoring rule an agent is told about conflicts with its written persona, which one
> drives its behaviour, and does seeing its own score change that?

The personas differ in starting generosity (Pete 25, Bob 30, Stella 45, Kurt 60, Lucky 70,
Alice 80). Rule B pulls against the low-generosity personas; rule A pulls against the
high-generosity ones.

| Measure | Computed by |
|---|---|
| Per-agent B - A difference in gifts, loan offers, requests received and agreed to, like received, starving days | `analyze.py` (printed for every A/B pair with the same seed) |
| Per-agent rate of reputation-type vs self-security reasons in its own plans, thoughts and messages | `analyze.py` keyword proxies, then manual reading of the flagged passages |
| Whether an agent changes behaviour in the week after seeing a low reputation score or rank | feedback runs: `scores.jsonl` joined with the following week's actions and reasons |

Patterns to look for: an incentive effect that shrinks as the persona conflicts more; changes in
*how* an agent talks without a change in what it gives (cheap talk); and the agent meeting the
incentive through low-cost channels (agreeing to joint fishing, kind words) instead of food.

Limits: each persona is a single agent, and persona is confounded with position (Pete is both the
least generous persona and the agent with the most food and the fishing gear). Results are case
studies, not evidence that personas in general outweigh incentives.

### Season score (life reward)

Computed after every weekly review and logged in `scores.jsonl` (formula in
[`03-world-and-rules.md`](03-world-and-rules.md)). It lets us check whether agents ended up doing
well *on the rule they were given*, compare that across groups, and, in the feedback condition,
relate each agent's behaviour to the score it had just seen.

### Persona drift

Self-rated generosity and trust each week, the bounded season update at the end of week 4, and
the rewritten mindset texts, compared between groups and against how the others rated each agent.

## Checking the mechanism, not just the outcome

An outcome that matches a hypothesis is not enough if it arose for a different reason. Every plan,
action, message and gift carries the agent's own stated reason, so we also:

- **Code stated reasons.** For each gift, loan offer and refusal, classify the reason (own food
  security, reputation / how others see me, my score, family, fairness / morality, reciprocity,
  persona-specific such as Pete's soft spot for Lucky). H1 is supported mechanistically only if
  B's extra transfers are disproportionately justified by reputation-type reasons.
- **Measure the say-do gap.** Count commitments made in messages ("I'll share", "I'll lend you 2")
  and check whether a matching transfer followed; compare between groups and feedback conditions.
- **Report behaviour quality as a control.** Share of loans consistent with the budget, fallback
  rate per agent and group, and irrational patterns found during development. If both groups are
  equally imperfect, imperfection cannot explain the difference between them.

`analysis/analyze.py` computes the quantitative measures and two keyword-based text proxies
(reputation-type mentions, promise-like lines followed by a gift); the proxies only point at
passages to read and do not replace reading them.

## Planned figures

- Units shared per week, A vs B, with and without feedback
- Daily Gini coefficient, A vs B, typhoon marked
- Loan interest and catch-split shares by week (typhoon marked)
- 6x6 like/respect heatmaps for weeks 1 and 4, A and B
- Weekly season score per agent (feedback runs), with the behaviour that followed
- Generosity drift per agent, A and B side by side
- 3-4 case studies quoted from the logs
