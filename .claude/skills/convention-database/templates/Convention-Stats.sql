-- Convention-Stats.sql
-- A few "who and what is most popular" questions about the
-- convention, answered by counting rows in the maps table. Open
-- your convention database and run this with Invoke Script; each query's
-- results appear in turn, ranked from most to least.
--
-- Every join here has the same shape: a map row names a table and a record's
-- prime on each side (tbl1 and prime1, tbl2 and prime2), so each join matches
-- the record's own prime and names both tables, and a value can never match a
-- record in the wrong table.

-- 1. Most popular speakers, by number of presentations.
SELECT
  trim(coalesce(c.first_name, '') || ' ' || coalesce(c.last_name, '')) AS speaker,
  COUNT(*)                                                               AS presentations
FROM maps m
JOIN contacts c ON c.prime = m.prime1
WHERE m.tbl1 = 'contacts' AND m.kind = 'presents' AND m.tbl2 = 'events'
GROUP BY c.prime
ORDER BY presentations DESC, speaker
LIMIT 10;

-- 2. Most popular locations, by number of events held there.
SELECT
  l.name   AS room,
  l.hotel  AS hotel,
  COUNT(*) AS events
FROM maps m
JOIN locations l ON l.prime = m.prime2
WHERE m.tbl1 = 'events' AND m.kind = 'located_at' AND m.tbl2 = 'locations'
GROUP BY l.prime
ORDER BY events DESC, room
LIMIT 10;

-- 3. Busiest days, by number of events.
SELECT
  event_date AS date,
  COUNT(*)   AS events
FROM events
GROUP BY event_date
ORDER BY events DESC;

-- Single-table questions need no SQL. From the events table you can type,
-- at the dot prompt:
--   filter event_date = '{{FIRST_DAY}}'    (the quotes here are ADO's filter
--                                         grammar for a text value, passed
--                                         through as written -- DbDo adds
--                                         no quoting of its own)
--   yield                               (how many events that day)
--   longest title                       (the longest session title)
--   reset-filter
--
-- Where DbDo's "type it verbatim" rule shows: value commands like
--   find {{ORGANIZATION}}
--   jump Amateur Radio
-- take the whole tail literally -- no surrounding quotes, no escaping.
