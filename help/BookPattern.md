# The Homer book pattern

*For the Homer Development Kit's help folder. Revised 8 October 2026, when the book publishing tools moved into the kit.*

## Contents

- Book publishing projects
- Folders
- Settings files
- The tools
- Where the code comes from
- Personal data stays in the project
- Sections, in order
- Chapters
- Glossary
- Timeline and Key Figures
- Copyright page
- About the Author and the author's other books

## Book publishing projects

A Homer project publishes books when its configs folder holds `books.inix`, the catalog of its books. That is one fact, and the kit's `kind` script reports it: "It also publishes books." Publishing books is a capability, not a kind of its own. A page, such as a GitHub Pages directory of the books, a collection, or a project of a single book may each publish books, and keeps its own kind for every other kit script.

The kit's book tools build each book as an EPUB, audit it, check it with EPUBCheck, Ace by DAISY and Kindle Previewer, and send it to Kindle Direct Publishing (KDP), together with its details, its AI answers and its accessibility answers. They work for any book and any author. Everything about a particular author or book is in the project's own settings files.

## Folders

A book publishing project uses the Homer folders, plus two of its own. Each folder starts with a different letter, so pressing a letter in a folder list moves straight to the folder you want:

- `books` -- one folder per book, named by its root: `books\<root>\<root>.md`, the manuscript, in Pandoc Markdown, with any of `<root>.bib` and `<root>.csl` (citations), `<root>.jpg` (the cover inside the EPUB), `<root>.css` (the book's own styles) and an `images` folder.
- `configs` -- the settings files below.
- `data` -- what the tools keep between runs: `data\books\<root>.inix` for what KDP holds for each book, and `data\receipts\<root>.inix` for what was uploaded and submitted.
- `help` -- the project's own guides.
- `logs` -- one log per run.
- `notes` -- drafts and working files, never published.
- `results` -- each book's EPUB and its audit, `<root>-audit.md` and `.htm`, with a summary of every book.
- `scripts` -- the kit's book tools, copied in (see "Where the code comes from").
- `templates` -- optional: a project's own `epub.css` or `tocEpub.lua`, used in place of the kit's only when `buildBooks.inix` says `ownTemplates = yes`; otherwise the kit's are used, so an improvement to them reaches every project.

## Settings files

The kit's `Templates\books` folder holds a starting copy of each; copy them to the project's `configs` folder and fill them in. Each explains its own keys.

- `books.inix` -- the catalog: one section per book, with its title, subtitle, author, series, ASIN, AI answers, reading-level target and the few settings a book may need.
- `buildBooks.inix` -- how books are built: the project's own author, where to look for a book's Word file and cover on the first run, picture sizes, and how often the checking tools are brought up to date.
- `<root>_KDP.inix` -- for a new book only, the answers to every KDP form, from `Templates\books\Book_KDP.inix`. A book already on KDP needs none: its details are read from KDP into `data\books`.

## The tools

Each runs from the project folder, and each writes its own log in `logs`:

- `scripts\buildBooks` -- builds and audits every book, or those named. A book is ready only when every check passes.
- `scripts\kdpBooks` -- reads every book's details from the KDP Bookshelf into `data\books`, and applies proposed changes to them.
- `scripts\kdpSubmit` -- fills in KDP's forms for a new book from its answers file, and submits it.
- `scripts\kdpUpdate` -- sends each ready book's EPUB and answers to its existing KDP title. A book unchanged since its last submission is left alone, and its pages on KDP are not opened: unchanged means its manuscript, cover, pictures and answers match, by content, never by file name or time. The everyday command is `scripts\kdpUpdate.cmd` with nothing after it: it builds any book that changed, then sends only the books that changed.

## Where the code comes from

The code lives in the kit, in its `scripts` folder, and nowhere else. Each tool's wrapper in a project, such as `scripts\buildBooks.cmd`, first copies the kit's current book tools into the project's `scripts` folder, as an app's build copies its kit tools, and logs each copy. So a fix made once in the kit reaches every book project on its next run. Without the kit on the computer, the copies already in the project run as they are.

## Personal data stays in the project

The kit's book tools hold no one's name, address, account or book. The author's name, the folders to search, a book's KDP title ID and every answer about a book come from the project's settings files and data. A project shares its own repository only if its author chooses to; its `data` folder, which holds what KDP holds, is the author's own.

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
