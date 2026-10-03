"""
Outcome measures for one or more runs (no LLM needed).

  python3 analysis/analyze.py ../island_sim/logs/A_r2 ../island_sim/logs/B_r2 --weeks 4

For every run, restricted to the first --weeks weeks:
  production, inequality (Gini), hunger, transfers (gifts, loans, cooperative fishing),
  ratings (cross- vs within-family liking, how each agent is rated), persona drift,
  the season life reward recomputed from the logs, and two text-based proxies:
  how often agents mention reputation-type reasons, and a rough say-do gap.

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
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    weeks = int(sys.argv[sys.argv.index("--weeks") + 1]) if "--weeks" in sys.argv else CFG["run"]["weeks"]
    args = [a for a in args if a != str(weeks)]
    res = [analyse(d, weeks) for d in args]
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
