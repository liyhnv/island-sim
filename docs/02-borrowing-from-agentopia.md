# What Was Borrowed from Agentopia, and What Was Changed

Agentopia ([arXiv:2606.07513](https://arxiv.org/abs/2606.07513)) simulates a large agent society
over many simulated years, with a weekly decision cycle and a "life reward" that combines social,
subjective and economic components. This project borrows two of its ideas, the **time structure**
and the **life reward**, and applies them to a much smaller, scarcity-driven scenario.

Section references below come from my reading notes on the paper; please check them against the
published version before citing.

## Adopted or adapted

| Design element | In Agentopia | In this simulator |
|---|---|---|
| Discrete time instead of a real-time engine | Time is cut into discrete turns (§3.2, App. B.1) | Same; this is the main reason for leaving AI Town |
| One activity per day | Each agent does one activity per day (§3.2, §3.4) | One action per day from a fixed menu (fish, gather clams, climb coconut trees, forage, build shelter, rest, heal, steal, or a pre-arranged cooperative fishing trip) |
| Weekly cycle Plan -> Contact -> Activity -> Review | Four-phase week (§3.2, App. B.2) | Kept, plus an evening campfire after each day |
| Periodic settlement and persona update | Yearly settlement every 10 weeks; persona update with bounded trait change (App. B.2, B.11) | A "season" every 4 weeks: the agent rewrites its *current mindset* from its diaries; generosity and trust may move at most +/-10. Core persona, age and family never change |
| Multi-round private messaging with propose / respond | Text messages plus structured proposals (§3.3, App. B.3) | 3 rounds per week, up to 2 messages per round; proposals for trade, loan or cooperative fishing, answered with accept/reject in the next round |
| Conversation inside a joint activity | 5-20 turn dialogue that takes up the day (§3.4, App. B.4) | Cooperative fishing: up to 6 turns to agree on the split of the catch; no agreement means the 1.5x team bonus is lost |
| Message visibility | Public, private or selected-recipient messages (App. B.4) | At the campfire an agent speaks to everyone or whispers to one person |
| Transfers between agents | Gift action during activities (App. B.4) | Gifts at the campfire (public), barter, loans, theft |
| Lifestyle choice each week | Frugal / moderate / comfortable / luxurious (App. B.12) | Ration level: normal / save (half) / skip, changeable every day |
| Decay of satisfaction | Needs decay weekly (App. B.10) | Food spoils weekly at type-specific rates; stamina falls with work and hunger |
| Social reward | Private like/respect ratings -> weighted PageRank with a reciprocity bonus (§4.1, eq. 1) | Same construction, on 6 nodes: weekly secret like and respect ratings, PageRank (damping 0.85) with reciprocity alpha = 2 (computed in the analysis stage) |
| Subjective reward | Satisfaction of several needs, with a penalty for the bottom of the distribution (§4.1, eq. 2) | Fullness, stamina and belonging (gifts received, deals accepted, joint work), minus a penalty per starving day |
| Economic reward | Change in savings (§4.1) | Change in the agent's own food holdings over the season |
| Weighted total | Fixed weights (§4.1, eq. 3) | **The experimental manipulation:** A = 0.6 economic / 0.2 social / 0.2 subjective; B = 0.2 / 0.6 / 0.2 |
| Agents know the reward rule | The reward is part of the world description | Same; the rule is written into every prompt and is the only difference between A and B |
| Ratings are private | Agents are told ratings are confidential | Same ("nobody will ever see this") |
| Environment events | Encounters and events arranged by the environment (§3.4, App. B.6) | Two scheduled shocks: a typhoon (week 3) with an advance forecast, and a radio broadcast (week 5) |
| Structured output with error feedback | Format errors are returned to the agent to correct (App. B.3) | JSON-schema constrained output; invalid answers are returned with the reason, up to 3 tries; then a logged default |
| Role-play principles | A list of role-play rules (Tables 7, 39) | A condensed set written into the persona prompt |
| Memory | File-system memory managed by the agent (§3.1, App. A.2) | Simplified: weekly diary, impressions of each other agent, a rolling memory of recent events, and what was heard |
| Analysis | Correlations, Gini, social networks, case studies (§5.2, App. D) | Gini, transfer matrices, rating heatmaps, case studies, plus a check of agents' stated reasons |

## Deliberately not borrowed

- **An LLM as the environment / referee** (§3.5). A 14B local model is not reliable enough to
  judge outcomes, and judged outcomes would differ between A and B for reasons unrelated to the
  manipulation. All outcomes are computed by fixed rules with a shared seed instead.
- **Training on the reward** (§4.2). Agentopia uses the life reward as a learning signal. Here
  model weights never change; the reward is only *described* to the agents, and the scores
  themselves are computed afterwards for analysis. Agents never see their own score. This is an
  important difference: what is tested here is whether *being told* a scoring rule changes
  behaviour, not whether agents learn from receiving rewards.
- **Scale and duration.** 6 agents and 40 action days instead of a large society over many
  simulated years.

## Additions that are not in Agentopia

These came from the scarcity setting and from problems found while developing
(see [`05-development-log.md`](05-development-log.md)):

- Households: family members eat from each other's food and share each other's debts.
- A credit market: loans with interest and a due day, automatic repayment after meals, a public
  announcement of defaults, and continued collection of overdue debt.
- A weekly food budget for each household, computed by the simulator and shown to the agents
  (holdings, expected production from recent actual output, need, debts, food at risk of
  spoiling, the shortfall to borrow or the safe surplus that may be lent or given).
- Institutional rules: children cannot borrow, lend, trade or hand out food; loans only to
  households that are actually short; gifts and loans together are limited to the household's
  safe surplus for the week; no gifts within a household.
- Public information about tools carried and what each person brings back from work each day,
  while food holdings stay private.
