---
name: app-help-guide
description: >-
  Builds a screen-reader-friendly help guide (Markdown plus a matching .htm) for
  a product, app, service or publication, from the publisher's OWN help pages:
  probe the estate, write a fenced harvester, gather the pages, build the guide,
  run the gates. Use this skill whenever the user asks to "do" a product for the
  help guide collection, to gather or re-gather a company's documentation, to
  judge whether a product has help worth gathering, to clean publisher furniture
  out of an existing guide, or to decide whether an estate should be refused —
  even if they only name an app and say "add this one."
---

# App Help Guide

One Markdown file holding a product's own help, and one HTML file built from it
with Pandoc. Nothing written here appears in the articles: the guide carries the
publisher's words, arranged so a screen reader user can move through them by
heading, search the whole product's help at once, and read it offline.

Four scripts in `scripts/` do the work, each with a `.cmd` wrapper:
`buildGuide.py` turns gathered pages into the guide and its pair,
`cleanFeedback.py` sweeps publisher feedback widgets out of guides already
built, `getLlmsGuide.py` gathers and builds in one run from a publisher's own
`llms.txt`, and `makeHarvester.py` writes a crawler for one estate.

Read `references/fence-faults.md` before writing a fence,
`references/guide-format.md` before building, and
`references/refusal-rules.md` before deciding an estate is not worth gathering.

## The four steps

1. **Probe before spending a run.** Ask a handful of the publisher's plausible
   help addresses and count the words, the headings and the links to other help
   pages on each. Never write a harvester for an address you have not seen
   answer: guessing costs a whole round, and it has.
2. **Fence.** Write the regular expression that says which addresses belong to
   this estate, and what is excluded — forums, translated editions, developer
   documentation, badge and profile pages, revision histories, the shop. Add the
   block to `makeHarvester.py` and generate the harvester.
3. **Harvest.** Add the guide to the collection's `data\addGuides.inix` (a
   section named for the guide, with `harvester=` and `asked=`). The person with
   the network runs build_release in the collection: its build gathers every
   guide not yet gathered for its asked day, through `harvestQueue`, and leaves
   each archive in `results`, with the run's log inside. They send those back.
   A harvester can still be run by hand from the collection's `scripts` folder. Read the log first: it says
   what was refused and why, and a run that gathered nothing says so in one line.
4. **Build.** Write a reader for that publisher's page shape in `buildGuide.py`
   and add the guide to its plan. In the collection, `build` (the first step of
   build_release) then builds every guide whose harvest is newer than the guide,
   runs the gates, and has the kit's fixPages build the `.htm` of each guide that
   changed -- one level-one heading, the language, a main landmark, working links.
   A gate failure fails the build, so nothing broken is pushed. The collection's ReadMe
   names its license: CC BY-SA 4.0 for the collection's own selection,
   arrangement and wording, while each guide's help text keeps its publisher's
   terms -- one sentence, kept whenever the ReadMe is rewritten.

## Where things go: the Homer layout

A collection of guides (C:\AppHelpGuides) keeps the Homer tree (11 November 2026):

- **The guides,** each `.md` with its `.htm`, at the top, beside the ReadMe and
  the License, with `build.cmd`, which runs `buildGuide --build`.
- **`scripts`:** the harvesters makeHarvester wrote, each `get<Product>Help.py`
  with its `.cmd`.
- **`data\harvests\<Product>Help`:** the pages a harvester saved, with
  `manifest.txt`. They stay between runs, because a run resumes over them and
  the build reads them. Never pushed (LocalFiles.txt).
- **`results\<Product>Help.zip`:** the archive to upload, with the run's log
  inside. An output that may be moved away; nothing reads it again.
