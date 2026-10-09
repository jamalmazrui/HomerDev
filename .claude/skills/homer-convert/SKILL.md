---
name: homer-convert
description: >-
  Converts documents and data between file formats the Homer way: Markdown to
  .htm with Pandoc, Word, Excel, PowerPoint, PDF, CSV, JSON and HTML to clean
  .htm or .txt with 2htm, tables among .inix, .csv, .tsv, Markdown and .xlsx
  with inixVert, and the rest with Pandoc, always writing the Homer encoding.
  Use when asked to convert, export or import a file, make the .htm copy of a
  .md, turn a document into accessible HTML or plain text, or move a table
  from one format to another, for Homer documentation or for a user's own
  files.
---

# Converting files

Pick the tool by what is converted, write the output in the Homer encoding,
and check the result. Web pages are `.htm`, never `.html`; settings and data
in INI form are `.inix`.

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

  It reads .docx .doc .rtf .odt, .pdf (through Word's PDF Reflow, so Word
  must be installed), .xlsx .xls, .pptx .ppt, .csv, .json, .htm .html, .md and
  .txt. It skips an output that exists unless `--force`; `--strip-images` drops
  images; `-l` writes 2htm.log beside the output.
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
