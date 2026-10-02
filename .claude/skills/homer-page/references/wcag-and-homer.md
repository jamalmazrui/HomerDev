# A page that meets WCAG 2.2 AA and the Homer conventions

These were learned publishing Blind Vibe Coding on 1 and 2 October 2026. The
kit's layout and stylesheet in `templates` already do all of it; this is what
to keep true when changing them, or when a project brings its own.

## Contents

- What the stock theme gets wrong
- Structure
- Links
- Color and focus
- Images
- Text and reading
- Homer rules that apply to a page
- How to check

## What the stock theme gets wrong

GitHub's Cayman theme, the kit's base, fails WCAG 2.2 AA as it stands:
headings are green on white at about 3.6 to 1 (normal-size text needs 4.5);
footer and quote text is gray at about 3.4 to 1; links are not underlined, so
color alone sets them apart (1.4.1); the header prints the site title as an h1
and the tagline as an h2 heading, so a document with its own h1 has two. The
kit's `style.scss` imports the theme and overrides each of these.

## Structure

- One h1, the title, printed by the layout. The subtitle is a paragraph, not a
  heading. The document's own headings start at h2 and never skip a level.
- Landmarks: a header, one main (`id="main-content"`, `tabindex="-1"` so the
  skip link moves focus there), and the footer inside main.
- A "Skip to main content" link is the first thing Tab reaches, visible when
  focused.
- `lang` on the html element, from the document's `lang` field.
- Every heading has an explicit id, so the contents list and the appendixes
  land where they say (post adds Pandoc's ids to the staged copy).

## Links

- Link text says where it goes; never a bare web address (the Homer rule).
  Repeated text such as "Read the transcript" is acceptable inside a resource's
  own list, where the context says which (2.4.4).
- Links in text are always underlined.
- Where the resource is a recording or a PDF, link straight to the file, and
  to a transcript when there is one.

## Color and focus

- Measure every pair of text and background colors, and note the ratio beside
  the color in the stylesheet. The kit's: white on navy 16.0, amber on navy
  8.7, teal headings 7.5, body text 13.4, muted text 7.3, links 7.2, visited
  links 9.0, all to 1.
- Focus is a 3-pixel navy outline with a white halo on light backgrounds and
  amber on the navy header: visible on both (2.4.7, 2.4.11).
- Respect reduced motion and forced colors (Windows high contrast) with their
  media queries.

## Images

- Decorative image beside text that says the same thing: `alt=""`.
- Meaningful image: alt text in the front matter, used by both the page and
  the link-preview tag.
- Never put words only in an image.

## Text and reading

- Atkinson Hyperlegible, the Braille Institute's typeface for low-vision
  readers, with Verdana as the fallback.
- Body text 1.1rem, line height 1.6, paragraphs at most 46rem wide, so a line
  stays under about 80 characters.
- The layout reflows on a narrow screen; nothing scrolls sideways at 320
  pixels (1.4.10).

## Homer rules that apply to a page

- Ninth-grade reading level and plain language; prefer lists to tables.
- Match the noun to the count; a field earns its line or is left out.
- Lists in alphabetical order unless another order is clearly more logical.
- On disk the document keeps the Homer encoding, BOM and CRLF; everything
  Jekyll reads is staged without a BOM (see jekyll-and-git.md).
- self.md and logs are never published.

## How to check

Read the page with JAWS or NVDA: the heading list (one h1, then h2s), the
landmark list, Tab from the top (skip link first), each image's alt text, and
the contents links. Run a contrast checker on any color you change. A dry run
lets you read the staged `index.md` before anything goes up.
