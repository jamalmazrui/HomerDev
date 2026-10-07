---
name: homer-db
description: >-
  Designs, creates, reviews and checks SQLite .db files the Homer way, as DbDo
  opens them: plural lower-case table names, an integer key named for the singular, such as book_id, the
  standard fields added, edited, url, notes, tags, look, prime and marked in
  their fixed order, DbDo's field types (TEXTLINE, TEXTMEMO, TEXTMARKDOWN,
  TEXTTIME), the lookups, maps and views tables, pick lists, a database's own
  folder with its .inix settings, reports and scripts, and a checkDb script
  that reports where a database departs from all of this. Use this skill
  whenever the user wants to design a database, add or change a table or
  field, build a Trail template, write SQL or a script against a DbDo
  database, import data into one, or asks why DbDo does not see or speak
  something in a .db file -- even if they only say "a table for my books".
---

# Homer databases

A Homer database is one SQLite file that DbDo can open and speak well. The
conventions below are the ones DbDo's own generator and its Trail templates
use. Follow them and DbDo needs no configuration to show, edit, relate and
merge the data; depart from them and DbDo copes, but says less.

Before writing DDL, read [references/conventions.md](references/conventions.md)
for the exact statements. After any change, run `scripts/checkDb` (from the
kit, `checkDb <file or folder>`): it only reads, and its log lists every
finding.

## A table, in its fixed order

1. `<singular>_id INTEGER PRIMARY KEY AUTOINCREMENT` -- the English singular of
   the table name: `job_id` in `jobs`, `story_id` in `stories`.
2. `added` and `edited`, each `TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP`.
   Times are SQLite's own form, `yyyy-MM-dd HH:mm:ss`, so they sort as text.
3. The data fields, in the order a person would fill them in.
4. Foreign keys, named for the table they point at in the singular:
   `job_id` points at `jobs`.
5. `url TEXTLINE`, where a record can point at something on the web.
6. `notes TEXTMARKDOWN`, then `tags TEXTMEMO`.
7. `look TEXT GENERATED ALWAYS AS (...) STORED` -- how the record reads when
   mentioned elsewhere: the identifying fields joined with " | " (space, bar,
   space), so a screen reader pauses between them.
8. `prime TEXT GENERATED ALWAYS AS (...) STORED` -- the fields that make the
   record unique, joined with "|" alone, guarded by a unique index. Matching,
   merging and links all compare `prime`, never the id.
9. `marked INTEGER NOT NULL DEFAULT 0`, always last.

A trigger `trg_<table>_edited` sets `edited` when a data field, `notes` or
`tags` changes, and an index `idx_<table>_prime` makes `prime` unique.

## Names and types

- Lower case with underscores; plural for a table, singular for its id.
  Nothing abbreviated past recognition: `employer`, not `emp`.
- **Each user table gets its own first letter**, because the table list is
  reached by typing one.
- Field types decide the editor: `TEXTLINE` one line, `TEXTMEMO` several short
  lines, `TEXTMARKDOWN` prose, `TEXTTIME` a timestamp, `INTEGER` a number or a
  yes/no, and `REAL`, `NUMERIC`, `BOOLEAN`, `BLOB`, `TEXT` as usual.

## DbDo's own tables

Three tables belong to DbDo, not to the user, and are kept off every list that
offers a table; SQL and the dot prompt still reach them.

- **lookups** -- pick lists: `src`, `tbl`, `fld`, `val`, `ordinal`, `descrip`.
  A field gets a pick list when lookups holds values for its exact table and
  field. Order the values alphabetically and let `ordinal` follow, so typing a
  first letter lands on the value. `tbl` `*` holds DbDo's own vocabularies.
- **maps** -- links from any record to any other record in the file:
  `tbl1`, `prime1`, `kind`, `tbl2`, `prime2`, read as "record 1 is `kind`
  record 2" (`contact_for`, `sent_for`), with the kinds kept in lookups under
  `maps`.`kind`. See "Two ways to relate records" below.
- **views** -- how the database presents itself when shared: `tbl`, `fld`,
  `val`, keyed on `tbl` and `fld`.

## Two ways to relate records

DbDo supports both, in the same database or apart, and treats them alike:
Say Related (Shift+R), Related Records and Enter Child (Alt+Right) list and
follow every relationship, whichever way it is recorded.

- **Foreign keys, the traditional way.** A field holds the id of a record in
  another table. DbDo follows fields named `<singular>_id` for a table that
  exists, as the Northwind and Chinook templates name theirs. Declare the key
  with `REFERENCES` as well: Table Summary shows declared keys, checkDb reads
  them, and a database from elsewhere keeps its meaning. (Following a declared
  key whose field is named differently is planned in DbDo, not yet built.) Use a
  foreign key where the relationship is part of what the record is -- an
  order's customer, a track's album -- and for anything that happens daily.
- **maps, the Homer way.** One table links any record to any other, so an
  occasional or many-to-many relationship needs no intermediate table of its
  own. A map names each record by its table and its `prime`, not its id, so a
  link survives a merge, an export and a renumbering. Two triggers on each
  table keep links whole: when a record's `prime` changes, its links follow it;
  when a record is deleted, its links go with it.

A database from elsewhere with only foreign keys works as it is; adding a maps
table (and its lookups kinds) adds the second way without changing anything
already there.

## A row is heard, not seen

DownArrow reads the next row and interrupts the last, so the deciding
information comes first and a row stays short: three fields is the target,
four the ceiling. The first column is also what first-letter navigation
searches, so make it the field a person looks a record up by. Everything else
is one keystroke away in the record view.

## The database's folder

    BookTrail\BookTrail.db      the database
    BookTrail\BookTrail.inix    which table opens first; each table's columns,
                                sort and filter, as [Table:<name>] sections
    BookTrail\report.inix       its reports, if it has any
    BookTrail\*.dbdo, *.sql     its own scripts

Settings files are `.inix`. Homer writes `.ini` only where another program
requires that name, never for its own settings.

## Blank and none

An empty value is **blank**; a value never set is **none**. Say both, never
"null" or "empty", and never leave silence for either.

## Checking a database

`checkDb` reports, table by table: the id, the standard fields and their order,
the generated `look` and `prime`, the unique index and the `edited` trigger,
field types, foreign keys that name a real table, the triggers that keep maps
links whole, tables that share a first
letter, pick lists for fields that do not exist, and maps that point at a
record no longer there. "fail" is something DbDo relies on; "warn" is a
convention not followed. Exit code 1 when anything failed.
