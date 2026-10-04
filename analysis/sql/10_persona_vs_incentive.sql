-- 10 Incentive vs persona: per agent, the B - A difference in what it gave and how it answered
-- requests, next to its starting generosity. Pairs runs of the same replication and feedback condition.
WITH per AS (
  SELECT r.run, r.grp, r.feedback, r.replication, a.agent, a.start_generosity,
         (SELECT COALESCE(SUM(amount), 0) FROM transfers t
           WHERE t.run = r.run AND t.from_agent = a.agent AND t.cross_household = 1) AS units_given,
         (SELECT COUNT(*) FROM proposals p WHERE p.run = r.run AND p.to_agent = a.agent AND p.to_asked_to_give = 1) AS asked,
         (SELECT COALESCE(SUM(agreed), 0) FROM proposals p WHERE p.run = r.run AND p.to_agent = a.agent AND p.to_asked_to_give = 1) AS agreed,
         (SELECT ROUND(AVG("like"), 1) FROM ratings g WHERE g.run = r.run AND g.target = a.agent) AS like_received,
         (SELECT ROUND(100.0 * AVG(mentions_reputation), 1) FROM texts x WHERE x.run = r.run AND x.agent = a.agent) AS rep_pct,
         (SELECT ROUND(100.0 * AVG(mentions_self), 1) FROM texts x WHERE x.run = r.run AND x.agent = a.agent) AS self_pct
  FROM runs r CROSS JOIN agents a
)
SELECT b.replication, b.feedback, b.agent, b.start_generosity,
       a.units_given AS given_A, b.units_given AS given_B,
       a.agreed || '/' || a.asked AS agreed_A, b.agreed || '/' || b.asked AS agreed_B,
       ROUND(b.like_received - a.like_received, 1) AS like_received_B_minus_A,
       ROUND(b.rep_pct - a.rep_pct, 1)             AS rep_mentions_B_minus_A,
       ROUND(b.self_pct - a.self_pct, 1)           AS self_mentions_B_minus_A
FROM per b JOIN per a
  ON a.replication = b.replication AND a.feedback = b.feedback AND a.agent = b.agent AND a.grp = 'A' AND b.grp = 'B'
ORDER BY b.replication, b.feedback, b.start_generosity;
