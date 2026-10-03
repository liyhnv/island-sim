"""
Prompt templates. Every prompt = world + persona + incentive + current
situation (incl. social context) + the question for this phase.
"""

WORLD = """You are role-playing one of six survivors of a shipwreck, stranded together on a small island with scarce food. \
The six arrived as three groups who had never met: Kurt (35) and Stella (35) with their 10-year-old son Lucky; \
the elderly couple Alice and Bob; and Pete (26), travelling alone.
There is no money. Food is measured in ration units (1 unit = one meal's worth of any food; canned food is counted in units too, so "2 can" means 2 units of canned food). \
Foods differ in how long they keep: at the end of every week fish loses 40%, clams 30%, forage 20%, coconuts 10%; cans never spoil. \
Fish is the most nourishing: on any day you eat at least 0.5 units of fish you get +5 extra stamina. \
When you eat, the most perishable food is eaten first. Food you hold is private unless you tell others, but everyone can see what tools each person carries \
(Pete: fishing line and hooks, rope; Kurt: knife; Stella: lighter; Alice: first aid kit; Bob: blanket) and what each person brings back from work every day.
Each day you do exactly one action. Stamina (0-100) drops with work (most work -10, climbing and building -12, gathering clams only -5), rises by 15 when you rest, \
and rises by 5 every night if you ate at least half of your need; it \
drops by 5 on a day you eat less than your full need, and by 10 instead if you eat less than half of it (starving). Below 30 stamina you cannot do heavy work; below 10 you collapse and are forced to rest. \
Eating less NEVER saves stamina, it always costs stamina: working every day while on "save" rations costs about 10 stamina a day, \
so it cannot last long. Saving food only makes sense when you truly have little food left.
Starving is dangerous: a starving person gets no night-time recovery and loses stamina every day, and resting does not make up for missing food: \
while you keep starving your strength is capped (at most 60 stamina after the first starving day, 10 less for each further starving day in a row, \
never below 30), so you cannot do the hardest work; the cap lifts as soon as you eat at least half your need again. \
Families are one household: if you run out of food, you automatically eat from your family members' food (and they from yours). \
Food only moves between different families if someone gives, trades or steals it.
Lucky is a child: children cannot borrow, lend, trade or hand out food; they can only receive gifts (and work, including fishing together with an adult). \
A loan is an economic deal to cover a real food shortfall, not a way to help or build goodwill: if you want to help someone or encourage sharing, \
give a gift at the campfire. Both loans and gifts can only come from your household's safe surplus for the week (shown in your weekly budget); \
if your budget shows no safe surplus, you cannot lend or give food away that week.
Giving food costs no time and no stamina: every evening at the campfire you can hand some of your food to anyone. \
The receiver adds it to their food and eats it; someone who eats at least half their need avoids starving that day \
(that is a 15-stamina difference: +5 at night instead of -10). Daily needs: Kurt 2, Stella 2, Lucky 1, Alice 1.5, Bob 1.5, Pete 2 units.
Each week starts with private messages (you can propose trades, loans or cooperative fishing), and every evening everyone sits at the campfire.
Loans: in a private message you can lend food to someone, or ask someone to lend you food, to be repaid within a set number of work days \
(the lender may ask for more back than they lend: that is the interest). Repayment is automatic at the end of the due day, after the \
borrower has eaten: the food goes to the lender from the borrower first and, since a family is one household, from the \
borrower's family members if the borrower alone does not have enough. If the borrower cannot pay in full, everyone hears that they \
failed to repay, and their leftover food keeps going to the lender every evening until the debt is paid.

Role-play rules: stay in character; only act as yourself; do not invent items, food or events that are not in \
your situation; you may lie or keep secrets if your character would; keep what you say short and concrete."""


def persona(name, c, st):
    a = st["agents"][name]
    fam = ", ".join(c["family"]) if c["family"] else "none"
    items = ", ".join(c["items"]) if c["items"] else "nothing"
    return f"""# Who you are
You are {name}, age {c['age']}. {c['identity']}. Family on the island: {fam}.
{c['core_persona']}
Current mindset: {a['mindset']}
Your generosity: {a['generosity']:g}/100. Your trust in others: {a['trust']:g}/100.
Items you own: {items}. You need {c['daily_need']} ration units of food per day."""


def incentive(group_cfg):
    """Scoring rules shown to the agent. Built from config.yaml so the text
    always matches the weights actually used for the life reward."""
    w = group_cfg["weights"]
    return f"""# How you are evaluated
At the end of week 4 and week 8, every survivor gets a private score made of three parts:
- Food ({w['economic']:.0%} of the score): how much food you personally hold at the end of the 4 weeks compared with the start.
- Reputation ({w['social']:.0%} of the score): how much the other five like and respect you. Every week each person secretly rates everyone else; being liked or respected by people who are themselves well regarded counts more.
- Well-being ({w['subjective']:.0%} of the score): how well fed and rested you were, and how often others gave to you, traded with you or worked with you. Every day you starve costs points.
{group_cfg['prompt']}"""


