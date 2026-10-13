-- Presenter-Events.sql
-- List every event a chosen presenter appears on, in time order, showing
-- the date, start time, and title.
--
-- How to use: open your convention database, then run this file with Invoke
-- Script. The results appear in a dialog you can read and copy. Change
-- the last name on the WHERE line to the presenter you care about -- for
-- a fuller list try Burke, Riccobono, or O'Connor.
--
-- How it works: presenters are people in the contacts table; the link
-- between a contact and the events they present is stored in the maps
-- table (kind = 'presents'). Each side of a map row holds a record's prime,
-- its readable identity: first|middle|last for a person, date|time|title for
-- an event. So the joins match c.prime and e.prime, never a string rebuilt
-- here, and they keep working if the way a prime is formed ever changes.

SELECT
  e.event_date AS date,
  e.start_time AS starts,
  e.title      AS event
FROM contacts c
JOIN maps m
  ON  m.tbl1 = 'contacts'
  AND m.kind = 'presents'
  AND m.tbl2 = 'events'
  AND m.prime1 = c.prime
JOIN events e
  ON  e.prime = m.prime2
WHERE c.last_name = 'Mallett'
ORDER BY e.event_date, e.start_time;
