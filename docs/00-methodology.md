# A Note on Methodology: How This Code Was Written

As in the AI Town phase, the implementation was produced with AI assistance (an LLM coding
assistant) working under my direction. I am stating this up front because it is a fair question
for any reader, and because the parts of the work that matter for this project are the ones I did
myself.

## What I did

- **Research design.** Chose the question (does the scoring rule an agent is told about change
  how a scarce economy behaves?), the A/B manipulation, the hypotheses, and which parts of
  Agentopia to adopt (see [`02-borrowing-from-agentopia.md`](02-borrowing-from-agentopia.md)).
- **Setting the world's parameters.** For example, the production coefficients (I asked for Kurt
  and Stella to be clearly more productive than the elderly couple, and for Pete's advantage to be
  reduced so that his surplus was large but not absurd), different stamina costs for different
  kinds of work, and different spoilage rates for different foods.
- **Insisting on realism and catching unrealistic behaviour.** Many of the rule changes in
  [`05-development-log.md`](05-development-log.md) started from my questions while reading the
  logs: that 1:1 barter between foods of different value is unrealistic; that agents with no food
  faced no consequences; that loans need a real motive, a sensible amount and a repayment plan;
  that a 10-year-old should not be borrowing or lending; that "I want to encourage sharing" should
  lead to a gift rather than a loan; that nobody should give away food their own household needs;
  that agents should be able to see who carries the fishing gear and what each person brings back.
- **Running the experiments.** All runs were executed on my own laptop with a local model,
  including managing interruptions (VPN changes, sleep, running other projects), resuming runs, and
  deciding when a run had to be stopped and restarted.
- **Reading the data and deciding what counts as a bug.** We agreed on an explicit rule halfway
  through: fix the code only when the program computes something wrong or shows the agents wrong
  or misleading information; when agents make poor choices with correct information, keep it and
  report it as a finding (see [`07-limitations.md`](07-limitations.md)).
- **Choosing replication over a single run** once it was clear that one run per group could not
  separate the effect of the incentive from luck.

## What the AI assistant did

Wrote and revised the Python code, prompts and validators to my specifications, ran mock (no-LLM)
tests and scripted scenario tests before each change was deployed, verified that the deployed files
on my machine matched the tested ones, and helped inspect the logs after each run.

## Being honest about the process

The assistant's checks were not perfect. One important bug (borrowers mis-filling the loan
amounts, which silently discarded their whole message round, see
[`05-development-log.md`](05-development-log.md), v6.2) was visible in the error counts for two
check-ins before it was understood, because the checks looked at whether rules were *violated* and
not at whether intended actions *failed to happen*. The check list was extended as a result
([`06-validation.md`](06-validation.md)). I report this because it is why the first full run on v6 was
treated as a pilot.
