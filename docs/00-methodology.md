# How This Code Was Written

As in the AI Town phase, the code was written with AI assistance (an LLM coding assistant) working under my direction. I say this up front because any reader could fairly ask about it, and because the parts of the work that matter for this project are the ones I did myself.

## What I did

- **Research design.** I chose the question (does the scoring rule an agent is told about change how a scarce economy behaves?), the A/B manipulation, the hypotheses, and which parts of Agentopia to adopt (see [`02-borrowing-from-agentopia.md`](02-borrowing-from-agentopia.md)).
- **Setting the world's parameters.** One example is the production coefficients. I asked for Kurt and Stella to be clearly more productive than the elderly couple, and for Pete's advantage to be reduced so that his surplus was large but not absurd. I also set different stamina costs for different kinds of work and different spoilage rates for different foods.
- **Insisting on realism and catching unrealistic behaviour.** Many of the rule changes in [`05-development-log.md`](05-development-log.md) started from questions I raised while reading the logs. 1:1 barter between foods of different value is unrealistic. Agents with no food faced no consequences. Loans need a real motive, a sensible amount and a repayment plan. A 10-year-old should not be borrowing or lending. "I want to encourage sharing" should lead to a gift rather than a loan. Nobody should give away food their own household needs. Agents should be able to see who carries the fishing gear and what each person brings back.
- **Running the experiments.** I ran all experiments on my own laptop with a local model. This included managing interruptions (VPN changes, sleep, running other projects), resuming runs, and deciding when a run had to be stopped and restarted.
- **Reading the data and deciding what counts as a bug.** Halfway through, the assistant and I agreed on an explicit rule. I fix the code only when the program computes something wrong or shows the agents wrong or misleading information. When agents make poor choices with correct information, I keep the result and report it as a finding (see [`07-limitations.md`](07-limitations.md)).
- **Choosing replication over a single run.** I made this choice once it was clear that one run per group could not separate the effect of the incentive from luck.

## What the AI assistant did

It wrote and revised the Python code, prompts and validators to my specifications. Before each change was deployed, it ran mock (no-LLM) tests and scripted scenario tests. It checked that the deployed files on my machine matched the tested ones, and it helped inspect the logs after each run.

## Being honest about the process

The assistant's checks were not perfect. One serious bug was visible in the error counts for two check-ins before anyone understood it. Borrowers were mis-filling the loan amounts, and this silently discarded their whole message round (see [`05-development-log.md`](05-development-log.md), v6.2). The checks missed it because they looked at whether rules were *violated* and not at whether intended actions *failed to happen*. As a result, the check list was extended ([`06-validation.md`](06-validation.md)). I report this because it is the reason the first full run on v6 was treated as a pilot.
