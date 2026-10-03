# Incentives Under Scarcity: A Turn-Based LLM Agent Society on a Shipwreck Island

A small, fully logged multi-agent simulation in which six LLM-driven survivors share a food-scarce
island for eight weeks. Two groups play the **same world with the same random luck**; the only
difference is the scoring rule the agents are told they will be judged by:

- **Group A (individualist):** your score depends mainly on the food you personally hold.
- **Group B (reputation):** your score depends mainly on how much the others like and respect you.

The question is whether, and how, that one sentence changes sharing, lending, inequality and who
goes hungry, and whether the changes happen for the reasons we expect.

This repository is the second phase of a project that started with a modified
[AI Town](https://github.com/a16z-infra/ai-town) (see the companion repository
**ai-town-island-research**). The turn-based design here borrows its time structure and reward
design from **Agentopia: Long-Term Life Simulation and Learning in Agent Societies**
([arXiv:2606.07513](https://arxiv.org/abs/2606.07513)).

> **Status (2026-10-03):** the simulator is complete and frozen for the main experiment.
> Replication 1 has finished; replication 2 is running; replication 3 is planned.
> **No results are reported here yet.** This README and `docs/` cover everything *up to* the
> results: design, what was borrowed from Agentopia and what was changed, every rule change made
> during development and why, the integrity checks, and the limitations already known.
> A results section will be added once all replications are complete and analysed.

## At a glance

| | |
|---|---|
| Agents | 6 (Kurt, Stella and their 10-year-old son Lucky; elderly couple Alice and Bob; Pete, travelling alone), personas carried over from the AI Town phase |
| Model | `qwen3:14b`, run locally with Ollama (thinking off, JSON-schema constrained output, temperature 0.7) |
| Time | 8 weeks x 5 action days = 40 days; each week = Plan -> Contact (3 rounds of private messages) -> 5 x (Action -> Eat -> Campfire) -> Review; seasons end after weeks 4 and 8 |
| Economy | 5 food types with different spoilage, per-action stamina costs, households that share food, gifts, barter, loans with interest and public default, cooperative fishing with a negotiated split |
| Shocks | Typhoon in week 3 (days 1-3: only clam gathering possible, forecast at the start of the week); radio in week 5 (rescue at the end of week 8) |
| Manipulation | Scoring rule in the prompt: A = 0.6 economic / 0.2 social / 0.2 subjective; B = 0.2 / 0.6 / 0.2 |
| Design | Paired A/B runs with the same seed per replication (42, 43, 44, ...) |
| Logs | Every plan, message, action, trade, loan, gift, rating, persona update and model error, as JSON Lines |
| Who decides what | The LLM only decides and talks; all outcomes (yields, injuries, spoilage, repayment) are computed by fixed rules from `config.yaml` and a seeded random generator |

## Hypotheses

| | Hypothesis | Main measures |
|---|---|---|
| H1 | The reputation group (B) shares more, ends less unequal, and its weakest members (Lucky, Alice, Bob) go hungry less | gifts and loans between households, Gini of food holdings, starving days |
| H2 | During the typhoon the food-rich agent (Pete) gains bargaining power: higher interest, better splits | loan interest by week, cooperative-fishing split shares, accepted/rejected requests |
| H3 | After the rescue news (week 5) effort and cooperation fall, more so in A | share of productive actions and of transfers, weeks 1-4 vs 5-8 |
| H4 | Cross-family liking grows faster in B; A splits along family lines | secret like/respect ratings, within- vs between-family gap |

See [`docs/04-experiment-design.md`](docs/04-experiment-design.md) for the full measures and the
analysis plan, including how we will check whether outcomes arise *for the hypothesised reasons*
(using the reasons agents give for every choice).

## How to read this repository

| Read | What it covers |
|---|---|
| [`docs/00-methodology.md`](docs/00-methodology.md) | How the code was written (AI-assisted, under my direction) and what my own contribution was |
| [`docs/01-from-ai-town.md`](docs/01-from-ai-town.md) | Why the project left AI Town, what carried over, and how this design removes the bottleneck found there |
| [`docs/02-borrowing-from-agentopia.md`](docs/02-borrowing-from-agentopia.md) | Which parts of Agentopia were adopted, which were adapted, and which were deliberately left out |
| [`docs/03-world-and-rules.md`](docs/03-world-and-rules.md) | The complete rulebook of the final simulator (v6) |
| [`docs/04-experiment-design.md`](docs/04-experiment-design.md) | Conditions, replications, hypotheses, measures, analysis plan |
| [`docs/05-development-log.md`](docs/05-development-log.md) | Every version of the simulator, what went wrong, the evidence, and the fix |
| [`docs/06-validation.md`](docs/06-validation.md) | How the simulator and each run are checked, and what the checks cannot catch |
| [`docs/07-limitations.md`](docs/07-limitations.md) | Known limitations, before seeing the results |
| [`docs/08-status-and-next-steps.md`](docs/08-status-and-next-steps.md) | Which runs exist, their caveats, and what comes next |

## Code

```
config.yaml          all numeric rules, events, the A/B scoring weights
characters.json      the six agents: persona, family, items, needs, productivity
llm.py               Ollama client: JSON-schema output, retries with error feedback, wait-and-stop if Ollama is down
prompts.py           every prompt: world rules, persona, scoring rule, current situation, task
engine.py            the weekly loop, rules, validators, logging, save/resume
run.py               entry point
view_log.py          prints one run as a readable week-by-week report
calibrate.py         scarcity calibration without any LLM
analysis/check_run.py  integrity checks for a finished or running run
```

## Running it

Requires Python 3.10+, [Ollama](https://ollama.com) and about 10 GB of free memory for the model.

```bash
pip install -r requirements.txt
ollama pull qwen3:14b

python3 run.py --group A --weeks 1 --mock     # quick test without any LLM (random answers)
python3 run.py --group A --run 1              # replication 1 of group A -> logs/A_r1/, seed 42
python3 run.py --group B --run 1              # replication 1 of group B -> logs/B_r1/, same seed
python3 run.py --group A --run 1 --resume     # continue after a stop (progress is saved after every stage)

python3 view_log.py A_r1 3                    # readable report of week 3
python3 analysis/check_run.py logs/A_r1 logs/B_r1
python3 calibrate.py
```

On a 24 GB MacBook Air, one group takes roughly 1 hour per simulated week; two groups can run in
parallel against the same Ollama server.

Run logs (`logs/`, `saves/`) and older development runs (`archive/`) are not committed yet; they
will be added with the results.
