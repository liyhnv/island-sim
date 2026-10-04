# The World and Its Rules (simulator v7)

All numbers live in [`config.yaml`](../config.yaml) and [`characters.json`](../characters.json). This page describes them in words. The LLM never decides an outcome. It chooses actions and says things, and the rules below compute what happens.

## The six survivors

| Agent | Age | Household | Items | Daily need | Productivity | Generosity / trust at start |
|---|---|---|---|---|---|---|
| Kurt | 35 | Kurt, Stella, Lucky | knife | 2 | 1.12 | 60 / 50 |
| Stella | 35 | Kurt, Stella, Lucky | lighter | 2 | 1.10 | 45 / 35 |
| Lucky | 10 | Kurt, Stella, Lucky | none | 1 | 0.38 | 70 / 85 |
| Alice | 68 | Alice, Bob | first aid kit | 1.5 | 0.65 | 80 / 60 |
| Bob | 70 | Alice, Bob | blanket | 1.5 | 0.65 | 30 / 25 |
| Pete | 26 | Pete | fishing line and hooks, rope | 2 | 1.20 | 25 / 30 |

Everyone starts with 3 units of canned food and 70 stamina. The island needs 10 units per day in total. Each agent has a fixed core persona and a "current mindset" that can change each season.

Productivity multiplies every yield. Calibration (`calibrate.py`, no LLM) puts the island's full-effort output at about 1.24x total need. I set this above 1 on purpose. In trial runs the LLM agents worked on only about 60% of days, and fresh food spoils, so the food that is actually available ends up below need.

## Food

| Type | Source | Spoils per week | Notes |
|---|---|---|---|
| fish | fishing | 40% | eating at least 0.5 fish in a day gives +5 stamina that night |
| clam | tide pools | 30% | |
| forage | forest | 20% | |
| coconut | trees | 10% | 25 coconuts on the island, no regrowth |
| can | starting stock | 0% | |

Food is measured in units, where one unit is one meal's worth. Canned food is counted in units too. Spoilage is applied at the end of each week. Agents eat the most perishable food first.

## A day

1. **Morning decision.** All six choose at the same time from the same state.
2. **Resolution** by the rules: work first, then cooperative fishing, then theft and healing.
3. **Eating.** Each agent eats according to its ration (normal = full need, save = half, skip = nothing). An agent who runs out eats from family members' food.
4. **Loan collection** for loans due today, after everyone has eaten.
5. **Campfire.** Each agent says one line, either to everyone or whispered to one person, and may hand food to someone.

### Actions

| Action | Yield (before productivity) | Stamina | Conditions |
|---|---|---|---|
| Fish | 3-4 with fishing gear, 0-2 without | -10 | stamina >= 40; blocked in the typhoon |
| Gather clams | 1-2, halved for everyone if more than 2 people go | -5 | always possible, light work |
| Climb coconut trees | 2-4 | -12 | age < 60, stamina >= 60, coconuts left; blocked in the typhoon |
| Forage | 2-4; 20% chance of injury (-20 stamina) | -10 | blocked in the typhoon |
| Build shelter | shared progress +1 | -12 | blocked in the typhoon (no gameplay effect, see limitations) |
| Rest | | +15 | |
| Heal | restores an injured person's 20 stamina | | only the first-aid-kit holder (Alice) |
| Steal | 1-3 units from a target | | 50% chance the victim finds out who it was |
| Cooperative fishing | both catches x 1.5, then split by negotiation | -10 each | only if agreed during the week's messages |

Below 30 stamina no heavy work is possible. An agent below 10 at the start of a day collapses and is forced to rest. The menu shown to an agent lists only what it can do today, with the best expected yield first. It marks options that give less than half the yield of the agent's best option as low yield. It also says how many people crowded the tide pools yesterday.

### Stamina and hunger

| Situation (per day) | Effect |
|---|---|
| ate at least half of need | +5 overnight |
| ate less than full need (but at least half) | -5 |
| ate less than half of need ("starving") | -10, no overnight recovery |
| starving several days in a row | stamina is capped at 60 after the first such day and 10 lower for each further day, never below 30; the cap lifts as soon as the agent eats at least half its need |

The cap means that resting cannot replace food. An earlier version let a starving agent rest at 90 stamina indefinitely. The floor of 30 keeps light work possible, so starvation does not become a trap the agent can never leave.

## A week