- **`data\addGuides.inix`:** the guides to gather. Each section is a guide's
  name, with `harvester=` (the block's script name in makeHarvester) and
  `asked=` (a day). The build's `harvestQueue` gathers each one not yet gathered
  for its day, records the day, exit code and page count in the harvest's
  `request.txt`, and moves an older gathering aside, whole, to
  `<Folder>-before-<day>`, so a fresh run never resumes over stale pages. A
  later `asked=` day gathers a guide again. The sections stay as the record.
  A delivery adds its own `data\addGuides-<day>.inix` rather than replacing
  this file: every `addGuides-*.inix` is read after it, and where two name the
  same guide, the later `asked=` day wins (harvestQueue version 4).
- **`logs`:** one log per run, `<Collection>-<task>-yyyyMMdd-HHmmss.log`, in UTF-8
  with a byte order mark and Windows line endings.

The kit's scripts are run from the kit, never copied into the collection: copies
only drift. The build settles an older collection once, logging every move:
harvesters at the top go to `scripts`, harvest folders to `data\harvests`,
harvest archives to `results`, logs to `logs`, and copies of the kit's scripts
to `notes\retired`.

## Running the scripts

    makeHarvester.cmd [folder] [products]   writes harvesters, by default into the collection's scripts
    harvestQueue.cmd [collection]           gathers what data\addGuides.inix asks for; the build runs it first
    build                                   in the collection: settle, build changed guides, gate, make .htm
    build GoodMaps                          rebuild one guide, as after its reader changes
    buildGuide.cmd [harvests] [guides] [products] [--changed]   the same build by hand
    cleanFeedback.cmd report                lists the furniture it would remove
    cleanFeedback.cmd                       removes it and rebuilds each .htm
    getLlmsGuide.cmd [products]             gathers from llms.txt and builds, in one run

Each writes a debugging log in the collection's logs folder: the environment,
every setting, every address with its status, and the reason for anything not
kept. A harvester sent to somebody on its own keeps its pages, archive and log
beside itself.

## Conventions (do not deviate without reason)

- **A category comes from the publisher**, not from the assistant: a breadcrumb
  trail, a section, a listing, a manual's own chapters. Where a publisher offers
  none, group by subject and **say so in the preamble**.
- **Where a publisher offers a listing** — Zendesk's `articles.json` and its
  kin — take it. The article count is then known before a page is built.
- **Where a publisher offers `llms.txt`, take it.** An index of every page by
  section, with a plain Markdown copy of each page (or the whole manual in one
  `llms-full.txt`), is the publisher's own text without the furniture, so no
  crawler or page reader is needed. Add the product to `getLlmsGuide.py`'s list
  with what it leaves out and why; the script reads robots.txt before fetching,
  computes Pandoc's own heading identifiers so internal links survive repeated
  titles, and checks every link in the built .htm. Expo, Hermes Agent and Kiro
  were the first three (13 October 2026). Hermes renames its llms-full.txt with
  a hash on every deploy, so use the stable /docs/llms-full.txt address.
- **A robots.txt may refuse the machine copies and allow the pages.** Kiro
  disallows `/llms.txt` and `/docs/*.md` for every agent but allows its web
  pages, so `getLlmsGuide.py` reads the sitemap's pages instead (its "sitemap"
  mode). Python's own robots parser ignores `*` and `$` in rules; the script
  reads the rules itself, longest match winning.
- **Let Pandoc read the publisher's Markdown as the publisher wrote it.** These
  sources are GitHub-style Markdown, where a heading needs no blank line before
  it; read as Pandoc's own dialect, a code block inside a list went unnoticed,
  shell comments became headings, and 64 Expo article headings vanished. Each
  article now goes through Pandoc (`-f gfm`) before its headings are
  renumbered, every fence scanner follows CommonMark (a fence line holds no
  further backtick; a closing fence holds nothing else), and Pandoc itself is
  asked for the article identifiers rather than predicting them.
- **A page that streams its article holds it out of place.** Kiro's pages
  are React streaming: `<main>` holds a placeholder, `<template id="B:1">`,
  and the article arrives later in `<div hidden id="S:1">`, itself holding a
  further placeholder. 234 pages came back with "no article text" until the
  reader put each block in its place as the browser's script would. Code is
  rebuilt as plain text in its language, and a small Pandoc filter labels any
  unlabelled code block "text", because Pandoc indents an unlabelled block and
  an indented comment line then reads as a heading.
- **Structured data beats drawn text.** Angi, CrimeCon and Udio all publish
  their own questions or trails as schema.org data in the page head; that is a
  better source than the prose, because it pairs each question with its answer.
- **Two volumes when an estate is two different things AND each stands alone.**
  Verizon's service and device halves, split on measurement rather than feel.
  One volume when a publisher covers several products in one estate: Hartgen's
  three, Get Accessible Apps' two.
- **One copy, not four hundred.** Where a network gives every member the same
  help under its own host, gather one.
- **Preambles name siblings.** Zotero, Mendeley and EndNote each point at the
  other two.

