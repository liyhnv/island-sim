-- 01 Overview: which runs are in the database and how many days / agents each has.
-- Run this first to check that the export worked.
SELECT r.run, r.grp, r.incentive, r.feedback, r.replication, r.weeks_used,
       COUNT(DISTINCT d.t)     AS days,
       COUNT(DISTINCT d.agent) AS agents
FROM runs r
JOIN daily_states d ON d.run = r.run
GROUP BY r.run
ORDER BY r.replication, r.feedback, r.grp;
