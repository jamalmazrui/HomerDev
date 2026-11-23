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
   nine addresses across four hosts. Edge is no way round it when the wall
   judges the browser too: Home Depot gave Edge its customer service hub, a
   page of 406 words that is only links, and then an "Error Page" of 83 words
   for every help page after it (17 November 2026). Refused, not retried.

## The other refusals

- **A listing is not help.** An App Store or Play page describes a product to a
  buyer.
- **An announcement is not help.** A newsroom post may be the fullest official
  description of a product and still belongs under a heading that says so.
- **A programme archive is not help.** A television show publishes episodes.
- **A model is not a product.** Gemini 4 Argon, announced on 30 September
  2026 and first offered to cybersecurity partners, is a model that reaches
  readers inside Gemini; its help, when there is any, belongs in the Gemini
  guide. Coverage of the announcement is news, not help.
- **A forum is not help.** Users answering each other is a different thing,
  however good the answers. Name the exception if you make one.
- **Too thin to hold its own name.** MakeMKV's whole site came to 938 words,
  70 of which were a PHP error. A guide that small misleads a reader who opens
  it expecting coverage. OOrion (23 November 2026, third try): oorion.fr has no
  help centre; its French application page holds about 1,000 words on each
  feature, but the English edition answered "Oops this page does not exist" to
  Edge, and the English front page holds 244 words, mostly a description. An
  English guide would be a few paragraphs, so OOrion is refused until it
  publishes English help. PiccyBot, the same day, passed: one page, but with
  setup steps for WhatsApp and Meta's glasses and the plans, about 1,200 words
  once its welcome, testimonials, honors and donations were left out.
- **No help at all.** Six small accessibility apps in a fortnight published an
  App Store listing, a privacy policy and nothing else. Say so plainly, and say
  it is no reflection on the app. Publications can be the same: MakeUseOf and
  How-To Geek (both Valnet) have an About page, a Contact form, a newsletter page
  and a Premium page with no questions on it; Parade has About, Contact and
  policy pages, and its newspaper insert's delivery questions belong to each
  newspaper (17 November 2026). Their articles teach skills, but a library of
  how-to articles is the publication's work, not help for using it. Tom's
  Guide (Future) is the same: About, Contact, policies, newsletters and a club
  sign-up, no help. The rule for every how-to site: gather its help for using
  the site, if it has any, never its articles. A store that also publishes how-to
  articles is the reverse case: Home Depot's customer service pages are help for
  shopping there, and its DIY project library stays outside the fence.
- **Already held under another name.** Every Stack Exchange site serves Stack
  Overflow's help centre with its own name put in, so the StackOverflow guide
  covers Stack Exchange, as its preamble says (17 November 2026).

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
