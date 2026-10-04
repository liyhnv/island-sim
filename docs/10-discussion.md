# Talk Versus Action

The clearest pattern I saw across development and all eight main runs was not a difference between A and B. It was that agents say much more than they do. This page collects what I observed, why I think it happens, and what I would change in a follow-up. The numbers come from `data/tables/` and [`09-results.md`](09-results.md). The explanations are my interpretation and are not tested here.

## What I saw

- **Agreement without transfer.** Kurt and Alice keep proposing that everyone "pool" their food and share it fairly. Kurt or Alice mention pooling in every main run (2 to 34 times per run), but there is no "pool" action in the game. They rarely name an amount. Alice never gave food to another household, and Kurt's gifts were at most 1.5 units in any run.
- **Promises that are not kept.** Lines like "I can share some of my fish" or "I'll give you some tomorrow" are rarely followed by a gift. Across the A runs, 0 to 4 such lines per run were followed by a gift within a day. B with scores hidden, replication 1, was the same (0 of 14).
- **Saying and giving in the same answer do not match.** At the campfire the model writes the line and the gift amount in one answer. For example, Pete told Kurt "If we fish together again, maybe we can split the catch evenly?" and told Stella "Maybe later, if things get tough", with a gift of 0 in the same answer. Nothing in the model checks that the two parts agree.
- **Conditional generosity.** When Pete did give food (only in group B), he attached conditions: "only if you promise to help me with some work later", "I need to know you'll use it wisely". His behaviour moved toward the incentive while his reasons stayed in character.

## Why I think it happens

1. Chat models are trained to be agreeable. Saying "we should all work together and share fairly" is the safest and most natural thing for an assistant-style model to say. Saying "I'll lend you 3, pay back 4 in 3 days" needs arithmetic and a position, and it carries the risk of being refused. Two agreeable agents can agree for weeks without either one forcing a concrete plan.
2. Talk is free here, but actions are not. Messages and campfire lines cost no food and no stamina, and nobody checks whether they were kept. Moving food costs food. For the model, empty talk is a zero-risk option. People who say things and do not follow through lose trust. In this simulation nothing makes broken promises costly, except for loan defaults.
3. The action menu is narrower than the agents' intentions. Kurt's persona wants everyone to pool food under a fair plan. The game only has gifts, trades and loans. What he most wants to do cannot be done, so it can only be talked about. I saw the same thing in AI Town, where agents had many ideas and very few actions.
4. Personas are written as values, not goals. "You want to convince everyone to share fairly" is an attitude, and the model expresses it faithfully by arguing for it. A goal like "make sure Alice's family does not go hungry this week" would more likely lead to numbers and proposals.
5. Agents cannot see each other's food. Without knowing who is short and by how much, it is hard to make a specific offer. People also speak in general terms when they lack information.
6. Model size may also play a part. The 14B model makes arithmetic slips, repeats the same message across rounds and loses track of what it promised a few days ago. A larger model would likely be more concrete. I did not test this, so I do not know how much of the gap it would close.

## What the results add

- Where giving happened, words and actions matched more often. In the two B runs of replication 2 (scores hidden and shown), where Pete gave the most, about half of the promise-like lines were followed by a gift (10 of 20 and 10 of 23). In the other six runs the rate stayed near zero. This follows the seed more than the feedback condition, so I read it as "once agents start giving, they mostly do what they say", not as an effect of seeing the score.
- The incentive changed behaviour more than language. Reputation-type words in plans were not consistently more frequent in B, but Pete's giving was. This is the opposite of what I expected after the first replication, where B mostly changed how agents talked.
- Conflicting demands were split across channels. Before feedback, a persona under the reputation rule could satisfy both sides at once. It could keep its food (persona) and speak warmly (incentive). Seeing a low score may be what made that split harder to keep up. With two replications, this is a guess, not a result.

## What I would change next

I have ordered these from the lightest change to the heaviest.

1. **Decide the action before writing the words.** At the campfire, ask for the gift amount first and the spoken line second. If the amount is already 0, the model is less likely to write "I'll share some with you". This only changes the order of the output fields.
2. **Remind agents of what they said.** Add one line to the prompt such as "Yesterday you told Alice you would share some fish if she was still struggling. She is still starving." This only fills in memory. The decision stays with the agent.
3. **Make promises a formal action.** The simulator would record a pledge (to whom, how much, by which day) like a loan, and if it is not kept everyone is told, as with loan defaults today. Then an empty promise has a reputation cost, which combines naturally with score feedback.

Which side would win once talk is constrained, persona or incentive? I cannot say in advance, which is why it is worth testing. My guess:

- **Consistency without score feedback:** probably the persona. Changing words is cheaper than changing actions, so agents would likely make their words colder ("I won't lend or give") rather than start giving. Words and actions would match, and both would follow the persona.
- **Consistency with score feedback:** colder words would cost reputation, and the agent would see its score fall. It would then have to accept a low score or start giving. Only in this case does the incentive get a real chance to reach behaviour.
