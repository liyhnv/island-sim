-- 07 Typhoon shock as a difference-in-differences.
-- Period "before" = weeks 1-2, "after" = weeks 3-4 (typhoon week and recovery week).
-- For each outcome: change from before to after in B, minus the same change in A.
-- With the same seed, A and B face the same luck, so the difference-in-differences shows how the
-- two incentive groups responded differently to the same shock.
WITH per_period AS (
  SELECT d.replication, d.feedback, d.grp,
         CASE WHEN d.week <= 2 THEN 'before' ELSE 'after' END AS period,
         AVG(d.fullness_pct)                                   AS fullness,
         AVG(CASE WHEN a.is_weak = 1 THEN d.fullness_pct END)  AS fullness_weak,
         SUM(d.starving) * 1.0 / COUNT(DISTINCT d.t)           AS starving_per_day
  FROM daily_states d JOIN agents a ON a.agent = d.agent
  GROUP BY d.replication, d.feedback, d.grp, period
)
SELECT replication, feedback,
       ROUND((MAX(CASE WHEN grp='B' AND period='after'  THEN fullness END) - MAX(CASE WHEN grp='B' AND period='before' THEN fullness END))
           - (MAX(CASE WHEN grp='A' AND period='after'  THEN fullness END) - MAX(CASE WHEN grp='A' AND period='before' THEN fullness END)), 1)
         AS did_fullness_all,
       ROUND((MAX(CASE WHEN grp='B' AND period='after'  THEN fullness_weak END) - MAX(CASE WHEN grp='B' AND period='before' THEN fullness_weak END))
           - (MAX(CASE WHEN grp='A' AND period='after'  THEN fullness_weak END) - MAX(CASE WHEN grp='A' AND period='before' THEN fullness_weak END)), 1)
         AS did_fullness_weak,
       ROUND((MAX(CASE WHEN grp='B' AND period='after'  THEN starving_per_day END) - MAX(CASE WHEN grp='B' AND period='before' THEN starving_per_day END))
           - (MAX(CASE WHEN grp='A' AND period='after'  THEN starving_per_day END) - MAX(CASE WHEN grp='A' AND period='before' THEN starving_per_day END)), 2)
         AS did_starving_per_day
FROM per_period
GROUP BY replication, feedback;

-- To see the four cells behind each number:  SELECT * FROM per_period;  (replace the final SELECT)
