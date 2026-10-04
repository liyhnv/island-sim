"""
Turn the raw run logs (JSON Lines) into clean, tidy tables for SQL and Tableau.

  python3 analysis/export_tables.py ../island_sim/logs/A_r2:4 ../island_sim/logs/B_r2:4 \
      ../island_sim/logs/A_r2_fb ../island_sim/logs/B_r2_fb --out data/tables

A run folder may end in ":N" to keep only weeks 1..N (used for the no-feedback run of
replication 2, which ran longer than 4 weeks). Folder names tell the condition:
A/B = scoring rule, "_rN" = replication N (seed 41 + N), "_fb" = agents saw their score.

Output (one CSV per table, plus island.db, a SQLite database with the same tables):

  runs          one row per run: group, incentive, feedback, replication, seed, weeks used
  agents        one row per agent: age, household, need, productivity, starting generosity/trust
  daily_states  one row per agent per day: food held, eaten, fullness, stamina, starving, typhoon day
  actions       one row per agent per day: what it did, what it brought back, its stated reason
  transfers     every gift, loan made and executed trade, as giver -> receiver with an amount
  proposals     every proposal sent in private messages (loan, trade, joint fishing) and its outcome
  coops         every joint fishing trip: catches, split, agreed or not, cancelled or not
  ratings       one row per rater per target per week: secret like and respect (0-100)
  scores        one row per agent per week: season score total, rank and three parts
                (logged by the simulator in v7 runs; recomputed with the same formula for older runs;
                the recomputation ignores loan repayments collected on the last evening of a week,
                which did not occur in the recomputed run)
  texts         every plan, thought, private message and campfire line, with two keyword flags
  personas      generosity / trust / mindset before and after the season update

Every table has run, grp (A/B), feedback (0 = scores hidden, 1 = shown) and replication (1/2)
columns, so runs can be stacked and filtered. Runs are labelled <group>-<condition>-<replication>,
e.g. B-shown-2; the runs table maps each label to its log folder (logs/B_r3_fb) and seed (44).
Replication k was run with run.py --run k+1 (seed 42 + k); --run 1 was the v6 pilot. t = (week - 1) * 5 + day is a running day number from 1 to 20.
"""

import csv
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
CHARS = json.load(open(os.path.join(ROOT, "characters.json")))
NAMES = list(CHARS)
HOUSE = {n: "+".join(sorted([n] + c["family"])) for n, c in CHARS.items()}
NEED = {n: c["daily_need"] for n, c in CHARS.items()}
TY = CFG["events"]["typhoon"]
DAYS = CFG["run"]["action_days_per_week"]
THRESH = CFG["hunger_threshold"]

REPUTATION_WORDS = re.compile(r"\b(trust|trusted|reputation|respect|liked|like me|think of me|see me|good name|"
                              r"goodwill|how others|the others see|the group sees|look bad|seen as)\b", re.I)
SELF_WORDS = re.compile(r"\b(my own (food|supply|stock|needs|family)|my family|our family|my household|"
                        r"self-reliant|rely on myself|can't afford|cannot afford|can't spare|cannot spare|"
                        r"keep (my|our) (food|supply|stock)|secure (my|our)|stable supply|need it (myself|for)|"
                        r"look after (my|our)|take care of (my|our))\b", re.I)


def load(d, name, weeks):
    path = os.path.join(d, name + ".jsonl")
    if not os.path.exists(path):
        return []
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return [r for r in rows if r.get("week", 0) <= weeks]


def tday(week, day):
    return (week - 1) * DAYS + day if day and 1 <= day <= DAYS else None


def pagerank(R, kind):
    rc = CFG["reward"]["social"]
    d, alpha = rc["damping"], rc["reciprocity_alpha"]
    w = {(i, j): R.get(i, {}).get(j, {}).get(kind, 50) / 100 for i in NAMES for j in NAMES if i != j}
    e = {(i, j): w[(i, j)] * (1 + alpha * w[(j, i)]) for (i, j) in w}
    out = {i: sum(e[(i, j)] for j in NAMES if j != i) or 1.0 for i in NAMES}
    S = {i: 1 / len(NAMES) for i in NAMES}
    for _ in range(100):
        S = {j: (1 - d) / len(NAMES) + d * sum(S[i] * e[(i, j)] / out[i] for i in NAMES if i != j) for j in NAMES}
    return S


