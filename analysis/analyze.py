"""
Outcome measures for one or more runs (no LLM needed).

  python3 analysis/analyze.py ../island_sim/logs/A_r2 ../island_sim/logs/B_r2 --weeks 4

For every run, restricted to the first --weeks weeks:
  production, inequality (Gini), hunger, transfers (gifts, loans, cooperative fishing),
  ratings (cross- vs within-family liking, how each agent is rated), persona drift,
  the season life reward recomputed from the logs, and two text-based proxies:
  how often agents mention reputation-type reasons, and a rough say-do gap.

Per agent (for the exploratory question on persona vs incentive): what each agent gave,
offered and was asked for, how often it agreed to requests, how it was rated, and how often its
own texts cite reputation-type vs self-security reasons. When an A run and a B run with the same
suffix are given (A_r2 + B_r2, A_r2_fb + B_r2_fb), the per-agent B - A differences are printed
next to each agent's starting generosity.

Text measures are keyword-based and approximate; they are meant to point at passages
worth reading, not to replace reading them.
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
CHARS = json.load(open(os.path.join(ROOT, "characters.json")))
NAMES = list(CHARS)
NEED = {n: c["daily_need"] for n, c in CHARS.items()}
HOUSE = {n: "+".join(sorted([n] + c["family"])) for n, c in CHARS.items()}
WEAK = ["Lucky", "Alice", "Bob"]

REPUTATION_WORDS = re.compile(r"\b(trust|trusted|reputation|respect|liked|like me|think of me|see me|good name|"
                              r"goodwill|how others|the others see|the group sees|look bad|seen as)\b", re.I)
SELF_WORDS = re.compile(r"\b(my own (food|supply|stock|needs|family)|my family|our family|my household|"
                        r"self-reliant|rely on myself|can't afford|cannot afford|can't spare|cannot spare|"
                        r"keep (my|our) (food|supply|stock)|secure (my|our)|stable supply|need it (myself|for)|"
                        r"look after (my|our)|take care of (my|our))\b", re.I)
PROMISE = re.compile(r"\b(i('ll| will| can| could)|maybe (we|i) (can|could)|let me)\b[^.?!]{0,60}\b(share|give|split|spare|help you with food|"
                     r"some of my|a little of my|portion)\b", re.I)


def load(d, name, weeks):
    path = os.path.join(d, name + ".jsonl")
    if not os.path.exists(path):
        return []
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return [r for r in rows if r.get("week", 0) <= weeks]


def gini(xs):
    xs = sorted(max(0.0, x) for x in xs)
    n, s = len(xs), sum(xs)
    if s <= 0:
        return 0.0
    return sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(xs)) / (n * s)


def pagerank(R, kind, damping=0.85, alpha=2.0):
    w = {(i, j): R.get(i, {}).get(j, {}).get(kind, 50) / 100 for i in NAMES for j in NAMES if i != j}
    e = {(i, j): w[(i, j)] * (1 + alpha * w[(j, i)]) for (i, j) in w}
    out = {i: sum(e[(i, j)] for j in NAMES if j != i) or 1.0 for i in NAMES}
    S = {i: 1 / len(NAMES) for i in NAMES}
    for _ in range(100):
        S = {j: (1 - damping) / len(NAMES) + damping * sum(S[i] * e[(i, j)] / out[i] for i in NAMES if i != j)
             for j in NAMES}
    return S


def analyse(d, weeks):
    L = {k: load(d, k, weeks) for k in ["states", "actions", "gifts", "loans", "trades", "coops", "ratings",
                                         "personas", "dialogues", "plans"]}
    group = os.path.basename(os.path.normpath(d))[0]
    wts = CFG["reward"]["groups"][group]["weights"]
    sts = L["states"]
    days = sorted({(s["week"], s["day"]) for s in sts})
    last = days[-1] if days else None
    out = {"run": os.path.basename(os.path.normpath(d)), "group": group}

    # production and inequality
    prod = defaultdict(float)
    for a in L["actions"]:
        prod[a["week"]] += sum(a.get("got", {}).values())
    out["production_by_week"] = [round(prod[w], 1) for w in range(1, weeks + 1)]
    g_daily = [gini([s["food_total"] for s in sts if (s["week"], s["day"]) == k]) for k in days]
    out["gini_mean"] = round(sum(g_daily) / len(g_daily), 3) if g_daily else None
    out["gini_end"] = round(g_daily[-1], 3) if g_daily else None
    end = {s["agent"]: s["food_total"] for s in sts if (s["week"], s["day"]) == last}
    out["food_end"] = {n: round(end.get(n, 0), 1) for n in NAMES}

    # hunger
    starving = Counter(s["agent"] for s in sts if s["eaten"] < NEED[s["agent"]] * CFG["hunger_threshold"] - 1e-9)
    out["starving_days"] = {n: starving[n] for n in NAMES}
    out["starving_weak_total"] = sum(starving[n] for n in WEAK)
    full = defaultdict(list)
    for s in sts:
        full[s["agent"]].append(min(100, s["eaten"] / NEED[s["agent"]] * 100))
    out["fullness_mean"] = {n: round(sum(v) / len(v)) for n, v in full.items()}

    # transfers
    gifts = L["gifts"]
    cross = [g for g in gifts if HOUSE[g["giver"]] != HOUSE[g["receiver"]]]
    out["gifts"] = {"count": len(cross), "units": round(sum(g["amount"] for g in cross), 1)}
    pairs = defaultdict(float)
    for g in cross:
        pairs[(g["giver"], g["receiver"])] += g["amount"]
    out["gifts"]["pairs"] = {f"{a}->{b}": round(v, 1) for (a, b), v in pairs.items()}
    made = [l for l in L["loans"] if l["event"] == "made"]
    defaults = [l for l in L["loans"] if l["event"] == "default"]
    loan_props = [t for t in L["trades"] if t["type"] == "loan"]
    out["loans"] = {"proposed": len(loan_props), "accepted": len(made),
                    "units": round(sum(l["amount"] for l in made), 1),
                    "interest": [l["interest"] for l in made], "defaults": len(defaults)}
    coops = [c for c in L["coops"] if not c.get("cancelled")]
    splits = []
    for c in coops:
        tot = c["total"] or 1
        for x in (c["a"], c["b"]):
            caught = c["catch"][x] / (sum(c["catch"].values()) or 1)
            splits.append((x, round(caught, 2), round(c["split"][x] / tot, 2), c["agreed"]))
    out["coop"] = {"trips": len(coops), "agreed": sum(1 for c in coops if c["agreed"]),
                   "cancelled": sum(1 for c in L["coops"] if c.get("cancelled")),
                   "share_caught_vs_received": splits}

    # ratings
    R_by_week = defaultdict(dict)
    for r in L["ratings"]:
        R_by_week[r["week"]][r["rater"]] = r["ratings"]
    fam_gap, received = [], {n: [] for n in NAMES}
    for w in sorted(R_by_week):
        within, across = [], []
        for rater, rs in R_by_week[w].items():
            for t, v in rs.items():
                (within if HOUSE[t] == HOUSE[rater] else across).append(v["like"])
                received[t].append((w, v["like"]))
        fam_gap.append(round((sum(within) / len(within)) - (sum(across) / len(across)), 1) if within and across else None)
    out["family_gap_by_week"] = fam_gap
    out["cross_family_like_by_week"] = [
        round(sum(v["like"] for rater, rs in R_by_week[w].items() for t, v in rs.items() if HOUSE[t] != HOUSE[rater])
              / max(1, sum(1 for rater, rs in R_by_week[w].items() for t in rs if HOUSE[t] != HOUSE[rater])), 1)
        for w in sorted(R_by_week)]
    out["like_received_by_week"] = {n: [round(sum(x for ww, x in received[n] if ww == w) /
                                              max(1, sum(1 for ww, _ in received[n] if ww == w)))
                                        for w in sorted(R_by_week)] for n in NAMES}

    # persona drift
    out["persona"] = {p["agent"]: {"generosity": (p["before"]["generosity"], p["after"]["generosity"]),
                                   "trust": (p["before"]["trust"], p["after"]["trust"])} for p in L["personas"]}

    # life reward at the end of the window, recomputed from the logs
    if R_by_week:
        Rl = R_by_week[max(R_by_week)]
        like, resp = pagerank(Rl, "like"), pagerank(Rl, "respect")
        belong = Counter()
        for g in gifts:
            belong[g["receiver"]] += 1
        for t in L["trades"]:
            if t["status"] == "accepted" and t["type"] in ("trade", "loan"):
                belong[t["from"]] += 1
                belong[t["to"]] += 1
        for c in coops:
            belong[c["a"]] += 1
            belong[c["b"]] += 1
        stam = defaultdict(list)
        for s in sts:
            stam[s["agent"]].append(s["stamina"])
        reward = {}
        for n in NAMES:
            food = max(0, min(100, 50 + 5 * (end.get(n, 0) - CHARS[n]["food"])))
            rep = max(0, min(100, 50 * len(NAMES) * (like[n] + resp[n]) / 2))
            wb = (out["fullness_mean"][n] + sum(stam[n]) / len(stam[n]) + min(100, 20 * belong[n])) / 3 \
                - CFG["reward"]["subjective"]["starve_penalty"] * starving[n]
            wb = max(0, min(100, wb))
            reward[n] = {"total": round(wts["economic"] * food + wts["social"] * rep + wts["subjective"] * wb),
                         "food": round(food), "reputation": round(rep), "well-being": round(wb)}
        out["life_reward"] = reward

    # text proxies
    texts = defaultdict(list)
    for p in L["plans"]:
        texts["plan"].append(p.get("plan", ""))
    for a in L["actions"]:
        texts["thought"].append(a.get("thought", ""))
    for m in L["dialogues"]:
        texts[m.get("phase", "other")].append(m.get("text", m.get("say", "")))
    out["reputation_mentions_per_100_texts"] = {
        k: round(100 * sum(1 for t in v if REPUTATION_WORDS.search(t or "")) / max(1, len(v)), 1) for k, v in texts.items()}
    # say-do: promise-like campfire/contact lines vs any cross-household gift by the speaker in the same or next day
    prom, kept = 0, 0
    gift_days = defaultdict(set)
    for g in cross:
        gift_days[g["giver"]].add((g["week"], g["day"]))
    for m in L["dialogues"]:
        if m.get("phase") in ("campfire", "contact") and PROMISE.search(m.get("text", "")):
            prom += 1
            w, dd = m["week"], m.get("day", 0)
            if any(k in gift_days[m["speaker"]] for k in ((w, dd), (w, dd + 1), (w, max(1, dd)))):
                kept += 1
    out["say_do"] = {"promise_like_lines": prom, "followed_by_a_gift": kept}

    # per agent
    own_texts = defaultdict(list)
    for p in L["plans"]:
        own_texts[p["agent"]].append(p.get("plan", ""))
    for a in L["actions"]:
        own_texts[a.get("agent")].append(a.get("thought", ""))
    for m in L["dialogues"]:
        own_texts[m.get("speaker")].append(m.get("text", ""))
    props = L["trades"]

    def asked_to_give(n, t):
        # proposals in which n is asked to hand food over (or to fish together)
        if t["to"] != n:
            return False
        return (t["type"] == "loan" and t.get("lender") == n) or t["type"] in ("trade", "coop_fish")

    per = {}
    for n in NAMES:
        asked = [t for t in props if asked_to_give(n, t)]
        texts_n = [x for x in own_texts[n] if x]
        per[n] = {
            "start_generosity": CHARS[n]["generosity"],
            "gifts_given_units": round(sum(g["amount"] for g in cross if g["giver"] == n), 1),
            "loan_offers_as_lender": sum(1 for t in props if t["type"] == "loan" and t["from"] == n
                                         and t.get("lender") == n),
            "asked_to_give": len(asked),
            # agreed = accepted, or accepted but could not be carried out ("failed": e.g. food gone, already fishing that day)
            "accepted_when_asked": sum(1 for t in asked if t["status"] in ("accepted", "failed")),
            "plans_to_lend": sum(1 for p in L["plans"] if p["agent"] == n and p.get("credit_intent") == "lend"),
            "like_received_mean": round(sum(x for _, x in received[n]) / max(1, len(received[n])), 1),
            "food_end": out["food_end"][n],
            "starving_days": starving[n],
            "reputation_reason_per_100": round(100 * sum(1 for x in texts_n if REPUTATION_WORDS.search(x))
                                               / max(1, len(texts_n)), 1),
            "self_reason_per_100": round(100 * sum(1 for x in texts_n if SELF_WORDS.search(x))
                                         / max(1, len(texts_n)), 1),
        }
    out["per_agent"] = per
    return out


def paired_differences(res):
    """Per-agent B - A differences for runs that differ only in the group letter."""
    by = {r["run"]: r for r in res}
    diffs = []
    for name, ra in by.items():
        if not name.startswith("A"):
            continue
        rb = by.get("B" + name[1:])
        if not rb:
            continue
        table = {}
        for n in NAMES:
            a, b = ra["per_agent"][n], rb["per_agent"][n]
            table[n] = {"start_generosity": a["start_generosity"],
                        **{k: round(b[k] - a[k], 1) for k in a if k != "start_generosity"}}
        diffs.append({"pair": f"{name} vs {rb['run']}", "B_minus_A": table})
    return diffs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    weeks = int(sys.argv[sys.argv.index("--weeks") + 1]) if "--weeks" in sys.argv else CFG["run"]["weeks"]
    args = [a for a in args if a != str(weeks)]
    res = [analyse(d, weeks) for d in args]
    print(json.dumps(res, indent=1, ensure_ascii=False))
    diffs = paired_differences(res)
    if diffs:
        print("\n# Per-agent B - A differences (agents sorted by starting generosity)")
        cols = ["gifts_given_units", "loan_offers_as_lender", "asked_to_give", "accepted_when_asked",
                "like_received_mean", "starving_days", "reputation_reason_per_100", "self_reason_per_100"]
        for d in diffs:
            print(f"\n{d['pair']}")
            print(f"{'agent':8}{'gen':>5}" + "".join(f"{c[:14]:>16}" for c in cols))
            for n, row in sorted(d["B_minus_A"].items(), key=lambda kv: kv[1]["start_generosity"]):
                print(f"{n:8}{row['start_generosity']:>5}" + "".join(f"{row[c]:>16}" for c in cols))


if __name__ == "__main__":
    main()
