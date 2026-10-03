# Known Limitations (written before the results)

## What the results can and cannot claim

- **These are LLM agents, not people.** Nothing here shows how humans would behave under the same
  incentives. The claim is limited to how a society of agents driven by one model responds to a
  change in the scoring rule it is told about. Every comparison is within the same model, rules
  and seeds, so the A/B *difference* is interpretable even where individual behaviour is not
  human-like.
- **Small samples.** 6 agents, 20 action days, two replications per group in the feedback
  condition and one (possibly two) without feedback. Results are exploratory:
  consistent directions and effect sizes, not significance tests.
- **No learning.** Unlike Agentopia, no model is trained on the reward. Without feedback the
  incentive is only a sentence in the prompt; with feedback the agent also sees its own score, but
  can react to it only through its context within one 4-week season.
- **Outcome vs mechanism.** A result can match a hypothesis for the wrong reason. The analysis
  therefore codes the reasons agents give for each choice (see
  [`04-experiment-design.md`](04-experiment-design.md)); where outcome and stated reason disagree,
  both are reported.

## The model

- **Bounded and inconsistent rationality.** `qwen3:14b` (run locally because of cost and
  hardware) makes arithmetic slips (cutting a loan's principal but not its repayment), follows its
  persona against its own interest (lending to the richest agent "to build trust"), repeats itself
  across rounds, and sometimes forgets that a debt was already repaid. Larger models would likely
  make fewer of these errors; the main experiment has not been repeated with another model.
- **Agreeable by training.** Chat models tend to agree and to talk in principles ("we should share
  fairly") rather than make concrete, costly commitments. The observed gap between what agents say
  and what they do partly reflects this, not only the incentives.
- **Persona dominance.** Strongly written personas (Alice the moral voice, Pete the self-reliant
  provider, Lucky who agrees with the last adult) may outweigh a one-sentence change in the
  scoring rule, which would bias the study toward finding no effect.
- **Stochasticity.** Sampling at temperature 0.7 means the same situation can produce different
  choices; replications address this only partially.

## The design

- **Scaffolding shapes behaviour.** The simulator computes a weekly budget with a recommended
  amount to borrow or a safe amount to lend, marks low-yield options, and states several norms
  in the rules (loans are for shortfalls, goodwill is expressed with gifts). Some of this exists
  because, without it, behaviour was not interpretable at all; but it means part of the observed
  "economic rationality" was supplied by the designer.
- **Hard rules trade realism for emergence.** Rules such as "children cannot borrow" or "no gifts
  beyond the safe surplus" make behaviour more sensible by construction. They are part of the
  world, the same in both groups, but they limit what can emerge (for example, a parent cannot
  sacrifice beyond the household's surplus to feed another family's child).
- **A fixed action menu.** Some intentions have no matching action (there is no way to "pool
  everyone's food"), so they can only be talked about; part of the say-do gap is created by the
  action space.
- **Simplified world.** Rule-computed outcomes instead of an LLM environment; no space, no chance
  encounters; building the shelter has no effect on anything (an unused design element);
  production values are calibrated, not empirical.
- **Private holdings.** Agents cannot see each other's food. This is realistic but makes it hard
  to direct help or credit to whoever needs it, and it interacts with the hypotheses.
- **Few transactions.** Barter almost never happens and credit is thin, so H2 rests on a small
  number of loans and cooperative trips per run.
- **Score scales are a design choice.** The fixed 0-100 scales (for example, 5 points per unit of
  food) decide how much each part can move. Other reasonable scales would weight the parts
  differently in practice, and agents in the feedback condition react to these particular numbers.
- **One shock, one season.** Four weeks with a single typhoon cannot show long-run dynamics
  (reputation built over many seasons, end-game effects); H3 was dropped for this reason.

## The process

- **Many iterations.** The rules changed substantially during development
  ([`05-development-log.md`](05-development-log.md)). Only runs on v6.2 / v7 are used as evidence;
  earlier runs were pilots.
- **The design was revised after seeing data.** The switch to 4 weeks and the addition of score
  feedback (v7) were decided after reading weeks 1-4 of replication 2. The reasons are documented,
  and the feedback replications are run fresh, but the no-feedback comparison rests on that one
  run.
- **Persona drift may be scripted by persona.** In replication 2 every agent's generosity and
  trust moved identically in A and B, which suggests that the season update follows the persona
  and the events more than the incentive.
- **Hardware and interruptions.** Runs were executed on a laptop, two groups in parallel against
  one model server, with pauses (sleep, network changes, other workloads). Progress is saved after
  every stage and resumed exactly, but server settings and load can differ between sessions.
- **AI-assisted implementation** (see [`00-methodology.md`](00-methodology.md)). Errors in the
  checks themselves are possible; one bug went unnoticed for two check-ins because of how the
  checks were designed.
