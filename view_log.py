"""
Print the logs of one run as a readable week-by-week report.

  python3 view_log.py A                # group A, all weeks
  python3 view_log.py A 2              # group A, week 2 only
  python3 view_log.py A --mock         # mock-mode logs
  python3 view_log.py A > report.txt   # save to a file
"""

import json
import os
import sys


def read(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    group = args[0] if args else "A"
    only_week = int(args[1]) if len(args) > 1 else None
    base = os.path.join("logs_mock" if "--mock" in sys.argv else "logs", group)
    L = {f: read(os.path.join(base, f + ".jsonl"))
         for f in ["plans", "actions", "states", "dialogues", "trades", "coops", "ratings", "personas", "errors", "loans"]}
    states = {(r["week"], r["day"], r["agent"]): r for r in L["states"]}

    weeks = sorted({r["week"] for r in L["plans"]})
    for w in weeks:
        if only_week and w != only_week:
            continue
        print(f"\n{'=' * 78}\nWEEK {w}\n{'=' * 78}")
        for p in [p for p in L["plans"] if p["week"] == w]:
            print(f"[plan] {p['agent']:<7} ration={p['ration']:<6} {p['plan']}")

        print("\n--- Private messages ---")
        for m in [m for m in L["dialogues"] if m["week"] == w and m["phase"] == "contact"]:
            prop = f"   [{m['proposal_id']}: {m['proposal_detail']}]" if m.get("proposal_id") else ""
            if m.get("gift"):
                prop += f"   [GIFT {m['gift']['amount']:g} {m['gift']['type']}]"
            print(f"(round {m['round']}) {m['speaker']} -> {m['to']}: {m['text']}{prop}")
        for t in [t for t in L["trades"] if t["week"] == w]:
            print(f"  => {t['id']} {t['type']} {t['from']}->{t['to']}: {t['status'].upper()}")

        for d in sorted({r["day"] for r in L["actions"] if r["week"] == w}):
            print(f"\n--- Day {d} ---")
            for a in [a for a in L["actions"] if a["week"] == w and a["day"] == d]:
                s = states.get((w, d, a["agent"]), {})
                act = a["action"]
                if act in ("give", "steal", "heal", "coop_fish"):
                    act += f" -> {a['target']}"
                got = ", ".join(f"{k} {v:g}" for k, v in a["got"].items()) or "-"
                extra = a["note"] or ("INJURED" if a["injured"] else "")
                print(f"{a['agent']:<7} {act:<18} got {got:<10} ate {s.get('eaten', '?'):<4} "
                      f"({a.get('ration', '?'):<6}) stamina {s.get('stamina', '?'):<5} food {s.get('food_total', '?'):<6} {extra}")
                if not a["thought"].startswith("("):
                    print(f"        \"{a['thought']}\"")
            coop_lines = [m for m in L["dialogues"] if m["week"] == w and m["day"] == d and m["phase"] == "coop"]
            if coop_lines:
                print("  [coop fishing talk]")
                for m in coop_lines:
                    print(f"    {m['speaker']}: {m['text']} (wants {m['my_share']:g} of {m['total']:g}"
                          + (", ACCEPTS" if m["accept"] else "") + ")")
            print("  [campfire]")
            for m in [m for m in L["dialogues"] if m["week"] == w and m["day"] == d and m["phase"] == "campfire"]:
                to = "" if m["to"] == "everyone" else f" (whispers to {m['to']})"
                gift = f"   [GIVES {m['gift_amount']:g} to {m['gift_to']}]" if m.get("gift_amount") else ""
                print(f"    {m['speaker']}{to}: {m['text']}{gift}")

        ls = [x for x in L["loans"] if x["week"] == w]
        if ls:
            print("\n--- Loans ---")
            for x in ls:
                if x["event"] == "made":
                    print(f"  D{x['day']} NEW {x['id']}: {x['lender']} lends {x['amount']:g} {x['lend_type']} to {x['borrower']}, "
                          f"repay {x['repay']:g} (interest {x['interest']:.0%}) by abs day {x['due']}")
                else:
                    extra = f", still owes {x['still_owed']:g}" if "still_owed" in x else ""
                    print(f"  D{x['day']} {x['event'].upper()} {x['id']}: {x['borrower']} -> {x['lender']} paid {x['paid_today']:g}{extra}")
        rs = [r for r in L["ratings"] if r["week"] == w]
        if rs:
            print("\n--- Review (secret ratings: like/respect) ---")
            for r in rs:
                cells = "  ".join(f"{o} {v['like']}/{v['respect']}" for o, v in r["ratings"].items())
                print(f"{r['rater']:<7} {cells}")
                print(f"        diary: {r['diary']}")
        for p in [p for p in L["personas"] if p["week"] == w]:
            b, a = p["before"], p["after"]
            print(f"\n[season] {p['agent']}: generosity {b['generosity']:g}->{a['generosity']:g}, "
                  f"trust {b['trust']:g}->{a['trust']:g}\n         new mindset: {a['mindset']}")

    e = L["errors"]
    print(f"\nFormat/rule errors: {len(e)} calls needed a retry, "
          f"{sum(x['fallback'] for x in e)} fell back to a default.")


if __name__ == "__main__":
    main()
