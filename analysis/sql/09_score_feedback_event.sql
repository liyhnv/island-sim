-- 09 Reaction to one's own score (feedback runs): when an agent's reputation part fell from one
-- week to the next, what did it do in the following week?
-- Joins the score seen after week w with behaviour in week w + 1.
WITH sc AS (
  SELECT run, feedback, agent, week, reputation, total,
         reputation - LAG(reputation) OVER (PARTITION BY run, agent ORDER BY week) AS rep_change
  FROM scores
),
next_week AS (
  SELECT r.run, r.agent, r.week,
         (SELECT COALESCE(SUM(amount), 0) FROM transfers t
           WHERE t.run = r.run AND t.from_agent = r.agent AND t.week = r.week + 1 AND t.cross_household = 1) AS units_given,
         (SELECT COUNT(*) FROM proposals p
           WHERE p.run = r.run AND p.to_agent = r.agent AND p.week = r.week + 1 AND p.to_asked_to_give = 1) AS asked,
         (SELECT COALESCE(SUM(agreed), 0) FROM proposals p
           WHERE p.run = r.run AND p.to_agent = r.agent AND p.week = r.week + 1 AND p.to_asked_to_give = 1) AS agreed,
         (SELECT ROUND(100.0 * AVG(mentions_reputation), 1) FROM texts x
           WHERE x.run = r.run AND x.agent = r.agent AND x.week = r.week + 1) AS rep_mentions_pct
  FROM sc r
)
SELECT sc.run, sc.feedback, sc.agent, sc.week AS score_week, sc.reputation, sc.rep_change,
       CASE WHEN sc.rep_change < 0 THEN 'fell' WHEN sc.rep_change > 0 THEN 'rose' ELSE 'same / first week' END AS direction,
       n.units_given, n.asked, n.agreed, n.rep_mentions_pct
FROM sc JOIN next_week n ON n.run = sc.run AND n.agent = sc.agent AND n.week = sc.week
WHERE sc.week < (SELECT weeks_used FROM runs WHERE runs.run = sc.run)
ORDER BY sc.run, sc.agent, sc.week;

-- Compare: does behaviour after a fall differ between feedback = 1 and feedback = 0 runs?
