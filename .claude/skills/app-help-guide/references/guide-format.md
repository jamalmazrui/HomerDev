# The guide format, the categories and the gates

## Files

`<Product>.md` and `<Product>.htm`, the second built from the first with
Pandoc:

    pandoc Product.md -f markdown -t html5 --standalone --toc --toc-depth=2 -o Product.htm

The name is upper camel case and spells out abbreviations, unless the
abbreviation is the name people use: `KindleDirectPublishing.md`, but
`BARD.md`, `NVDA.md`, `ESPN.md`.

## Headings

- `h1` the guide title, once.
- `h2` a topic category. Alphabetical, except `Miscellaneous`, which is last.
- `h3` an article title. Alphabetical inside its category.
- `h4` and below: the headings inside an article, pushed down to fit.

A category needs **two articles** or it folds into `Miscellaneous`. Before
folding, ask whether the category is wrong rather than the count: a single
article about payments belongs with the rest of what the product does, not in
a drawer.

## The contents list

Every article, grouped by category, in the same order as the body, each a link
to its own anchor. The gate below checks that the two agree.

## The preamble

Three or four sentences, no more:

- What the guide holds and when it was gathered.
- What it deliberately leaves out, and why — translated editions, developer
  material, a changelog, a forum.
- Any sibling guide in the collection, so a reader can find the other half.
- Any caution the reader needs before acting: a product that spends money, a
  guide that will age quickly, an exception to the collection's own rules.

## The gates, run before anything is delivered

- **Contents matches articles**, in number and in order.
- **No heading jumps a level** (h2 to h4 is a fault).
- **No duplicate anchors.** Where two articles share a title, disambiguate in
  the title itself rather than leaving two identical links.
- **No bare addresses** in the text.
- **Dollar signs escaped**, or Pandoc reads them as broken mathematics.
- **The median article word count** is reported. A median in the low tens
  means the harvest caught menus rather than articles.
- **The HTML pair builds** and carries its own contents page.

## Furniture

Remove the publisher's furniture by NAMING it, never by condemning words. The
feedback widgets — Zendesk's *Was this article helpful?*, Intercom's *Did this
answer your question?*, HelpDocs' five-line apology, Amazon's *Was this
information helpful?* — go, and their Yes and No only when adjacent to the
question. `cleanFeedback.py` does this and logs every line it removes.

**A heading is furniture only when it is one of those named phrases.** An
article's own title is never furniture: an early filter once ate a page called
*Table of Contents* because the rule was about words rather than about
publishers.
