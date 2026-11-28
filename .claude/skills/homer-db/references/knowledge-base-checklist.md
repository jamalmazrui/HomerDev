# Checklist: a knowledge base that comes alive in DbDo

A knowledge base is a database built by a script from a collection someone
already keeps -- a magazine's issues, a set of directory pages, a folder of
guides -- so that DbDo can search, play, read and open every item in it. The
TalkingBookTopics template is the worked example. Go through this list when
designing one and again before its first full build. Each item came from a
build that went wrong without it.

## Contents

- Purpose and source
- Records and keys
- Fields that DbDo acts on
- Values
- Full-text search
- Descriptions and settings
- The builder
- Checks
- Personal or shipped
- Size and sharing

## Purpose and source

- **Name the questions it answers** before naming a table: what a person will
  look up, play, read or open. One record is one such thing.
- **Read the most regular form of the source.** Where Pandoc made a page from
  Markdown, the page is often the better input: Pandoc writes every link and
  field one way, however the Markdown spelled it.
- **Survey the whole collection first.** Count every heading level, every
  field label and every missing link across all of it, not a sample. The
  survey decides the columns.
- **Skip what repeats.** Contents lists and appendixes list the same items
  again; read only the body.

## Records and keys

- **Each user table has its own first letter** (books, issues, updates), so
  typing one reaches it.
- **The row speaks three fields**, the deciding one first; look is those
  fields.
- **The prime is what makes a record itself, tested on the full data.** Log
  every collision with its record and read them: a title alone repeats across
  authors and across a broadcast aired twice. When two records differ only by
  their media, the media address belongs in the prime.
- **A long prime costs size.** Its text is stored again in the prime column
  and its unique index; log the file size so the cost is seen.
- **A parent links its children by a foreign key** named <singular>_id, with
  an index, and keeps their count as a field, so the parent's row can say it.

## Fields that DbDo acts on

- **stream_url holds the audio or video**, so Play Media (Control+P) plays it,
  and marked records play as a play list.
- **url holds the item's own page**, opened with Control+Shift+U. Where there
  is none, point url at the item's place in a local page
  (file:///...#heading-id), so it opens in context, and check that every such
  anchor exists in its page.
- **Markdown goes in TEXTMARKDOWN only when the source has structure**, so
  Preview Markdown in Web Browser shows it; plain text goes in TEXTMEMO.

## Values

- **Numbers are numbers.** A duration becomes whole minutes and a date becomes
  yyyy-MM-dd, so sorting and filtering work. Log how many parsed.
- **Nothing is dropped.** A value that does not parse, and every field without
  a column of its own, goes in one details field, a "Label: value" a line. Log
  a census of the labels seen.
- **Gather white space.** Generated HTML wraps long lines, so a title arrives
  broken in two; treat every run of white space as one space.

## Full-text search

- **Index with the kit's homerFts**: an external-content FTS5 table that keeps
  itself current, with no prefix indexes, which cost size for a speed nobody
  hears.
- **Store the weights as the index's rank**, a title counting most, so every
  search that orders by rank weighs alike.
- **Run sample searches in the build** and log each count and its first hits,
  so a log shows whether ranking makes sense.

## Descriptions and settings

- **Describe the database, each table and each field** in defs: a row with tbl
  * for the database, tbl alone for a table, tbl and fld for a field. Shift+F1
  reads them.
- **The .inix opens it well**: FollowTemplate = yes for a database rebuilt from
  its source, InitialTable, each table's SelectFields, and a header that says
  how to play, find and read an item.
- **Ship three to five saved searches** that show it off: one full-text with a
  snippet of the passage, one newest first, one by size.

## The builder

- **A script in scripts with its .cmd wrapper**, finding the source folder from
  its argument, an environment variable, or a drive's root.
- **--due rebuilds only when needed**: the database missing, or older than the
  script or any source file.
- **Build to <name>.db.building**, VACUUM it, then replace the old file, so a
  failed build never leaves half a database.
- **Log everything**: the environment, one line a source file, collisions,
  the label census, sample searches, totals, size and time. The console says a
  line at least every ten seconds.
- **Never stop the build.** No source folder means nothing to do; a failure is
  reported, and the build goes on.
- **Write names tidy will not change.** A constant is named like a variable,
  with no c_ in front. tidy renames an obsolete name, which makes the script
  newer than its database, so the next build rebuilds it for nothing.

## Checks

- **describeFields, then checkTemplates --repair**, then checkDb with no
  failures, before anything is shipped or installed.
- **Every saved search runs**, and checkTemplates reports its row count.

## Personal or shipped

- **A personal knowledge base** stays on its owner's computer:
  LocalFiles.txt names its script, its .cmd and its template folder, the
  installer excludes the folder, the build installs it in the user's own
  templates folder, its field sentences live in its own defs, and no public
  document names it. Leave its folder out of the installer's inputs too, or
  every rebuild of it makes a new installer, and push reads it again.
- **A shipped one** puts its sentences in fieldDescriptions.inix and is
  described in the app's help and history.

## Size and sharing

- **Log the size and where it goes.** Log the database's size beside its
  source files' size, and each table and index from dbstat. Built with no
  prefix indexes, a database has run 1.7 to 2.2 times its source, and zips to
  about a third. A long prime shows up as a large prime index.
- **Over 100 MB, it cannot go in a GitHub repository.** Share it as a release
  download that Get Database adds from its url.
- **Copy only what may be shared, and credit the source.** The text belongs to
  its publisher.
