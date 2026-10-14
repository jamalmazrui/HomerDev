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
3. **Harvest.** The person with the network runs the harvester and sends back
   its `.log` and its `.zip`. Read the log first: it says what was refused and
   why, and a run that gathered nothing says so in one line.
4. **Build.** Write a reader for that publisher's page shape in `buildGuide.py`,
   run it, check the gates, and build the `.htm`, then finish it with the
   homer-convert skill's `toHomerEncoding` -- the Homer encoding, and the title
   said once where Pandoc's title block repeats the guide's first heading.
   cleanFeedback does both when it rebuilds a page. The collection's ReadMe
   names its license: CC BY-SA 4.0 for the collection's own selection,
   arrangement and wording, while each guide's help text keeps its publisher's
   terms -- one sentence, kept whenever the ReadMe is rewritten.

## Running the scripts

    makeHarvester.cmd .            writes every configured harvester here
    buildGuide.cmd harvests guides builds each guide from its harvest folder
    cleanFeedback.cmd report       lists the furniture it would remove
    cleanFeedback.cmd              removes it and rebuilds each .htm
    getLlmsGuide.cmd [products]    gathers from llms.txt and builds, in one run

Each writes a debugging log beside itself: the environment, every setting, every
address with its status, and the reason for anything not kept.

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
  the redirect looked like a dead estate and was a live one.
- **Count what you leave out, and say it.** Every guide that drops material —
  translations, a changelog, an administrator's half, badge pages — says how
  many and why, in its preamble or its log.
