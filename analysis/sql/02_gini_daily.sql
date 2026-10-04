-- 02 Inequality: Gini coefficient of food holdings for every run and day,
-- plus the weekly average and the whole-run average for the same run.
-- Gini = sum over agents of (2i - n - 1) * x_i / (n * sum x), with x sorted from poorest (i = 1) to richest.
-- 0 = everyone holds the same, 1 = one agent holds everything.
WITH ranked AS (
  SELECT run, grp, feedback, replication, t, week, typhoon_day,
         MAX(food_total, 0)                                          AS x,
         ROW_NUMBER() OVER (PARTITION BY run, t ORDER BY food_total) AS i,
         COUNT(*)      OVER (PARTITION BY run, t)                    AS n,
         SUM(MAX(food_total, 0)) OVER (PARTITION BY run, t)          AS total
  FROM daily_states
),
daily AS (
  SELECT run, grp, feedback, replication, t, week, MAX(typhoon_day) AS typhoon_day,
         SUM((2 * i - n - 1) * x) / (MAX(n) * MAX(total)) AS gini
  FROM ranked
  GROUP BY run, t
)
SELECT run, grp, feedback, replication, t, week, typhoon_day,
       ROUND(gini, 3)                                         AS gini,
       ROUND(AVG(gini) OVER (PARTITION BY run, week), 3)      AS gini_week_avg,  -- same value on all 5 days of a week
       ROUND(AVG(gini) OVER (PARTITION BY run), 3)            AS gini_run_avg    -- same value on all days of a run
FROM daily
ORDER BY run, t;

-- One row per week instead of per day:
-- SELECT DISTINCT run, grp, feedback, week, gini_week_avg FROM ( <the query above> ) ORDER BY run, week;