1. **Plan.** Each agent receives its household's food budget (described below). It then picks a starting ration, a credit intention (borrow / lend / neither, with an amount and a partner) and a short plan.
2. **Contact.** Three rounds of private messages, up to two per round. A message may carry one proposal, which is answered in the next round. No new proposals can be made in the last round.
3. **Five days** as described above.
4. **Review.** Each agent writes a private diary entry. It gives secret like and respect ratings (0-100) for each other agent with a short impression, and rates its own generosity and trust.
5. **Score.** The season's life reward so far is computed for every agent (see below).
6. **Season** (end of week 4, which is the end of the run). The agent rereads its four diaries and rewrites its current mindset. Generosity and trust move at most +/-10.

### Weekly food budget (computed by the simulator, per household)

- Holdings, need for the week, debts the household owes and debts owed to it.
- Expected production. On typhoon days this is a clam estimate. On normal days it is a blend of what the agent's best work could give (x 0.8) and what it *actually* brought in over its last five normal days.
- Balance = holdings + expected production - need - debts. In the typhoon week the budget also shows the food left when the typhoon ends.
- If the worst balance is negative, the household should borrow about that amount (or eat half on some days). Otherwise the **safe surplus** = balance minus one day's food per person.
- How much of the food held would rot by the end of the week if it is not eaten, lent or traded.

## Exchange

| Channel | Rules |
|---|---|
| Trade | Proposed in a message. It executes immediately on acceptance if both agents still hold the food. Only between different households and not with children |
| Loan | The lender hands food over now. The borrower repays a stated total (interest allowed) within 1-10 work days. Repayment is taken automatically at the end of the due day after meals, first from the borrower and then from the borrower's family. A missed repayment is announced to everyone, and the borrower's leftover food is taken every evening until the debt is cleared |
| Gift | Only at the campfire, seen by everyone, never repaid |
| Cooperative fishing | Agreed for a specific day. It is cancelled (and logged) if either agent cannot fish that day. The split is negotiated in up to 6 turns. If there is no agreement, each agent keeps only its own catch |
| Theft | A daily action (see above) |

### Institutional limits on credit and gifts (v6)

- **Children** (Lucky) cannot borrow, lend, trade or hand out food. They can receive gifts and can fish together with an adult.
- **Loans only for a real shortfall.** A loan is cancelled if the borrower's household shows no shortfall this week. Once a household has borrowed, it cannot borrow more than its remaining shortfall. The rules tell agents that helping someone or building goodwill should be done with a gift, not a loan.
- **Safe surplus.** All the food a household lends or gives away in a week cannot add up to more than its safe surplus from the weekly budget. A household that is break-even or short cannot lend or give away food that week.
- **No gifts within a household**, since family members already share food.
- **No duplicate deals.** A proposal identical to an open or accepted one between the same two agents in the same week is not sent again.

## What agents can see

- Their own food, stamina, ration, plan, debts and credits, diary, impressions of others, recent memories and what they heard. Debts and credits come with a repayment plan and a reminder that repayment is automatic and that gifts do not count.
- **Public:** every person's tools, what everyone did yesterday and roughly how much each person brought back, who looks weak from hunger, defaults on loans, and gifts made at the campfire.
- **Private:** other agents' food holdings and the content of messages between other people.
- Their own scoring rule (A or B), described in plain words.
- In the **feedback** condition only, their own season score after each weekly review (see below).

## Events

- **Typhoon**, week 3, days 1-3. Only clam gathering (or rest) is possible. Everyone is warned at the start of the week. On each typhoon day the prompt says so, and from day 4 it states that the typhoon is over.
- The run ends after week 4. Earlier 8-week versions also had a radio message in week 5 announcing a rescue. I removed it in v7 (see the development log).

## The season score (life reward)

The score is computed after every weekly review, counting from the start of the season, with the group's weights (A: 0.6 / 0.2 / 0.2, B: 0.2 / 0.6 / 0.2). Each part is on a fixed 0-100 scale:

| Part | Computation |
|---|---|
| Food (economic) | 50 + 5 x (food held now - food held at the season start), clipped to 0-100 |
| Reputation (social) | weighted PageRank on the latest secret like ratings and, separately, on the respect ratings (damping 0.85, reciprocity bonus alpha = 2); the two are averaged and scaled so that an average agent scores 50 |
| Well-being (subjective) | mean of average fullness (%), average stamina and belonging (20 points per gift received, accepted deal or cooperative trip, max 100), minus 5 per starving day |

Scores are logged in `scores.jsonl` in every run. With `--feedback`, each agent sees its own total, its rank among the six, and the three parts in every prompt of the following week. It never sees the individual ratings it received.

## When the model fails

Every answer must match a JSON schema and pass a rule validator. An invalid answer is returned to the model with the reason, up to 3 tries. After that a default is used and logged as a fallback (for actions, the default is rest). For private messages I salvage the answer where possible. Broken proposals are dropped, but the message text and valid replies are kept. If Ollama itself is unreachable, the program waits up to 30 minutes and then stops with its progress saved.