def export_run(spec, T):
    d, _, w = spec.partition(":")
    name = os.path.basename(os.path.normpath(d))
    weeks = int(w) if w else CFG["run"]["weeks"]
    grp = name[0]
    m = re.search(r"_r(\d+)", name)
    rep = int(m.group(1)) if m else 0
    fb = 1 if name.endswith("_fb") else 0
    L = {k: load(d, k, weeks) for k in ["states", "actions", "gifts", "loans", "trades", "coops", "ratings",
                                         "personas", "dialogues", "plans", "scores"]}
    # Readable run labels: <group>-<hidden|shown>-<replication>. The main replications were started with
    # run.py --run 2 and --run 3 (seeds 43 and 44; --run 1 was the v6 pilot), so replication = N - 1.
    replication = rep - 1
    condition = "shown" if fb else "hidden"
    label = f"{grp}-{condition}-{replication}"
    base = {"run": label, "grp": grp, "feedback": fb, "replication": replication}
    wts = CFG["reward"]["groups"][grp]["weights"]
    T["runs"].append({**base, "condition": condition, "incentive": "individualist" if grp == "A" else "reputation",
                      "seed": 41 + rep, "log_folder": name, "weeks_used": weeks,
                      "w_food": wts["economic"], "w_reputation": wts["social"], "w_wellbeing": wts["subjective"]})

    for s in L["states"]:
        n = s["agent"]
        T["daily_states"].append({**base, "week": s["week"], "day": s["day"], "t": tday(s["week"], s["day"]),
                                  "agent": n, "food_total": s["food_total"], "eaten": s["eaten"],
                                  "need": NEED[n], "fullness_pct": round(min(100, s["eaten"] / NEED[n] * 100), 1),
                                  "starving": int(s["eaten"] < NEED[n] * THRESH - 1e-9),
                                  "stamina": s["stamina"], "debt": s.get("debt", 0),
                                  "typhoon_day": int(s["week"] == TY["week"] and s["day"] in TY["days"]),
                                  **{f"food_{k}": v for k, v in s["food"].items()}})
    for a in L["actions"]:
        T["actions"].append({**base, "week": a["week"], "day": a["day"], "t": tday(a["week"], a["day"]),
                             "agent": a["agent"], "action": a["action"], "target": a.get("target", "none"),
                             "food_got": round(sum(a.get("got", {}).values()), 2), "ration": a.get("ration"),
                             "forced": int(bool(a.get("forced"))), "injured": int(bool(a.get("injured"))),
                             "thought": a.get("thought", "")})

    # transfers: gifts, loans made, executed trades (both directions), coop shares above own catch
    for g in L["gifts"]:
        T["transfers"].append({**base, "week": g["week"], "day": g["day"], "kind": "gift",
                               "from_agent": g["giver"], "to_agent": g["receiver"], "amount": g["amount"],
                               "cross_household": int(HOUSE[g["giver"]] != HOUSE[g["receiver"]]), "note": g.get("where", "")})
    for l in L["loans"]:
        if l.get("event") == "made":
            T["transfers"].append({**base, "week": l["week"], "day": l.get("day", 0), "kind": "loan",
                                   "from_agent": l["lender"], "to_agent": l["borrower"], "amount": l["amount"],
                                   "cross_household": 1, "note": f"repay {l.get('repay')}, interest {l.get('interest')}"})
    for p in L["trades"]:
        if p["type"] == "trade" and p["status"] == "accepted":
            for giver, recv, amt, ty in ((p["from"], p["to"], p["give_amount"], p["give_type"]),
                                         (p["to"], p["from"], p["get_amount"], p["get_type"])):
                T["transfers"].append({**base, "week": p["week"], "day": 0, "kind": "trade",
                                       "from_agent": giver, "to_agent": recv, "amount": amt,
                                       "cross_household": 1, "note": ty})
        T["proposals"].append({**base, "week": p["week"], "id": p["id"], "type": p["type"],
                               "from_agent": p["from"], "to_agent": p["to"], "round": p.get("round"),
                               "status": p["status"],
                               "agreed": int(p["status"] in ("accepted", "failed")),
                               "lender": p.get("lender"), "borrower": p.get("borrower"),
                               "amount": p.get("lend_amount", p.get("give_amount")),
                               "repay_or_get": p.get("repay", p.get("get_amount")),
                               "interest_pct": round(100 * (p["repay"] / p["lend_amount"] - 1), 1)
                               if p["type"] == "loan" and p.get("lend_amount") else None,
                               "to_asked_to_give": int(p["type"] in ("trade", "coop_fish")
                                                       or (p["type"] == "loan" and p.get("lender") == p["to"]))})
    for c in L["coops"]:
        row = {**base, "week": c["week"], "day": c["day"], "a": c["a"], "b": c["b"],
               "cancelled": int(bool(c.get("cancelled"))), "reason": c.get("reason", "")}
        if not c.get("cancelled"):
            caught = sum(c["catch"].values()) or 1
            row.update(catch_a=c["catch"][c["a"]], catch_b=c["catch"][c["b"]], total=c["total"],
                       got_a=c["split"][c["a"]], got_b=c["split"][c["b"]], agreed=int(c["agreed"]),
                       caught_share_a=round(c["catch"][c["a"]] / caught, 3),
                       got_share_a=round(c["split"][c["a"]] / (c["total"] or 1), 3))
        T["coops"].append(row)

    R_by_week = {}
    for r in L["ratings"]:
        R_by_week.setdefault(r["week"], {})[r["rater"]] = r["ratings"]
        for tgt, v in r["ratings"].items():
            T["ratings"].append({**base, "week": r["week"], "rater": r["rater"], "target": tgt,
                                 "like": v["like"], "respect": v["respect"],
                                 "same_household": int(HOUSE[tgt] == HOUSE[r["rater"]]),
                                 "impression": v.get("impression", "")})

    # scores: logged (v7) or recomputed weekly with the simulator's formula
    if L["scores"]:
        for s in L["scores"]:
            T["scores"].append({**base, "week": s["week"], "agent": s["agent"], "total": s["total"],
                                "rank": s["rank"], "food": s["food"], "reputation": s["reputation"],
                                "wellbeing": s["well-being"], "shown_to_agent": int(s.get("shown_to_agent", False)),
                                "source": "logged"})
    else:
        T["scores"].extend(recompute_scores(L, base, wts, R_by_week, weeks))

    texts = [("plan", p["week"], 0, p["agent"], "", p.get("plan", "")) for p in L["plans"]]
    texts += [("thought", a["week"], a["day"], a["agent"], "", a.get("thought", "")) for a in L["actions"]]
    texts += [(m.get("phase", ""), m["week"], m.get("day", 0), m.get("speaker"), m.get("to", ""), m.get("text", ""))
              for m in L["dialogues"]]
    for phase, wk, dy, who, to, txt in texts:
        T["texts"].append({**base, "week": wk, "day": dy, "phase": phase, "agent": who, "to_agent": to,
                           "text": txt, "mentions_reputation": int(bool(REPUTATION_WORDS.search(txt or ""))),
                           "mentions_self": int(bool(SELF_WORDS.search(txt or "")))})
    for p in L["personas"]:
        T["personas"].append({**base, "week": p["week"], "agent": p["agent"],
                              "generosity_before": p["before"]["generosity"], "generosity_after": p["after"]["generosity"],
                              "trust_before": p["before"]["trust"], "trust_after": p["after"]["trust"],
                              "mindset_before": p["before"]["mindset"], "mindset_after": p["after"]["mindset"]})


