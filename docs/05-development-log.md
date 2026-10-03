# Development Log

How the simulator got from the original plan to the version used for the main experiment, with
the evidence behind each change. Folder names in `archive/` refer to the run logs kept for each
stage (not yet committed).

A rule adopted halfway through governs everything after it:

> **Fix the code only when the simulator computes something wrong, or shows the agents wrong or
> misleading information. When agents make poor choices with correct information, keep the
> behaviour and report it.**

Before that rule, several changes did nudge behaviour through the prompts (budgets, credit
hints, warnings). They are listed here so the reader can judge how much of the agents' behaviour
is shaped by scaffolding; see also [`07-limitations.md`](07-limitations.md).

---

## v0: Plan and calibration (late September)

- Started from the plan: 6 agents, rule-computed outcomes, uniform 20% weekly spoilage, a target
  of full-effort output at 80-90% of need, `qwen3:8b`.
- Added per-agent **productivity** multipliers so that the old couple and the child produce less
  than the adults and Pete the most. The values were tuned on request: Kurt and Stella raised,
  Pete's advantage lowered (final: Pete 1.2, Kurt 1.12, Stella 1.1, Alice 0.65, Bob 0.65,
  Lucky 0.38).
- **Calibration target changed** from 0.80-0.90 to 1.10-1.25 of need, measured with a greedy
  "full effort" policy (1.24). Reason: in trial runs agents worked only about 60% of days and
  fresh food spoils, so a capacity below need produced collapse rather than scarcity.

## v1: First full engine and trial runs (`logs_trial_A`, `logs_A_v1`, `logs_A_broken`)

| Problem observed | Fix |
|---|---|
| `qwen3:8b` ignored stamina and its own state | Switched to `qwen3:14b` |
| Some calls generated JSON endlessly and froze the run | Output length cap and a per-call timeout |
| Runs stopped silently when Ollama became unreachable | Wait up to 30 minutes, then stop with progress saved and print the resume command |
| Nobody shared; when the rules were unclear, "gifts" appeared inside private messages without any transfer | Gifts became a separate, free, public act at the campfire, rather than a daily action costing a whole day |
| In cooperative fishing, failing to agree still paid the team bonus, rewarding the harder bargainer | No agreement means the bonus is lost and each keeps its own catch |
| One bad week pushed agents into permanent exhaustion | Overnight recovery for agents who ate at least half their need; resting kept possible while hungry |
| Every action cost the same and every food spoiled at the same rate | Per-action stamina costs (clams light, climbing and building heavy); per-food spoilage (fish 40% ... cans 0%); a stamina bonus for eating fish |

## v2-v3: Typhoon and credit (`logs_A_v3_noloans` is the last run before loans)

| Problem observed | Fix |
|---|---|
| The typhoon barely mattered: agents simply foraged instead of fishing | The typhoon blocks fishing, cooperative fishing, coconuts, forest and building: only clams remain; a forecast is given at the start of the week |
| An agent with no food faced no consequences and had no way to obtain food except begging | Loans: interest, due day, automatic repayment, public default, collection of overdue debt |
| First credit version: no loans at all; agents misread the forecast and did no forward planning | A weekly food budget computed by the simulator; a credit intention in the weekly plan; a clearer forecast |
| Overcorrection: almost everyone planned to lend, including to their own family | Budgets computed per household; "usually neither" as the default; no loans or trades within a family |
| In a test, all three members of one family borrowed separately (one of them twice) for a single shortfall | A household borrowing limit, checked when a loan is proposed *and* when it is accepted |
| On days 4-5 after the typhoon everyone still gathered clams; the warning still read "a typhoon will hit on days 1-3" | Day-specific messages ("typhoon today, day 2 of 1-3" / "the typhoon is over") and a note on how crowded the tide pools were yesterday |
| A borrower was declared in default while his wife held enough food | Repayment draws on the borrower first, then on his family (the household already shares food) |
| The lender (Pete) believed *he* owed the borrower and handed the loan amount over again as a gift | The lender is told explicitly that the food was already handed over and he owes nothing |
| Agents making proposals in the last message round (which can never be answered) failed validation three times, losing the whole round including their replies | Such proposals are dropped silently and the rest of the answer is kept |
| Long messages were cut off mid-JSON | Higher output limit; messages limited to three sentences |
| Turning a VPN on or off on the laptop broke the connection to the local model | The client talks to `127.0.0.1` directly and ignores proxy settings |
| A household's budget showed a large surplus while in reality it ran out of food that week, because expected production assumed best work at 80% of days | Expected production blends the formula with each agent's *actual* output on its last five normal days; the budget shows food that would rot by week's end; options with less than half the best yield are marked "low yield"; agents with no loans are told so; the lendable amount keeps a one-day safety buffer |

## v4: First full A/B pilot (`logs_A_v4`, `logs_B_v4`)

Group A completed 8 weeks; group B was stopped in week 7. Two bugs and a data gap were found.