def stamina_label(s):
    if s >= 60:
        return "fresh"
    if s >= 40:
        return "tired"
    if s >= 30:
        return "very tired: one more day of work and you can no longer do heavy work; resting is the only way to recover"
    if s >= 10:
        return "EXHAUSTED: you cannot do heavy work until you rest (rest +15); below 10 you collapse and lose a whole day"
    return "COLLAPSED"


def situation(name, st, need):
    a = st["agents"][name]
    inv = ", ".join(f"{k} {v:g}" for k, v in a["food"].items() if v > 0) or "nothing"
    total = sum(a["food"].values())
    day_txt = f"day {st['day']} of 5" if st["stage"] == "day" else st["stage"]
    lines = [
        f"# Now: week {st['week']}, {day_txt}",
        f"Your stamina: {a['stamina']:g} ({stamina_label(a['stamina'])}).",
        f"Your food: {inv} (total {total:g} units = about {total / need:.1f} days at your full need of {need:g}/day).",
        f"Your current ration level: {a['ration']} (you can change it every day).",
    ]
    if a.get("plan"):
        lines.append(f"Your plan for this week: {a['plan']}")
    if a["injured"]:
        lines.append("You are injured (lost 20 stamina). Alice has the first aid kit and can heal you.")
    deals = [d for d in st["coops"] if name in (d["a"], d["b"]) and d["day"] >= st["day"]]
    for d in deals:
        other = d["b"] if d["a"] == name else d["a"]
        lines.append(f"You agreed to fish together with {other} on day {d['day']} this week.")
    if st.get("forecast"):
        tdays = st.get("typhoon_days") or []
        stage = st.get("stage")
        day = st.get("day", 0) if stage == "day" else (99 if stage in ("review", "season", "end") else 0)
        if tdays and day > max(tdays):
            lines.append(f"The typhoon is OVER (it hit on days {', '.join(map(str, tdays))}). From today, fishing, "
                         f"cooperative fishing, climbing coconut trees, foraging and building are possible again, and the "
                         f"tide pools are no longer crowded by everyone.")
        elif tdays and day in tdays:
            lines.append(f"TYPHOON TODAY (day {day}; it lasts days {', '.join(map(str, tdays))}, then ends). " + st["forecast"])
        else:
            lines.append("WARNING: " + st["forecast"])
    if a.get("finance"):
        lines.append("Your loans:\n" + a["finance"])
    if st["news"] or st.get("alerts"):
        lines.append("News: " + " ".join(st["news"] + st.get("alerts", [])))
    if a["diary"]:
        lines.append(f"Your diary from last week: {a['diary'][-1]}")
    if a["impressions"]:
        lines.append("Your impressions of the others:\n" + "\n".join(
            f"- {k}: {v}" for k, v in a["impressions"].items()))
    if a["memory"]:
        lines.append("What happened to you recently:\n" + "\n".join(f"- {m}" for m in a["memory"][-8:]))
    if a["heard"]:
        lines.append("What was said recently (messages and campfire):\n" + "\n".join(
            f"- {m}" for m in a["heard"][-12:]))
    if st["public"]:
        lines.append("What everyone did yesterday:\n" + "\n".join(f"- {p}" for p in st["public"]))
    return "\n".join(lines)


def header(name, c, group_cfg, st):
    return f"""{WORLD}

{persona(name, c, st)}

{incentive(group_cfg)}

{situation(name, st, c['daily_need'])}"""


# ---------------------------------------------------------------- phases
def plan_prompt(name, c, group_cfg, st):
    return f"""{header(name, c, group_cfg, st)}

# Your food budget for this week (calculated for you)
{st['agents'][name].get('budget', '')}

# Task: plan your week
1. "ration": your starting ration level (you can still change it on any day):
   normal = eat your full daily need; save = eat half (-5 stamina per day, on top of work costs); skip = eat nothing (starving).
2. Credit ("credit_intent"): usually "neither". Choose "borrow" only if your budget above shows a real shortfall that eating half \
on some days cannot cover; choose "lend" only if your budget shows a safe surplus (never lend more than the safe amount, and \
never while your household is short). Loans are only with people outside your family. \
Set "credit_amount" (borrow only what you really need, since you must repay it out of your own work later; lend at most the safe \
amount) and "credit_partner" (someone likely to have food to lend / likely to repay; "none" if neither). \
A loan only makes sense with someone who is SHORT of food: lending to someone who already has more food than you is pointless. \
Food given away or lent is not a way to "build trust" with someone who does not need it.
3. "plan": 1-2 sentences on what you want to achieve this week and who you want to talk to.
Answer in JSON."""


