# Development Log

This log shows how the simulator went from the original plan to the version used for the main experiment, and the evidence behind each change. Folder names in `archive/` refer to the run logs kept for each stage (not yet committed).

I adopted one rule halfway through, and it governs everything after that point:

> **Fix the code only when the simulator computes something wrong, or shows the agents wrong or misleading information. When agents make poor choices with correct information, keep the behaviour and report it.**

Before that rule, several changes did nudge behaviour through the prompts (budgets, credit hints, warnings). I list them here so the reader can judge how much of the agents' behaviour comes from scaffolding. See also [`07-limitations.md`](07-limitations.md).

---

## v0. Plan and calibration (late September)

- I started from the plan: 6 agents, rule-computed outcomes, uniform 20% weekly spoilage, a target of full-effort output at 80-90% of need, and `qwen3:8b`.
- I added per-agent **productivity** multipliers so that the old couple and the child produce less than the adults, and Pete produces the most. The values were tuned on request. Kurt and Stella were raised and Pete's advantage was lowered (final: Pete 1.2, Kurt 1.12, Stella 1.1, Alice 0.65, Bob 0.65, Lucky 0.38).
- I changed the **calibration target** from 0.80-0.90 to 1.10-1.25 of need, measured with a greedy "full effort" policy (1.24). The reason is that in trial runs agents worked only about 60% of days and fresh food spoils, so a capacity below need led to collapse instead of scarcity.

## v1. First full engine and trial runs (`logs_trial_A`, `logs_A_v1`, `logs_A_broken`)

| Problem observed | Fix |
|---|---|
| `qwen3:8b` ignored stamina and its own state | Switched to `qwen3:14b` |
| Some calls generated JSON endlessly and froze the run | Output length cap and a per-call timeout |
| Runs stopped without warning when Ollama became unreachable | Wait up to 30 minutes, then stop with progress saved and print the resume command |
| Nobody shared. When the rules were unclear, "gifts" appeared inside private messages without any transfer | Gifts became a separate, free, public act at the campfire, instead of a daily action that cost a whole day |
| In cooperative fishing, failing to agree still paid the team bonus, which rewarded the harder bargainer | No agreement means the bonus is lost and each agent keeps its own catch |
| A family did not feed its own child: at the end of week 2 Kurt held 7.7 units and Stella 8.9, while their son Lucky had 0. Each person's food was counted separately and the model never thought of giving food to family | Families became households: whoever runs out eats from family members' food. Sharing across households still needs a gift, trade or theft, so the cross-household measures in H1 are not affected. Food eaten from family is logged separately (`from_family`) |
| Starving cost nothing: Bob ate nothing from week 1 day 2 onward, rested every day and stayed at 90 stamina, so he had no reason to ask for help | A starving day gives no overnight recovery and costs 10 stamina. After two or more starving days, the others can see that he "looks weak". (A loophole remained and was closed in v5, see below) |
| Campfire lines and messages repeated themselves: Pete said "I won't share unless I can trust you" five nights in a row, and Lucky said "I talked to Alice and Bob" every day | The campfire and message instructions ask agents not to repeat earlier lines and to respond to what happened that day, or to ask someone a direct question |
| One bad week pushed agents into permanent exhaustion | Overnight recovery for agents who ate at least half their need. Resting is still possible while hungry |
| Every action cost the same and every food spoiled at the same rate | Per-action stamina costs (clams light, climbing and building heavy). Per-food spoilage (fish 40% ... cans 0%). A stamina bonus for eating fish |

## v2-v3. Typhoon and credit (`logs_A_v3_noloans` is the last run before loans)