| Problem | Evidence | Fix (v5) |
|---|---|---|
| **Starving while resting cost nothing.** Rest +15 (capped at 100) minus starvation -10 left a starving agent at 90 stamina indefinitely | Bob (group A) starved on 17 days and stayed at stamina 90 while resting "waiting for Alice's guidance" | A falling stamina cap for consecutive starving days (60, then -10 per day, floor 30), stated in the rules |
| **Misleading unit for canned food.** The rules said "1 can = 3 units", but internally cans were already counted in units | In group B, Kurt cut a requested loan from 4.5 to 1.99 units but left the repayment at 2.5 (26% interest); Alice accepted, reading "1.99 can" as 5.97 units | The rules say canned food is counted in units; deals read "X units of can"; every loan shows its interest rate |
| Cancelled cooperative-fishing trips (partner too exhausted, typhoon) were not recorded | 3 accepted deals in group A never happened | Cancellations are logged with the reason and both agents' stamina |

v5 also added `--run N` (paired seeds per replication, separate log folders).

## v5 -> v6: Design changes before the main experiment (`*_r1_v5_partial`)

Replication 1 was started on v5 and stopped after 3-4 weeks to change the experimental
conditions. These are design decisions, not bug fixes, and are documented as such:

| Observation | Change (v6) |
|---|---|
| Alice offered a 20% loan to 10-year-old Lucky, whose family had plenty, "to build trust" with his parents; Lucky accepted, repaid 0.6 automatically, and also "repaid" 1.4 more in campfire gifts, paying 2.0 for a 0.5 loan | **Children cannot borrow, lend, trade or hand out food**; they can receive gifts |
| Loans repeatedly offered for social reasons ("to build trust", "to encourage sharing") to agents who were not short, often the richest agent | **A loan is cancelled if the borrower's household has no shortfall**; the rules state that goodwill is expressed with gifts, not loans |
| Agents gave or lent food their own household needed | **Gifts and loans together are limited to the household's weekly safe surplus**; no gifts within a household |
| Borrowers kept "repaying" through gifts after the debt was cleared | Borrowers are reminded that repayment is automatic and gifts do not count |
| Agents could not tell who had the means to help: they saw that Pete went fishing but not his catch or his gear | **Tools carried and each person's daily catch are public**; food holdings stay private |

## v6.1: Duplicate deals (applied during replication 1)

- **Evidence:** in replication 1 (group B, week 3) Pete offered Alice a loan of 2 for 2.5; Alice
  accepted it *and* sent the same deal back as a new proposal; Pete re-sent his offer as well. All
  three were accepted: Alice received 6 units and owed 7.5, defaulting on all three during the
  typhoon, while Pete said in the next round "I've already lent you 2 units".
- **Fix:** an identical open or accepted deal between the same two agents in the same week is not
  created again; the sender is told to answer the existing proposal instead.
- Replication 1 was resumed with the fix from group A week 5 and group B week 4. The incident
  occurred once (B, week 3) and is flagged in the analysis.

## v6.2: Borrowers' requests silently discarded (applied after replication 1)

- **Evidence:** across replication 1 there were 18 contact-phase fallbacks, 4 in group A and 14 in
  group B, 11 of them by Alice, the agent most often in need. Nearly all had the same cause: a
  borrower filled the loan's `give_amount` (meaning *the food the lender hands over*) as 0,
  reading it as "what I give". After three invalid tries the *whole* round was replaced by an empty
  answer, so the agent's messages and its replies to others were lost too. In group B's last week
  Kurt and Stella, both starving, tried to borrow and failed this way.
- **Why it matters:** it suppressed credit requests from exactly the agents who needed credit, and
  more in B than in A, so it biases the A/B comparison of the credit market in replication 1.
- **Fix:** a proposal with no amounts at all is kept as a plain message; a half-filled one gets a
  role-specific correction with an example; if all tries fail, the broken proposal is dropped but
  the message text and valid replies are kept. The help text includes a worked borrowing example.
- **Why it was missed for two check-ins:** see [`00-methodology.md`](00-methodology.md) and
  [`06-validation.md`](06-validation.md).
- Replication 2 was restarted from the beginning on v6.2.

---

## Pilot observations worth keeping (not results)

These come from development runs under rules that later changed. They are recorded because they
shaped the design and the analysis plan, not as evidence for the hypotheses.

- **Lending as a social gesture.** Kurt and Alice repeatedly offered loans to Pete, the richest
  agent, explicitly "to build trust" or to persuade him to share; Pete refused, saying he could not
  commit to repaying and needed to keep his own supply stable. This persisted even after daily catches were made public.
- **Agreement without transfer.** Kurt and Alice spent three weeks agreeing in private messages
  that food should be pooled "fairly", without either ever naming an amount or moving any food.
- **Persona-consistent exceptions.** Pete, unwilling to share with adults, repeatedly gave fish to
  Lucky and split cooperative catches equally with him when Lucky had caught nothing.
- **Self-sacrifice inside a household.** During the typhoon Alice went on half rations until she
  collapsed while Bob, holding food, kept eating full rations.
- **A debt cycle.** In one reputation-group run Pete lent to Alice almost every week at 25-33%;
  her repeated defaults triggered daily collection of her household's food, and each new loan was
  largely used to repay the previous one.
- **Repetition.** Agents sometimes sent near-identical messages round after round and did not adapt
  after being refused several times.