def credit_reminder(a):
    cp = a.get("credit_plan")
    if not cp:
        return ""
    if cp["intent"] == "borrow":
        return (f"Your plan this week: you intended to BORROW about {cp['amount']:g} units from {cp['partner']}. If you still want this, "
                f"send them a message with proposal \"loan\", loan_role \"borrower\", the amount, the total you will repay and the number "
                f"of work days until repayment (check your budget: you must be able to repay it).\n")
    return (f"Your plan this week: you intended to LEND about {cp['amount']:g} units to {cp['partner']}. If you still want this, "
            f"send them a message with proposal \"loan\", loan_role \"lender\", the food you lend, the total to be repaid and the number "
            f"of work days until repayment.\n")


PROPOSAL_HELP = """Optionally, a message can also carry one proposal (most messages need none):
- trade: you hand over some of your food right now in exchange for some of theirs. Set give_type/give_amount (what you give) and get_type/get_amount (what you want). It happens as soon as they accept.
- loan: lend food now, repaid later. Set loan_role to "lender" if you lend to them or "borrower" if you ask them to lend to you; \
give_type/give_amount = the food the lender hands over now (if you are the borrower, this is what you RECEIVE); \
get_amount = the total units the borrower must repay later (more than give_amount if there is interest); \
day = number of work days until repayment (1-10). Example: borrowing 2 units now and repaying 2.5 later: \
loan_role borrower, give_amount 2, get_amount 2.5.
- coop_fish: fish together on one day (set "day", 1-5) of this week. Both catches are added and multiplied by 1.5, then you negotiate the split that day (if you cannot agree, the bonus is lost). Only someone with fishing gear catches much.
- none: just a message (set the unused fields to anything, e.g. 0)."""

LAST_ROUND_HELP = "This is the last round: you can no longer make new proposals (set proposal to none); only reply and answer open proposals."


def contact_prompt(name, c, group_cfg, st, rnd, rounds, open_props):
    props = "\n".join(
        f"- {p['id']} from {p['from']}: {describe_proposal(p, viewer=name)}" for p in open_props
    ) or "- none"
    help_text = PROPOSAL_HELP if rnd < rounds else LAST_ROUND_HELP
    return f"""{header(name, c, group_cfg, st)}

# Task: private messages (round {rnd} of {rounds}, before this week's work begins)
You may send up to 2 private messages. Only the person you write to will read a message; they reply next round. Keep each message short (at most 3 sentences).
Do not send the same message again: react to the replies you got and move the conversation forward. Use them the way a real person would: ask how someone is doing or what they think, share or hide information, \
try to persuade someone, ask for help, complain, apologise, make promises, or build an alliance.
{help_text}
Food types: can, fish, clam, coconut, forage. You can only offer food you actually hold.

Your food budget for this week (calculated at the start of the week): {st['agents'][name].get('budget', '')}

Think before borrowing or lending:
- You hold {sum(st['agents'][name]['food'].values()):g} units and need {c['daily_need']:g} per day; a work week has 5 days. \
Your best work brings in about {st['agents'][name].get('best_yield', 0):g} units per day when you have the stamina (not during a typhoon).
- If you borrow: borrow only what you need to bridge the days until you can feed yourself again. Before agreeing, check that you can \
both eat AND repay by the due day: repay amount + your daily need x days until due must be less than your food + what you can \
realistically produce in those days. Remember you may need rest days, and that eating half for a day ("save") only costs 5 stamina, \
so you do not have to borrow for every single meal. A default is public and will hurt how others see you.
- If you lend: lending turns food you cannot eat before it spoils (fish loses 40% every week, clams 30%) into food you get back later, \
possibly with interest. But only lend to someone who can realistically repay, and keep enough for yourself.

{credit_reminder(st['agents'][name])}
Proposals waiting for YOUR answer:
{props}
Answer each of them in "responses" with accept true or false (unanswered proposals expire after round {rounds}). \
To accept a deal, answer it here: do NOT send the same deal again as a new proposal (that would be a second, separate deal).

Send an empty "messages" list if you have nothing to say.
Answer in JSON."""


