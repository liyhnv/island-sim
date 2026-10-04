-- 11 Reading the reasons: passages flagged by the keyword proxies, for manual coding.
-- Change the agent / run / flag to pull a sample; read them and record your own code
-- (reputation, own food security, family, fairness, reciprocity, persona) in a spreadsheet.
SELECT run, week, day, phase, agent, to_agent, mentions_reputation, mentions_self, text
FROM texts
WHERE agent = 'Pete'
  AND (mentions_reputation = 1 OR mentions_self = 1)
ORDER BY run, week, day;

-- How good are the keyword flags? Draw a random sample of 30 and code them by hand:
-- SELECT run, agent, phase, text, mentions_reputation, mentions_self FROM texts ORDER BY RANDOM() LIMIT 30;
