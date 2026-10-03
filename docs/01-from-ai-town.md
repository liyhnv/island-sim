# From AI Town to a Turn-Based Simulator

## Where the AI Town phase ended

In the AI Town phase (companion repository **ai-town-island-research**) the same six survivors
lived in a real-time 2D town. Three rounds of patches tried to make *who talks to whom* depend on
what agents wanted. The decision logs showed the limit of that approach: most "who should I talk
to?" decisions never reached the motivation scoring at all (52% and then 67% of invite decisions
ended in `no_candidates`), and the engine had no persistent state for commitments to specific
people, so a promise made in one conversation left no trace that could be followed up.

## What changed, and why it addresses that bottleneck

| AI Town limitation | How the island simulator handles it |
|---|---|
| Who meets whom is decided by movement, distance and cooldown, before any motivation is consulted | There is no map. In each of the three weekly message rounds every agent chooses **who** to write to (up to two people) directly, so "no eligible candidate" cannot happen |
| Motivation (`identity`, `plan`, later `currentSubGoal`) is free text, overwritten after each conversation | Each agent has explicit, persistent state: food by type, stamina, debts and credits, a weekly plan and credit intention, a diary, impressions of each other agent, a rolling memory, and a "current mindset" updated each season within limits |
| No first-class record of commitments | Proposals (trade, loan, cooperative fishing) are objects with an id and a status (open, accepted, rejected, expired, failed). Loans have a due day, are collected automatically and a default is announced to everyone |
| Real-time engine: most compute goes into walking and path-finding; time is tied to the wall clock | Discrete turns: a simulated week costs about 100-120 model calls regardless of wall-clock time, and the run can stop and resume at any stage |
| The LLM's own outputs determine what happens | The LLM only decides and talks. Yields, injuries, spoilage, eating and repayment are computed by rules from `config.yaml` and one seeded random generator, so A and B face identical luck |
| Before/after comparison inside one continuously running world (code deployed mid-run) | Freshly seeded paired runs: A and B start from the same state and seed; replications use new seeds |

## What carried over

- **The cast and their personas**, translated from the AI Town character definitions:
  Kurt (organiser, wants pooled rationing), Stella (protects Lucky, slow to trust), Lucky
  (10, trusting, repeats the last adult), Alice (moral voice for sharing), Bob (fearful, hides
  food, defers to Alice), Pete (best provider, distrusts pooling, soft on Lucky).
- **The scarcity question** itself: will a small group under food scarcity converge on sharing,
  hoarding, or something in between, and what drives that?
- **Auditable decisions.** The decision-logging idea from AI Town became the core of this design:
  every decision is a JSON record with the agent's stated reason, and every model failure is
  logged with whether a default had to be used.
- **"Deployment is invisible."** AI Town taught that a code change can silently fail to deploy.
  Here every change is tested in mock mode first, and the files on the experiment machine are
  compared by checksum with the tested versions before a run starts.

## What was given up

- **Space and chance encounters.** Agents cannot bump into each other, observe each other at a
  distance or gather spontaneously; all interaction happens through scheduled channels (private
  messages, the evening campfire, cooperative fishing).
- **Visual inspection.** There is nothing to watch; everything is read from logs.
- **Open-ended action.** Agents choose from a fixed menu each day. This makes the economy
  measurable, but it also means that some intentions (for example "let's pool all our food")
  have no matching action and can only be talked about, which is itself one of the things we
  observe (see [`07-limitations.md`](07-limitations.md)).
