---
name: blind-creators
description: >-
  Maintains Jamal Mazrui's four companion reference directories of blind and
  low-vision creators: BlindAuthors.md, BlindDevelopers.md, BlindPresenters.md,
  and the consolidated BlindCreators.md (each with a matching .htm). Use this
  skill whenever the user asks to evaluate, vet, add, update, verify, or remove
  a person or work in any of these directories; to check whether someone
  qualifies as a blind author, developer, or presenter; to regenerate the
  consolidated Blind Creators listing; to audit a directory file for format
  and link problems; or to bump and package a new release — even if they only
  forward an email or name an app and ask "is this person worth listing."
---

# Blind Creators Directories

Four screen-reader-friendly Markdown reference guides, each published as a
GitHub Pages site and as a downloadable .md:

- **Blind Authors** — sole-authored books published 2000 or later, available
  today as electronic text or audio through a working link.
- **Blind Developers** — apps a blind or low-vision person created or led,
  reachable through a working link, actively developed or maintained in 2020
  or later.
- **Blind Presenters** — sustained leadership in time-based media (podcasts,
  talks, video, broadcast, film) from 2010 onward, with at least three solo
  public presentations.
- **Blind Creators** — one alphabetical listing consolidating the other three,
  so a person who writes, codes, and speaks appears once with every category
  under a single entry. It is generated, never hand-edited.

Read `references/inclusion-rules.md` before evaluating anyone. Read
`references/entry-formats.md` before writing or editing an entry. The two
scripts in `scripts/` do the mechanical work; each has a `.cmd` wrapper.

## The workflow for a candidate

1. **Identify the person and the work.** Emails and announcements usually name
   several people; only the creator of the work is a candidate. Forwarders,
   list moderators, and testers are not, unless they have their own work.
2. **Verify blindness or low vision positively.** A first-person statement by
   the person, a bio on their own site or store listing, or reliable reporting
   counts. "Builds tools for screen reader users" does not. Absence of
   disqualifying evidence is never enough (the default-No rule).
3. **Verify the work at a URL you actually opened.** Fetch the store page,
   repository, or publisher page. If it cannot be opened, the work is not
   mentioned in the document at all; the person may still qualify on another,
   verified work.
4. **Apply the category test** from `references/inclusion-rules.md`. Decide
   one of three outcomes: **include**, **pending** (evidence insufficient), or
   **excluded** (a confirmed disqualifying fact). Say which and why in chat.
5. **Gather the Profiles set**: website, GitHub, LinkedIn, App Store developer
   page, Wikipedia, podcast — every link opened, labels alphabetical.
6. **Draft the entry** in the exact format for that directory, with up to
   three works, newest first, each with a one-line description.
7. **Edit the source .md**, keep the person's alphabetical place (by surname,
   case-insensitive), update the count in the intro and subtitle, bump the
   version (new entry = minor; correction = patch), then run
   `checkDirectory.cmd` on the file.
8. **Regenerate Blind Creators** with `buildCreators.cmd` whenever any of the
   three sources changed, then check it too.
9. **Deliver** the changed `.md` files plus their `.htm` files (Pandoc) at the
   root of a single `files.zip`, and summarize the verification in chat.
   Verification notes, caveats, and dead-end searches never go in the
   documents.

## Running the scripts

Check one directory file (encoding, anchors, bare URLs, works per entry,
Profiles order, surname order, count claims) and optionally rebuild its .htm:

    checkDirectory.cmd BlindDevelopers.md
    checkDirectory.cmd BlindDevelopers.md --htm

Rebuild the consolidated listing from the three sources in the same folder
(the version bumps its minor number unless `--version` is given):

    buildCreators.cmd
    buildCreators.cmd --version v3.4.0 --htm

Both write a detailed log beside the script (`<script>-yyyyMMdd-HHmmss.log`).
The console stays short; the log has everything.

## Conventions (do not deviate without reason)

- **Encoding**: every `.md` and `.htm` is UTF-8 with a BOM and CRLF endings.
  (This SKILL.md is plain UTF-8 because YAML front matter must start at the
  first byte.)
- **File names**: CamelCase, no underscore — `BlindAuthors.md`,
  `BlindDevelopers.md`, `BlindPresenters.md`, `BlindCreators.md`. Older
  sessions used `Blind_Authors.md`; the underscore forms are retired.
