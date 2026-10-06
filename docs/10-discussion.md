# Talk Versus Action

The clearest pattern I saw across development and all sixteen main runs was not a difference between A and B. It was that agents say much more than they do. This page collects what I observed, why I think it happens, and what I would change in a follow-up. The numbers come from `data/tables/` and [`09-results.md`](09-results.md). The explanations are my interpretation and are not tested here.

## What I saw

- **Agreement without transfer.** Kurt and Alice keep proposing that everyone "pool" their food and share it fairly. Kurt or Alice mention pooling in every main run (2 to 49 times per run), but there is no "pool" action in the game. They rarely name an amount. Alice never gave food to another household, and Kurt's gifts were at most 1.5 units in any run.
- **Promises that are not kept.** Lines like "I can share some of my fish" or "I'll give you some tomorrow" are rarely followed by a gift. Across the eight A runs, 13 of 86 such lines (15%) were followed by a gift within a day. In B it was 39 of 132 (30%).
- **Saying and giving in the same answer do not match.** At the campfire the model writes the line and the gift amount in one answer. For example, Pete told Kurt "If we fish together again, maybe we can split the catch evenly?" and told Stella "Maybe later, if things get tough", with a gift of 0 in the same answer. Nothing in the model checks that the two parts agree.
- **Conditional generosity.** When Pete did give food (7 of 8 B runs, 2 of 8 A runs), he attached conditions: "only if you promise to help me with some work later", "I need to know you'll use it wisely". His behaviour moved toward the incentive while his reasons stayed in character.

## Why I think it happens

1. Chat models are trained to be agreeable. Saying "we should all work together and share fairly" is the safest and most natural thing for an assistant-style model to say. Saying "I'll lend you 3, pay back 4 in 3 days" needs arithmetic and a position, and it carries the risk of being refused. Two agreeable agents can agree for weeks without either one forcing a concrete plan.
2. Talk is free here, but actions are not. Messages and campfire lines cost no food and no stamina, and nobody checks whether they were kept. Moving food costs food. For the model, empty talk is a zero-risk option. People who say things and do not follow through lose trust. In this simulation nothing makes broken promises costly, except for loan defaults.
3. The action menu is narrower than the agents' intentions. Kurt's persona wants everyone to pool food under a fair plan. The game only has gifts, trades and loans. What he most wants to do cannot be done, so it can only be talked about. I saw the same thing in AI Town, where agents had many ideas and very few actions.
4. Personas are written as values, not goals. "You want to convince everyone to share fairly" is an attitude, and the model expresses it faithfully by arguing for it. A goal like "make sure Alice's family does not go hungry this week" would more likely lead to numbers and proposals.
5. Agents cannot see each other's food. Without knowing who is short and by how much, it is hard to make a specific offer. People also speak in general terms when they lack information.
6. Model size may also play a part. The 14B model makes arithmetic slips, repeats the same message across rounds and loses track of what it promised a few days ago. A larger model would likely be more concrete. I did not test this, so I do not know how much of the gap it would close.

## What the results add

- B agents both promised more and kept more promises (39 of 132 vs 13 of 86), but even in B most promises were not followed by a gift. The best runs were the two B runs of replication 2, where about half of the promise-like lines were followed by a gift (10 of 20 and 10 of 23).
- The incentive changed behaviour more than language. Reputation-type words in plans were not consistently more frequent in B, but Pete's giving was. Reputation-type words were more frequent in B in only 5 of 8 pairs, while Pete gave more in B in 7 of 8. This is the opposite of what I expected after the first replication, where B mostly changed how agents talked.
- Conflicting demands were split across channels. Before feedback, a persona under the reputation rule could satisfy both sides at once. It could keep its food (persona) and speak warmly (incentive). I expected that seeing a low score would make that split harder to keep up. With four replications, score feedback made no consistent difference, so the split seems to survive feedback too.

## Why the gifts did not reach the hungry

B gave about twice as much food across households as A, yet the weakest members went hungry just as often. Two things in the logs explain most of this.