| Problem observed | Fix |
|---|---|
| The typhoon barely mattered, because agents just foraged instead of fishing | The typhoon blocks fishing, cooperative fishing, coconuts, forest and building, so only clams remain. A forecast is given at the start of the week |
| An agent with no food faced no consequences and could only get food by begging | Loans with interest, a due day, automatic repayment, public default, and collection of overdue debt |
| In the first credit version there were no loans at all. Agents misread the forecast and did no planning ahead | A weekly food budget computed by the simulator, a credit intention in the weekly plan, and a clearer forecast |
| This overcorrected. Almost everyone planned to lend, including to their own family | Budgets computed per household, "usually neither" as the default, and no loans or trades within a family |
| In a test, all three members of one family borrowed separately (one of them twice) for a single shortfall | A household borrowing limit, checked when a loan is proposed *and* when it is accepted |
| On days 4-5 after the typhoon everyone still gathered clams. The warning still read "a typhoon will hit on days 1-3" | Day-specific messages ("typhoon today, day 2 of 1-3" / "the typhoon is over") and a note on how crowded the tide pools were yesterday |
| A borrower was declared in default while his wife held enough food | Repayment draws on the borrower first, then on his family (the household already shares food) |
| The lender (Pete) believed *he* owed the borrower and handed over the loan amount again as a gift | The lender is told directly that the food was already handed over and he owes nothing |
| Agents who made proposals in the last message round (which can never be answered) failed validation three times and lost the whole round, including their replies | Such proposals are dropped without notice and the rest of the answer is kept |
| Long messages were cut off mid-JSON | Higher output limit, and messages limited to three sentences |
| Turning a VPN on or off on the laptop broke the connection to the local model | The client talks to `127.0.0.1` directly and ignores proxy settings |
| A household's budget showed a large surplus while in reality it ran out of food that week, because expected production assumed best work at 80% of days | Expected production blends the formula with each agent's *actual* output on its last five normal days. The budget shows food that would rot by the end of the week. Options with less than half the best yield are marked "low yield". Agents with no loans are told so. The lendable amount keeps a one-day safety buffer |

## v4. First full A/B pilot (`logs_A_v4`, `logs_B_v4`)

Group A completed 8 weeks. Group B was stopped in week 7. I found two bugs and a data gap.

| Problem | Evidence | Fix (v5) |
|---|---|---|
| **Starving while resting cost nothing.** Rest +15 (capped at 100) minus starvation -10 left a starving agent at 90 stamina indefinitely | Bob (group A) starved on 17 days and stayed at stamina 90 while resting "waiting for Alice's guidance" | A falling stamina cap for consecutive starving days (60, then -10 per day, floor 30), stated in the rules |
| **Misleading unit for canned food.** The rules said "1 can = 3 units", but internally cans were already counted in units | In group B, Kurt cut a requested loan from 4.5 to 1.99 units but left the repayment at 2.5 (26% interest). Alice accepted, reading "1.99 can" as 5.97 units | The rules say canned food is counted in units, deals read "X units of can", and every loan shows its interest rate |
| Cancelled cooperative-fishing trips (partner too exhausted, typhoon) were not recorded | 3 accepted deals in group A never happened | Cancellations are logged with the reason and both agents' stamina |

v5 also added `--run N` (paired seeds per replication, separate log folders).

## v5 to v6. Design changes before the main experiment (`*_v5_partial`)

A pilot run on v5 (seed 42) was stopped after 3-4 weeks so I could change the experimental conditions. These are design decisions, not bug fixes, and I document them that way.

| Observation | Change (v6) |
|---|---|
| Alice offered a 20% loan to 10-year-old Lucky, whose family had plenty, "to build trust" with his parents. Lucky accepted, repaid 0.6 automatically, and also "repaid" 1.4 more in campfire gifts, so he paid 2.0 for a 0.5 loan | **Children cannot borrow, lend, trade or hand out food.** They can receive gifts |
| Loans were offered again and again for social reasons ("to build trust", "to encourage sharing") to agents who were not short, often the richest agent | **A loan is cancelled if the borrower's household has no shortfall.** The rules state that goodwill is shown with gifts, not loans |
| Agents gave or lent food their own household needed | **Gifts and loans together are limited to the household's weekly safe surplus.** No gifts within a household |
| Borrowers kept "repaying" through gifts after the debt was cleared | Borrowers are reminded that repayment is automatic and gifts do not count |
| Agents could not tell who was able to help. They saw that Pete went fishing but not his catch or his gear | **Tools carried and each person's daily catch are public.** Food holdings stay private |

## v6.1. Duplicate deals (found in the v6 pilot)

I then ran a full pilot pair on v6 (seed 42). I used it to find problems, not as data.

- **Evidence.** In the v6 pilot (group B, week 3) Pete offered Alice a loan of 2 for 2.5. Alice accepted it *and* sent the same deal back as a new proposal, and Pete sent his offer again too. All three were accepted. Alice received 6 units and owed 7.5, and she defaulted on all three during the typhoon, while Pete said in the next round "I've already lent you 2 units".
- **Fix.** An identical open or accepted deal between the same two agents in the same week is not created again. The sender is told to answer the existing proposal instead.
- The pilot was resumed with the fix. The incident occurred once.

