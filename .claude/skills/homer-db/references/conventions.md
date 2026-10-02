# Homer database conventions in detail

## Contents

- A user table, as DbDo makes it
- lookups, maps and views
- Seeded vocabularies
- Where the shipped databases differ (2 October 2026)

## A user table, as DbDo makes it

For a table `books` with fields `title` and `author`, look and prime on both:

    CREATE TABLE "books" (
      "book_id" INTEGER PRIMARY KEY AUTOINCREMENT,
      added TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      edited TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      "title" TEXTLINE,
      "author" TEXTLINE,
      url TEXTLINE,
      notes TEXTMARKDOWN,
      tags TEXTMEMO,
      look TEXT GENERATED ALWAYS AS (rtrim(
        iif("title" IS NOT NULL AND length(CAST("title" AS TEXT))>0, CAST("title" AS TEXT) || ' | ', '') ||
        iif("author" IS NOT NULL AND length(CAST("author" AS TEXT))>0, CAST("author" AS TEXT) || ' | ', ''),
        ' | ')) STORED,
      prime TEXT GENERATED ALWAYS AS (
        coalesce(CAST("title" AS TEXT),'') || '|' || coalesce(CAST("author" AS TEXT),'')) STORED,
      marked INTEGER NOT NULL DEFAULT 0
    );
    CREATE TRIGGER "trg_books_edited" AFTER UPDATE OF "title", "author", "notes", "tags"
      ON "books" FOR EACH ROW
      WHEN OLD."title" IS NOT NEW."title" OR OLD."author" IS NOT NEW."author"
        OR OLD."notes" IS NOT NEW."notes" OR OLD."tags" IS NOT NEW."tags"
      BEGIN UPDATE "books" SET edited = CURRENT_TIMESTAMP WHERE "book_id" = NEW."book_id"; END;
    CREATE UNIQUE INDEX "idx_books_prime" ON "books" (prime);

When the database has a maps table, each user table also carries the two
triggers that keep links whole (tested with SQLite 3.45: a stored generated
`prime` is available to AFTER triggers as NEW.prime and OLD.prime):

    CREATE TRIGGER "trg_books_maps" AFTER UPDATE ON "books" FOR EACH ROW
      WHEN OLD.prime IS NOT NEW.prime
      BEGIN
        UPDATE maps SET prime1 = NEW.prime WHERE tbl1 = 'books' AND prime1 = OLD.prime;
        UPDATE maps SET prime2 = NEW.prime WHERE tbl2 = 'books' AND prime2 = OLD.prime;
      END;
    CREATE TRIGGER "trg_books_maps_delete" AFTER DELETE ON "books" FOR EACH ROW
      BEGIN
        DELETE FROM maps WHERE (tbl1 = 'books' AND prime1 = OLD.prime)
                            OR (tbl2 = 'books' AND prime2 = OLD.prime);
      END;

A foreign key, by contrast, may be declared in the usual way:

    "album_id" INTEGER REFERENCES "albums" ("album_id")

- `look` skips blank parts, so a record with no author reads "Title" rather
  than "Title |". `prime` keeps every part, so it always has the same shape.
- The fields in `look` and in `prime` need not be the same: `look` is what a
  person needs to recognize the record; `prime` is what makes it unique.
- Generated columns need SQLite 3.31 or later, and STORED keeps them
  queryable and indexable.

## lookups, maps and views

    lookups: lookup_id, added, edited, src TEXTLINE, tbl TEXTLINE,
             fld TEXTLINE, val TEXTLINE, ordinal INTEGER, descrip TEXTMEMO,
             url TEXTLINE, notes, tags, look, prime, marked
             prime: src|tbl|fld|val
    maps:    map_id, added, edited, tbl1 TEXTLINE, prime1 TEXTLINE,
             kind TEXTLINE, tbl2 TEXTLINE, prime2 TEXTLINE,
             notes, tags, look, prime, marked
             prime: tbl1|prime1|kind|tbl2|prime2
             plus indexes on (tbl1, prime1) and (tbl2, prime2)
    views:   tbl TEXTLINE NOT NULL, fld TEXTLINE NOT NULL, val TEXTLINE,
             PRIMARY KEY (tbl, fld) -- the one table without the standard fields

A map names records by their `prime`, never their id, so a link survives a
merge, an export and a renumbering.

## Seeded vocabularies

A new database's lookups table holds DbDo's field types under `tbl` `*` and
`fld` `type`, and these generic `maps.kind` values: `affiliated_with`,
`located_at`, `member_of`, `part_of`, `related_to`. A template replaces them
with its own, as JobTrail does with `contact_for`, `sent_for` and `works_at`.

## Where the shipped databases differ (2 October 2026)

checkDb found these in DbDo's templates. None stops DbDo; each is worth fixing
when a template is next rebuilt.

- **No `trg_<table>_edited` trigger** in most templates' tables, so `edited`
  changes only when DbDo itself saves. A script or another program that edits
  the file leaves it stale.
- **lookups and maps have no index on prime** in most templates, and JobTrail's
  tables have a plain, not unique, prime index.
- **url is not always just before notes** (CellarTrail's wines, SchoolTrail's
  students and teachers).
- **No template carries the maps triggers above**, and DbDo re-points links
  only when a table's prime definition is rebuilt, not when a record is edited.
  So editing a field that is part of a record's prime, or deleting the record,
  leaves its links pointing at nothing until DbDo or the database adds them.
- **DbDo recognizes its own tables by name alone**, so a user's own table named
  maps, lookups or views would be hidden. Recognizing them by their columns too
  (maps has tbl1, prime1, kind, tbl2 and prime2) would prevent that.
- **DbDo's generator makes the id by dropping one trailing s**, which would
  give `storie_id` for `stories`. The templates rightly use `story_id`; the
  generator should take the English singular, as checkDb does.
