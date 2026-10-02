# What GitHub Pages and git need, and the failures behind each rule

## Contents

- Jekyll
- Encoding and git
- Branches and releases
- Reading a failed post

## Jekyll

- **Front matter must start on byte one.** A byte order mark before `---`
  hides it, and the page is published as plain text without the layout. post
  strips the mark from everything it stages; on disk the Homer encoding stays.
- **Pandoc and kramdown name headings differently.** Pandoc keeps periods and
  drops everything before the first letter ("the-.inix-format",
  "october-2026"); kramdown does neither. post writes Pandoc's id into every
  staged heading as `{#id}`, which both read, so one contents list serves the
  .htm and the page.
- **Liquid reads every page.** Text like `{{ secrets.TOKEN }}` or `{%` in a
  document stops the whole site from building. post wraps such a body in
  `{% raw %}` and `{% endraw %}`.
- **Hard wraps.** kramdown's GFM input turns every line break inside a
  paragraph into a `<br>` unless `hard_wrap: false`, and Homer documents wrap
  at 80 columns. post's `_config.yml` sets it.
- **A layout replaces the theme's.** `_layouts/default.html` is used instead
  of Cayman's, and `assets/css/style.scss` (with its empty front matter) is
  compiled with the theme imported first, so only the overrides need writing.
- **.htm files are served as they are.** Files without front matter are copied
  untouched, so the Pandoc .htm beside the page keeps every link that points to
  it working.

## Encoding and git

- Staged text is CRLF without a BOM, and `.gitattributes` says `* -text`, the
  kit's own rule: git leaves line endings alone and stops warning "LF will be
  replaced by CRLF". Images, icons, audio and fonts are marked `binary`.
- `.gitignore` names `_site/`, `.jekyll-cache/`, `.jekyll-metadata`,
  `.sass-cache/`, `*.log` and `Thumbs.db`.
- Files written for the GitHub API (the Pages JSON) must have no BOM, or the
  API rejects them.

## Branches and releases

- An app's `main` and tags belong to push and release. A page pushed to main
  would replace the code, and a release made from a document's version would
  collide with the installer's. So an app's page goes to `gh-pages`, force-
  pushed from a staging folder, and post makes no release.
- A page project's repository is the page: main, a release per version, and a
  description kept equal to "title: subtitle". The first run of the earlier
  postPage left the description as the folder name because the document had no
  front matter; post now updates it on every run.

## Reading a failed post

The log is `logs\<App>-post-yyyyMMdd-HHmmss.log`. Each command is one `run`
line with `exit=` and `ms=`, its output on `| ` lines beneath. Look for the
first `WARN` or `ERROR`. "pages build status=errored" quotes GitHub's own
message, usually a Liquid or front matter problem in the document.
