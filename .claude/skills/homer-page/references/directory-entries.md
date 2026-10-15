# Directory entries

These rules apply to every Homer directory: a GitHub Page that lists works,
such as Blind Skills, Tech Training, Blind Presenters or a podcast directory.
They came from Jamal Mazrui's review of Blind Skills on 15 October 2026 and
hold for every directory from then on. A directory's own builder or post step
applies them in code; this file says what the code must produce and why.

## The shape of an entry

Each entry is a level-3 heading whose title links straight to the work: the
audio file or the video page, so a player can take the title with the address.
Under it, in this order:

1. A description of one or two sentences, in a paragraph of its own.
2. A Source page link, in a paragraph of its own, when one exists.
3. A Transcript link, in a paragraph of its own, when one exists.
4. The remaining fields, one to a paragraph, in alphabetical order.

## The rules, in alphabetical order

**Description.** One or two sentences in a paragraph right after the heading,
with no "Description:" label: a paragraph just under a heading already
describes it, so a label only adds a word for a screen reader to say. A
publisher's long summary is cut to its first two sentences.

**Fields.** Each field is its own paragraph, written `**Label:** value`, and
the fields come in alphabetical order by label. A field is shown only when a
real value is known; an empty field, or a word standing for empty, is left out.

**Length.** The field is called Length, not Duration, since it is fewer
syllables. Its value is whole minutes, rounded, with no "about": "Length: 4
minutes", "Length: 1 minute". Seconds do not matter for choosing what to play,
and everyone understands that a length is rounded. A play list may still carry
the length in seconds, which is what the M3U format wants.

**Links.** A source page and a transcript are links whose text says what they
are: `[Source page](address)` and `[Transcript](address)`, each in a paragraph
of its own after the description. "Source page: Source page" says the same
thing twice, so neither link gets a label. Every directory says Source page,
including a podcast's page for one episode.

**Near-constant fields.** A field whose value is almost always the same, such
as Medium when nearly every entry is a video, is dropped: it tells a reader
little and costs a line in every entry. When the value can be derived, keep
deriving it in code (an address ending in .mp3 is audio) rather than showing
it. An appendix that groups entries by such a field goes with it.

**Presenter.** The label stays singular, Presenter, however many people it
names, and the names keep the order the source gives them. A list of
"Presenter, Presenter" would be no clearer for being called Presenters.

**Required values.** When a directory says a field is required, as Blind Skills
requires Length and Year, an entry that lacks it is left out rather than
listed with a guess. The tool that fills the value reads it from the work
itself (yt-dlp for a video, ffprobe for an audio file), keeps each answer so it
is read once, and names every entry it leaves out in a file in the project's
data folder, so the decision can be reviewed. When the tool itself cannot run,
nothing is left out: the run stops instead.

**Statistics.** A directory opens its By the Numbers section with a few
observations a reader would find notable, computed from the entries, never
typed by hand: what is largest, how long the works run, where most come from,
how recent they are. A count anyone can see in the table of contents, or an
observation nobody would repeat, is left out. A total is shown only when every
entry is counted in it, so a directory part-way through completion never
states a partial sum.

**Subtitle.** Every directory's subtitle begins "A Directory of" and its count, then says what is counted: "A Directory of 144 Resources for Travel, Recreation, and Tourism While Blind or Low Vision". The count comes from code, never typed: a directory's builder writes it, or, for a page written by hand, the post step counts and corrects it. Leave the subtitle out of `pagetitle`; the page layout forms the window title from the title and subtitle, so a second copy only goes stale.

**Year.** The year is the one the publisher states. Where the publisher states
none, the year a video host shows the work was posted is the year, since it
comes from the platform and not from a guess. A year read from a search index
is not used.
