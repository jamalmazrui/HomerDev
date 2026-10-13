-- Speaker-Directory.sql
-- A directory of everyone presenting at the convention: name, the
-- organization and role they are billed under, how many sessions they
-- appear on, and -- where it could be verified -- a link to their official
-- bio or professional profile. Open your convention database, run this with
-- Invoke Script, then Export the result (Control+Shift+X) if you want to
-- keep a copy as a document or spreadsheet.
--
-- This is the payoff of two things the database keeps separate but joins
-- on demand: the maps table records who presents (kind = 'presents'), and
-- the contacts table carries a 'url' for each person it could be confirmed
-- for. A blank link just means no authoritative page was verified for that
-- person -- the row is still complete and useful.
--
-- The join is c.prime = m.prime1: a person's identity is first|middle|last,
-- which is the value every 'presents' map stores on its contacts side.
-- GROUP BY collapses a person's several sessions into one directory line
-- and COUNT(*) reports how many there are.

SELECT
  c.last_name || ', ' || c.first_name AS name,
  c.enterprise                        AS organization,
  c.job                               AS role,
  COUNT(*)                            AS sessions,
  c.url                               AS link
FROM maps m
JOIN contacts c ON c.prime = m.prime1
WHERE m.tbl1 = 'contacts' AND m.kind = 'presents' AND m.tbl2 = 'events'
  AND c.last_name IS NOT NULL AND c.last_name <> ''
GROUP BY c.prime
ORDER BY c.last_name, c.first_name;

-- To see only the busiest presenters, change the ORDER BY line to
--   ORDER BY sessions DESC, name
-- To list only those with a confirmed link, add to the WHERE clause
--   AND c.url IS NOT NULL AND c.url <> ''
