"""
Integrity checks for one simulation run (no LLM needed).

  python3 analysis/check_run.py logs/A_r2
  python3 analysis/check_run.py logs/A_r2 logs/B_r2      # several runs, one after another

Checks that the RULES were applied correctly and that the LLM interface did not
silently distort the data. It does not judge whether agents behaved "sensibly".

  1. Food conservation   island food(today) = food(yesterday) + produced - eaten
                         (and minus spoilage at each week boundary); transfers
                         between agents (gifts, loans, trades) must net to zero
  2. Starvation cap      stamina never exceeds the cap for consecutive starving days
  3. Safe surplus        gifts + loans given by a household in a week <= its weekly
                         safe surplus ("lendable" in the weekly budget)
  4. Minors              no loans, trades or gifts handed out by a child
  5. Loan targets        no loan to a household whose budget showed no shortfall
  6. Family gifts        no gifts between members of the same household
  7. Fallbacks           answers replaced by a default after 3 invalid tries,
                         per agent and phase (a skew between agents or groups biases
                         the comparison even when every rule check passes)
  8. Intent -> action    agents who planned to borrow/lend: did they actually send
                         a loan proposal, and was one accepted?
"""

import json
import os
import sys
from collections import Counter, defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
CHARS = json.load(open(os.path.join(ROOT, "characters.json")))
NEED = {n: c["daily_need"] for n, c in CHARS.items()}
HOUSE = {n: "+".join(sorted([n] + c["family"])) for n, c in CHARS.items()}
MINORS = {n for n, c in CHARS.items() if c["age"] < 18}
SPOIL = CFG["food"]["spoil_rate_weekly"]
CAP = CFG["stamina"].get("starving_cap")
START_FOOD = sum(c["food"] for c in CHARS.values())


def load(run_dir, name):
    path = os.path.join(run_dir, name + ".jsonl")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def check(run_dir):
    L = {k: load(run_dir, k) for k in ["states", "actions", "gifts", "loans", "trades", "errors", "plans", "dialogues"]}
    sts, acts, gifts, plans = L["states"], L["actions"], L["gifts"], L["plans"]
    made = [x for x in L["loans"] if x["event"] == "made"]
    problems = 0
    print(f"\n=== {run_dir} ===")
    days = sorted({(s["week"], s["day"]) for s in sts})
    print(f"Days logged: {len(days)} (last: week {days[-1][0]} day {days[-1][1]})" if days else "No states logged yet.")

    # 1. food conservation
    tot, eat, got = defaultdict(float), defaultdict(float), defaultdict(float)
    for s in sts:
        tot[(s["week"], s["day"])] += s["food_total"]
        eat[(s["week"], s["day"])] += s["eaten"]
    for a in acts:
        got[(a["week"], a["day"])] += sum(a.get("got", {}).values())
    prev, bad = START_FOOD, []
    last_day = CFG["run"]["action_days_per_week"]
    for k in days:
        if k[1] == 1 and k[0] > 1:
            prev -= sum(s["food"][t] * r for s in sts if (s["week"], s["day"]) == (k[0] - 1, last_day)
                        for t, r in SPOIL.items())
        if abs(prev + got[k] - eat[k] - tot[k]) > 0.1:
            bad.append(k)
        prev = tot[k]
    print(f"1. Food conservation: {len(bad)} mismatching days" + (f" {bad}" if bad else ""))
    problems += len(bad)

    # 2. starvation cap
    streak, viol, n_starving = defaultdict(int), [], 0
    for s in sorted(sts, key=lambda s: (s["week"], s["day"])):
        n = s["agent"]
        streak[n] = streak[n] + 1 if s["eaten"] < NEED[n] * CFG["hunger_threshold"] - 1e-9 else 0
        if streak[n] and CAP:
            n_starving += 1
            if s["stamina"] > max(CAP["floor"], CAP["start"] - CAP["step"] * (streak[n] - 1)) + 1e-9:
                viol.append((s["week"], s["day"], n))
    print(f"2. Starvation cap: {n_starving} starving agent-days, {len(viol)} above the cap" + (f" {viol}" if viol else ""))
    problems += len(viol)

    # 3. safe surplus
    allow = {(p["week"], HOUSE[p["agent"]]): p["budget"]["lendable"] for p in plans if "budget" in p}
    need = {(p["week"], HOUSE[p["agent"]]): p["budget"]["borrow_need"] for p in plans if "budget" in p}
    spent = defaultdict(float)
    for g in gifts:
        spent[(g["week"], HOUSE[g["giver"]])] += g["amount"]
    for m in made:
        spent[(m["week"], HOUSE[m["lender"]])] += m["amount"]
    over = [(k, round(v, 2), allow.get(k)) for k, v in spent.items() if v > allow.get(k, 0) + 1e-6]
    print(f"3. Safe surplus: {len(over)} household-weeks over the limit" + (f" {over}" if over else ""))
    problems += len(over)

    # 4-6. minors, loan targets, family gifts
    kids = [g for g in gifts if g["giver"] in MINORS] + [m for m in made if {m["lender"], m["borrower"]} & MINORS]
    kids += [t for t in L["trades"] if t["status"] == "accepted" and t["type"] == "trade" and {t["from"], t["to"]} & MINORS]
    not_short = [m for m in made if need.get((m["week"], HOUSE[m["borrower"]]), 0) <= 0]
    fam = [g for g in gifts if HOUSE[g["giver"]] == HOUSE[g["receiver"]]]
    print(f"4. Child finance events: {len(kids)}")
    print(f"5. Loans to households with no shortfall: {len(not_short)}")
    print(f"6. Gifts within a household: {len(fam)}")
    problems += len(kids) + len(not_short) + len(fam)

    # 7. fallbacks
    fb = Counter((e["agent"], e["phase"]) for e in L["errors"] if e["fallback"])
    salv = sum(1 for e in L["errors"] if any("salvaged" in x for x in e["errors"]))
    print(f"7. Fallbacks (default answer after 3 invalid tries): {sum(fb.values())}" + (f" {dict(fb)}" if fb else "")
          + f"; salvaged contact answers: {salv}")
    if fb:
        reasons = Counter(e["errors"][-1][:70] for e in L["errors"] if e["fallback"])
        for r, c in reasons.most_common(3):
            print(f"     {c}x  {r}")

    # 8. intent -> action
    print("8. Credit intents -> loan proposals sent / loans accepted:")
    for p in plans:
        if p.get("credit_intent", "neither") == "neither":
            continue
        sent = [d for d in L["dialogues"] if d["week"] == p["week"] and d.get("phase") == "contact"
                and d["speaker"] == p["agent"] and d.get("proposal") == "loan" and not d.get("duplicate_of")]
        acc = [t for t in L["trades"] if t["week"] == p["week"] and t["type"] == "loan" and t["status"] == "accepted"
               and p["agent"] in (t.get("lender"), t.get("borrower"))]
        print(f"     W{p['week']} {p['agent']:<6} {p['credit_intent']:<6} {p['credit_amount']:g} with {p['credit_partner']}: "
              f"{len(sent)} sent, {len(acc)} accepted")
    print("RESULT:", "all rule checks passed" if problems == 0 else f"{problems} rule problems found",
          "(review fallbacks separately)")


if __name__ == "__main__":
    for d in sys.argv[1:] or ["logs/A_r1"]:
        check(d)
