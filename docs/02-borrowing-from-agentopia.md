# What I Borrowed from Agentopia and What I Changed

Agentopia ([arXiv:2606.07513](https://arxiv.org/abs/2606.07513)) simulates a large agent society over many simulated years. It uses a weekly decision cycle and a "life reward" that combines social, subjective and economic parts. I borrowed two of its ideas, the **time structure** and the **life reward**, and applied them to a much smaller scenario built around scarcity.

The section references below come from my reading notes on the paper. Please check them against the published version before citing.

## Adopted or adapted

| Design element | In Agentopia | In this simulator |
|---|---|---|
| Discrete time instead of a real-time engine | Time is cut into discrete turns (§3.2, App. B.1) | Same. This is the main reason I moved away from AI Town |
| One activity per day | Each agent does one activity per day (§3.2, §3.4) | One action per day from a fixed menu (fish, gather clams, climb coconut trees, forage, build shelter, rest, heal, steal, or a pre-arranged cooperative fishing trip) |
| Weekly cycle of Plan, Contact, Activity and Review | Four-phase week (§3.2, App. B.2) | Kept, with an evening campfire added after each day |
| Periodic settlement and persona update | Yearly settlement every 10 weeks, and a persona update with bounded trait change (App. B.2, B.11) | One 4-week "season". At its end the agent rewrites its *current mindset* from its diaries. Generosity and trust may move at most +/-10. Core persona, age and family never change |
| Multi-round private messaging with propose / respond | Text messages plus structured proposals (§3.3, App. B.3) | 3 rounds per week, up to 2 messages per round. Proposals for trade, loan or cooperative fishing are answered with accept/reject in the next round |
| Conversation inside a joint activity | 5-20 turn dialogue that takes up the day (§3.4, App. B.4) | Cooperative fishing: up to 6 turns to agree on how to split the catch. Without agreement the 1.5x team bonus is lost |
| Message visibility | Public, private or selected-recipient messages (App. B.4) | At the campfire an agent speaks to everyone or whispers to one person |
| Transfers between agents | Gift action during activities (App. B.4) | Gifts at the campfire (public), barter, loans, theft |
| Lifestyle choice each week | Frugal / moderate / comfortable / luxurious (App. B.12) | Ration level: normal / save (half) / skip, which can change every day |
| Decay of satisfaction | Needs decay weekly (App. B.10) | Food spoils weekly at rates that depend on its type. Stamina falls with work and hunger |
| Social reward | Private like/respect ratings feed a weighted PageRank with a reciprocity bonus (§4.1, eq. 1) | Same construction on 6 nodes: weekly secret like and respect ratings, and PageRank (damping 0.85) with reciprocity alpha = 2, computed after every weekly review |
| Subjective reward | Satisfaction of several needs, with a penalty for the bottom of the distribution (§4.1, eq. 2) | Fullness, stamina and belonging (gifts received, deals accepted, joint work), minus a penalty for each starving day |
| Economic reward | Change in savings (§4.1) | Change in the agent's own food holdings over the season |
| Weighted total | Fixed weights (§4.1, eq. 3) | **The experimental manipulation:** A = 0.6 economic / 0.2 social / 0.2 subjective; B = 0.2 / 0.6 / 0.2 |
| Agents know the reward rule | The reward is part of the world description | Same. The rule is written into every prompt and is the only difference between A and B |
| Ratings are private | Agents are told ratings are confidential | Same ("nobody will ever see this") |
| Environment events | Encounters and events arranged by the environment (§3.4, App. B.6) | One scheduled shock: a typhoon in week 3 with an advance forecast |
| Structured output with error feedback | Format errors are returned to the agent to correct (App. B.3) | Output is constrained by a JSON schema. An invalid answer is returned with the reason, up to 3 tries, and after that a default is used and logged |
| Role-play principles | A list of role-play rules (Tables 7, 39) | A shorter set written into the persona prompt |
| Memory | File-system memory managed by the agent (§3.1, App. A.2) | Simplified: a weekly diary, impressions of each other agent, a rolling memory of recent events, and what the agent heard |
| Analysis | Correlations, Gini, social networks, case studies (§5.2, App. D) | Gini, transfer matrices, rating heatmaps, case studies, and a check of the reasons agents give |

## What I chose not to borrow

- **An LLM as the environment or referee** (§3.5). A 14B local model is not reliable enough to judge outcomes. Its judgments would also differ between A and B for reasons that have nothing to do with the manipulation. Instead, all outcomes are computed by fixed rules with a shared seed.
- **Training on the reward** (§4.2). Agentopia uses the life reward as a learning signal. In my simulator the model weights never change. The reward is described to the agents and computed every week. In the *feedback* condition each agent also sees its own running score (total, rank and the three parts, but never who rated it how). It can react to this score within the run, but only through its context. So what I test is whether being told a scoring rule, and seeing one's score, changes behaviour. I do not test whether agents learn from rewards.
- **Scale and duration.** I use 6 agents and 20 action days instead of a large society over many simulated years.

## Additions that are not in Agentopia

I added these because of the scarcity setting and because of problems I found during development (see [`05-development-log.md`](05-development-log.md)):

- Households. Family members eat from each other's food and share each other's debts.
- A credit market. Loans have interest and a due day. Repayment happens automatically after meals, defaults are announced publicly, and overdue debt keeps being collected.
- A weekly food budget for each household. The simulator computes it and shows it to the agents. It covers holdings, expected production based on recent actual output, need, debts, food at risk of spoiling, and either the shortfall to borrow or the safe surplus that may be lent or given.
- Institutional rules. Children cannot borrow, lend, trade or hand out food. Loans go only to households that are actually short. Gifts and loans together cannot exceed the household's safe surplus for the week. There are no gifts within a household.
- Public information about the tools each person carries and what each person brings back from work each day. Food holdings stay private.
