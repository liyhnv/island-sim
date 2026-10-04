-- 08 Season score per agent per week (total, rank and the three parts, each 0-100).
-- source = "logged" (computed by the simulator during the run) or "recomputed" (older runs).
SELECT s.run, s.grp, s.feedback, s.week, s.agent, s.total, s.rank,
       s.food, s.reputation, s.wellbeing, s.shown_to_agent, s.source
FROM scores s
ORDER BY s.run, s.week, s.rank;