## Gotchas learned the hard way

- **A help-shaped address may be a single article.** Check before believing.
- **A site that answers a probe may refuse a crawler.** Some hosts refuse
  repeat visitors; a pause of minutes would help but a run cannot wait.
- **Frames hide half an estate.** Read `src` on `frame` and `iframe` as well as
  `href`; EndNote's whole help system was invisible until that was fixed.
- **A 404 and a 400 mean different things.** No such page, versus "not like
  that" — the second means the connection is being judged, and the address may
  be perfectly real.
- **Identical word counts across different addresses** mean the site is serving
  one shell. Stop guessing addresses.
- **An estate can move house.** plainlanguage.gov now redirects to digital.gov;
  the redirect looked like a dead estate and was a live one. GoodMaps' HubSpot
  knowledge base moved every article under `/migration/` between a probe and the
  run (11 November 2026): the addresses the probe saw answered 404, and the
  site map, read as a seed, found all of them. Seed a site map when there is one.
- **An article's own heading can take an article's anchor.** Pandoc names
  headings in the order it meets them, so a heading "Favorites" inside an earlier
  article took the identifier the contents entry for the article "Favorites"
  pointed to. The builder now gives such a heading an identifier of its own, and
  computes anchors by Pandoc's rule: a leading digit goes ("2D Map View" is
  `d-map-view`) and periods stay ("llama.cpp").
- **Count what you leave out, and say it.** Every guide that drops material —
  translations, a changelog, an administrator's half, badge pages — says how
  many and why, in its preamble or its log.
- **Every estate goes through the generator, never a script of its own.** On 2
  November 2026 a one-off harvester, getDougLeeTargetsHelp.py, was written for
  fifteen of Doug Lee's scripted apps beside `makeHarvester.py` instead of in
  it -- the Homer DRY rule broken, as with FreeWill in October. Its thirteen
  plain estates are now blocks in `makeHarvester.py`. Before writing any code
  for a new product, look here first: a listing, `llms.txt`, a sitemap or a
  fenced crawl almost always fits one of the four scripts.

## Estates that need a browser

A block with `"sFetch": "edge"` is fetched by Microsoft Edge (makeHarvester
version 3, 14 November 2026): headless, in a profile made for the run, with
`--dump-dom` after `"iBrowserWait"` seconds of the page's script (30 by default,
what OpenTable's Salesforce pages needed). Such a run refuses any page nine
tenths the same words as the first page it saved -- scaffolding without its
article -- and says so in the log. Edge sometimes crashes as it shuts down after
printing the page (exit 0xC0000005, 39 times in 196 on Twitch); a page that closes
its html element is kept whatever the exit code (1.263.0). Glassdoor is the first block to use it and
Twitch (19 November 2026) the second, its reader waiting on its first harvest;
Coursera and Dell Command Update's user's guide are candidates, and Adobe Connect if its pages keep answering Python with HTTP 403.
A run at thirty seconds a page is slow: keep its ceiling honest and put it last
in addGuides.inix. Should a site need clicking rather than waiting, these lessons
from the hang of 2 November 2026 apply to a fuller browser road.
Edge opened on its blank page and nothing followed, because only
the launch had a time limit and the console never said what it was waiting
for:

- Launch with Playwright's persistent context, which hands back a usable tab,
  rather than a separate context and page step.
- Upgrade Playwright before the first launch of a run; an old Playwright can
  stall against a newer Edge.
- Give every browser step its own time limit, and say before each wait what it
  waits for and for how long ("Waiting up to 60 seconds for ..."), as the
  Homer rule for browser automation asks. Log every page change.
- Run one visible-browser harvest at a time.

## One harvest, several guides

A help centre that covers several surfaces of one product may be split into one
guide a surface, all read from a single harvest. Claude (19 November 2026) is
the model: `getClaudeHelp` gathers support.claude.com once, and buildGuide's
`readClaudeTrails` reads every article with its whole trail of Intercom
collections, once a build. `claudeSurface` then places each article in exactly
one guide (ClaudeWeb, ClaudeDesktop, ClaudeIos, ClaudeCowork, ClaudeCode,
ClaudeDuet), dropping Mac-only, Android-only, administrator and left-out
collections. When the new guides replace an older single guide, name the pair in
the build loop's retirement list: once every new guide is built and clean, the
build moves the old guide and its page to notes\retired.
