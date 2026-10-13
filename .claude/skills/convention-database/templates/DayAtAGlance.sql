-- DayAtAGlance.sql - one convention day, ordered by start time.
-- The event's first day, found from the events themselves. For another day,
-- replace the parenthesized part with that day's date, such as '{{FIRST_DAY}}'.
select e.start_time as Start, e.end_time as Finish, e.title as Event,
       l.name as Location
from events e
left join maps m on m.tbl1 = 'events' and m.prime1 = e.prime
                and m.kind = 'located_at' and m.tbl2 = 'locations'
left join locations l on l.prime = m.prime2
where e.event_date = (select min(event_date) from events)
order by e.start_time, e.title;
