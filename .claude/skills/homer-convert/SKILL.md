---
name: homer-convert
description: >-
  Converts files between any two types the Homer way, through the HomerDev
  kit's one shared Conversion (Conversion.cs and conversion.py): documents
  (Word, PDF, EPUB, Markdown, .htm, text, RTF, OpenDocument), tables (Excel,
  CSV, TSV, .inix, SQLite .db in DbDo's form), audio and video (mp3, mp4, mkv,
  wav and more, transcripts and spoken documents), and records (contact cards
  .vcf, calendars .ics, playlists .m3u .pls .xspf, feed lists .opml, subtitles
  .srt .vtt). Every file made is finished for a screen reader. Use when asked
  to convert, export or import a file, change a file's format, make the .htm of
  a .md, add a conversion to an app or to the route table, or work out why a
  conversion took the way it did.
---

# Converting files

Every Homer app converts with the same code: the kit's Conversion, which reads
its ways from exec\conversions.inix (help\Conversions.md has the whole story).

- **Any two types.** The table names the best direct ways. A pair it does not
  name, or whose every way fails, goes in two of its own steps through a hub:
  Markdown, else a web page, else a table of comma-separated values. So a contact
  card reaches Excel (vcf2csv, then csv2xlsx) and a PDF reaches PowerPoint.
- **Each way best first.** Each step of a way is judged by the type it is handed,
  and the log names every way tried and why one was passed over. A route table
  found away from the program is logged as a warning: an older installed kit's
  table once quietly took BatCon's PDFs away from Edge.
- **PDF without Office:** Edge prints a web page to a tagged PDF; Word's export,
  with structure tags, is the last resort.
- **Two scripts both languages run, word for word:** SQLite (a .db in DbDo's
  form, and back to Markdown) and records (contact cards, calendars, playlists,
  feed lists and subtitles, to and from a table). The kit's build fails if the
  C# and Python copies differ.
- **Media** -- audio and video among themselves, a transcript from either, a
  document spoken as audio or video -- goes through ffmpeg, Whisper and the
  kit's voices (ConversionMedia.cs).
- **Every file is finished, then checked:** title, author and language, workbook
  header names and layout, table header rows, front matter, EPUB accessibility
  metadata, tagged PDF; what a person must fix is logged under extCheck's rule
  names. The homer-quality skill runs the same checks on any file.
- **.htm, never .html,** for a page a Homer program makes; settings and data in
  INI form are .inix. Text results are UTF-8 with a byte order mark and CRLF.

## Which tool

- **Converting a file from one type to another inside a Homer program**: never
  call Pandoc or Office from the app. Use the kit's shared engine,
  `exec\\Python\\conversion.py` -- `convert(source, target)`, `toText(source)`,
  `plan(source, type)` -- which takes its routes from `exec\\conversions.inix`:
  only approved components (Pandoc, NuGet and PyPI packages, Tesseract), plain
  text by the quickest way, Office only as the last resort. No other converting
  program is looked for, offered or installed. The C# twin, `Conversion.cs`, reads the same table. A route that is
  missing goes into the table, not into the app.

- **A Homer document, Markdown to .htm** (every .md in a Homer project has
  one): Pandoc, reading Pandoc's own Markdown.

  ```
  pandoc -f markdown -t html5 --standalone --metadata title="History" -o help\History.htm help\History.md
  ```

  Give a title (or a `title:` in the file's front matter), or Pandoc warns and
  guesses one. A long document takes `--toc`. A paragraph holding only
  `\pagebreak` is a page break: add `-L pagebreak.lua` (the pandoc-ext filter).
- **Word, Excel, PowerPoint, PDF, CSV, JSON, HTML, Markdown or text, to
  accessible .htm or .txt**: 2htm, which keeps the headings, lists, tables
  and reading order a screen reader needs.

  ```
  2htm --force -o out report.docx slides.pptx *.xlsx
  2htm --plain-text C:\docs\*.pdf
  ```

  It reads .docx .doc .rtf .odt, .pdf (through the kit's PDF reader, with OCR
  for scans; no Word needed), .xlsx .xls, .pptx .ppt, .csv, .json, .htm .html,
  .md and .txt. It skips an output that exists unless `-f`
  (`--force-replacements`); `-i` drops images; logging is automatic.
- **A table between .inix, .csv, .tsv, Markdown and .xlsx**, in any direction:
  inixVert. `.inix` is the screen-reader-friendly form: one `[RecordNNN]`
  section per row, one `field = value` line per field.

  ```
  inixVert contacts.xlsx contacts.inix /quiet
  ```

  Exit code 0 is success, 3 a failed conversion, 4 bad arguments; the log is
  inixVert.log beside the program. From a .md or .mdx to .md or .txt it
  expands fenced `inix` blocks into Markdown tables instead.
- **Anything else Pandoc reads and writes** (EPUB, DOCX to Markdown, reStructuredText,
  AsciiDoc, LaTeX, MediaWiki, RTF): Pandoc with `-f` and `-t`. EdSharp's
  Import and Export tables hold a tested command for each pair; see
  [references/conversions.md](references/conversions.md).

In a program, prefer the kit to a shelled-out tool where it can do the job:
`Inix` (C#) or `inix` (Python) converts tables, and the conversion engine
reads a PDF's text, or its text with headings worked out from type sizes.

## Encoding

Read input with encoding detection (Ude in the kit), never assuming UTF-8.
Write output as UTF-8 with a byte order mark and CRLF line endings. Pandoc and
most tools write UTF-8 without the mark and with bare line feeds, so put each
file they write into the Homer encoding afterwards:

```bash
python scripts/toHomerEncoding.py help/History.htm
```

It takes files, folders or wildcards, leaves `.cmd`, `.bat` and SKILL.md
without the mark as the Homer rule says, and reports what it changed.

## Check the result

- A Homer document's .htm is rebuilt from its .md whenever the .md changes;
  never edit the .htm by hand.
- A converted document meant for others can be checked with extCheck (Word,
  Excel, PowerPoint and Markdown) before it goes out.
- Open the output, or read its headings, to confirm the structure survived:
  a document whose headings became bold paragraphs has lost what a screen
  reader navigates by.
