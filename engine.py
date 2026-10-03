"""
Simulation engine.

One week:
  1. Plan     - each agent picks a starting ration level and writes a short plan
  2. Contact  - 3 rounds of private messages; trades and cooperative fishing
                can be proposed and accepted (trades happen immediately)
  3. 5 days   - each day: all 6 choose an action from the same morning state
                (agents with a coop-fishing deal fish together and negotiate
                the split) -> rules resolve outcomes -> everyone eats
                -> evening campfire (1 line each, public or whispered) -> save
  4. Review   - diary, secret like/respect ratings of the others, self-rating
  5. Season   - after week 4 and 8: rewrite "current mindset" from the diaries;
                generosity/trust move at most +/-10
  Week end: fresh food spoils 20%.

The LLM only decides and talks. All numbers (yields, injuries, theft) come
from config.yaml rules and one seeded random generator.
Progress is saved after every stage, so a run can be resumed at any point.
"""

import json
import os
import random
import time

import prompts

FOOD_TYPES = ["can", "fish", "clam", "coconut", "forage"]
EAT_ORDER = ["fish", "clam", "forage", "coconut", "can"]   # overwritten from config (most perishable first)
PRODUCTIVE = ["fish", "clam", "coconut", "forage", "shelter"]


# ---------------------------------------------------------------- schemas
def plan_schema(others):
    return {"type": "object",
            "properties": {"ration": {"type": "string", "enum": ["normal", "save", "skip"]},
                           "credit_intent": {"type": "string", "enum": ["borrow", "lend", "neither"]},
                           "credit_amount": {"type": "number"},
                           "credit_partner": {"type": "string", "enum": ["none"] + others},
                           "plan": {"type": "string"}},
            "required": ["ration", "credit_intent", "credit_amount", "credit_partner", "plan"]}


def action_schema(names):
    return {"type": "object",
            "properties": {
                "action": {"type": "string",
                           "enum": ["fish", "clam", "coconut", "forage", "shelter",
                                    "rest", "give", "steal", "heal"]},
                "target": {"type": "string", "enum": names + ["none"]},
                "amount": {"type": "number"},
                "ration": {"type": "string", "enum": ["normal", "save", "skip"]},
                "thought": {"type": "string"}},
            "required": ["action", "target", "amount", "ration", "thought"]}


def contact_schema(others, open_ids):
    msg = {"type": "object",
           "properties": {
               "to": {"type": "string", "enum": others},
               "text": {"type": "string"},
               "proposal": {"type": "string", "enum": ["none", "trade", "loan", "coop_fish"]},
               "loan_role": {"type": "string", "enum": ["lender", "borrower"]},
               "give_type": {"type": "string", "enum": FOOD_TYPES},
               "give_amount": {"type": "number"},
               "get_type": {"type": "string", "enum": FOOD_TYPES},
               "get_amount": {"type": "number"},
               "day": {"type": "integer"}},
           "required": ["to", "text", "proposal", "loan_role", "give_type", "give_amount",
                        "get_type", "get_amount", "day"]}
    resp = {"type": "object",
            "properties": {"proposal_id": {"type": "string", "enum": open_ids or ["none"]},
                           "accept": {"type": "boolean"}},
            "required": ["proposal_id", "accept"]}
    return {"type": "object",
            "properties": {"messages": {"type": "array", "items": msg, "maxItems": 2},
                           "responses": {"type": "array", "items": resp}},
            "required": ["messages", "responses"]}


def coop_schema():
    return {"type": "object",
            "properties": {"say": {"type": "string"}, "my_share": {"type": "number"},
                           "accept": {"type": "boolean"}},
            "required": ["say", "my_share", "accept"]}


def campfire_schema(others):
    return {"type": "object",
            "properties": {"to": {"type": "string", "enum": ["everyone"] + others},
                           "text": {"type": "string"},
                           "gift_to": {"type": "string", "enum": ["none"] + others},
                           "gift_amount": {"type": "number"}},
            "required": ["to", "text", "gift_to", "gift_amount"]}


def review_schema(others):
    one = {"type": "object",
           "properties": {"like": {"type": "integer", "minimum": 0, "maximum": 100},
                          "respect": {"type": "integer", "minimum": 0, "maximum": 100},
                          "impression": {"type": "string"}},
           "required": ["like", "respect", "impression"]}
    return {"type": "object",
            "properties": {
                "diary": {"type": "string"},
                "ratings": {"type": "object", "properties": {o: one for o in others},
                            "required": others},
                "self_generosity": {"type": "integer", "minimum": 0, "maximum": 100},
                "self_trust": {"type": "integer", "minimum": 0, "maximum": 100}},
            "required": ["diary", "ratings", "self_generosity", "self_trust"]}


def season_schema():
    return {"type": "object",
            "properties": {"mindset": {"type": "string"},
                           "generosity": {"type": "integer", "minimum": 0, "maximum": 100},
                           "trust": {"type": "integer", "minimum": 0, "maximum": 100}},
            "required": ["mindset", "generosity", "trust"]}


