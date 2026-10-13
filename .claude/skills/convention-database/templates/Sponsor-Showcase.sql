-- Sponsor-Showcase.sql
-- Who is backing the convention, and with what? Two questions answered
-- from the maps table using relationship kinds OTHER than 'presents':
-- 'sponsors' (an organization backs an event) and 'offers' (an
-- organization provides a product or service). Open your convention database
-- and run this with Invoke Script; each query's results appear in turn.
--
-- How it works: organizations live in the contacts table as rows with an
-- enterprise but no last name, so an organization's identity -- its prime --
-- is simply the enterprise name, which is exactly the value the maps rows
-- point at. That makes every join the same plain shape, c.prime = m.prime1;
-- only the kind on the WHERE line and the far table change. Swap 'sponsors'
-- for 'presents' and you have the speaker query; the model does not care.

-- 1. Sponsored events: each organization and the events it sponsors.
SELECT
  c.enterprise AS sponsor,
  e.event_date AS date,
  e.title      AS event
FROM maps m
JOIN contacts c ON c.prime = m.prime1
JOIN events   e ON e.prime = m.prime2
WHERE m.tbl1 = 'contacts' AND m.kind = 'sponsors' AND m.tbl2 = 'events'
ORDER BY c.enterprise, e.event_date, e.start_time;

-- 2. Products and services on offer: each organization and what it makes
--    or provides (the projects it offers), with the kind of each.
SELECT
  c.enterprise AS organization,
  p.name       AS offering,
  p.kind       AS kind
FROM maps m
JOIN contacts c ON c.prime = m.prime1
JOIN projects p ON p.prime = m.prime2
WHERE m.tbl1 = 'contacts' AND m.kind = 'offers' AND m.tbl2 = 'projects'
ORDER BY c.enterprise, p.name;

-- Want the reverse -- which organization makes a given product? Read the
-- same 'offers' rows from the project side, or just open the maps table in
-- the grid, filter kind = offers, and arrow through it. A relationship you
-- can query in SQL is the same relationship you can browse as rows.