def recompute_scores(L, base, wts, R_by_week, weeks):
    pen = CFG["reward"]["subjective"]["starve_penalty"]
    rows, prev = [], {}
    belong = defaultdict(lambda: defaultdict(int))   # week -> agent -> events
    for g in L["gifts"]:
        belong[g["week"]][g["receiver"]] += 1
    for p in L["trades"]:
        if p["status"] == "accepted" and p["type"] in ("trade", "loan"):
            belong[p["week"]][p["from"]] += 1
            belong[p["week"]][p["to"]] += 1
    for c in L["coops"]:
        if not c.get("cancelled"):
            belong[c["week"]][c["a"]] += 1
            belong[c["week"]][c["b"]] += 1
    for w in range(1, weeks + 1):
        if w not in R_by_week:
            continue
        st = [s for s in L["states"] if s["week"] <= w]
        last = {s["agent"]: s["food_total"] for s in st if s["week"] == w and s["day"] == DAYS}
        # states are logged before the evening campfire, so add the last evening's gifts
        for g in L["gifts"]:
            if g["week"] == w and g["day"] == DAYS:
                last[g["giver"]] = last.get(g["giver"], 0) - g["amount"]
                last[g["receiver"]] = last.get(g["receiver"], 0) + g["amount"]
        like, resp = pagerank(R_by_week[w], "like"), pagerank(R_by_week[w], "respect")
        total = {}
        parts = {}
        for n in NAMES:
            mine = [s for s in st if s["agent"] == n]
            days = max(1, len(mine))
            full = sum(min(100, s["eaten"] / NEED[n] * 100) for s in mine) / days
            stam = sum(s["stamina"] for s in mine) / days
            starving = sum(1 for s in mine if s["eaten"] < NEED[n] * THRESH - 1e-9)
            bel = min(100, 20 * sum(belong[k][n] for k in range(1, w + 1)))
            food = max(0, min(100, 50 + 5 * (last.get(n, 0) - CHARS[n]["food"])))
            rep = max(0, min(100, 50 * len(NAMES) * (like[n] + resp[n]) / 2))
            wb = max(0, min(100, (full + stam + bel) / 3 - pen * starving))
            parts[n] = (food, rep, wb)
            total[n] = wts["economic"] * food + wts["social"] * rep + wts["subjective"] * wb
        order = sorted(NAMES, key=lambda n: -total[n])
        for n in NAMES:
            rows.append({**base, "week": w, "agent": n, "total": round(total[n]), "rank": order.index(n) + 1,
                         "food": round(parts[n][0]), "reputation": round(parts[n][1]), "wellbeing": round(parts[n][2]),
                         "shown_to_agent": 0, "source": "recomputed"})
    return rows


