---
name: convention-database
description: >-
  Builds a DbDo database of a convention, conference or similar event -- any
  organization's -- from its published agenda: every session with its date,
  times and room, every speaker and sponsor, and the programs and products the
  sessions feature, linked so a screen reader user can go from a session to
  who presents it and where, or from a speaker to everything they present.
  Ships an empty Convention.db with the schema and link kinds, and the scripts
  that turn marked sessions into a calendar file, an accessible schedule page
  and contact cards. Use this skill whenever the user wants to organize, plan,
  navigate or share the agenda of a convention, conference, summit, expo,
  workshop series or annual meeting, or asks for an accessible schedule,
  personal itinerary or speaker directory of one.
---

# Convention database

A convention agenda is long, dense and visual: a grid of days, times, rooms and
names that a screen reader reads as one long run of text. As a DbDo database it
becomes four short lists joined by links, so a reader asks the question they
actually have -- what is on now, where is it, who is speaking, what else does
she present -- and hears only the answer.

This skill grew from the 2026 national convention of a large membership
organization of blind people: 242 sessions, 38 rooms, 153 speakers and sponsors
and 90 programs, built into a database DbDo shipped as a template that year. The
data is past; the design and the lessons are not, and they are here for the
next event of any organization.

## What it makes

`templates/Convention.db`, empty and ready, in the Homer way (the homer-db
skill): each table with the standard fields, look, prime and triggers.

- **events** -- one row per agenda entry: `event_date`, `start_time`,
  `end_time`, `title`, `details`, `url`. Dates as `YYYY-MM-DD` and times in
  24-hour `HH:MM`, so a plain text sort is chronological.
- **locations** -- the rooms and spaces: `name`, `level`, `hotel` (or venue).
- **projects** -- the programs, products, services and organizations the
  sessions are about: `name`, `kind`, `descrip`, `url`.
- **contacts** -- people, and organizations as rows with an `enterprise` and no
  last name, so an organization's prime is its own name.
- **maps** -- every relationship, as a row naming a record on each side and the
  kind between them: **presents** (a contact presents at, chairs or leads an
  event; the billed role rides in the map row's notes), **located_at** (an event
  is in a location), **sponsors**, **features** (an event features a project),
  **offers** (a contact provides a project), **affiliated_with** and
  **part_of**.
- **lookups** -- the link kinds and project kinds, each with its meaning, so
  Record Edit offers them as comboboxes. Add the venue's hotels or buildings as
  `locations.hotel` values.

Beside it, copied with the database into the event's own folder:

- **Convention.inix** -- opens on events, each row speaking date, start time and
  title.
- **Marked-Calendar.js** -- the sessions in the current view (usually the marked
  ones) as an iCalendar file to import into any calendar.
- **Marked-Schedule.js** -- the same sessions as an accessible web page, one
  table per day under a heading for the day.
- **Marked-Contacts.js** -- the people in the current view as contact cards.
- **Queries**: ConventionSchedule, DayAtAGlance, Presenter-Events,
  Speaker-Directory, SpeakerSessions, Sponsor-Showcase, Convention-Stats; and
  **scripts**: Daily-Schedule, Topic-Track; and **report.inix** with a daily
  agenda and a session list.

Rename all of it for the event, such as `Summit2027.db` and `Summit2027.inix`,
in a folder of the same name.

## Building one

1. **Get the agenda in text.** The organization's own agenda: a web page, a
   PDF or a Word file, converted with the kit's conversion classes (the
   homer-convert skill). Keep the source file and its address; every record's
   url points back to it or to a page for that session.
2. **Read the events first.** One row per entry with a time. Carry the day
   down from the day heading above it. A time range gives start and end; a
   lone time gives only a start. Turn 12-hour times into 24-hour.
3. **Make the rooms from the events.** Each distinct room named, with its level
   and building when the agenda's own rules give them -- one convention's rule
   was that a room number starting with N is on level N. Link each event to its
   room with **located_at**.
4. **Make people and organizations from the names.** A name billed with a role
   and affiliation -- "Jane Doe, Director, Example Agency" -- is a contact
   presenting the event, with "Director, Example Agency" in the map row's
   notes, and the agency an organization **affiliated_with** her. A sponsor
   line makes an organization that **sponsors** the event. The same person
   spelled two ways is one contact: match on name, not on the whole billing.
5. **Make projects from what sessions are about.** Named programs (academies,
   awards, fairs, camps, scholarship programs), products and services, by
   pattern and by a short list of known names; merge a shorter name into the
   fuller title it abbreviates. A session **features** a project; an
   organization **offers** one.
6. **Fill in the placeholders** in the copied files: `{{FIRST_DAY}}` with the
   event's first date and `{{ORGANIZATION}}` with the host's name.
7. **Check it.** `checkDb` on the database: every table conforms, and every map
   row resolves to exactly one record at each end. Run every query and report
   once on the real data; one that returns nothing is a join to look at.

## Lessons from the first one

- **Verify every link, or leave it out.** A speaker's url is set only when an
  official bio or profile was confirmed for that person; a blank link is fine,
  a wrong one is not.
- **Never invent the agenda's facts.** A room, a time or a role that the agenda
  does not give stays empty.
- **Sessions stand alone.** No sub-events or tracks as structure: a track is a
  word in the title or a project the session features, found with a filter.
- **Links are rows, not columns.** Who presents what, and which room, live in
  maps, so a session with five speakers needs no fifth speaker column, and the
  same query shape answers "everything this speaker does" and "everything in
  this room".
- **Mark, then export.** People plan by marking sessions as they listen; the
  three scripts read only the current view, so a filter on `marked = true`
  turns a reader's choices into a calendar, a page or contact cards.
- **The data dates; the database does not.** After the event, keep the
  database as a record of who presented what, but do not ship it as a
  template: an agenda is current for one week of one year.
