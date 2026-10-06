# Known Limitations (written before the results)

## What the results can and cannot claim

- **These are LLM agents, not people.** Nothing here shows how humans would behave under the same incentives. The claim is limited to how a society of agents driven by one model responds to a change in the scoring rule it is told about. Every comparison uses the same model, rules and seeds, so the A/B *difference* can be interpreted even where individual behaviour is not human-like.
- **Small samples.** There are 6 agents, 20 action days, and four replications per group and feedback condition (sixteen runs in total). The results are exploratory. They show consistent directions and effect sizes, not significance tests.
- **No learning.** Unlike Agentopia, no model is trained on the reward. Without feedback the incentive is only a sentence in the prompt. With feedback the agent also sees its own score, but it can react only through its context within one 4-week season.
- **Outcome vs mechanism.** A result can match a hypothesis for the wrong reason. For this reason the analysis codes the reasons agents give for each choice (see [`04-experiment-design.md`](04-experiment-design.md)). Where the outcome and the stated reason disagree, both are reported.

## The model

- **Bounded and inconsistent rationality.** `qwen3:14b` (run locally because of cost and hardware) makes arithmetic slips (cutting a loan's principal but not its repayment), follows its persona against its own interest (lending to the richest agent "to build trust"), repeats itself across rounds, and sometimes forgets that a debt was already repaid. Larger models would probably make fewer of these errors. The main experiment has not been repeated with another model.
- **Agreeable by training.** Chat models tend to agree and to talk in principles ("we should share fairly") instead of making concrete, costly commitments. The gap I observed between what agents say and what they do partly reflects this, and not only the incentives.
- **Persona dominance.** Strongly written personas (Alice the moral voice, Pete the self-reliant provider, Lucky who agrees with the last adult) may outweigh a one-sentence change in the scoring rule. This would bias the study toward finding no effect. The personas are also much simpler than real people: a few fixed traits, some written as absolutes, which the model follows closely (see [`10-discussion.md`](10-discussion.md)).
- **Unequal fallback rates.** Default answers after three invalid tries were more frequent in A (19 across eight runs) than in B (7), mostly in replication 2. In replications 3 and 4 the counts were low and similar (A 3, B 5). Most were failed borrowing requests and gifts above the safe surplus. Messages were kept and only the invalid proposal was dropped, but credit requests in A are slightly under-counted.
- **Replication 1 with scores hidden ran on v6.2.** Its week-1 outcomes are not identical to the v7 run with the same seed, so the v6.2 and v7 code paths are not exactly equivalent. For seeds 44, 45 and 46, where all runs used v7, week 1 is identical across feedback conditions (see `09-results.md`).
- **Text measures are keyword proxies.** Reputation-word counts and the say-do measure flag passages. They are not a coding of reasons.
- **Persona and position are confounded.** Each persona is played by one agent, and the least generous persona (Pete) is also the richest agent. So the exploratory question of incentive vs persona can only be answered case by case.
- **Resting without a reason.** Bob often chose to rest even at full stamina, where resting gains nothing (2 to 17 of 20 days per run). This alone moves the elderly couple's hunger a lot, and it varies far more between runs than anything the scoring rule changed.
- **No reasoning about spoilage.** Food-rich agents kept food that was going to rot (fish loses 40% a week) instead of giving or lending it. Pete lost an estimated 12-19 units this way in weeks 1-3 of each run. The weekly budget shows how much he could safely lend, but the model does not seem to weigh "give it away" against "let it rot".
- **Stochasticity.** Sampling at temperature 0.7 means the same situation can lead to different choices. Replications only partly address this.

## The design

- **Scaffolding shapes behaviour.** The simulator computes a weekly budget with a recommended amount to borrow or a safe amount to lend, marks low-yield options, and states several norms in the rules (loans are for shortfalls, goodwill is shown with gifts). Some of this exists because without it the behaviour could not be interpreted at all. Still, it means that part of the observed "economic rationality" was supplied by me as the designer.
- **Hard rules trade realism for emergence.** Rules such as "children cannot borrow" or "no gifts beyond the safe surplus" make behaviour more sensible by construction. They are part of the world and the same in both groups, but they limit what can emerge. For example, a parent cannot give up more than the household's surplus to feed another family's child.
- **A fixed action menu.** Some intentions have no matching action (there is no way to "pool everyone's food"), so agents can only talk about them. Part of the say-do gap is created by the action space.
- **Simplified world.** Outcomes are computed by rules instead of an LLM environment. There is no space and there are no chance encounters. Building the shelter has no effect on anything (an unused design element). Production values are calibrated, not empirical.
- **Private holdings.** Agents cannot see each other's food. This is realistic, but it makes it hard to direct help or credit to whoever needs it, and it interacts with the hypotheses.
- **Few transactions.** Barter almost never happens and credit is thin, so H2 rests on a small number of loans and cooperative trips per run.
- **Score scales are a design choice.** The fixed 0-100 scales (for example, 5 points per unit of food) decide how much each part can move. Other reasonable scales would weight the parts differently in practice, and agents in the feedback condition react to these particular numbers.
- **One shock, one season.** Four weeks with a single typhoon cannot show long-run dynamics (reputation built over many seasons, end-game effects). I dropped H3 for this reason.

## The process

- **Many iterations.** The rules changed a lot during development ([`05-development-log.md`](05-development-log.md)). Only runs on v6.2 / v7 are used as evidence. Earlier runs were pilots.
- **I revised the design after seeing data.** I decided on the switch to 4 weeks and the addition of score feedback (v7) after reading weeks 1-4 of the first main replication. The reasons are documented, and every other main run was started fresh on v7 after that decision.
- **Persona drift may be scripted by persona.** In every main run, each agent's generosity and trust moved in the same way in A and B. This suggests that the season update follows the persona and the events more than the incentive.
- **Hardware and interruptions.** Runs were executed on a laptop, with two groups in parallel against one model server, and with pauses (sleep, network changes, other workloads). Progress is saved after every stage and resumed exactly, but server settings and load can differ between sessions.
- **AI-assisted implementation** (see [`00-methodology.md`](00-methodology.md)). The checks themselves may contain errors. One bug went unnoticed for two check-ins because of how the checks were designed.
