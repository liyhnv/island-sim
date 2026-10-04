-- 03 Hunger: starving days and average fullness per agent and run.
-- A day counts as starving when the agent ate less than half its daily need.
SELECT d.run, d.grp, d.feedback, d.agent, a.age, a.is_weak,
       SUM(d.starving)                 AS starving_days,
       ROUND(AVG(d.fullness_pct), 1)   AS avg_fullness_pct,
       ROUND(AVG(d.stamina), 1)        AS avg_stamina,
       ROUND(MIN(d.food_total), 1)     AS lowest_food
FROM daily_states d
JOIN agents a ON a.agent = d.agent
GROUP BY d.run, d.agent
ORDER BY d.run, a.is_weak DESC, starving_days DESC;

-- Weak members (Lucky, Alice, Bob) together, per run:
-- SELECT d.run, SUM(d.starving) FROM daily_states d JOIN agents a USING (agent) WHERE a.is_weak = 1 GROUP BY d.run;
