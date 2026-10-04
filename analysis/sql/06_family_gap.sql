-- 06 Family lines: average secret "like" rating given to own household vs to other households, per week.
-- gap = within - across. H4 expects the gap to shrink faster in group B.
SELECT run, grp, feedback, week,
       ROUND(AVG(CASE WHEN same_household = 1 THEN "like" END), 1) AS like_within,
       ROUND(AVG(CASE WHEN same_household = 0 THEN "like" END), 1) AS like_across,
       ROUND(AVG(CASE WHEN same_household = 1 THEN "like" END)
           - AVG(CASE WHEN same_household = 0 THEN "like" END), 1) AS gap
FROM ratings
GROUP BY run, week
ORDER BY run, week;