- **Web pages** are `.htm`, never `.html`, produced from the `.md` by Pandoc.
- **Links**: reader-friendly text with the URL in the href; never a bare URL;
  never a URL that was not opened and confirmed.
- **Sorting**: people by surname, case-insensitive; Profiles by label; works
  newest first (the source order is what Blind Creators reproduces).
- **Nicknames, online names, and show names.** The owner's rule, following the
  Chicago Manual of Style, AP, and MLA: when a person is popularly known by a
  nickname, online name, or show name, put it in double quotation marks between
  the given name and the surname in the heading and everywhere the name is
  listed: Michael "Mick" Curran, Andre "Onj" Louis, Thomas "AnonyMouse"
  Domville, Tommy "The Blind Film Critic" Edison. Capitalize a descriptive
  epithet used as a name. Do not repeat the nickname in the bio. A handle-only
  person whose real name cannot be found is listed by the handle alone, with
  no quotation marks, since the handle is then the name (Dash); say in the bio
  that the person is also written as another form. Sorting still uses the
  surname (the last word of the name). Pen names for a different byline (Kim
  Nova writes as Kim Loftis) stay in the bio, not the heading.
- **Counts**: the subtitle and the intro state how many people are listed;
  match the noun to the count. Every count in the text must equal the number
  of entries, and the Blind Creators intro and conclusion must agree.
- Prefer lists to tables; write at a ninth-grade reading level without losing
  accuracy; no editorial commentary inside the documents.

## Gotchas learned the hard way

- **Self-description in a store listing counts; a reviewer's guess does not.**
  "Built by a blind developer" written by the developer in their own App Store
  text is positive evidence. A tester saying "I think he's blind" is not.
- **Team products need a named lead.** A person listed as "the team" behind
  an org's app is pending until a page names them as creator or lead.
- **Co-created works** are shown as "Title (co-created with Name)" and count
  toward inclusion only if the person also has at least one work of their own.
- **A person may be in one directory and belong in another.** Check all three
  before adding; a developer who also hosts a podcast gets a Presenters entry
  only if the presenter test passes on its own.
- **Forwarded emails may be UTF-16.** Saved Outlook .htm files sometimes are;
  if the text looks like letters separated by nulls, decode as UTF-16 before
  reading. Only the person who built the work is a candidate; forwarders,
  list owners, event chairs, and testers are not.
- **Contributions to someone else's product are not apps.** A patch or feature
  merged into a large product (a screen-reader help feature in an editor, a
  fixed fork of a library) does not show that the person created or led an
  app. Look for a product that is theirs.
- **Handle-only people.** The owner has ruled that when no real name can be
  found, the online name is used (see the nickname convention above). Still
  gather the person's own first-person evidence before listing.
- **A link seen only inside an email is not verified.** Search for the page
  and open it before it goes in a document; otherwise leave that work out.
- **Appendix order follows the title rule.** In every appendix list, sort
  case-insensitively ignoring a leading A, An, or The, and strip the link
  markup before comparing so a closing bracket does not decide the order.
  Older editions sorted some appendixes by the raw title; re-sort a group
  whenever you add to it and say so.
- **Offering development services is not a published app.** Someone who sells
  custom software to blind users needs at least one app of their own at a
  working link before they can be listed; the service announcement alone is
  pending.
- **Beware namesakes.** A famous programmer or author with the same name is not
  the candidate. Confirm identity from the person's own page before using any
  biography.
- **A family member on a product team is not verified.** Being named among a
  company's developers says nothing about blindness; look for the person's own
  statement.
- **Co-hosted work does not count toward the three solo presentations.** A
  co-hosted podcast can establish a series, but the three that qualify a
  presenter must be theirs alone; find recordings of solo talks, solo episodes,
  or her or his own sessions.
- **Real names.** When the owner asks for a real name and no page the person
  controls gives one, do not guess or infer it from an email address; report
  what was checked and ask the owner to supply it.
- **Future events do not count.** A talk announced for next week is not yet a
  public presentation.
- **Blind Creators must be regenerated, not patched.** Hand edits are lost on
  the next build; put the change in the source directory instead.
- **Duplicate surnames** get disambiguated anchors (`cr-adams-kirk`,
  `cr-adams-nicholas`); the build script does this automatically.