## v6.2. Borrowers' requests discarded without notice (found in the v6 pilot)

- **Evidence.** Across the v6 pilot there were 18 contact-phase fallbacks, 4 in group A and 14 in group B. Alice, the agent most often in need, had 11 of them. Nearly all had the same cause. A borrower filled the loan's `give_amount` (meaning *the food the lender hands over*) as 0, reading it as "what I give". After three invalid tries the *whole* round was replaced by an empty answer, so the agent's messages and its replies to others were lost as well. In group B's last week, Kurt and Stella were both starving, tried to borrow, and failed this way.
- **Why it matters.** It suppressed credit requests from exactly the agents who needed credit, and more in B than in A, so it would have biased the A/B comparison of the credit market.
- **Fix.** A proposal with no amounts at all is kept as a plain message. A half-filled one gets a role-specific correction with an example. If all tries fail, the broken proposal is dropped but the message text and valid replies are kept. The help text includes a worked borrowing example.
- **Why it was missed for two check-ins.** See [`00-methodology.md`](00-methodology.md) and [`06-validation.md`](06-validation.md).
- The first main replication (seed 43, `--run 2`) was started from the beginning on v6.2. It ran cleanly, with no fallbacks, and all checks in [`06-validation.md`](06-validation.md) passed.

## v7. Four weeks, one shock, and score feedback (design change)

These are design decisions, not bug fixes. I made them after reading weeks 1-4 of the first main replication (with scores hidden).

| Observation | Change (v7) |
|---|---|
| The original plan ran 8 weeks with two events, the typhoon (week 3) and a radio message announcing a rescue (week 5), to test an end-game effect (H3). In the first main replication, the typhoon's after-effects (debts, depleted holdings, starving households) were still unfolding in weeks 4-5, so any change after the radio could not be separated from the aftermath of the typhoon | **One season of 4 weeks with the typhoon only.** The radio event and H3 were removed and left to future work. This also halves the cost of a run (about 6 hours per A/B pair), which allows more replications in the time available |
| The reputation incentive had no visible consequence. Pete in group B was rated low week after week, kept refusing every loan and gift request, and showed no sign of knowing how others saw him. His stated reasons were the same as in group A | **Score feedback** as a second factor (`--feedback`). After every weekly review each agent sees its own season total, rank and the three parts, but never who rated it how |
| The life reward was only going to be computed after the run | The season score is computed after every weekly review and logged in `scores.jsonl` in every run, with or without feedback |
| A first version scaled each part relative to the other agents (min-max), which turned tiny differences into large swings | Fixed 0-100 scales. Food is 50 + 5 x change in own food. Reputation is scaled so that an average agent scores 50. Well-being comes from fullness, stamina and belonging |

This run (now labelled A/B-hidden-1) was stopped after week 5. Its weeks 1-4 are the no-feedback comparison for seed 43 (see [`04-experiment-design.md`](04-experiment-design.md)). All other main runs use v7: scores shown for replications 1 to 4, and scores hidden for replications 2 to 4. Replications 3 and 4 were added after the first eight runs, with no code changes.

---

## Pilot observations worth keeping (not results)

These come from development runs under rules that later changed. I record them because they shaped the design and the analysis plan, not as evidence for the hypotheses.

- **Lending as a social gesture.** Kurt and Alice offered loans to Pete, the richest agent, many times, saying openly that it was "to build trust" or to persuade him to share. Pete refused. He said he could not commit to repaying and needed to keep his own supply stable. This continued even after daily catches were made public.
- **Agreement without transfer.** Kurt and Alice spent three weeks agreeing in private messages that food should be pooled "fairly", but neither of them ever named an amount or moved any food.
- **Exceptions that fit the persona.** Pete was unwilling to share with adults, but he gave fish to Lucky many times and split cooperative catches equally with him when Lucky had caught nothing.
- **Self-sacrifice inside a household.** During the typhoon Alice went on half rations until she collapsed, while Bob, who held food, kept eating full rations.
- **A debt cycle.** In one reputation-group run Pete lent to Alice almost every week at 25-33%. Her repeated defaults triggered daily collection of her household's food, and most of each new loan went to repaying the previous one.
- **Repetition.** Agents sometimes sent near-identical messages round after round and did not adapt after being refused several times.
