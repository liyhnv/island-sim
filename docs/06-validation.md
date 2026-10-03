# Validation: How the Simulator and Each Run Are Checked

## Before a change is used in an experiment

1. **Mock runs.** A full 8-week run of both groups with random, schema-valid answers instead of an
   LLM (`python3 run.py --group A --run 1 --mock`). This exercises every code path, including
   invalid answers, at no cost.
2. **Scripted scenarios.** Small scripts that replay a specific situation with chosen answers and
   assert the outcome, for example: a family trying to borrow three times for one shortfall (only
   one loan may go through); a debt due when the borrower is empty but his wife is not (the family
   pays); a child proposing a loan, a child handing out food, a gift larger than the safe surplus
   (all rejected with the right message); the same loan offered, accepted and re-sent (one loan
   only); a borrower sending zero amounts or a half-filled request (kept as talk / salvaged).
   Each new fix is added as a scenario and the earlier scenarios are re-run.
3. **Deployment check.** The files on the experiment machine are compared by checksum with the
   tested files before a run is started or resumed (an AI Town lesson: a change that silently
   fails to deploy produces data from the wrong code).

## During and after every run: `analysis/check_run.py`

```bash
python3 analysis/check_run.py logs/A_r2 logs/B_r2
```

| Check | What would indicate a problem |
|---|---|
| Food conservation | Island food today differs from yesterday + production - consumption (minus spoilage at week boundaries); gifts, loans and trades must net to zero |
| Starvation cap | An agent's stamina above the cap for its current run of starving days |
| Safe surplus | A household giving plus lending more in a week than its weekly safe surplus |
| Children | Any loan, trade or gift-giving involving Lucky |
| Loan targets | A loan to a household whose budget showed no shortfall |
| Family gifts | A gift between members of the same household |
| Fallbacks, per agent and phase, with reasons | Any concentration on one agent, phase or group (see below) |
| Credit intent -> action | An agent who planned to borrow or lend but never managed to send a proposal |

The first six check that **rules were applied**. The last two check that **intended actions were
not silently lost**, which the first six cannot see: a request that never reaches anyone does not
violate any rule, it just leaves a gap in the data.

## Why the last two checks were added

During replication 1, fallback counts were printed at every check-in (3, then 9, then 18), but they
were only looked at as totals and judged small. Read per agent and per group, they showed that
almost all of them were the same agent (Alice) failing to submit borrowing requests, and that they
were three times as frequent in group B as in group A: a systematic bias, not noise (see
[`05-development-log.md`](05-development-log.md), v6.2). Fallbacks are now always broken down by
agent, phase, group and reason, and any agent whose planned credit action never reached anyone is
listed.

## What these checks cannot catch

- Whether an agent's reasoning is sensible. Poor choices made with correct information are
  data, not errors.
- Whether the agents understood the rules the way they are written. Misunderstandings show up only
  in the stated reasons and messages, which are read manually for every run.
- Problems in the model server itself (for example, sampling differences caused by running two
  groups in parallel or by changing Ollama settings between sessions).
