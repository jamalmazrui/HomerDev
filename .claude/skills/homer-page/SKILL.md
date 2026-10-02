---
name: homer-page
description: >-
  Publishes a Homer project's document as a GitHub Page that meets WCAG 2.2 AA
  and the Homer conventions, with the kit's post script: front matter, one h1,
  heading ids that work in both Pandoc and GitHub's kramdown, an accessible
  layout and stylesheet, a logo, a hero image with alt text, favicons, the
  gh-pages branch for an app or the main branch for a page-only project, and a
  check of GitHub's build. Use this skill whenever the user wants to post,
  publish, host or update a GitHub Page, a github.io site or a web version of a
  guide, directory or help document; asks to add an image, logo or favicon to
  such a page; or asks whether a published page is accessible, even if they
  only say "postPage", "post it" or "put it online".
---

# Homer page

A Homer project publishes a document as a web page with one command, `post`,
run in the project folder. The script lives in the kit at `scripts/post.cmd`
and `scripts/post.ps1`; an app that uses it adds `post.cmd post.ps1` to
`kitTools` in its build script, and each build refreshes them into its own
`scripts` folder. Read `scripts/post.ps1` in the kit for why each step is
there; run it rather than repeating its steps by hand.

Before changing a page's design, read
[references/wcag-and-homer.md](references/wcag-and-homer.md). Before
diagnosing a failed post, read
[references/jekyll-and-git.md](references/jekyll-and-git.md).

## Four kinds of resource

post asks the kit's kind.py what the folder holds, as every kit script does
(`kind` in a folder says it aloud, with the fact that decided it):

- **An app, a collection or the kit** is a repository whose `main` and tags
  push and release own. post publishes to the `gh-pages` branch only, never
  makes a release, takes the owner and name from the `origin` remote, and
  refuses `-Branch main`. The page is `help/<App>.md` for an app or the kit,
  and the ReadMe for a collection, with its .htm documents beside it.
- **A page** (such as `C:\BlindVibeCoding`, which need not be a repository)
  is its own repository: post creates it if needed, publishes to `main`, sets
  its description to "title: subtitle", and makes a release named by the
  document's `version` when that release does not exist yet.
- **Unknown**: post publishes nothing and says to run `kind`.

## The steps

1. **Front matter first.** The document needs, at minimum:

       ---
       title: "Blind Vibe Coding"
       subtitle: "Building Apps Nonvisually with AI"
       description: "One plain sentence for search results and link previews."
       author: "Jamal Mazrui"
       date: "October 2026"
       version: "v1.1.0"
       lang: en-US
       license: "CC BY-SA 4.0"
       license_url: "https://creativecommons.org/licenses/by-sa/4.0/"
       ---

   The license is MIT for an app or the kit and CC BY-SA 4.0 for a page or
   a collection (HomerDev.md, "Licenses for each kind"); the footer shows it,
   and one sentence in the text names it for the .htm. Optional, for the kit's layout: `logo` (an SVG shown beside the title with
   empty alt, and used as the favicon), `icon_png` (32 by 32), `touch_icon`
   (180 by 180), `image` (a hero illustration), `image_alt` (its alt text,
   required with `image`), and `social_image` (a 1200 by 630 PNG for link
   previews, described by the same `image_alt`). Paths start with `/assets/`.
2. **No body h1.** The layout prints the title as the page's one h1, and
   Pandoc makes the .htm's h1 from the same title. post removes a first-line
   `# Title` from the staged copy, but the source is cleaner without it.
3. **Site files in their place.** In an app: `help/site/` holding `assets/`
   (images in `assets/images`, named `<App>-logo.svg` and so on), and
   `_layouts/` or `_includes/` only to override the kit's. In a page project:
   the same folders at the top. With neither layout nor stylesheet, post uses
   the kit's, from this skill's `templates` folder.
4. **Rebuild the .htm** with the project's build (or Pandoc), so the .htm
   files staged beside the page are current; links from the page to them must
   keep working.
5. **Dry run.** `post -DryRun` stages everything into `%TEMP%\<App>_page` and
   stops. Read the log; check the staged `index.md` for the ids and the h1.
6. **Post.** `post`. The console says what was staged, pushed and published;
   the log, `logs\<App>-post-yyyyMMdd-HHmmss.log`, says everything else.
7. **Confirm.** The script waits up to three minutes for GitHub's build and
   reports "built" or GitHub's own error. Then open the page and check it with
   a screen reader: one h1, landmarks, the skip link, the images' alt text.

## Images

- The logo beside the title is decorative there: `alt=""`, since the title
  says the same thing. A hero illustration carries meaning: write alt text that
  says who is shown and what they are doing, in one or two sentences.
- Keep every image as SVG for the page and a PNG for link previews and
  favicons. Render the PNGs from the SVGs; never hand-draw them twice.
- Show real assistive technology accurately. A long white cane like the NFB's
  is straight white fiberglass, with a loop at the handle and a metal glide tip.
  Braille cells keep more space between cells than between a cell's dots.

## Exit codes

0 published (or dry run done); 2 git or gh missing; 3 no GitHub origin, or
main named for an app; 4 gh not signed in; 5 no document, or self.md named;
6 commit or repository creation failed; 7 push failed; 8 Pages could not be
pointed at the branch; 9 release failed; 10 GitHub could not build the page;
99 anything unexpected, with the stack in the log.