def main():
    args = sys.argv[1:]
    out = args[args.index("--out") + 1] if "--out" in args else os.path.join(ROOT, "data", "tables")
    specs = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--out")]
    os.makedirs(out, exist_ok=True)
    T = defaultdict(list)
    for c in NAMES:
        ch = CHARS[c]
        T["agents"].append({"agent": c, "age": ch["age"], "household": HOUSE[c], "household_size": len(ch["family"]) + 1,
                            "is_minor": int(ch["age"] < 18), "is_weak": int(c in ("Lucky", "Alice", "Bob")),
                            "daily_need": ch["daily_need"], "productivity": ch["productivity"],
                            "start_generosity": ch["generosity"], "start_trust": ch["trust"],
                            "items": ", ".join(ch["items"])})
    for spec in specs:
        export_run(spec, T)

    # build the database in a temporary folder and copy it over (SQLite can fail on synced/network folders)
    db_path = os.path.join(out, "island.db")
    tmp_db = os.path.join(tempfile.mkdtemp(), "island.db")
    db = sqlite3.connect(tmp_db)
    for name, rows in T.items():
        cols = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        with open(os.path.join(out, name + ".csv"), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=cols)
            wr.writeheader()
            wr.writerows(rows)
        db.execute(f"CREATE TABLE {name} ({', '.join(cols)})")
        db.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})",
                       [[r.get(c) for c in cols] for r in rows])
        print(f"{name:14} {len(rows):6} rows")
    db.commit()
    db.close()
    shutil.copyfile(tmp_db, db_path)
    print("written to", out)


if __name__ == "__main__":
    main()
