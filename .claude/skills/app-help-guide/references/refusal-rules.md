# When to refuse, and how to say so

A refusal backed by evidence is worth as much to the collection as a guide. It
stops the same estate being attempted again, and it tells the reader something
true about the product.

## The four shapes of a closed door

1. **Browser-drawn.** A plain request returns the frame and none of the words.
   *Signature*: several different addresses return the SAME word count — the
   site is serving one shell for every path. Tripadvisor, Disney+, Thumbtack,
   YouDescribe.
2. **Defended by silence.** The host never answers. Adobe and REI both timed
   out at ninety seconds, twice.
3. **Behind a sign-in.** Vanguard's help; Angi's staff desk, which redirects to
   a single-sign-on page.
4. **The request itself refused.** Every address answers 400. The page exists
   and the host is awake; what is being judged is the connection. Meta, on
   nine addresses across four hosts.

## The other refusals

- **A listing is not help.** An App Store or Play page describes a product to a
  buyer.
- **An announcement is not help.** A newsroom post may be the fullest official
  description of a product and still belongs under a heading that says so.
- **A programme archive is not help.** A television show publishes episodes.
- **A forum is not help.** Users answering each other is a different thing,
  however good the answers. Name the exception if you make one.
- **Too thin to hold its own name.** MakeMKV's whole site came to 938 words,
  70 of which were a PHP error. A guide that small misleads a reader who opens
  it expecting coverage.
- **No help at all.** Six small accessibility apps in a fortnight published an
  App Store listing, a privacy policy and nothing else. Say so plainly, and say
  it is no reflection on the app.

## The browser fallback

For an estate that is refused AND small, drive Edge with `--dump-dom`: it loads
the page, waits for it to settle, prints the finished document and exits. One
command per page, no debugging port, about two seconds a page.

Headless is enough — the checks that refuse a plain request are about the
connection, not about whether a window is drawn.

**Do not use it for large estates.** At two seconds a page, a thousand pages is
an evening, and the run will probably stop halfway.

## Scope: who the reader is

This collection is for people USING software, not building it. A command-line
option or a configuration file belongs in a guide however technical it looks; a
scripting interface, a plugin header, a braille library or a game engine does
not.

**The exception is screen-reader scripting** — JAWS and NVDA — because
scripting a screen reader is how a blind user makes an inaccessible program
usable. State the exception in the guide's own preamble rather than leaving it
implied.

## What never goes in

Anything not published by the product's own maker. Third-party blogs, review
sites and tutorial mills may be accurate and are still somebody else's words.
Where only third-party material exists, the honest answer is that the product
publishes no help.
