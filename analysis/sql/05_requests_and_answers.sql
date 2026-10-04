-- 05 Requests: how often each agent was asked to give (a loan where it is the lender, a trade,
-- or joint fishing) and how often it agreed. "agreed" includes deals accepted but not carried out
-- (status "failed": e.g. the food was gone).
SELECT run, grp, feedback, to_agent AS asked_agent, type,
       COUNT(*)                          AS times_asked,
       SUM(agreed)                       AS times_agreed,
       ROUND(100.0 * SUM(agreed) / COUNT(*), 0) AS agreed_pct
FROM proposals
WHERE to_asked_to_give = 1
GROUP BY run, to_agent, type
ORDER BY run, times_asked DESC;
