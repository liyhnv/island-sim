"""
Entry point.

  python3 run.py --group A --weeks 1            # start a new run of group A
  python3 run.py --group A --weeks 8 --resume   # continue from the last save
  python3 run.py --group A --weeks 1 --mock     # test without Ollama (random answers)
  python3 run.py --group A --run 2              # repetition 2 of group A (logs/A_r2, seed 43)
  python3 run.py --group A --run 2 --feedback   # same, agents see their own score each week (logs/A_r2_fb)

Logs go to logs/<group>/, saves to saves/<group>/.
Mock runs use logs_mock/ and saves_mock/ so they never mix with real data.
"""

import argparse
import json
import os
import shutil
import sys

import yaml

from engine import Engine
from llm import LLM, MockLLM, OllamaDown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", choices=["A", "B"], required=True)
    ap.add_argument("--weeks", type=int, default=None, help="default: run.weeks in config.yaml")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--feedback", action="store_true",
                    help="agents see their own season score after every weekly review (logs go to <group>_r<N>_fb)")
    ap.add_argument("--run", type=int, default=None,
                    help="repetition number (1, 2, 3...): logs go to logs/<group>_r<N>/, seed = base seed + N - 1 "
                         "(groups A and B of the same repetition share the seed)")
    ap.add_argument("--test", action="store_true",
                    help="quick check: the typhoon comes in week 1; logs go to logs_test/ (never mixed with real data)")
    args = ap.parse_args()

    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    with open("characters.json") as f:
        chars = json.load(f)
    weeks = args.weeks or cfg["run"]["weeks"]

    suffix = "_mock" if args.mock else ""
    if args.test:
        cfg["events"]["typhoon"]["week"] = 1
        # start with roughly the food people actually held when the typhoon hit in an earlier full run
        for name, food in {"Kurt": 2, "Stella": 6, "Lucky": 0, "Alice": 0, "Bob": 4, "Pete": 12}.items():
            chars[name]["food"] = food
        suffix += "_test"
    name = args.group
    if args.run:
        cfg["run"]["seed"] = cfg["run"]["seed"] + args.run - 1
        cfg["llm"]["seed"] = cfg["run"]["seed"]
        name = f"{args.group}_r{args.run}"
        print(f"Repetition {args.run}: group {args.group}, seed {cfg['run']['seed']}")
    if args.feedback:
        cfg["reward"]["feedback"] = True
        name += "_fb"
        print("Score feedback ON: agents see their own season score every week")
    cfg["run"]["weeks"] = weeks
    log_dir = os.path.join(f"logs{suffix}", name)
    save_dir = os.path.join(f"saves{suffix}", name)

    if not args.resume and os.path.exists(os.path.join(save_dir, "latest.json")):
        ans = input(f"A saved run {name} exists. Start over and DELETE it? [y/N] ")
        if ans.strip().lower() != "y":
            print("Stopped. Use --resume to continue the saved run.")
            sys.exit(0)
        shutil.rmtree(log_dir, ignore_errors=True)
        shutil.rmtree(save_dir, ignore_errors=True)

    llm = MockLLM(cfg, seed=cfg["run"]["seed"]) if args.mock else LLM(cfg)
    if not args.mock:
        try:
            llm.check()
        except OllamaDown:
            print("Ollama is not running. Open the Ollama app (llama icon in the menu bar) and try again.")
            sys.exit(1)
    eng = Engine(cfg, chars, args.group, llm, log_dir, save_dir)
    if args.resume:
        eng.load()
        print(f"Resumed at week {eng.st['week']}, day {eng.st['day']}.")
    try:
        eng.run(weeks)
    except OllamaDown:
        print(f"\nSTOPPED: Ollama was unreachable for {cfg['llm'].get('wait_if_down_minutes', 10)} minutes.")
        print(f"Progress is saved at week {eng.st['week']} ({eng.st['stage']}). Open the Ollama app, then run:")
        flags = (" --test" if args.test else "") + (" --mock" if args.mock else "") + (f" --run {args.run}" if args.run else "") + (" --feedback" if args.feedback else "")
        print(f"  python3 run.py --group {args.group} --weeks {weeks}{flags} --resume")
        sys.exit(1)
    print(f"Finished. Logs in {log_dir}/")


if __name__ == "__main__":
    main()
