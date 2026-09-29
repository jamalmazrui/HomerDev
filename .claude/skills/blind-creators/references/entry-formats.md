# Entry Formats

Copy these shapes exactly. Every file starts with YAML front matter, then an
H1, an intro, a Table of Contents, the entries, and appendixes. Anchors are
explicit Pandoc/kramdown attributes in braces so they survive both GitHub
Pages and Pandoc.

## Front matter (all four files)

    ---
    title: "Blind Developers"
    subtitle: "35 Creators of Apps While Blind or Low Vision"
    author: "Jamal Mazrui"
    version: "v2.20.1"
    lang: en
    ---

The subtitle carries the count. Blind Creators uses a fixed subtitle,
"Authoring Books, Developing Apps, or Making Presentations While Blind or Low
Vision", and states its counts in the intro instead.

## Blind Developers entry

    ### Firstname Lastname {#dev-lastname}

    One or two sentences on who they are and what they build.
    Profiles: [GitHub](https://...), [LinkedIn](https://...), [Website](https://...).

    #### [App Name](https://where-to-get-it/) {#app-slug}

    One sentence on what the app does, for whom, and on which platforms.

    #### Unlinked App Name {#app-slug}

    A work with no working public link is written without a link, and only
    when it is verified some other way (a store listing that will not open
    for Claude is still a working link for the reader; a rumor is not).

Rules: up to three `####` works, newest first. A co-created work reads
`#### [NVDA Remote](https://...) {#nvda-remote}` with "co-created with
Christopher Toth" in its description, and a second developer's entry may point
back: `#### NVDA Remote (co-created)` with "see the full entry under
[NVDA Remote](#nvda-remote)". The Profiles line ends with a period and lists
labels alphabetically. The Table of Contents lists developers alphabetically
by surname; a "Projects by Platform" appendix groups every work by platform,
ordered by title, in the form `- [App (Lastname)](#app-slug)`.

## Blind Authors entry

    ### Firstname Lastname {#auth-lastname}

    One or two sentences on who they are.
    Profiles: [Amazon](https://...), [Goodreads](https://...), [Website](https://...).

    #### [Book Title: Subtitle (2021)](https://where-to-buy-or-read/) {#book-slug}

    One sentence on what the book is.

Rules: the year of first publication in parentheses inside the link text;
up to three books, newest first; every book at a working digital-edition
link. Appendixes list books by title and by year.

## Blind Presenters entry

    ### Firstname Lastname {#pres-lastname}

    One or two sentences on who they are.
    Profiles: [Podcast](https://...), [Website](https://...), [Wikipedia](https://...).

    #### [Series or Talk Title (2015)](https://...) {#work-lastname-slug}

    One sentence on the work and the role held.

Rules: up to three works; a year in parentheses where a single talk or a
series start date is known; a "Media by Type" appendix groups works under
Podcasts and audio, Video and online series, Television and film, Talks and
keynotes, Broadcast — ordered by title, in the form
`- [Title](#work-slug) — Firstname Lastname`.

## Blind Creators entry (generated)

    ## Firstname Lastname {#cr-lastname}

    Bio (the longest bio found across the three sources).

    Profiles:

    - [GitHub](https://...)
    - [Website](https://...)

    ### Apps

    - [App Name](https://...) — One-line description.

    ### Books

    - [Book Title (2021)](https://...) — One-line description.

    ### Presentations

    - [Series Title](https://...) — One-line description.

Rules: people are H2, categories are H3 in the fixed order Apps, Books,
Presentations, and a category appears only when the person has work in it.
Works are bullet lines, up to three per category, in source order. Duplicate
surnames get `cr-lastname-firstname` anchors. The intro states the total, the
per-category counts, how many people span two categories and three, and names
those in all three; the conclusion repeats the total and the multi-category
count. The build script computes all of these.

## Anchor slugs

- Person: `dev-`, `auth-`, `pres-`, `cr-` plus the surname in lowercase ASCII
  (`odonoghue`, `polykanine`); add `-firstname` only to break a collision.
- Work: a short lowercase ASCII slug of the title (`nvda-coach`,
  `tg-drop-deck`); it must be unique within the file. A work whose title
  starts with a digit gets a letter prefix (`app-2htm`).

## Names and sorting

- Surname is the last word of the name, ignoring a trailing parenthetical
  such as "(d. 2020)". "J.J. Meddaugh" sorts under Meddaugh; "T. V. Raman"
  under Raman; "Gary O'Donoghue" under Odonoghue.
- Sorting is case-insensitive; accents are folded (André sorts as Andre).
- A nickname in quotation marks sits between the given name and the surname
  (Michael "Mick" Curran) and does not change the surname sort. A handle-only
  person is listed by the handle with no quotation marks (Dash) and sorts under
  it.
