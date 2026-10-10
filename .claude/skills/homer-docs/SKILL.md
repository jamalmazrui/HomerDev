---
name: homer-docs
description: >-
  Writes and reviews the documentation of a Homer Tools app or of the Homer
  Development Kit: the standard document set (ReadMe, the app's guide,
  Announce, Developer, History, Hotkeys, License), each Markdown file with its
  Pandoc .htm, at a ninth-grade reading level, with the Homer heading, list,
  link and key-naming conventions. Use when writing or revising any Homer
  document, a History entry, a Hotkeys list, release notes or a ReadMe, or when
  checking documents before a release.
---

# Homer documents

A Homer document is read with a screen reader, usually by heading. It says
things plainly, in the order a reader needs them, with nothing to decode.

## The set

Every app ships these, each as `.md` with a `.htm` made from it by Pandoc
(never edited by hand): **ReadMe** (a quick start), **Announce** (what is
new), **the app's own guide** `<App>.md` (the full reference), **Developer**
(how it is built), **History** (the changes, readably), **Hotkeys** (every
key, sorted several ways) and **License** (the MIT license verbatim, naming
the app and Jamal Mazrui). ReadMe and License sit at the top of the project;
the rest in `help`. What each holds is in
[references/document-set.md](references/document-set.md).

## Writing

- **Ninth-grade reading level**, plain language, never at the cost of
  technical accuracy. Developer and History may go further into detail.
- **Say the word a key comes from** wherever a key is introduced: "Shift+C is
  Say Cell". Headings use the command's own word, not a synonym ("Order and
  Where Filter", not "Sorting and Filtering").
- **Key names** as JAWS writes them: Alt, Control, Shift, Windows in that
  order, "Control" spelled out, the reader key as "JAWS" or "NVDA".
- **Match the noun to the count** ("1 match"); zero is an answer.
- **Lists rather than tables**, except in reports for sighted managers or
  developers. Lists in lowercase alphabetical order unless another order is
  clearly more logical. "In order by title" ignores a leading A, An or The,
  case-insensitively; "by author" is by surname.
- **Links**: a URL only when verified; link text that says where it goes
  and reads well out of context -- never "click here" or "read more", never a
  bare URL. A screen reader user often lists a page's links on their own.
- **An image or diagram says what it shows**: alternative text for an image,
  and a text description beside a diagram.
- **A page break** is a paragraph holding only `\pagebreak`, rendered with the
  pagebreak Lua filter.
- Report what a program does, not what it could do; no promotional words.

## Headings

A document has one H1, its title. A guide's H2s are topic categories in
alphabetical order, with "Miscellaneous" last; a category needs two or more
articles or folds into Miscellaneous. H3s are the articles, alphabetical
within their category; H4 and below sit inside an article. No level is
skipped. A long document opens with a contents list.

The page built from it has one H1 too. Pandoc makes the front matter's
`title:` into a level-one heading of its own, so a document that also opens
with a `# ` line of the same title, or that uses `# ` for its sections, became
a page with two or more. Every Homer build's encoding pass (the kit's
`fixEncoding`, also used by homer-convert and fixPages) leaves each `.htm`
beside a `.md` with exactly one: a repeated title keeps one copy, an author's
single `# ` heading stays the page's heading, sections under the title move
down a level, and a page with none gets its own title. check fails a page
built from Markdown without exactly one H1.

## History

Newest first. Each entry is headed with the version and date. It says what
changed for the person using the app, and why, in sentences rather than
commit messages; a fix names the symptom a user saw. A kit or build change
the user never sees goes in Developer or the kit's own History, not the
app's.

## Check before release

Run the document check on the project; fix what it reports, then rebuild the
`.htm` files (the build does this) and run it again:

```bash
python scripts/checkDocs.py C:/<App>
```

It reports documents missing from the set, a `.md` without its `.htm` or an
`.htm` older than its `.md`, heading problems (not one H1, a skipped level),
bare URLs, vague link text, an image with no alternative text, a long
document with no contents list, and each document's reading
grade, flagging a user document above grade 9. Zero findings is a real
answer.
