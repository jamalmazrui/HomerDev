---
name: podcast-directory
description: >-
  Builds a screen-reader-friendly, single-page directory (Markdown plus a matching
  .htm) of a podcast from its public RSS feed: every episode listed with its date,
  length, and summary, and a title link that plays the audio directly. Use this
  skill whenever the user wants to catalog, index, archive, or make an accessible
  directory or guide of a podcast or set of podcasts; harvest a show's episodes
  into a file; turn a podcast feed or Apple Podcasts link into a browsable list;
  or add a show to a PodcastDirectories-style collection, even if they do not say
  the word "directory."
---

# Podcast Directory Builder

Turn a podcast's public RSS feed into one flat, screen-reader-friendly page that
lists every episode. A blind screen reader user can then read the whole show top
to bottom, jump by heading, search it all at once with the browser's find command,
and open any episode with a link that plays it, with no app, sign-in, or ads in
the way.

Two small scripts in `scripts/` do the work: `harvestShows.py` fetches feeds into
one tab-separated file per show, and `buildDirectory.py` turns that file into the
`.md` and `.htm`. Each has a `.cmd` wrapper so it runs from the command line
without typing a Python or PowerShell invocation.

## The pipeline

1. **Resolve the feed.** Preferred input is the show's Apple Podcasts numeric id
   (the digits after `id` in a `podcasts.apple.com/.../id########` link). The
   harvester turns that id into the RSS feed through the free iTunes lookup API.
   A few shows' ids do not expose a feed through that lookup; for those, give the
   direct RSS feed URL instead (the harvester accepts either an id or an
   `http...` feed URL in the same field). Verify every id or URL before use, per
   the never-ship-an-unverified-link rule.
2. **Harvest to TSV.** `harvestShows.py` writes one `<Slug>_Episodes.tsv` per show
   with these columns: guid, date, title, link, duration, season, episode, type,
   audio_url, summary. It also saves the raw feed as `<Slug>_feed.xml` and writes
   `harvestShows.log`.
3. **Build the directory.** `buildDirectory.py` reads one TSV and writes
   `<Slug>.md`, then `<Slug>.htm` via Pandoc, finished by the homer-convert
   skill's `toHomerEncoding`: the Homer encoding, and the title said once where
   Pandoc's title block repeats the page's first heading. It self-verifies and logs.
4. **Verify.** Confirm zero broken internal anchors, zero duplicate anchors, zero
   bare URLs, and UTF-8 BOM with CRLF endings (the builder reports the first three
   in its log).
5. **(Optional) Add to a collection.** Slot the show into a themed category and
   regenerate the collection's README and Announce pages and its single zip.
   The README keeps its License section: CC BY-SA 4.0 for the collection's own
   selection, arrangement and wording, while each episode's title, description
   and audio keep their publisher's terms.

## Running the scripts

Harvest one show (by Apple id or direct feed URL, set in the SHOWS list near the
top of `harvestShows.py`):

    harvestShows.cmd --only=Casefile

Build its directory from the harvested TSV:

    buildDirectory.cmd --tsv Casefile_Episodes.tsv --slug Casefile ^
        --name "Casefile True Crime" --title "Casefile True Crime Directory" ^
        --subtitle "A Screen-Reader-Friendly Guide to Casefile" ^
        --intro "Casefile presents meticulously researched accounts of real crimes."

Useful build options: `--by-guest` pulls a Guest field and a by-guest appendix
from titles shaped like "Title | Name" (interview and book-summary shows);
`--brief` trims each summary to one sentence; `--nosummary` and `--noappendix`
shrink very large directories.

## The output format (what buildDirectory.py produces)

- **Pandoc front matter**: title, subtitle, author, date, version, lang, toc:
  false, and an abstract naming the episode count and year span.
- **Intro**: an H1 title, a one-paragraph description of the show, a paragraph
  stating how many public episodes and which years, and a paragraph on how it is
  organized.
- **Table of contents**: a link per year group, a Trailers link when present, and
  links to the appendixes.
- **Body**: episodes grouped by **year, earliest year first**; within a year,
  **oldest episode first**, so the show reads the way it unfolded. Each episode is
  an H3 whose linked title **plays the audio** (`audio_url`); when the show has a
  distinct episode web page, a plain "Episode page" link follows on its own line.
  Then the fields that exist, one per line, in **alphabetical order**: Date,
  Duration, Episode, Guest (only with `--by-guest`), Season, Summary. A field with
  no value is omitted entirely.
- **Trailers and Cross-Promotions**: any `type = trailer` rows gathered in one
  section at the end of the body.
- **Appendixes**: A by date (newest first, grouped by year), B by title, and
  (with `--by-guest`) C by guest.

## Conventions (do not deviate without reason)

- **Encoding**: every `.md` and `.htm` is UTF-8 **with a BOM and CRLF** endings.
  (This SKILL.md itself is plain UTF-8 without a BOM, because a skill's YAML front
  matter must begin at the first byte.)
- **File names / slugs**: CamelCase, **no underscore** (e.g. `Casefile`,
  `AmericanHistoryTellers`, `48Hours`). A leading digit is fine; explicit HTML5
  ids survive Pandoc.
- **Title sort**: case-insensitive, ignoring a leading "A", "An", or "The".
  **Author/guest sort**: by surname, case-insensitive.
- **Autoplay link**: the title points at the episode's own audio file, never at a
  web page, so one press plays it. Fall back to the feed link only when no audio
  URL exists.
- **Summaries**: strip HTML tags and any bare URLs; never leave a bare URL in the
  page. Use reader-friendly link text everywhere else.
- **Match the noun to the count** ("1 episode", "2 episodes"; "0" is a real
  answer, not an error).
- Prefer lists to tables throughout, for screen reader friendliness.

## Finding shows to add

- **A lead is not a feed.** Newsletters, event invitations, course pages, and
  video links name a topic, not a podcast: a NASA *webinar* announcement or a
  "vibe coding" YouTube *course* is not a show to harvest. Confirm a real RSS feed
  exists before adding anything, and if none does, say so rather than inventing
  one.
- **A publisher usually runs several shows.** When one fits, check the whole
  slate. NASA alone runs Houston We Have a Podcast, NASA's Curious Universe, Small
  Steps Giant Leaps, Gravity Assist, On a Mission, and The Invisible Network - the
  last three at `https://www.nasa.gov/feeds/podcasts/<slug>`.
- **Verify every id or feed URL against the source**; list nothing you could not
  confirm.
- **Older or delisted shows** may be gone from Apple Podcasts while their RSS feed
  still works. Use the publisher's direct feed URL (the harvester takes it in
  place of an id), exactly as for an id the iTunes lookup cannot resolve.

## Gotchas learned the hard way

- **iTunes lookup returns no feed for some ids** (the harvest logs "could not
  resolve a feed"). Fix by supplying the show's direct RSS feed URL in place of
  the id; do not silently drop the show.
- **Premium or members-only shows** publish only part of their catalog in the free
  feed (for example, deep back catalogs sold on the creator's own site). The
  directory reflects what the public feed carries; say so rather than implying it
  is complete.
- **Very large catalogs** (many thousands of episodes) make heavy pages. The
  audio and page URLs set a size floor that trimming text cannot beat, so reduce
  the entry count (a length or quality filter) rather than only shortening
  summaries.
- **Re-harvest to refresh**: daily and weekly shows drift; re-run the harvest
  before publishing so counts are current.