# ---------------------------------------------------------------- engine
class Engine:
    def __init__(self, cfg, chars, group, llm, log_dir, save_dir):
        self.cfg = cfg
        self.chars = chars
        self.names = list(chars)
        self.group = group
        self.group_cfg = cfg["reward"]["groups"][group]
        self.llm = llm
        self.log_dir = log_dir
        self.save_dir = save_dir
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(save_dir, exist_ok=True)
        self.rng = random.Random(cfg["run"]["seed"])
        global EAT_ORDER
        EAT_ORDER = cfg["food"].get("eat_order", EAT_ORDER)
        self.st = self.initial_state()

    def others(self, n):
        return [x for x in self.names if x != n]

    # ---------- state
    def initial_state(self):
        agents = {}
        for n, c in self.chars.items():
            agents[n] = {
                "food": {"can": float(c["food"]), "fish": 0.0, "clam": 0.0,
                         "coconut": 0.0, "forage": 0.0},
                "stamina": float(c["stamina"]),
                "injured": False,
                "ration": "normal",
                "plan": "",
                "mindset": c["current_mindset"],   # rewritten at season end
                "generosity": float(c["generosity"]),
                "trust": float(c["trust"]),
                "memory": [],        # what happened to this agent
                "heard": [],         # messages and campfire lines this agent heard/said
                "diary": [],         # one entry per week
                "impressions": {},   # other -> short impression (from last review)
                "starving_days": 0,
            }
        return {
            "week": 1, "day": 1,
            "stage": "plan",         # plan -> contact -> day -> review -> (season) -> next week
            "contact_round": 1,
            "agents": agents,
            "coconuts_left": self.cfg["actions"]["coconut"]["total_stock"],
            "shelter_progress": 0,
            "public": [],            # what everyone saw yesterday
            "news": [],              # lasting news (the radio message)
            "alerts": [],            # today only (typhoon)
            "proposals": [],         # this week's proposals
            "coops": [],             # this week's agreed coop-fishing days
            "next_pid": 1,
            "loans": [],             # all loans ever made (active, repaid, overdue)
            "forecast": "",          # advance warning of this week's typhoon
        }

    # ---------- save / resume
    def pos(self):
        """Position of the NEXT stage within the week (used to trim logs on resume)."""
        s = self.st["stage"]
        return {"plan": 0, "contact": 0.5 + self.st["contact_round"] / 10,
                "day": self.st["day"], "review": 6, "season": 6.5}[s]

    def save(self):
        v, state, gauss = self.rng.getstate()
        data = {"state": self.st, "rng": [v, list(state), gauss]}
        path = os.path.join(self.save_dir, "latest.json")
        with open(path + ".tmp", "w") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(path + ".tmp", path)  # atomic: never leaves a half-written save

    def load(self):
        with open(os.path.join(self.save_dir, "latest.json")) as f:
            data = json.load(f)
        self.st = data["state"]
        v, state, gauss = data["rng"]
        self.rng.setstate((v, tuple(state), gauss))
        self._trim_logs()

    def _trim_logs(self):
        """Drop log lines written after the last save (e.g. from a crash mid-stage)."""
        here = (self.st["week"], self.pos())
        for fname in os.listdir(self.log_dir):
            path = os.path.join(self.log_dir, fname)
            with open(path) as f:
                rows = [json.loads(line) for line in f if line.strip()]
            keep = [r for r in rows if (r["week"], r["pos"]) < here]
            with open(path, "w") as f:
                for r in keep:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def log(self, fname, row, pos=None):
        row = {"week": self.st["week"], "pos": self.pos() if pos is None else pos, **row,
               "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        with open(os.path.join(self.log_dir, fname), "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def ask(self, n, phase, prompt, schema, validate=None):
        d, errs = self.llm.ask(prompt, schema, validate)
        if errs:
            self.log("errors.jsonl", {"day": self.st["day"], "agent": n, "phase": phase,
                                      "errors": errs, "fallback": d is None})
        return d

    def hear(self, n, text):
        self.st["agents"][n]["heard"] = (self.st["agents"][n]["heard"] + [text])[-30:]

    def remember(self, n, text):
        self.st["agents"][n]["memory"] = (self.st["agents"][n]["memory"] + [text])[-12:]

    # ---------- food helpers
    def total_food(self, n):
        return sum(self.st["agents"][n]["food"].values())

    def remove_food(self, n, amount):
        """Take `amount` units from n (fresh first). Returns {type: units} removed."""
        food = self.st["agents"][n]["food"]
        taken = {}
        for t in EAT_ORDER:
            if amount <= 1e-9:
                break
            x = min(food[t], amount)
            if x > 0:
                food[t] = round(food[t] - x, 2)
                taken[t] = round(x, 2)
                amount -= x
        return taken

    def add_food(self, n, parts):
        for t, x in parts.items():
            self.st["agents"][n]["food"][t] = round(self.st["agents"][n]["food"][t] + x, 2)

    def cost(self, act):
        """Stamina cost of one day of this action."""
        return self.cfg["actions"][act].get("stamina_cost", self.cfg["stamina"]["labor_cost"])

    def abs_day(self, week=None, day=None):
        """Action-day counter: W1D1 = 1, W2D1 = 6, ..."""
        w = self.st["week"] if week is None else week
        d = self.st["day"] if day is None else day
        return (w - 1) * self.cfg["run"]["action_days_per_week"] + d

    def day_label(self, n_abs):
        per = self.cfg["run"]["action_days_per_week"]
        return f"week {(n_abs - 1) // per + 1} day {(n_abs - 1) % per + 1}"

    def best_yield(self, n):
        """Average yield of this agent's best ordinary work (ignoring today's stamina/typhoon)."""
        A, c = self.cfg["actions"], self.chars[n]
        k = c["productivity"]
        opts = [sum(A["clam"]["yield"]) / 2 * k, sum(A["forage"]["yield"]) / 2 * k]
        gear = A["fish"]["gear_item"] in c["items"]
        opts.append(sum(A["fish"]["yield_with_gear" if gear else "yield_without_gear"]) / 2 * k)
        if c["age"] <= A["coconut"]["max_age"] and self.st["coconuts_left"] > 0:
            opts.append(sum(A["coconut"]["yield"]) / 2 * k)
        return round(max(opts), 1)

    def household(self, n):
        return [n] + self.chars[n]["family"]

    def is_minor(self, n):
        return self.chars[n]["age"] < self.cfg.get("social", {}).get("adult_age", 18)

    def hkey(self, n):
        return "+".join(sorted(self.household(n)))

    def allowance(self, n):
        """What this household may still give away or lend this week (its safe surplus from the weekly budget)."""
        return round(self.st.setdefault("allowance", {}).get(self.hkey(n), 0.0), 2)

    def spend_allowance(self, n, amount):
        al = self.st.setdefault("allowance", {})
        al[self.hkey(n)] = round(max(0.0, al.get(self.hkey(n), 0.0) - amount), 2)

    def household_borrowed(self, n):
        """Units the household borrowed in this week's private messages."""
        start = self.abs_day(day=0)
        house = self.household(n)
        return round(sum(L["amount"] for L in self.st["loans"] if L["borrower"] in house and L["made"] == start), 2)

    def household_remaining_need(self, n):
        need = self.st["agents"][n].get("budget_numbers", {}).get("borrow_need", 0)
        return round(max(0.0, need - self.household_borrowed(n)), 2)

    def member_budget(self, m, ty_days):
        """Week numbers for one person: holdings, expected production, need, debts, food left after the typhoon."""
        A, c = self.cfg["actions"], self.chars[m]
        per = self.cfg["run"]["action_days_per_week"]
        clam_est = round(sum(A["clam"]["yield"]) / 2 * c["productivity"] * A["clam"]["crowd_factor"], 1)
        work_est = self.best_yield(m)
        hist = self.st["agents"][m].get("prod_hist", [])
        actual = round(sum(hist) / len(hist), 1) if hist else None
        # blend what the work could give with what this person ACTUALLY produced on recent normal days (rests, poor choices)
        per_day = round(0.8 * work_est if actual is None else min(0.8 * work_est, (0.8 * work_est + 2 * actual) / 3), 1)
        expected = round(ty_days * clam_est + (per - ty_days) * per_day, 1)
        owed = round(sum(L["repay"] - L["paid"] for L in self.st["loans"]
                         if L["borrower"] == m and L["status"] in ("active", "overdue")), 1)
        owed_to = round(sum(L["repay"] - L["paid"] for L in self.st["loans"]
                            if L["lender"] == m and L["status"] in ("active", "overdue")), 1)
        hold = round(self.total_food(m), 1)
        need = round(c["daily_need"] * per, 1)
        through = round(hold - owed + ty_days * (clam_est - c["daily_need"]), 1)
        return {"hold": hold, "expected": expected, "need": need, "owed": owed, "owed_to_me": owed_to,
                "balance": round(hold + expected - need - owed, 1), "after_typhoon": through,
                "clam_est": clam_est, "work_est": work_est, "per_day": per_day, "actual": actual,
                "spoil": round(sum(self.st["agents"][m]["food"][t] * r
                                   for t, r in self.cfg["food"]["spoil_rate_weekly"].items()), 1)}

    def food_budget(self, n):
        """Expected food balance for the coming week at HOUSEHOLD level (family members share food)."""
        per = self.cfg["run"]["action_days_per_week"]
        ty = self.cfg["events"]["typhoon"]
        ty_days = len(ty["days"]) if self.st["week"] == ty["week"] else 0
        c = self.chars[n]
        house = [n] + c["family"]
        b = {m: self.member_budget(m, ty_days) for m in house}
        me = b[n]
        H = {k: round(sum(b[m][k] for m in house), 1) for k in ("hold", "expected", "need", "owed", "owed_to_me", "balance", "after_typhoon")}
        worst = min(H["balance"], H["after_typhoon"]) if ty_days else H["balance"]
        borrow_need = round(max(0.0, -worst), 1)
        lendable = round(max(0.0, worst - 0.2 * H["need"]), 1)   # keep a safety buffer of ~1 day's food per person
        self.st["agents"][n]["budget_numbers"] = {"me": {k: me[k] for k in ("hold", "expected", "need", "owed", "balance", "after_typhoon")},
                                                 "household": H, "borrow_need": borrow_need, "lendable": lendable}
        who = "you" if len(house) == 1 else f"your household ({', '.join(house)}, who eat from each other's food)"
        act_txt = (f"; on your last normal work days you ACTUALLY brought in {me['actual']:g} per day on average, "
                   f"counting rest days and poor catches" if me["actual"] is not None else "")
        parts = [f"For {who}: food held {H['hold']:g}; needed this week {H['need']:g}; "
                 f"expected production about {H['expected']:g}"
                 + (f" (only clams on the {ty_days} typhoon days, ~{me['clam_est']:g} per day for you; on normal days your best work gives "
                    f"~{me['work_est']:g}{act_txt}; the estimate uses ~{me['per_day']:g} per normal day for you)" if ty_days else
                    f" (your best work gives ~{me['work_est']:g} per day{act_txt}; the estimate uses ~{me['per_day']:g} per day for you)") + "."]
        spoil = round(sum(b[m]["spoil"] for m in house), 1)
        if spoil >= 1:
            parts.append(f"If not eaten, lent or traded, about {spoil:g} units of the food {'you hold' if len(house) == 1 else 'the household holds'} "
                         f"will rot at the end of this week (fish -40%, clams -30%, forage -20%, coconuts -10%).")
        if H["owed"]:
            parts.append(f"Debts to repay: {H['owed']:g}.")
        if H["owed_to_me"]:
            parts.append(f"Owed to {'you' if len(house) == 1 else 'your household'}: {H['owed_to_me']:g}.")
        parts.append(f"Balance for the week: {'+' if H['balance'] >= 0 else ''}{H['balance']:g}.")
        if ty_days:
            parts.append(f"During the typhoon days food runs low first: after the typhoon {'you' if len(house) == 1 else 'the household'} "
                         f"will have about {H['after_typhoon']:g} units left" + (" (i.e. you run out before you can work normally again)."
                                                                                  if H['after_typhoon'] < 0 else "."))
        if borrow_need > 0:
            parts.append(f"=> {'You' if len(house) == 1 else 'Your household'} may need to BORROW about {borrow_need:g} units "
                         f"(or cover it by eating half on some days). You have no safe surplus: you cannot lend or give food away this week."
                         + (" Only one family member needs to arrange a loan." if len(house) > 1 else ""))
        elif lendable > 0.5:
            parts.append(f"=> {'You' if len(house) == 1 else 'Your household'} could safely LEND OR GIVE AWAY at most about {lendable:g} units "
                         f"in total this week (this is your safe surplus); you do not need to borrow.")
        else:
            parts.append("=> You are roughly break-even: no need to borrow, and no safe surplus: you cannot lend or give food away this week.")
        return " ".join(parts)

    def refresh_finance(self, morning=False):
        """Write each agent's debts/credits and a repayment plan into their state (shown in prompts).
        morning=True: today's work is still ahead (counts as a remaining work day)."""
        if self.st["stage"] in ("plan", "contact"):
            today = self.abs_day(day=0)          # before day 1 of this week
        else:
            today = self.abs_day() - (1 if morning else 0)
        for n in self.names:
            need = self.chars[n]["daily_need"]
            lines = []
            for L in self.st["loans"]:
                if L["status"] not in ("active", "overdue"):
                    continue
                left = round(L["repay"] - L["paid"], 2)
                if L["borrower"] == n:
                    days_left = L["due"] - today
                    if L["status"] == "overdue":
                        when = f"OVERDUE since {self.day_label(L['due'])}: everyone knows; your leftover food is taken every evening until it is paid"
                        lines.append(f"- You owe {L['lender']} {left:g} units ({when}).")
                    else:
                        food = self.total_food(n)
                        gap = round(max(0, left + need * days_left - food), 1)
                        y = self.best_yield(n)
                        work_days = gap / y if y else 99
                        lines.append(
                            f"- You owe {L['lender']} {left:g} units, due at the end of {self.day_label(L['due'])} "
                            f"({days_left} work day{'s' if days_left != 1 else ''} left before then). "
                            f"To eat normally until then AND repay, you need {left:g} + {need:g}x{days_left} = "
                            f"{round(left + need * days_left, 1):g} units; you hold {food:g}, so you must still produce about {gap:g} "
                            f"(your best work gives about {y:g} per day, so roughly {work_days:.1f} work days). "
                            f"Repayment is taken automatically on the due day; food you hand over at the campfire is a gift "
                            f"and does NOT count as repayment.")
                elif L["lender"] == n:
                    state = "OVERDUE" if L["status"] == "overdue" else f"due end of {self.day_label(L['due'])}"
                    lines.append(f"- {L['borrower']} owes YOU {left:g} units ({state}). You are the LENDER: you already handed over "
                                 f"the food when the loan was made, so you owe nothing and do not need to give {L['borrower']} anything; "
                                 f"the repayment comes to you automatically.")
            if not lines:
                lines.append("- You have no loans: you owe nobody anything and nobody owes you anything "
                             "(food handed over as a gift is never paid back).")
            if self.st["stage"] in ("plan", "contact") and self.st["agents"][n].get("budget_numbers"):
                need_h = self.st["agents"][n]["budget_numbers"].get("borrow_need", 0)
                got_h = self.household_borrowed(n)
                if need_h > 0 or got_h > 0:
                    lines.append(f"- This week {'you have' if len(self.household(n)) == 1 else 'your household has'} borrowed "
                                 f"{got_h:g} units so far; the expected shortfall was {need_h:g}, so you still need about "
                                 f"{max(0, round(need_h - got_h, 1)):g} more. Do not borrow beyond that.")
            self.st["agents"][n]["finance"] = "\n".join(lines)
            self.st["agents"][n]["best_yield"] = self.best_yield(n)

    def typhoon_today(self):
        ty = self.cfg["events"]["typhoon"]
        return self.st["week"] == ty["week"] and self.st["day"] in ty["days"]

    def can_fish(self, n):
        a, S, A = self.st["agents"][n], self.cfg["stamina"], self.cfg["actions"]
        return (a["stamina"] >= S["heavy_work_min"] and a["stamina"] >= A["fish"]["min_stamina"]
                and a["stamina"] >= S["collapse_below"] and not self.typhoon_today())

    def fish_catch(self, n):
        A = self.cfg["actions"]["fish"]
        gear = A["gear_item"] in self.chars[n]["items"]
        return round(self.rng.randint(*A["yield_with_gear" if gear else "yield_without_gear"])
                     * self.chars[n]["productivity"], 1)

    # ================================================================ PLAN
    def plan_phase(self):
        self.st["clam_yesterday"] = 0
        ty = self.cfg["events"]["typhoon"]
        if ty.get("forecast") and self.st["week"] == ty["week"]:
            days = ", ".join(map(str, ty["days"]))
            self.st["typhoon_days"] = list(ty["days"])
            self.st["forecast"] = (f"A TYPHOON WILL HIT THE ISLAND ON DAYS {days} OF THIS WEEK. On those days it is IMPOSSIBLE "
                                   f"to fish (also no cooperative fishing), to climb coconut trees, to go into the forest or to build. "
                                   f"The ONLY work possible is gathering clams in the tide pools, and with everyone crowding the "
                                   f"pools each person gets only about half a normal clam catch.")
        self.refresh_finance()
        planned = {}   # household (frozenset) -> (member, amount) who will arrange a loan
        self.st["allowance"] = {}
        for n in self.names:
            self.st["agents"][n]["budget"] = self.food_budget(n)
            self.st["allowance"][self.hkey(n)] = self.st["agents"][n]["budget_numbers"]["lendable"]
            key = frozenset(self.household(n))
            if key in planned and len(key) > 1:
                who, amt = planned[key]
                self.st["agents"][n]["budget"] += (f" NOTE: {who} has already planned to borrow about {amt:g} units for your "
                                                   f"household this week, so you do not need to borrow as well.")
            p = prompts.plan_prompt(n, self.chars[n], self.group_cfg, self.st)
            others = self.others(n)

            def check(d, n=n):
                if d["credit_intent"] != "neither" and self.is_minor(n):
                    return "You are a child: children cannot borrow or lend. Set credit_intent to neither."
                if d["credit_intent"] == "lend" and d["credit_amount"] > self.allowance(n) + 1e-9:
                    return (f"Your budget shows a safe surplus of only {self.allowance(n):g} units this week, so you cannot plan to lend "
                            f"{d['credit_amount']:g}. Lend at most that, or choose neither.")
                if d["credit_intent"] == "borrow" and self.st["agents"][n]["budget_numbers"]["borrow_need"] <= 0:
                    return "Your budget shows no shortfall this week, so there is nothing to borrow for. Choose neither."
                if d["credit_intent"] != "neither":
                    if d["credit_partner"] == "none" or d["credit_amount"] <= 0:
                        return "If you intend to borrow or lend, name a partner and an amount above 0 (otherwise choose neither)."
                    if d["credit_partner"] in self.chars[n]["family"]:
                        return "Your family already shares food; loans are only between different families. Pick someone else or neither."
                    if self.is_minor(d["credit_partner"]):
                        return f"{d['credit_partner']} is a child: children cannot borrow or lend (you can give a child a gift instead). Pick someone else or neither."
                    if d["credit_intent"] == "lend" and d["credit_amount"] > self.total_food(n) + 1e-9:
                        return f"You cannot plan to lend more than you hold ({self.total_food(n):g})."
                return None
            d = self.ask(n, "plan", p, plan_schema(others), check) or {
                "ration": "normal", "credit_intent": "neither", "credit_amount": 0, "credit_partner": "none", "plan": ""}
            a = self.st["agents"][n]
            a["ration"], a["plan"] = d["ration"], d["plan"]
            a["credit_plan"] = ({"intent": d["credit_intent"], "amount": d["credit_amount"], "partner": d["credit_partner"]}
                                if d["credit_intent"] != "neither" else None)
            if d["credit_intent"] == "borrow":
                planned.setdefault(key, (n, d["credit_amount"]))
            self.log("plans.jsonl", {"day": 0, "agent": n, **d, "budget": a["budget_numbers"]})
        self.st["stage"], self.st["contact_round"] = "contact", 1
        self.save()

    # ================================================================ CONTACT
    def contact_validator(self, n, rnd, rounds, open_ids):
        def check(d):
            if len(d["messages"]) > self.cfg["social"]["messages_per_round"]:
                return "You can send at most 2 messages per round."
            food = self.st["agents"][n]["food"]
            for m in d["messages"]:
                if m["to"] == n:
                    return "You cannot message yourself."
                if m["proposal"] != "none" and rnd >= rounds:
                    m["proposal"] = "none"   # last round: new proposals could never be answered, so drop them silently
                    continue
                if m["proposal"] in ("loan", "trade") and self.is_minor(n):
                    return "You are a child: children cannot borrow, lend or trade. Set proposal to none (you can still talk, and fish together with an adult)."
                if m["proposal"] in ("loan", "trade") and self.is_minor(m["to"]):
                    return f"{m['to']} is a child: children cannot borrow, lend or trade. If you want to help a child, give a gift at the campfire. Set proposal to none."
                if m["proposal"] in ("loan", "trade") and m["to"] in self.chars[n]["family"]:
                    return f"{m['to']} is your family and already shares your food; loans and trades are only between different families (set proposal to none)."
                if m["proposal"] in ("loan", "trade") and m["give_amount"] <= 0 and m["get_amount"] <= 0:
                    m["proposal"] = "none"   # a deal with no amounts is just talk about a deal: keep it as a plain message
                    continue
                if m["proposal"] == "loan":
                    if m["give_amount"] <= 0 or m["get_amount"] <= 0:
                        if m["loan_role"] == "borrower":
                            return ("You are asking to BORROW, so set give_amount = how many units you want to receive now "
                                    "(e.g. 2) and get_amount = how many units you will pay back later (e.g. 2.5). Both must be "
                                    "greater than 0. To accept a loan someone already offered you, answer it under responses instead.")
                        return ("You are offering to LEND, so set give_amount = how many units you hand over now (e.g. 2) "
                                "and get_amount = how many units they must pay back later (e.g. 2.5). Both must be greater than 0.")
                    if not 1 <= m["day"] <= self.cfg["loans"]["max_days"]:
                        return f"For a loan, day (days until repayment) must be between 1 and {self.cfg['loans']['max_days']}."
                    if m["loan_role"] == "lender" and m["give_amount"] > food[m["give_type"]] + 1e-9:
                        return f"You only have {food[m['give_type']]:g} {m['give_type']} to lend."
                    if m["loan_role"] == "lender" and m["give_amount"] > self.allowance(n) + 1e-9:
                        return (f"Your household's safe surplus this week is only {self.allowance(n):g} units (see your budget), "
                                f"so you cannot lend {m['give_amount']:g}. Lend less or set proposal to none.")
                if m["proposal"] == "trade":
                    if m["give_amount"] <= 0 or m["get_amount"] <= 0:
                        return "Trade amounts must be greater than 0."
                    if m["give_amount"] > food[m["give_type"]] + 1e-9:
                        return f"You only have {food[m['give_type']]:g} {m['give_type']} to give."
                if m["proposal"] == "coop_fish" and not 1 <= m["day"] <= self.cfg["run"]["action_days_per_week"]:
                    return "For coop_fish, day must be between 1 and 5."
            remaining = self.household_remaining_need(n)
            asked = sum(m["give_amount"] for m in d["messages"] if m["proposal"] == "loan" and m["loan_role"] == "borrower")
            lending = 0.0
            for r in d["responses"]:
                if r["accept"] and r["proposal_id"] != "none":
                    pr = next((p for p in self.st["proposals"] if p["id"] == r["proposal_id"]), None)
                    if pr and pr["type"] in ("loan", "trade") and self.is_minor(n):
                        return "You are a child: children cannot borrow, lend or trade, so you must decline this proposal (accept false)."
                    if pr and pr["type"] == "loan" and pr["borrower"] == n:
                        asked += pr["lend_amount"]
                    if pr and pr["type"] == "loan" and pr["lender"] == n:
                        lending += pr["lend_amount"]
            if lending > self.allowance(n) + 1e-9:
                return (f"Accepting would mean lending {lending:g} units, but your household's safe surplus this week is only "
                        f"{self.allowance(n):g} (see your budget). Decline, or accept less.")
            if asked > 0 and remaining <= 0.05:
                return ("Your budget shows your household is not short of food this week, so you should not borrow. "
                        "Decline loan offers (accept false) and do not ask for loans.")
            if asked > remaining + 0.5:
                return (f"That would mean borrowing {asked:g} units, but {'you' if len(self.household(n)) == 1 else 'your household'} "
                        f"still only needs about {remaining:g} this week (already borrowed {self.household_borrowed(n):g}). "
                        f"Borrow less, decline some offers, or do not borrow.")
            ids = [r["proposal_id"] for r in d["responses"] if r["proposal_id"] != "none"]
            if len(ids) != len(set(ids)) or any(i not in open_ids for i in ids):
                return f"Only answer each open proposal once. Open proposals: {', '.join(open_ids) or 'none'}."
            return None
        return check

    def contact_round(self):
        rnd = self.st["contact_round"]
        rounds = self.cfg["social"]["contact_rounds"]
        w = self.st["week"]
        props = self.st["proposals"]
        answers = {}
        self.refresh_finance()
        for n in self.names:
            open_props = [p for p in props if p["to"] == n and p["status"] == "open" and p["round"] < rnd]
            open_ids = [p["id"] for p in open_props]
            p = prompts.contact_prompt(n, self.chars[n], self.group_cfg, self.st, rnd, rounds, open_props)
            check = self.contact_validator(n, rnd, rounds, open_ids)
            d = self.ask(n, "contact", p, contact_schema(self.others(n), open_ids), check)
            if d is None:
                # salvage: keep the messages as plain talk (drop the broken proposals), keep valid answers if possible
                last = getattr(self.llm, "last", None)
                if isinstance(last, dict) and isinstance(last.get("messages"), list):
                    for keep_resp in (True, False):
                        cand = {"messages": [dict(m, proposal="none") for m in last["messages"]][:2],
                                "responses": list(last.get("responses", [])) if keep_resp else []}
                        try:
                            if check(cand) is None:
                                d = cand
                                self.log("errors.jsonl", {"day": self.st["day"], "agent": n, "phase": "contact",
                                                          "errors": ["salvaged: proposals dropped, messages kept"
                                                                     + ("" if keep_resp else ", responses dropped")],
                                                          "fallback": False})
                                break
                        except Exception:
                            pass
            answers[n] = d or {"messages": [], "responses": []}

        # 1. answers to earlier proposals
        for n, d in answers.items():
            for r in d["responses"]:
                if r["proposal_id"] == "none":
                    continue
                prop = next(p for p in props if p["id"] == r["proposal_id"])
                if r["accept"]:
                    self.accept_proposal(prop)
                else:
                    prop["status"] = "rejected"
                    self.remember(prop["from"], f"W{w}: {n} rejected your proposal ({prompts.describe_proposal(prop)}).")
                self.log("trades.jsonl", {"day": 0, **prop})

        # 2. new messages and proposals (read by the recipient next round)
        for n, d in answers.items():
            for m in d["messages"]:
                self.hear(m["to"], f"W{w} private message from {n}: \"{m['text']}\"")
                self.hear(n, f"W{w} you wrote privately to {m['to']}: \"{m['text']}\"")
                row = {"day": 0, "phase": "contact", "round": rnd, "speaker": n, "to": m["to"],
                       "text": m["text"], "proposal": m["proposal"]}
                if m["proposal"] in ("loan", "trade"):
                    dup = self.same_deal(n, m)
                    if dup:   # the same deal already exists this week: do not create a second copy of it
                        self.remember(n, f"W{w}: your proposal to {m['to']} was not sent again: it is the same deal as "
                                         f"{dup['id']} ({prompts.describe_proposal(dup)}), which is already {dup['status']}. "
                                         f"To accept an offer, answer it under responses.")
                        row["duplicate_of"] = dup["id"]
                        m = dict(m, proposal="none")
                if m["proposal"] != "none":
                    prop = {"id": f"P{self.st['next_pid']}", "type": m["proposal"], "from": n,
                            "to": m["to"], "round": rnd, "status": "open"}
                    self.st["next_pid"] += 1
                    if m["proposal"] == "trade":
                        prop.update(give_type=m["give_type"], give_amount=round(m["give_amount"], 2),
                                    get_type=m["get_type"], get_amount=round(m["get_amount"], 2))
                    elif m["proposal"] == "loan":
                        lender, borrower = (n, m["to"]) if m["loan_role"] == "lender" else (m["to"], n)
                        prop.update(lender=lender, borrower=borrower, lend_type=m["give_type"],
                                    lend_amount=round(m["give_amount"], 2), repay=round(m["get_amount"], 2),
                                    days=int(m["day"]))
                    else:
                        prop["fish_day"] = m["day"]
                    props.append(prop)
                    row["proposal_id"] = prop["id"]
                    row["proposal_detail"] = prompts.describe_proposal(prop)
                self.log("dialogues.jsonl", row)

        # 3. advance
        if rnd >= rounds:
            for p in props:
                if p["status"] == "open":
                    p["status"] = "expired"
                    self.log("trades.jsonl", {"day": 0, **p})
            self.st["stage"], self.st["day"] = "day", 1
        else:
            self.st["contact_round"] += 1
        self.save()

    def same_deal(self, n, m):
        """An open or accepted proposal this week between the same two people with the same terms, if any."""
        for p in self.st["proposals"]:
            if p["status"] not in ("open", "accepted") or {p["from"], p["to"]} != {n, m["to"]} or p["type"] != m["proposal"]:
                continue
            if p["type"] == "loan":
                lender, borrower = (n, m["to"]) if m["loan_role"] == "lender" else (m["to"], n)
                if (p["lender"], p["borrower"], p["lend_type"]) == (lender, borrower, m["give_type"]) and \
                        abs(p["lend_amount"] - m["give_amount"]) < 0.01 and abs(p["repay"] - m["get_amount"]) < 0.01:
                    return p
            elif p["type"] == "trade":
                same = (p["from"] == n and (p["give_type"], p["get_type"]) == (m["give_type"], m["get_type"])
                        and abs(p["give_amount"] - m["give_amount"]) < 0.01 and abs(p["get_amount"] - m["get_amount"]) < 0.01)
                mirror = (p["to"] == n and (p["give_type"], p["get_type"]) == (m["get_type"], m["give_type"])
                          and abs(p["give_amount"] - m["get_amount"]) < 0.01 and abs(p["get_amount"] - m["give_amount"]) < 0.01)
                if same or mirror:
                    return p
        return None

    def give_food(self, giver, receiver, amount, ftype=None, where="campfire"):
        """Hand food over (costs no time). Returns the amount actually given."""
        w, day = self.st["week"], self.st["day"]
        if ftype:
            have = self.st["agents"][giver]["food"][ftype]
            amt = round(min(amount, have), 2)
            parts = {ftype: amt} if amt > 0 else {}
            if amt > 0:
                self.st["agents"][giver]["food"][ftype] = round(have - amt, 2)
        else:
            parts = self.remove_food(giver, min(amount, self.total_food(giver)))
            amt = round(sum(parts.values()), 2)
        if amt <= 0:
            return 0
        self.add_food(receiver, parts)
        when = f"W{w}" if where == "private message" else f"W{w}D{day}"
        self.remember(receiver, f"{when}: {giver} gave you {amt:g} units of food ({where}).")
        self.remember(giver, f"{when}: you gave {receiver} {amt:g} units of food ({where}).")
        self.log("gifts.jsonl", {"day": day if where != "private message" else 0, "giver": giver,
                                 "receiver": receiver, "amount": amt, "parts": parts, "where": where})
        return amt

    def accept_proposal(self, p):
        w = self.st["week"]
        a, b = p["from"], p["to"]
        if p["type"] == "trade":
            fa, fb = self.st["agents"][a]["food"], self.st["agents"][b]["food"]
            if fa[p["give_type"]] + 1e-9 < p["give_amount"] or fb[p["get_type"]] + 1e-9 < p["get_amount"]:
                p["status"] = "failed"
                msg = f"W{w}: the trade between {a} and {b} failed: someone no longer had the food ({prompts.describe_proposal(p)})."
                self.remember(a, msg)
                self.remember(b, msg)
                return
            fa[p["give_type"]] = round(fa[p["give_type"]] - p["give_amount"], 2)
            fb[p["give_type"]] = round(fb[p["give_type"]] + p["give_amount"], 2)
            fb[p["get_type"]] = round(fb[p["get_type"]] - p["get_amount"], 2)
            fa[p["get_type"]] = round(fa[p["get_type"]] + p["get_amount"], 2)
            p["status"] = "accepted"
            self.remember(a, f"W{w}: {b} accepted your trade: {prompts.describe_proposal(p, viewer=a)}.")
            self.remember(b, f"W{w}: you accepted {a}'s trade: {prompts.describe_proposal(p, viewer=b)}.")
        elif p["type"] == "loan":
            lender, borrower = p["lender"], p["borrower"]
            fl = self.st["agents"][lender]["food"]
            if fl[p["lend_type"]] + 1e-9 < p["lend_amount"]:
                p["status"] = "failed"
                for x in (lender, borrower):
                    self.remember(x, f"W{w}: the loan from {lender} to {borrower} failed: {lender} no longer had "
                                     f"{p['lend_amount']:g} units of {p['lend_type']}.")
                return
            if self.household_remaining_need(borrower) <= 0.05:
                p["status"] = "failed"
                for x in (lender, borrower):
                    self.remember(x, f"W{w}: the loan from {lender} to {borrower} was cancelled: {borrower}'s household is not short "
                                     f"of food this week, so no loan was needed (to help someone who is not short, give a gift instead).")
                return
            if p["lend_amount"] > self.allowance(lender) + 1e-9:
                p["status"] = "failed"
                for x in (lender, borrower):
                    self.remember(x, f"W{w}: the loan from {lender} to {borrower} was cancelled: {lender}'s household has no safe "
                                     f"surplus left for it this week.")
                return
            # household cap: once a family has borrowed this week, it may not borrow beyond its shortfall
            if self.household_borrowed(borrower) > 0 and p["lend_amount"] > self.household_remaining_need(borrower) + 0.5:
                p["status"] = "failed"
                got = self.household_borrowed(borrower)
                for x in (lender, borrower):
                    self.remember(x, f"W{w}: the loan from {lender} to {borrower} was cancelled: {borrower}'s household "
                                     f"had already borrowed {got:g} units this week, which covers its shortfall.")
                return
            fl[p["lend_type"]] = round(fl[p["lend_type"]] - p["lend_amount"], 2)
            self.add_food(borrower, {p["lend_type"]: p["lend_amount"]})
            due = self.abs_day(day=0) + p["days"]   # contact happens before day 1 of this week
            loan = {"id": p["id"], "lender": lender, "borrower": borrower, "lend_type": p["lend_type"],
                    "amount": p["lend_amount"], "repay": p["repay"], "paid": 0.0, "made": self.abs_day(day=0),
                    "due": due, "status": "active",
                    "interest": round(p["repay"] / p["lend_amount"] - 1, 3)}
            self.st["loans"].append(loan)
            self.spend_allowance(lender, p["lend_amount"])
            p["status"] = "accepted"
            self.log("loans.jsonl", {"day": 0, "event": "made", **loan})
            self.remember(lender, f"W{w}: you lent {borrower} {p['lend_amount']:g} units of {p['lend_type']} (already handed over); "
                                  f"{borrower} must repay {p['repay']:g} units by the end of {self.day_label(due)}.")
            self.remember(borrower, f"W{w}: you borrowed {p['lend_amount']:g} units of {p['lend_type']} from {lender}; "
                                    f"you must repay {p['repay']:g} units by the end of {self.day_label(due)}.")
        else:
            busy = [c for c in self.st["coops"] if c["day"] == p["fish_day"] and {a, b} & {c["a"], c["b"]}]
            if busy:
                p["status"] = "failed"
                self.remember(a, f"W{w}: fishing with {b} on day {p['fish_day']} failed: someone is already fishing with another person that day.")
                return
            self.st["coops"].append({"a": a, "b": b, "day": p["fish_day"], "pid": p["id"]})
            p["status"] = "accepted"
            self.remember(a, f"W{w}: {b} agreed to fish with you on day {p['fish_day']}.")
            self.remember(b, f"W{w}: you agreed to fish with {a} on day {p['fish_day']}.")

    # ================================================================ DAY
    def menu(self, n):
        """Actions this agent may take today, with a one-line description."""
        A, S = self.cfg["actions"], self.cfg["stamina"]
        a, c = self.st["agents"][n], self.chars[n]
        blocked = self.cfg["events"]["typhoon"]["blocked_actions"] if self.typhoon_today() else []
        heavy_ok = a["stamina"] >= S["heavy_work_min"]
        k = c["productivity"]

        def rng_text(lo, hi):  # yields shown to the agent already include their productivity
            return f"{round(lo * k, 1):g}-{round(hi * k, 1):g} units, average {round((lo + hi) / 2 * k, 1):g}"
        work = []  # (average yield, key, text) -> listed best-first so poor options are obvious
        if heavy_ok and a["stamina"] >= A["fish"]["min_stamina"] and "fish" not in blocked:
            gear = A["fish"]["gear_item"] in c["items"]
            lo, hi = A["fish"]["yield_with_gear" if gear else "yield_without_gear"]
            txt = f"fish ({'with your fishing gear' if gear else 'WITHOUT fishing gear, often catches nothing'}; {rng_text(lo, hi)}; -{self.cost('fish')} stamina; fish spoils fastest but eating it gives +5 stamina)"
            work.append(((lo + hi) / 2, "fish", txt))
        lo, hi = A["clam"]["yield"]
        ny = self.st.get("clam_yesterday")
        crowd = f" - yesterday {ny} people went, so everyone got half" if ny and ny > A["clam"]["crowd_limit"] else ""
        work.append(((lo + hi) / 2 * (0.5 if crowd else 1), "clam", f"gather clams in tide pools ({rng_text(lo, hi)}; halved if more than 2 people go{crowd}; light work, allowed even when exhausted; -{self.cost('clam')} stamina)"))
        if (heavy_ok and a["stamina"] >= A["coconut"]["min_stamina"] and c["age"] <= A["coconut"]["max_age"]
                and self.st["coconuts_left"] > 0 and "coconut" not in blocked):
            lo, hi = A["coconut"]["yield"]
            work.append(((lo + hi) / 2, "coconut", f"climb coconut trees ({rng_text(lo, hi)}; {self.st['coconuts_left']:g} coconuts left on the island; coconuts keep well; -{self.cost('coconut')} stamina)"))
        if heavy_ok and "forage" not in blocked:
            lo, hi = A["forage"]["yield"]
            work.append(((lo + hi) / 2, "forage", f"forage in the forest ({rng_text(lo, hi)}; 20% chance of injury: -20 stamina; -{self.cost('forage')} stamina)"))
        work.sort(key=lambda x: -x[0])
        top = work[0][0] if work else 0
        m = {key: (txt + (f" [LOW YIELD for you: less than half of your best option ({work[0][1]})]" if avg < 0.5 * top else ""))
             for avg, key, txt in work}
        if heavy_ok and "shelter" not in blocked:
            m["shelter"] = f"build the shared shelter (no food; progress {self.st['shelter_progress']} so far; -{self.cost('shelter')} stamina)"
        m["rest"] = ("rest (you are already well rested, so this gains you almost nothing)"
                     if a["stamina"] >= 90 else "rest (+15 stamina)")
        m["steal"] = "secretly steal 1-3 units from someone (50% chance they find out it was you)"
        if A["forage"]["heal_item"] in c["items"]:
            hurt = [x for x in self.names if self.st["agents"][x]["injured"]]
            if hurt:
                m["heal"] = f"heal an injured person with your first aid kit (+20 stamina to them); injured: {', '.join(hurt)}"
        if self.typhoon_today():
            m = {"_note": "A typhoon is hitting the island: only gathering clams (or resting) is possible today.", **m}
        return m

    def validator(self, n, menu):
        def check(d):
            act = d["action"]
            if act not in menu:
                return f"'{act}' is not available to you today. Pick one of: {', '.join(k for k in menu if k != '_note')}."
            if act in ("give", "steal") or (act == "heal" and d["target"] == "none"):
                if d["target"] in ("none", n):
                    return f"'{act}' needs a target other than yourself."
            if act == "give":
                if d["amount"] <= 0 or d["amount"] > self.total_food(n) + 1e-9:
                    return f"amount must be between 0 and your food ({self.total_food(n):g})."
            if act == "heal" and not self.st["agents"][d["target"]]["injured"]:
                return f"{d['target']} is not injured."
            return None
        return check

    def coop_negotiation(self, a, b, catch):
        """Up to N turns of talk to split the joint catch. Returns {a: units, b: units}."""
        w, day = self.st["week"], self.st["day"]
        mult = self.cfg["actions"]["coop_fish"]["multiplier"]
        total = round((catch[a] + catch[b]) * mult, 1)
        max_turns = self.cfg["actions"]["coop_fish"]["max_dialogue_turns"]
        transcript, last_offer = [], {}
        for turn in range(1, max_turns + 1):
            me, other = (a, b) if turn % 2 == 1 else (b, a)
            p = prompts.coop_prompt(me, self.chars[me], self.group_cfg, self.st, other, catch,
                                    total, transcript, turn, max_turns)

            def check(d, other=other):
                if not 0 <= d["my_share"] <= total + 1e-9:
                    return f"my_share must be between 0 and {total:g}."
                if d["accept"] and other not in last_offer:
                    return f"{other} has not made an offer yet, so you cannot accept."
                return None
            d = self.ask(me, "coop", p, coop_schema(), check) or {"say": "...", "my_share": total / 2, "accept": False}
            transcript.append(f"{me}: \"{d['say']}\" (wants {d['my_share']:g} for self"
                              + (", ACCEPTS the last offer" if d["accept"] else "") + ")")
            self.log("dialogues.jsonl", {"day": day, "phase": "coop", "turn": turn, "speaker": me,
                                         "to": other, "text": d["say"], "my_share": d["my_share"],
                                         "accept": d["accept"], "total": total})
            if d["accept"]:
                other_gets = round(min(last_offer[other], total), 1)
                split = {other: other_gets, me: round(total - other_gets, 1)}
                break
            last_offer[me] = d["my_share"]
        else:  # no deal: the teamwork bonus is lost, each keeps only their own catch
            split = {a: round(catch[a], 1), b: round(catch[b], 1)}
        deal = "agreed" if len(transcript) and "ACCEPTS" in transcript[-1] else "no agreement"
        for x, y in ((a, b), (b, a)):
            self.remember(x, f"W{w}D{day}: you fished with {y}; together {total:g} units; "
                             f"{deal}: you got {split[x]:g}, {y} got {split[y]:g}.")
        self.log("coops.jsonl", {"day": day, "a": a, "b": b, "catch": catch, "total": total,
                                 "split": split, "agreed": deal == "agreed", "turns": len(transcript)})
        return split

    def play_day(self):
        w, day = self.st["week"], self.st["day"]
        A, S = self.cfg["actions"], self.cfg["stamina"]

        # news
        radio = self.cfg["events"]["radio"]
        if (w, day) == (radio["week"], radio["day"]):
            self.st["news"].append(radio["message"])
        self.st["alerts"] = (["A typhoon is hitting the island today: no fishing, climbing, forest or building."]
                             if self.typhoon_today() else [])

        # 0. today's coop-fishing deals
        pairs = []
        for c in self.st["coops"]:
            if c["day"] != day:
                continue
            if self.can_fish(c["a"]) and self.can_fish(c["b"]):
                pairs.append((c["a"], c["b"]))
            else:
                why = "the typhoon" if self.typhoon_today() else "someone is too exhausted"
                self.log("coops.jsonl", {"day": day, "a": c["a"], "b": c["b"], "cancelled": True, "reason": why,
                                         "stamina": {x: self.st["agents"][x]["stamina"] for x in (c["a"], c["b"])}})
                for x in (c["a"], c["b"]):
                    self.remember(x, f"W{w}D{day}: the planned fishing of {c['a']} and {c['b']} was cancelled ({why}).")
        partner = {x: y for a, b in pairs for x, y in ((a, b), (b, a))}

        # 1. everyone decides from the same morning state
        self.refresh_finance(morning=True)
        choices = {}
        for n in self.names:
            a = self.st["agents"][n]
            if n in partner:
                choices[n] = {"action": "coop_fish", "target": partner[n], "amount": 0,
                              "ration": a["ration"], "thought": "(agreed cooperative fishing)"}
                continue
            if a["stamina"] < S["collapse_below"]:
                choices[n] = {"action": "rest", "target": "none", "amount": 0, "ration": a["ration"],
                              "thought": "(collapsed from exhaustion: forced rest)", "forced": True}
                continue
            m = self.menu(n)
            p = prompts.action_prompt(n, self.chars[n], self.group_cfg, self.st, m)
            d = self.ask(n, "action", p, action_schema(self.names), self.validator(n, m))
            choices[n] = d or {"action": self.cfg["llm"]["fallback_action"], "target": "none",
                               "amount": 0, "ration": a["ration"],
                               "thought": "(fallback after invalid answers)"}

        # 2. resolve (work -> coop -> give -> steal -> heal)
        n_clam = sum(1 for d in choices.values() if d["action"] == "clam")
        clam_factor = A["clam"]["crowd_factor"] if n_clam > A["clam"]["crowd_limit"] else 1.0
        self.st["clam_yesterday"] = n_clam
        results = {n: {"got": {}, "injured": False, "note": ""} for n in self.names}

        order = self.names[:]
        self.rng.shuffle(order)  # who reaches the coconuts first is random
        for n in order:
            d, a, act = choices[n], self.st["agents"][n], choices[n]["action"]
            k = self.chars[n]["productivity"]
            got = 0.0
            if act == "rest":
                a["stamina"] = min(S["max"], a["stamina"] + S["rest_gain"])
            elif act in PRODUCTIVE:
                if act == "fish":
                    got = self.fish_catch(n)
                elif act == "clam":
                    got = self.rng.randint(*A["clam"]["yield"]) * clam_factor * k
                elif act == "coconut":
                    raw = min(self.rng.randint(*A["coconut"]["yield"]), self.st["coconuts_left"])
                    self.st["coconuts_left"] -= raw
                    got = raw * k
                elif act == "forage":
                    got = self.rng.randint(*A["forage"]["yield"]) * k
                    if self.rng.random() < A["forage"]["injury_prob"]:
                        a["stamina"] -= A["forage"]["injury_stamina"]
                        a["injured"] = True
                        results[n]["injured"] = True
                elif act == "shelter":
                    self.st["shelter_progress"] += A["shelter"]["progress"]
                a["stamina"] = max(S["min"], a["stamina"] - self.cost(act))
                if got:
                    got = round(got, 1)
                    self.add_food(n, {A[act]["food_type"]: got})
                    results[n]["got"] = {A[act]["food_type"]: got}

        for a_, b_ in pairs:  # cooperative fishing
            catch = {a_: self.fish_catch(a_), b_: self.fish_catch(b_)}
            split = self.coop_negotiation(a_, b_, catch)
            for x in (a_, b_):
                self.st["agents"][x]["stamina"] = max(S["min"], self.st["agents"][x]["stamina"] - self.cost("coop_fish"))
                if split[x]:
                    self.add_food(x, {"fish": split[x]})
                results[x]["got"] = {"fish": split[x]}
                results[x]["note"] = f"fished with {partner[x]} (caught {catch[x]:g}, total {sum(catch.values()) * A['coop_fish']['multiplier']:.1f})"

        if not self.typhoon_today():  # remember what each person actually produced on normal days (for the budget)
            for n in self.names:
                h = self.st["agents"][n].setdefault("prod_hist", [])
                h.append(round(sum(results[n]["got"].values()), 2))
                del h[:-5]

        for n in self.names:  # give
            d = choices[n]
            if d["action"] == "give":
                amt = min(d["amount"], self.total_food(n))
                parts = self.remove_food(n, amt)
                self.add_food(d["target"], parts)
                results[n]["note"] = f"gave {amt:g} units to {d['target']}"
                self.remember(d["target"], f"W{w}D{day}: {n} gave you {amt:g} units of food.")

        for n in self.names:  # steal
            d = choices[n]
            if d["action"] == "steal":
                victim = d["target"]
                amt = min(self.rng.randint(*A["steal"]["amount"]), self.total_food(victim))
                parts = self.remove_food(victim, amt)
                self.add_food(n, parts)
                caught = self.rng.random() < A["steal"]["detect_prob"]
                results[n]["note"] = f"stole {amt:g} units from {victim} ({'caught' if caught else 'unseen'})"
                results[n]["stolen"] = {"victim": victim, "amount": amt, "caught": caught}
                if amt > 0:
                    self.remember(victim, f"W{w}D{day}: {n if caught else 'someone'} stole {amt:g} units of your food.")

        for n in self.names:  # heal
            d = choices[n]
            if d["action"] == "heal":
                t = self.st["agents"][d["target"]]
                if t["injured"]:
                    t["injured"] = False
                    t["stamina"] = min(S["max"], t["stamina"] + A["forage"]["injury_stamina"])
                    self.remember(d["target"], f"W{w}D{day}: {n} healed your injury.")
                    results[n]["note"] = f"healed {d['target']}"

        # 3. eat (today's ration choice also becomes the default for the next days)
        #    pass 1: everyone eats from their own food
        eaten, want, from_family = {}, {}, {n: {} for n in self.names}
        fish_eaten = {n: 0.0 for n in self.names}
        for n in self.names:
            a = self.st["agents"][n]
            a["ration"] = choices[n]["ration"]
            want[n] = self.chars[n]["daily_need"] * self.cfg["rations"][a["ration"]]
            parts = self.remove_food(n, want[n])
            fish_eaten[n] += parts.get("fish", 0)
            eaten[n] = round(sum(parts.values()), 2)
        #    pass 2: whoever is still short eats from their family's leftovers (one household)
        if self.cfg["food"].get("family_shares_food", True):
            for n in self.names:
                for f in sorted(self.chars[n]["family"], key=lambda x: -self.total_food(x)):
                    short = round(want[n] - eaten[n], 2)
                    if short <= 1e-9:
                        break
                    parts = self.remove_food(f, short)
                    fish_eaten[n] += parts.get("fish", 0)
                    took = round(sum(parts.values()), 2)
                    if took > 0:
                        eaten[n] = round(eaten[n] + took, 2)
                        from_family[n][f] = took
                        self.remember(f, f"W{w}D{day}: {n} ate {took:g} units of your food (family shares).")
        #    hunger
        for n in self.names:
            a, need = self.st["agents"][n], self.chars[n]["daily_need"]
            if eaten[n] < need * self.cfg["hunger_threshold"] - 1e-9:
                a["stamina"] = max(S["min"], a["stamina"] - S["hunger_penalty"])
                a["starving_days"] += 1
                a["starve_streak"] = a.get("starve_streak", 0) + 1
            else:
                a["starve_streak"] = 0
                if eaten[n] < need - 1e-9:
                    a["stamina"] = max(S["min"], a["stamina"] - S["underfed_penalty"])
                # a night's sleep on a (half-)full stomach
                a["stamina"] = min(S["max"], a["stamina"] + S.get("overnight_recovery", 0))
            # protein bonus for eating fish
            pb = self.cfg["food"].get("protein_bonus")
            if pb and fish_eaten[n] >= pb["min_fish"] - 1e-9:
                a["stamina"] = min(S["max"], a["stamina"] + pb["stamina"])
            # starving several days in a row: resting cannot replace food, so strength is capped
            cap = S.get("starving_cap")
            if cap and a.get("starve_streak", 0) > 0:
                limit = max(cap["floor"], cap["start"] - cap["step"] * (a["starve_streak"] - 1))
                a["stamina"] = min(a["stamina"], limit)

        # 3b. loan repayments (automatic, after everyone has eaten)
        self.collect_loans()

        # 4. memory, public view, logs
        public = []
        for n in self.names:
            d, r = choices[n], results[n]
            if d["action"] == "steal":
                seen = f"was seen stealing from {d['target']}" if r["stolen"]["caught"] else "stayed around camp"
            elif d["action"] in ("give", "heal"):
                seen = r["note"]
            elif d["action"] == "coop_fish":
                seen = f"fished together with {d['target']}"
            elif d.get("forced"):
                seen = "collapsed from exhaustion and had to rest"
            else:
                seen = d["action"]
                brought = round(sum(r["got"].values()), 1)
                if d["action"] in PRODUCTIVE and d["action"] != "shelter":
                    seen += f" (came back with about {brought:g} units)" if brought > 0 else " (came back with nothing)"
            if d["action"] == "coop_fish":
                seen += f" (they came back with about {round(sum(results[n]['got'].values()) + sum(results[d['target']]['got'].values()), 1):g} units together)"
            if self.st["agents"][n].get("starve_streak", 0) >= 2:
                seen += f" (looks weak: has barely eaten for {self.st['agents'][n]['starve_streak']} days)"
            public.append(f"{n}: {seen}")
            if d["action"] != "coop_fish":  # coop already wrote its own memory line
                gained = ", ".join(f"{t} {x:g}" for t, x in r["got"].items())
                self.remember(n, (f"W{w}D{day}: you collapsed from exhaustion and could only rest"
                                  if d.get("forced") else f"W{w}D{day}: you chose {d['action']}")
                              + (f", got {gained}" if gained else (", got nothing" if d["action"] in ("fish", "clam", "coconut", "forage") else ""))
                              + (", and got injured" if r["injured"] else "")
                              + (f"; {r['note']}" if r["note"] else "")
                              + f"; ate {eaten[n]:g}/{self.chars[n]['daily_need']:g}"
                              + (" incl. fish (+5 stamina)" if fish_eaten[n] >= self.cfg["food"].get("protein_bonus", {}).get("min_fish", 99) - 1e-9 else "")
                              + (" (" + ", ".join(f"{v:g} from {k}'s food" for k, v in from_family[n].items()) + ")"
                                 if from_family[n] else "") + ".")
            self.log("actions.jsonl", {
                "day": day, "agent": n, "action": d["action"], "target": d["target"],
                "amount": d["amount"], "ration": d["ration"], "thought": d["thought"],
                "got": r["got"], "injured": r["injured"], "note": r["note"],
                "forced": d.get("forced", False),
                **({"stolen": r["stolen"]} if "stolen" in r else {})})
        for n in self.names:
            a = self.st["agents"][n]
            self.log("states.jsonl", {
                "day": day, "agent": n,
                "food_total": round(self.total_food(n), 2), "food": a["food"],
                "stamina": a["stamina"], "injured": a["injured"], "ration": a["ration"],
                "eaten": eaten[n], "fullness": round(eaten[n] / self.chars[n]["daily_need"] * 100),
                "from_family": from_family[n], "fish_eaten": round(fish_eaten[n], 2),
                "debt": round(sum(L["repay"] - L["paid"] for L in self.st["loans"]
                                  if L["borrower"] == n and L["status"] in ("active", "overdue")), 2),
                "starving_days": a["starving_days"],
                "generosity": a["generosity"], "trust": a["trust"],
                "coconuts_left": self.st["coconuts_left"],
                "shelter_progress": self.st["shelter_progress"]})
        self.st["public"] = public

        # 5. campfire
        self.campfire()

        # 6. advance the clock
        self.st["alerts"] = []
        if day == self.cfg["run"]["action_days_per_week"]:
            self.st["stage"] = "review"
        else:
            self.st["day"] += 1
        self.save()

    def collect_loans(self):
        w, day = self.st["week"], self.st["day"]
        today = self.abs_day()
        for L in self.st["loans"]:
            if L["status"] not in ("active", "overdue") or L["due"] > today:
                continue
            b, l = L["borrower"], L["lender"]
            left = round(L["repay"] - L["paid"], 2)
            # the household shares food, so it also shares the debt: borrower pays first, then family members
            got, helpers = 0.0, []
            for m in self.household(b):
                need = round(left - got, 2)
                if need <= 1e-6:
                    break
                parts = self.remove_food(m, min(need, self.total_food(m)))
                paid = round(sum(parts.values()), 2)
                if paid > 0:
                    self.add_food(l, parts)
                    got = round(got + paid, 2)
                    if m != b:
                        helpers.append(m)
                        self.remember(m, f"W{w}D{day}: {paid:g} units of your food went to {l} to repay your family's debt ({b} borrowed).")
            if got > 0:
                L["paid"] = round(L["paid"] + got, 2)
            left = round(L["repay"] - L["paid"], 2)
            if left <= 1e-6:
                L["status"] = "repaid"
                L["repaid_on"] = today
                late = today > L["due"]
                self.remember(b, f"W{w}D{day}: you {'finally ' if late else ''}repaid your debt to {l} in full.")
                self.remember(l, f"W{w}D{day}: {b} {'finally ' if late else ''}repaid you in full ({L['repay']:g} units).")
                self.log("loans.jsonl", {"day": day, "event": "repaid_late" if late else "repaid", "id": L["id"],
                                         "lender": l, "borrower": b, "paid_today": got})
            else:
                if L["status"] == "active":   # first time it is missed: a public default
                    L["status"] = "overdue"
                    for x in self.names:
                        who = "you" if x == b else b
                        self.hear(x, f"W{w}D{day}: {who} failed to repay {l} on time (still owes {left:g} units).")
                    self.log("loans.jsonl", {"day": day, "event": "default", "id": L["id"], "lender": l,
                                             "borrower": b, "paid_today": got, "still_owed": left})
                elif got > 0:
                    self.log("loans.jsonl", {"day": day, "event": "partial", "id": L["id"], "lender": l,
                                             "borrower": b, "paid_today": got, "still_owed": left})
                if got > 0:
                    self.remember(b, f"W{w}D{day}: {got:g} units of your food went to {l} to repay your debt; still owe {left:g}.")
                    self.remember(l, f"W{w}D{day}: {b} paid you {got:g} units; still owes {left:g}.")

    # ================================================================ CAMPFIRE
    def campfire(self):
        w, day = self.st["week"], self.st["day"]
        lines = {}
        self.refresh_finance()
        for n in self.names:
            others = self.others(n)
            p = prompts.campfire_prompt(n, self.chars[n], self.group_cfg, self.st, others)
            def check(d, n=n):
                if d["to"] == n:
                    return "You cannot whisper to yourself."
                if d["gift_to"] != "none":
                    if d["gift_to"] == n:
                        return "You cannot give food to yourself."
                    if self.is_minor(n):
                        return "You are a child: you can receive gifts but not hand out food. Set gift_to to none and gift_amount to 0."
                    if d["gift_to"] in self.chars[n]["family"]:
                        return f"{d['gift_to']} is your family and already eats from your food. Set gift_to to none."
                    if d["gift_amount"] > self.allowance(n) + 1e-9:
                        return (f"Your household's safe surplus left this week is only {self.allowance(n):g} units (see your budget), "
                                f"so you cannot give {d['gift_amount']:g}. Give at most that, or set gift_to to none.")
                    if d["gift_amount"] <= 0 or d["gift_amount"] > self.total_food(n) + 1e-9:
                        return f"gift_amount must be between 0 and your food ({self.total_food(n):g}), or set gift_to to none."
                return None
            lines[n] = self.ask(n, "campfire", p, campfire_schema(others), check)
        for n, d in lines.items():  # everyone speaks "at the same time", then hears
            if d is None:
                continue
            if d["to"] == "everyone":
                for x in self.names:
                    self.hear(x, f"W{w}D{day} campfire, {'you' if x == n else n} said to everyone: \"{d['text']}\"")
            else:
                self.hear(d["to"], f"W{w}D{day} campfire, {n} whispered to you: \"{d['text']}\"")
                self.hear(n, f"W{w}D{day} campfire, you whispered to {d['to']}: \"{d['text']}\"")
            gift = 0
            if d["gift_to"] != "none" and d["gift_amount"] > 0:
                gift = self.give_food(n, d["gift_to"], min(d["gift_amount"], self.allowance(n)))
                if gift:
                    self.spend_allowance(n, gift)
                    for x in self.others(n):
                        if x != d["gift_to"]:
                            self.hear(x, f"W{w}D{day} campfire: you saw {n} give {gift:g} units of food to {d['gift_to']}.")
            self.log("dialogues.jsonl", {"day": day, "phase": "campfire", "speaker": n,
                                         "to": d["to"], "text": d["text"],
                                         "gift_to": d["gift_to"] if gift else "none", "gift_amount": gift})

    # ================================================================ REVIEW
    def review_phase(self):
        w = self.st["week"]
        self.refresh_finance()
        for n in self.names:
            others = self.others(n)
            p = prompts.review_prompt(n, self.chars[n], self.group_cfg, self.st, others)
            d = self.ask(n, "review", p, review_schema(others), self.review_validator(others))
            if d is None:
                continue
            a = self.st["agents"][n]
            a["diary"].append(d["diary"])
            a["impressions"] = {o: d["ratings"][o]["impression"] for o in others}
            self.log("ratings.jsonl", {"day": 6, "rater": n, "ratings": d["ratings"],
                                       "self_generosity": d["self_generosity"],
                                       "self_trust": d["self_trust"], "diary": d["diary"]})
        season = self.cfg["run"]["season_length_weeks"]
        self.st["stage"] = "season" if w % season == 0 else "end"
        if self.st["stage"] == "end":
            self.end_week()
        self.save()

    def review_validator(self, others):
        def check(d):
            for o in others:
                r = d["ratings"].get(o)
                if r is None:
                    return f"Missing rating for {o}."
                if not (0 <= r["like"] <= 100 and 0 <= r["respect"] <= 100):
                    return "Ratings must be between 0 and 100."
            return None
        return check

    # ================================================================ SEASON
    def season_phase(self):
        season = self.cfg["run"]["season_length_weeks"]
        cap = self.cfg["persona_update"]["max_shift_per_season"]
        w = self.st["week"]
        for n in self.names:
            a = self.st["agents"][n]
            first = w - season + 1
            diaries = [(first + i, t) for i, t in enumerate(a["diary"][-season:])]
            p = prompts.season_prompt(n, self.chars[n], self.st, diaries)
            d = self.ask(n, "season", p, season_schema())
            if d is None:
                continue
            before = {"mindset": a["mindset"], "generosity": a["generosity"], "trust": a["trust"]}
            a["mindset"] = d["mindset"]
            a["generosity"] = max(a["generosity"] - cap, min(a["generosity"] + cap, d["generosity"]))
            a["trust"] = max(a["trust"] - cap, min(a["trust"] + cap, d["trust"]))
            self.log("personas.jsonl", {"day": 6, "agent": n, "before": before,
                                        "after": {"mindset": a["mindset"], "generosity": a["generosity"],
                                                  "trust": a["trust"]},
                                        "requested": {"generosity": d["generosity"], "trust": d["trust"]}})
        self.end_week()
        self.save()

    def end_week(self):
        rates = self.cfg["food"]["spoil_rate_weekly"]
        for n in self.names:
            food = self.st["agents"][n]["food"]
            for t, r in rates.items():
                food[t] = round(food[t] * (1 - r), 2)
        self.st.update(week=self.st["week"] + 1, day=1, stage="plan", contact_round=1,
                       proposals=[], coops=[], forecast="")

    # ================================================================ MAIN LOOP
    def run(self, weeks, verbose=True):
        say = print if verbose else (lambda *a: None)
        while self.st["week"] <= weeks:
            w, s = self.st["week"], self.st["stage"]
            if s == "plan":
                say(f"=== Week {w}: Plan ===")
                self.plan_phase()
            elif s == "contact":
                r = self.st["contact_round"]
                self.contact_round()
                n_msg = sum(1 for p in self.st["proposals"])
                say(f"W{w} contact round {r} done | proposals so far: {n_msg}")
            elif s == "day":
                d = self.st["day"]
                self.play_day()
                summary = ", ".join(f"{n} {self.st['agents'][n]['stamina']:g}st/{self.total_food(n):g}f"
                                    for n in self.names)
                say(f"W{w}D{d} done | {summary}")
            elif s == "review":
                self.review_phase()
                say(f"W{w} review done")
            elif s == "season":
                self.season_phase()
                say(f"W{w} season update done (mindsets rewritten)")
