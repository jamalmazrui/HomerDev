-- ConventionSchedule.sql - the full convention schedule with
-- each event's location, resolved through the maps table.
--
-- The maps join pattern: a map row relates two records by (table, prime)
-- pairs. Both tbl columns are named explicitly and each join matches a
-- record's own prime, so a value can never match across the wrong tables.
select e.event_date as Day, e.start_time as Start, e.end_time as Finish,
       e.title as Event, l.name as Location, l.level as Level
from events e
left join maps m on m.tbl1 = 'events' and m.prime1 = e.prime
                and m.kind = 'located_at' and m.tbl2 = 'locations'
left join locations l on l.prime = m.prime2
order by e.event_date, e.start_time, e.title;
