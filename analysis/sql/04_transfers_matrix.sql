-- 04 Who gives to whom: total food moved between agents (gifts, loans, trades) per run.
-- Long format; in Tableau put from_agent on rows, to_agent on columns, units as colour.
SELECT run, grp, feedback, from_agent, to_agent, kind,
       COUNT(*)              AS times,
       ROUND(SUM(amount), 1) AS units
FROM transfers
WHERE cross_household = 1
GROUP BY run, from_agent, to_agent, kind
ORDER BY run, units DESC;