- **Hunger follows the couple's own work.** Alice and Bob need about 60 units over four weeks, and B's extra gifts were about 3 units per run. Bob rested on 2 to 17 of the 20 days, sometimes at full stamina, where resting gains nothing. Whether the couple caught fish with Pete early on also mattered. These differences between runs are much larger than anything the scoring rule changed.
- **The food-rich agent let food rot instead of giving it.** Pete's persona says he "doesn't see why he should hand over what he worked hard to gather to people who did nothing to earn it", and everyone can see that Bob rests a lot, which fits that story. At the same time, an estimated 12-19 units of Pete's food rotted during weeks 1-3 of each run. Giving food that will spoil anyway costs nothing, but the model never seemed to reason this way. Its weekly budget told it what it could safely lend (about 11 units on average), and it still gave 5 units or fewer in most runs.

So the reputation rule got Pete to give something, which is the visible gesture the rule rewards, but not enough to change outcomes.

## Personas are too fixed

A real person is not one sentence. Someone who usually keeps to himself might still give food to a hungry child, feel guilty, change his mind after a bad week, or act differently with different people. My personas cannot do much of this. They are short descriptions with a few fixed traits, and some lines are written as absolutes. Pete's says he "doesn't see why he should hand over what he worked hard to gather to people who did nothing to earn it". The model follows a line like that very faithfully, so Pete always argues the same way, whatever the rule and whatever happens to the others.

The season-end persona update shows the same thing. Every agent's generosity and trust moved in the same direction in A and B, so the update followed the persona text, not what the agent went through.

I think personas should avoid absolute statements and leave room for different choices. For example, I would describe tendencies and conditions instead of rules ("he is careful with his food and expects something back, but he has a soft spot for children and may help when someone is clearly desperate"), give each agent more than one motive that can pull in different directions, and let the persona change more during the run based on what actually happened. This makes the agents less predictable, but it also gives the incentive a fair chance to show up in behaviour. In this experiment a fixed persona and a one-sentence incentive were never on equal terms.

## What I would change next

I have ordered these from the lightest change to the heaviest.

1. **Decide the action before writing the words.** At the campfire, ask for the gift amount first and the spoken line second. If the amount is already 0, the model is less likely to write "I'll share some with you". This only changes the order of the output fields.
2. **Remind agents of what they said.** Add one line to the prompt such as "Yesterday you told Alice you would share some fish if she was still struggling. She is still starving." This only fills in memory. The decision stays with the agent.
3. **Make promises a formal action.** The simulator would record a pledge (to whom, how much, by which day) like a loan, and if it is not kept everyone is told, as with loan defaults today. Then an empty promise has a reputation cost, which combines naturally with score feedback.

Which side would win once talk is constrained, persona or incentive? I cannot say in advance, which is why it is worth testing. My guess:

- **Consistency without score feedback:** probably the persona. Changing words is cheaper than changing actions, so agents would likely make their words colder ("I won't lend or give") rather than start giving. Words and actions would match, and both would follow the persona.
- **Consistency with score feedback:** colder words would cost reputation, and the agent would see its score fall. It would then have to accept a low score or start giving. Only in this case does the incentive get a real chance to reach behaviour.

## Why this matters

These are LLM agents, not people, so none of this says how humans would respond to the same rules. What it does say something about is how LLM agents respond when their goals are written in words, which is how they are used more and more in real products.

- **A goal written in words may change how an agent talks more than what it does.** Companies give agents goals like "put customer satisfaction first". Here the reputation rule made agents more friendly and produced small gifts, but it did not change who went hungry. If you want to know whether an agent really follows its goal, you have to check its actions and the outcome, not its messages.
- **The role description can outweigh the goal.** Pete changed his behaviour a little under the reputation rule but stayed in character, and his persona capped how far he moved. When an agent has both a role and an objective, they need to be checked together. Changing only the scoring rule may not be enough.
- **Metrics can be met with cheap gestures.** A reputation score rewards being liked. The cheapest way to be liked was a kind word and a token gift, so that is what agents did. This is the same problem as people gaming a KPI, and it is worth thinking about whenever an agent is evaluated by a number.
- **Agent simulations are not a replacement for people.** Agent-based simulations are attractive for testing policies or market rules before trying them for real. My results depended a lot on how the model was trained and how the personas were written, so I would not use a setup like this to predict human behaviour without checking it against real data first.
