# The document set

## Contents
- ReadMe
- The app's guide
- Announce
- Developer
- History
- Hotkeys
- License
- The kit's own documents

## ReadMe

`ReadMe.md` at the top of the project, where GitHub and a person opening the
folder find it. A quick start: what the app does in two or three sentences,
how to install it (the direct link to `<App>_setup.exe` on the latest
release), how to start it (its desktop hotkey), the three or four things to do
first, and where the full guide is. No history, no build detail.

## The app's guide

`help/<App>.md`, the full reference, organized for navigation by heading:
H2 topic categories alphabetically ("Miscellaneous" last), H3 articles
alphabetically within each, H4 and below inside an article. Each command is
described with its key, its menu, and the word the key comes from. The
program opens it with F1.

## Announce

`help/Announce.md`: what is new in this release, for someone deciding whether
to update, in a few short paragraphs. Suitable for an email or a list post.

## Developer

`help/Developer.md`: how the app is built and released -- its layout, the
build and its steps, what it fetches, the kit classes it uses, the release
routine, and anything a maintainer must know that a user need not. May be
more technical than the other documents.

## History

`help/History.md`, opened by Shift+F1. Newest first; each entry headed with
the version and date; changes described for the user, with the reason.

## Hotkeys

`help/Hotkeys.md`, generated from the program's own command table by
`makeHotkeys.py` during the build, never kept by hand. Three H2 sections, each
with H3 groups: **by menu**, **by key** (grouped by modifier family, function
keys together) and **by command**. Every entry is one list item whose lines
are joined with a backslash hard break: the sorted-on thing, what it does,
then the other half of the pair. The memory association for each key is
written once, in the by-menu section; the rules behind the associations open
the document.

## License

`License.md` at the top: the MIT license verbatim, naming the app and Jamal
Mazrui as the copyright holder.

## The kit's own documents

The kit keeps the same set plus its guides: `help/HomerDev.md` (the kit's
full guide), the Camel Type style guides, `FinishPage.md`, `Logging.md`,
`Tutorials.md` and the migration briefing `HomerDev_update.md`.
