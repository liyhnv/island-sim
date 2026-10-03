"""
Scarcity calibration (no LLM).

Simulates the island with a simple random policy and reports
  full-effort output / total island need
averaged over many runs. Target: 0.80-0.90 (see config.yaml).

Two policies are simulated, both resting when stamina < REST_BELOW:
  - random: pick uniformly among the productive actions allowed today
  - greedy: pick the allowed action with the highest expected yield
    ("full effort" benchmark; this is the one compared to the target)

Simplifications (this only measures production capacity):
  - no eating, spoilage, hunger, trading, or cooperative fishing
  - forage injuries are applied but never healed
  - the week-3 typhoon is included

Usage:
  python3 calibrate.py
"""

import random
import json
import yaml

REST_BELOW = 40  # agents rest when stamina falls below this

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
with open("characters.json") as f:
    chars = json.load(f)

A = cfg["actions"]
ST = cfg["stamina"]
WEEKS = cfg["run"]["weeks"]
DAYS = cfg["run"]["action_days_per_week"]
TYPHOON = cfg["events"]["typhoon"]


def yield_factor(name):
    """Per-character productivity x global yield multiplier."""
    return chars[name]["productivity"] * cfg.get("production", {}).get("yield_multiplier", 1.0)


def allowed_actions(name, stamina, coconuts_left, week, day):
    """Return the productive actions this agent may do today."""
    c = chars[name]
    typhoon_today = week == TYPHOON["week"] and day in TYPHOON["days"]
    blocked = TYPHOON["blocked_actions"] if typhoon_today else []
    heavy_ok = stamina >= ST["heavy_work_min"]

    options = ["clam"]  # clams: anyone, any time
    if heavy_ok and stamina >= A["fish"]["min_stamina"] and "fish" not in blocked:
        options.append("fish")
    if (heavy_ok and stamina >= A["coconut"]["min_stamina"]
            and c["age"] <= A["coconut"]["max_age"]
            and coconuts_left > 0 and "coconut" not in blocked):
        options.append("coconut")
    if heavy_ok:
        options.append("forage")
    return options


def expected_yield(name, act):
    """Expected yield of one action, used by the greedy policy."""
    if act == "fish":
        has_gear = A["fish"]["gear_item"] in chars[name]["items"]
        return sum(A["fish"]["yield_with_gear" if has_gear else "yield_without_gear"]) / 2 * yield_factor(name)
    return sum(A[act]["yield"]) / 2 * yield_factor(name)


def choose(name, stamina, coconuts_left, week, day, policy, rng, n_clam_so_far):
    options = allowed_actions(name, stamina, coconuts_left, week, day)
    if policy == "random":
        return rng.choice(options)
    # greedy: clams lose value once the pool is crowded
    def value(act):
        v = expected_yield(name, act)
        if act == "clam" and n_clam_so_far >= A["clam"]["crowd_limit"]:
            v *= A["clam"]["crowd_factor"]
        return v
    return max(options, key=value)


def simulate(rng, policy):
    stamina = {n: ST["initial"] for n in chars}
    output = {n: 0.0 for n in chars}
    coconuts_left = A["coconut"]["total_stock"]

    for week in range(1, WEEKS + 1):
        for day in range(1, DAYS + 1):
            # 1. everyone chooses
            choice = {}
            for n in chars:
                if stamina[n] < REST_BELOW:
                    choice[n] = "rest"
                else:
                    n_clam = sum(1 for a in choice.values() if a == "clam")
                    choice[n] = choose(n, stamina[n], coconuts_left, week, day,
                                       policy, rng, n_clam)

            n_clam = sum(1 for a in choice.values() if a == "clam")
            clam_factor = A["clam"]["crowd_factor"] if n_clam > A["clam"]["crowd_limit"] else 1.0

            # 2. resolve
            for n, act in choice.items():
                if act == "rest":
                    stamina[n] = min(ST["max"], stamina[n] + ST["rest_gain"])
                    continue

                if act == "fish":
                    has_gear = A["fish"]["gear_item"] in chars[n]["items"]
                    lo, hi = A["fish"]["yield_with_gear" if has_gear else "yield_without_gear"]
                    got = rng.randint(lo, hi)
                elif act == "clam":
                    got = rng.randint(*A["clam"]["yield"]) * clam_factor
                elif act == "coconut":
                    got = min(rng.randint(*A["coconut"]["yield"]), coconuts_left)
                    coconuts_left -= got
                elif act == "forage":
                    got = rng.randint(*A["forage"]["yield"])
                    if rng.random() < A["forage"]["injury_prob"]:
                        stamina[n] -= A["forage"]["injury_stamina"]

                output[n] += got * yield_factor(n)
                stamina[n] = max(ST["min"], stamina[n] - A[act].get("stamina_cost", ST["labor_cost"]))
                if act == "fish" and got >= cfg["food"]["protein_bonus"]["min_fish"]:
                    stamina[n] = min(ST["max"], stamina[n] + cfg["food"]["protein_bonus"]["stamina"])  # eats own fish

            # overnight recovery (agents are assumed fed in this capacity check)
            for n in chars:
                stamina[n] = min(ST["max"], stamina[n] + ST.get("overnight_recovery", 0))

    return output, coconuts_left


def run_policy(policy, total_need, runs):
    rng = random.Random(cfg["run"]["seed"])
    ratios, per_agent, coco_left = [], {n: 0.0 for n in chars}, 0.0
    for _ in range(runs):
        out, left = simulate(rng, policy)
        ratios.append(sum(out.values()) / total_need)
        for n in chars:
            per_agent[n] += out[n] / runs
        coco_left += left / runs
    return ratios, per_agent, coco_left


def main():
    runs = cfg["calibration"]["runs"]
    total_days = WEEKS * DAYS
    total_need = sum(c["daily_need"] for c in chars.values()) * total_days
    lo, hi = cfg["calibration"]["target_ratio"]
    print(f"Runs: {runs}, action days: {total_days}, total need: {total_need:.0f} units")
    print(f"Target (greedy): {lo:.2f}-{hi:.2f}")

    for policy in ["random", "greedy"]:
        ratios, per_agent, coco_left = run_policy(policy, total_need, runs)
        avg = sum(ratios) / runs
        print(f"\n=== {policy} policy ===")
        print(f"Output / need: mean {avg:.2f}, min {min(ratios):.2f}, max {max(ratios):.2f}")
        if policy == "greedy":
            verdict = "OK" if lo <= avg <= hi else ("TOO HIGH, lower yields" if avg > hi else "TOO LOW, raise yields")
            print(f"Verdict: {verdict}")
        print(f"Coconuts left at end (of {A['coconut']['total_stock']}): {coco_left:.1f}")
        for n in chars:
            need = chars[n]["daily_need"] * total_days
            print(f"  {n:<7} {per_agent[n]:6.1f} units  (own need {need:.0f})")


if __name__ == "__main__":
    main()
