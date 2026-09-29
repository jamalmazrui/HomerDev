# Fence faults, each of which has cost a run

A fence is the regular expression saying which addresses belong to an estate.
These are the mistakes this project has actually made, in the order they cost
the most time.

## A negative lookahead needs no leading slash

Writing `/help/(?!/badges/)` never fires, because after `/help/` the remaining
text is `badges/25/civic-duty` with no slash in front of it. **Cost: three
runs** — Ablr, the Khan Academy forum, and Stack Overflow, where 445 of 600
pages gathered were badge descriptions.

Write `(?!badges)`, and test it with a predicate before shipping.

## A language edition hides in three places

1. **A path segment** — `/fr/`, `/de/`.
2. **An underscore form** — calibre publishes `/zh_CN/` and `/pt_BR/`, which a
   hyphen-based list misses entirely. **128 translated pages** got through.
3. **A file name** — HumanWare publishes `AR-UG-Stream3V14.html`, with the
   language nowhere in the path.

And a publisher may file a **German edition under the English name**, which no
address rule can catch. Where it matters, decide by READING the page: keep a
document only when its own contents heading is in the language you want.

## A seed refused by its own fence

A tightened fence that demands a page name ending in `.html` refuses the bare
directory that is the first seed, and the run gathers nothing. Every generated
harvester tests its seeds against its own fence before starting and stops
loudly, because a silent nothing once went unnoticed for two rounds.

## A wiki links every version of every page

A GitHub wiki offers each page's whole revision history, each at an address
ending in a forty-character hash. **115 of 120 pages** gathered from the NVDA
add-on guide were past revisions of the same document. Refuse `_history`,
`_edit` and any forty-character hexadecimal segment.

## A site serves its own source beside every page

Bitwarden publishes the Markdown source of every help page at the same address
with `.md` appended: **334 of 672 pages** were each article a second time.

## A fence that admits a magazine

Angi's help lives at `/faq`, but `articles/[a-z0-9-]+\.htm` — written thinking
of help articles — admitted its library of **eleven thousand home-improvement
pieces**. Name what you mean.

## A subject gate is not a fence

Microsoft's accessibility section holds Teams, Word and Excel pages whose own
headings say "use a screen reader to…", so a subject gate on *screen reader*
keeps them. **61 of 120 pages** gathered for Narrator were other products. The
gate was working; the fence was too wide.

## The city-site problem

Craigslist runs hundreds of city sites, each serving the same help under its
own name. One copy is the volume; four hundred copies is a mistake. The same
shape appears wherever a network gives every member its own host.
