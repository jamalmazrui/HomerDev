# The Homer book pattern

*For the Homer Development Kit's help folder. Revised 3 October 2026 from the Blind Vibe Coding project.*

## Contents

- Files and folders
- Sections, in order
- Chapters
- Glossary
- Timeline and Key Figures
- Copyright page
- About the Author and the author's other books

## Files and folders

A book is a Homer project of its own kind, beside app, kit, page and collection. The kit's `check` can tell it by `<Book>.yaml` with `to: epub3` beside a `<Book>.md` at the top; until check knows the kind, run it as a page and read the report with that in mind. The project keeps `version.txt` for the edition (stepped by hand for each submission, since the book has no build-time version resource) and `RepoFiles.txt` for the files it publishes, so `push`, `tidy` and `release` work as they do for an app; the build script is `build.cmd`, as the kit's buildname rule asks. A book uses the Homer folder layout, including `notes` for the drafts, audits and transcripts a book accumulates; `notes` is a standard folder of every Homer project of every kind, ignored by Git and never packaged by an installer, and `tidy` moves stray files into it, dropping duplicates and suffixing name collisions. The layout: sources and the build at the top; `configs` for the KDP answers; `exec` for the built EPUB, which is not kept in Git; `help` for the project's guides; `logs` for one log per run; `pages` for a companion GitHub page and its images; `scripts` for the publishing and image scripts with their tests; `templates` for forms such as the bug report.

- `Book.md`: the manuscript, Pandoc Markdown, UTF-8 with BOM and CRLF.
- `Book.bib`: BibLaTeX entries, each web source with url and urldate.
- `Book.yaml`: Pandoc defaults: from markdown, to epub3, citeproc, reference-location document, toc, css, cover.
- `Book.jpg`: the cover, 1,600 by 2,560 pixels, RGB JPEG at 300 dots per inch, saved with full color sampling. Draw it with a script (`scripts\makeCover.py`) rather than by hand, so every size, color and position is a number a screen reader user can read and change, and so the web copies (JPEG, PNG, SVG mark, social card) come from the same source. Check contrast in the script: at least 4.5 to 1 for text.
- `book.css`: underlined links, no forced text colors.
- `configs\Book_KDP.inix`: the KDP form answers, in .inix rather than JSON (see Inix.md); the kit's `templates\Book_KDP.inix` is the starting point. `scripts\kdpSubmit.py` reads it, fills the KDP form, and updates a published book from the same file.
- `ACCESSIBILITY.md` at the top of the repository: GitHub shows it as an Accessibility tab; the kit's `templates\ACCESSIBILITY.md` is the starting point.

## Sections, in order

The YAML gives title, subtitle, author, date, lang and rights, plus
bibliography and csl when the book cites sources. Then, at level 2:

1. Copyright
2. Table of Contents, holding only `[TOC]`
3. Introduction, with Organization and Background at level 3
4. The chapters
5. Conclusion
6. Any reference sections the book needs: Quick Reference, Appendix A, B, C
7. Timeline, when the chapters are not in date order
8. Key Figures
9. Glossary (Strange Truths books call it Key Terms)
10. Further Reading
11. Bibliography, holding only `::: {#refs}` and `:::`
12. Also by the Author (in a series: Also in the Series)
13. About the Author

A book for screen reader users is read in speech, in braille, or in both; write so that either works, which means real headings, no meaning carried by layout alone, and punctuation that reads well cell by cell.

Standard section names stay bare, with no colon and subtitle. Each
back-matter section opens with one italic sentence saying what it holds.
Sections are separated by a line of three hyphens.

## Chapters

- Heading: `## N. Title — a short subtitle in lower case`, numbered from 1.
- Narrative books open each chapter with its story; tutorial books open with a real person who did something similar, then: What You Will Build, What You Need, Steps, Check Your Work, When Something Goes Wrong, Practice.
- Every chapter ends with **Learn More**: free resources, grouped by kind (articles, podcasts, guides), each a link whose text names the resource and its publisher, linking to the resource itself rather than a page about it.

## Glossary

```
### Term {#book--term}

One to three plain sentences defining the term.
```

The prefix before `--` is a short slug for the book. Entries are in
alphabetical order. The first time each term appears in the chapters, it
links to its entry: `[term](#book--term)`. Skip code, quoted prompts and
headings when choosing that first use, and skip a use where the word means
something else.

## Timeline and Key Figures

**Timeline**: `- **Month Year**: what happened.[@key] See [chapter N](#book-chNN).`
Give chapters explicit ids, such as `{#book-ch07}`, so these links are stable.

**Key Figures**: `- [Name](link). Role. What the book draws on. Chapters N and M.`
In alphabetical order by surname for living subjects, or chronological for
historical ones. Link to the person's own site, a profile, or the source
the book cites; leave the name unlinked when no link is verified.

## Copyright page

State who holds the copyright, and say plainly how AI was used. When an AI
drafted the prose, follow KDP's definition: that is AI-generated content,
even after substantial editing. Name the tool, say what the author did
(chose topics, directed, verified facts, edited, made every decision), and
say the author discloses it to KDP. Add when sources were last checked.

KDP's definitions, unchanged since September 2023 and still current in 2026:
content an AI tool created, text, images or translations, is AI-generated,
even after substantial edits, and must be disclosed when the book is published
or republished; content the author created and then edited, refined or checked
with an AI tool is AI-assisted, and need not be disclosed. Use the term that
matches how the book was made, and never call drafted text AI-assisted.

Model wording when an AI drafted the text, with the tool's maker and name,
and the kind of book, filled in:

> An AI model, Anthropic's Claude, drafted the text of this book at the
> author's direction, in the style of narrative nonfiction. The author chose
> every topic, guided the writing, checked the facts against the sources
> cited, edited the text, and made every editorial decision. Amazon Kindle
> Direct Publishing defines text that an AI tool drafted as AI-generated, even
> after substantial editing, so this book is AI-generated by that definition,
> and the author discloses it to KDP.

When the author wrote the text and used AI only to edit, check or research:

> The author wrote this book. An AI model, Anthropic's Claude, helped to edit
> and check the text and to research sources. Amazon Kindle Direct Publishing
> defines this as AI-assisted content.

## About the Author and the author's other books

About the Author is copied word for word from the author's reference file;
checkBook --bio confirms it. Also by the Author lists each other title as
`**[Full Title: Subtitle](https://www.amazon.com/dp/ASIN)**. One sentence.`,
in order by title ignoring a leading "The", followed by any compilation and
a link to the author's Amazon page.
