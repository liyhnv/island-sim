# Known Limitations (written before the results)

## What the results can and cannot claim

- **These are LLM agents, not people.** Nothing here shows how humans would behave under the same
  incentives. The claim is limited to how a society of agents driven by one model responds to a
  change in the scoring rule it is told about. Every comparison is within the same model, rules
  and seeds, so the A/B *difference* is interpretable even where individual behaviour is not
  human-like.
- **Small samples.** 6 agents, 40 days, 2-3 main replications per group. Results are exploratory:
  consistent directions and effect sizes, not significance tests.
- **The incentive is only described, never experienced.** Unlike Agentopia, no reward is fed back
  and no model is trained. What is manipulated is a sentence in the prompt.
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
- **Scores computed after the fact.** The life reward is computed from the logs with the formula
  described to the agents; an agent cannot know how well it is doing during the run.

## The process

- **Many iterations.** The rules changed substantially during development
  ([`05-development-log.md`](05-development-log.md)). Only runs on the final version (v6.2) are
  used as main evidence; earlier runs are kept for transparency.
- **Replication 1 is not clean.** It ran on v6 with the duplicate-deal fix applied mid-run, and it
  suffered from the borrower-request bug, which hit group B three times as often as group A. It is
  reported as supplementary only.
- **Hardware and interruptions.** Runs were executed on a laptop, two groups in parallel against
  one model server, with pauses (sleep, network changes, other workloads). Progress is saved after
  every stage and resumed exactly, but server settings and load can differ between sessions.
- **AI-assisted implementation** (see [`00-methodology.md`](00-methodology.md)). Errors in the
  checks themselves are possible; one bug went unnoticed for two check-ins because of how the
  checks were designed.
