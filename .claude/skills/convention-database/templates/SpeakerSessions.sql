-- SpeakerSessions.sql - every event a given person presents, chairs,
-- or leads, with their stated role for each. Change the last_name
-- literal to look up someone else.
--
-- This is the canonical "all events related to a contact" query: the
-- IN-subquery through maps keeps the outer SELECT single-table, so
-- the resulting recordset remains editable in DbDo.
select e.event_date as Day, e.start_time as Start, e.title as Event,
       m.notes as Role
from events e
join maps m on m.tbl2 = 'events' and m.prime2 = e.prime
           and m.kind = 'presents' and m.tbl1 = 'contacts'
where m.prime1 in (select c.prime from contacts c where c.last_name = 'Chan')
order by e.event_date, e.start_time;