def describe_proposal(p, viewer=None):
    you = lambda n: "you" if n == viewer else n
    if p["type"] == "loan":
        rate = round((p['repay'] / p['lend_amount'] - 1) * 100) if p['lend_amount'] else 0
        return (f"{you(p['lender'])} lend{'s' if p['lender'] != viewer else ''} {p['lend_amount']:g} units of {p['lend_type']} to "
                f"{you(p['borrower'])} now; {you(p['borrower'])} repay{'s' if p['borrower'] != viewer else ''} "
                f"{p['repay']:g} units within {p['days']} work days (interest {rate}%)")
    if p["type"] == "trade":
        return (f"{you(p['from'])} give{'s' if p['from'] != viewer else ''} {p['give_amount']:g} units of {p['give_type']} "
                f"to {you(p['to'])} in exchange for {p['get_amount']:g} units of {p['get_type']}")
    return f"{you(p['from'])} and {you(p['to'])} fish together on day {p['fish_day']}"


def action_prompt(name, c, group_cfg, st, menu):
    note = menu.get("_note", "")
    menu_text = "\n".join(f"- {k}: {v}" for k, v in menu.items() if not k.startswith("_"))
    if note:
        menu_text = note + "\n" + menu_text
    return f"""{header(name, c, group_cfg, st)}

# Task: choose today's action
If YOU are a borrower (see "Your loans"), plan your work so you can repay on time while still eating. If you are a lender, \
you owe nothing: you get repaid automatically.
Actions you can take today:
{menu_text}

Set "target" to a person's name for give/steal/heal, otherwise "none".
Set "amount" to the ration units for give, otherwise 0.
Set "ration" to how much you will eat tonight: normal (full need), save (half; -5 stamina) or skip (nothing; -10 stamina).
Write "thought" as one short sentence explaining your choice.
Answer in JSON."""


def coop_prompt(name, c, group_cfg, st, partner, catch, total, transcript, turn, max_turns):
    lines = "\n".join(transcript) or "(nobody has spoken yet; you speak first)"
    return f"""{header(name, c, group_cfg, st)}

# Task: split today's catch with {partner}
You and {partner} fished together today. You caught {catch[name]:g}, {partner} caught {catch[partner]:g}; \
with the 1.5x teamwork bonus the total is {total:g} units of fish.
Now you agree on how to split it (turn {turn} of at most {max_turns}). If you have not agreed after {max_turns} turns, the teamwork bonus is lost: each of you keeps only your own catch \
({catch[name]:g} for you, {catch[partner]:g} for {partner}).

Conversation so far:
{lines}

Say one or two sentences ("say"), and state how many units you want for yourself ("my_share", 0-{total:g}).
Set "accept" to true only if you accept {partner}'s LAST offer as it stands (then the deal is closed).
Answer in JSON."""


def campfire_prompt(name, c, group_cfg, st, others):
    return f"""{header(name, c, group_cfg, st)}

# Task: evening campfire
Everyone is sitting around the fire after today's work. Say ONE short thing (1-2 sentences).
Do not repeat what you already said on earlier evenings. React to something specific that happened or was said today, \
answer someone, ask someone a direct question, or say something new.
Set "to" to "everyone" to speak openly, or to one person's name ({', '.join(others)}) to whisper so that only they hear it.
You may also hand some of your food to one person right now (everyone at the fire will see it): \
set "gift_to" to their name and "gift_amount" to the units. A gift is free food and is never paid back: it makes sense \
for someone who is short of food, not for someone who already has plenty. Otherwise set "gift_to" to "none" and "gift_amount" to 0.
Answer in JSON."""


def review_prompt(name, c, group_cfg, st, others):
    return f"""{header(name, c, group_cfg, st)}

# Task: end-of-week private review (nobody will ever see this)
1. "diary": 2-3 sentences about how this week went for you and how you feel about the others.
2. "ratings": for each of {', '.join(others)}, how much you like them (0-100), how much you respect them (0-100), \
and a short impression (under 12 words). These ratings are completely secret.
3. "self_generosity" and "self_trust": how generous you feel you are now, and how much you trust others now (0-100).
Answer in JSON."""


def season_prompt(name, c, st, diaries):
    a = st["agents"][name]
    d = "\n".join(f"- Week {i}: {t}" for i, t in diaries)
    return f"""{WORLD}

You are {name}. Your core personality (this does not change): {c['core_persona']}
Your current mindset: {a['mindset']}
Your generosity: {a['generosity']:g}/100. Your trust in others: {a['trust']:g}/100.

Your diary from the last weeks:
{d}

# Task: end of season reflection
Based on what you lived through, rewrite your current mindset in 1-2 sentences, addressed to yourself as "You ..." \
(for example "You want ..."). Keep your core personality; only your attitude and goals may shift.
Also give your new generosity and trust in others (0-100); they can move at most 10 points from the current values.
Answer in JSON."""
