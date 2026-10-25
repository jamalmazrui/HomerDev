---
title: "Homer Conversions"
author: "Jamal Mazrui"
---

Every Homer app converts files through one shared copy of the code: Conversion.cs in C#, conversion.py in Python, and one routing table both read, exec\\conversions.inix. This page explains the design and records which engine each conversion uses and why.

## Names and Routes

Each conversion is named by its source and target types, joined by a 2: pdf2txt, pdf2docx, docx2md. The routing table has one section per conversion. Its ways line lists the engines to try, best first; the first whose engines are all present is used. A way can take steps, as in pdfstructure:md > pandoc, which makes Markdown and then hands it to Pandoc.

Both the source and the target decide the way. A plain text target wants speed, so pdf2txt reads only the PDF's text layer. A Word target wants structure, so pdf2docx works out headings, lists and tables first.

## Engines

Each engine is either internal code, which starts no program and is the quickest, or an outside program, used where its quality is worth the start-up time.

- **copy** (internal): the file as it is.
- **edge** (outside, comes with Windows): Microsoft Edge prints a web page to a tagged PDF, headless and with a profile of its own, so a PDF needs no Office (kit 1.90.0). Whether every Edge version tags the PDF is unconfirmed; test a result with a screen reader.
- **ocr** (outside): Tesseract reads a scanned page. In C#, the kit's PdfReader runs it, so a scanned page gets headings and lists too; in Python, pypdfium2 draws each page for it. Never used for a quick read, since it can take minutes.
- **officecom** (outside, last resort): Microsoft Office through COM. Used only where nothing free will do. When Office is needed and missing, an Alert box says so once per session, and says how to avoid it.
- **pandoc** (outside): Pandoc, for the markup and document formats it reads and writes.
- **pdfstructure** (internal where it can be): a PDF's headings, lists and reading order. In C#, the kit's PdfReader, HomerScribe's reader, in an app that compiles PdfReader.cs and ConversionPdf.cs with PdfPig; otherwise pymupdf4llm through Python. A document of scans fails it, so OCR reads it next.
- **pdftext** (internal when it can be): a PDF's text layer. PdfPig in-process when PdfPig is beside the program; otherwise PyMuPDF's plain text through Python.
- **sqlite** (outside, Python): a table to an SQLite database, one table named after the file with its fields from the first row, or a database to Markdown, each table under its own heading (kit 1.90.0). Python has SQLite built in and the kit has none of its own, so both languages run the same short script; the kit's build fails if the two copies ever differ.
- **table** (internal): rows and columns, through the kit's Table class, with cells placed by their references.
- **zipxml** (internal): the text inside a Word, Excel, PowerPoint or OpenDocument file, read straight from its XML.

## Any Two Types, PDF Included

Every Homer app converts between any two of the types the kit knows, with the same code (kit 1.90.0, the author's rule of 24 October 2026). The types are known by their usual Windows extensions, plus .inix.

- **Through Markdown.** The table names 100 pairs and cannot name every one. A pair it does not name goes in two of its own steps through Markdown, which nearly every type reads into and writes out of: pdf to xlsx is pdf2md, then md2xlsx. A type with no Markdown route goes through a web page instead: json to pdf is json2htm, then htm2pdf. Each step is an ordinary route, with its own best-first ways and its own log lines.
- **Even when a route exists.** When every way of a named pair fails, as docx2pdf's Word does on a computer without Office, the same two steps are tried before giving up, and the error says what each attempt found.
- **PDF in and out.** A PDF is read by pdfstructure, with OCR for scans. A PDF is made by Edge from a web page, so md2pdf, htm2pdf and anything that reaches them need no Office. Word stays first for docx2pdf and odt2pdf, since its own export keeps the most of a Word file's layout.
- **Databases in and out.** The sqlite engine makes and reads SQLite databases, so a table becomes a .db and a .db becomes anything Markdown can.
- **What cannot be made.** JSON to a table, EPUB or PowerPoint, since JSON has no single table and those two would need a third step. A type to itself.
- **Asking first.** Conversion.canConvert, and canConvert in Python, answer for the hub too, so BatCon's list and every app's picker offer exactly what convert can do.

## Every File Finished for a Screen Reader

Whatever engine makes a file -- the kit's own writers, Pandoc, Edge or Office -- the kit opens it once more when it is done, gives it what a screen reader needs, and logs what it could not fix (kit 1.91.0). The findings use extCheck's rule names, so a log reads like an extCheck report. A middle file of a two-step conversion is left alone, since a program reads it next, not a person.

- **Excel (.xlsx):** header names for every table, a frozen header row, a sheet name from the file's name in place of a lone "Sheet1" or "Data", and the workbook's title, author and language. Merged cells are reported.
- **EPUB (.epub):** a title from the book's first heading and a language, when the package has none.
- **Markdown (.md):** front matter with a title from the first heading and a language, when there is none. Skipped heading levels, no headings at all, and pictures without alternative text are reported.
- **PDF (.pdf):** tagged. Edge prints a page that has its language and title; Word now exports with its structure tags and heading bookmarks rather than Save As, whose tags depend on a setting in Word.
- **PowerPoint (.pptx):** title, author and language. Slides without a title and pictures without alternative text are reported.
- **Web pages (.htm):** the Homer page form, as before: one H1, main, language and title. Pictures without alternative text are reported.
- **Word (.docx):** title from the first heading, author and language, and the language in the default style, so every run of text is read in it. A document without headings, and pictures without alternative text, are reported.

- **extCheck's rules judge every file the kit makes,** in an app that compiles the kit's Quality.cs, where they now live. Markdown has all of extCheck's rules (kit 1.92.0), and extCheck runs them from there too. Word, Excel and PowerPoint have extCheck's rules read from the file's own XML, with extCheck's names, wording and thresholds, so no Office is needed (kit 1.92.1): capitals, typed bullets, repeated spaces, skipped or repeated headings, a long stretch before the first heading, empty table cells, two-way table headers, vague or plain links, floating text boxes and unlabeled form fields in Word; hidden rows and columns, blank rows used for layout, default table names, tables without headers, long sheet names, and charts and pictures without alternative text in Excel; small text, typed bullets, capitals, fast or automatic advancing, repeating or rapid animation, a title not read first, and missing speaker notes in PowerPoint. Two need Office's rendering and stay in extCheck for now: color used alone, and a form field's help text beyond what the file holds.
- **Every EPUB gets EPUB Accessibility 1.1 metadata** where it has none (kit 1.92.2, from GLOW): how it can be read (textual, and visual when it has pictures), that text alone suffices, its features (structural navigation, a table of contents when it has one, alternative text when it has pictures), no hazards, and a short summary. Each is a claim the kit can stand behind for a book it made from a document; it claims no conformance it has not tested.
- **A Word paragraph that looks like a heading but is not styled as one** is reported as FauxHeading, scored by GLOW's signals: bold, large type, short, no closing punctuation, capitals or title case, one line, a numbering pattern, less for a name or a "Note:". Only bold or large text is reported.
- **A Markdown file with more than one top heading** is reported, MultipleTopHeadings: one H1, its title.
- **Every PDF is checked for a title and bookmarks** as well (kit 1.92.2, from GLOW), since the title is what a reader announces and bookmarks let it move by headings.
- **Every PDF is checked for tags and a language,** from IsTagged in KeyLine: a structure tree, the marked-content flag and /Lang. A PDF whose catalog is packed in a compressed stream could hide them, so the finding asks you to listen to it before taking it as untagged.

The title is the document's first heading where it has one, else its file's name with underscores read as spaces. The language is Windows' own, and the author is the Windows user.

### Header names in a workbook

JAWS and NVDA read a table's column or row headers as you move through it when the table's top-left cell carries a workbook name beginning ColumnTitle, RowTitle or Title (both). This comes from the author's xlHeaders.vbs of 2024, which drove Excel to do it. The kit reads and writes the workbook's own XML instead, so no Office is needed, and it improves the test in two ways.

- **A table is a region:** a rectangle of filled cells set apart by blank rows and columns, as Excel's own CurrentRegion finds it. It needs at least two rows and two columns.
- **Column headers** are a top row whose every cell is filled, text, and different from the rest, ignoring case. **Row headers** are the same, down the first column.
- **An empty top-left corner** no longer hides a two-way table: the top row is tested from its second cell and the first column from its second cell, and both passing makes a Title. xlHeaders found no headers in such a table.
- **A header must be text,** so a row of different numbers is not taken for headers.
- **A table already named** keeps its name. A new name takes the next free two-digit number: ColumnTitle01, ColumnTitle02.
- **The first named table's headers are frozen,** so they stay in view while a sighted reader scrolls.

### A workbook laid out for reading

From the author's xlFormat.vbs in KeyLine (kit 1.91.1). A workbook the kit's own writer made, which has no styles of its own, is also laid out: each column as wide as its longest text, up to 40 characters, with longer text wrapped; the header row bold; and every row set to the top, so a wrapped row reads in step with its neighbors. A workbook that already has styles keeps them. xlFormat also deleted any column with a blank header; the kit keeps the column, since deleting it loses data, and reports it (BlankOrGenericColumnHeader).

### Tables in a Word file

From docxIt's FormatTables in KeyLine (kit 1.91.1). A table whose first row is all text, every cell different, has that row marked as its header row, so Word repeats it on each page and a screen reader announces it as headers, and its header-row style is turned on. It also gets a bookmark JAWS reads as it does an Excel name: ColumnTitle01, or Title01 when its first column is distinct text too. docxIt gave every table the same bookmark, ColumnTitle, so each replaced the last; the kit numbers them. A table without such a first row is reported (TableMissingHeaderRow).

### Databases in DbDo's form

A database the kit makes is one DbDo opens with nothing to set up, as the homer-db skill describes. Its table is named for the file, plural and in lower case, with the English singular for its id: people.db holds people, with person_id. Its fields come in DbDo's order: the id, added and edited, the data fields with DbDo's types (TEXTLINE, TEXTMEMO, INTEGER or REAL, from what the column holds), url, notes and tags, look (the first three fields, joined with " | "), prime (every data field) and marked. It has the edited and maps triggers, a unique index on prime, and DbDo's own lookups, maps and views tables, seeded with DbDo's field types and link kinds. A row that repeats another exactly is left out and counted. checkDb passes such a database with no warnings. Turning a database back into Markdown leaves out DbDo's own tables and the fields DbDo keeps for itself.

## Records: Contacts, Calendars, Playlists, Feeds and Subtitles

The plain-text formats people pass records in convert like any other type (kit 1.93.0). Each becomes a table, one record to a row, and a table becomes each of them, so they reach every other type through the table: contact cards to Excel, a calendar to a web page, a spreadsheet of names back to contact cards.

- **Contact cards (.vcf):** name, given and family names, organization, title, email, phone, mobile, address, web, birthday and note. Several emails or phones share one field, separated by semicolons.
- **Calendars (.ics, and vCalendar's .vcs):** summary, start, end, location, description, web, organizer, the repeat rule and the event's id. Times keep their time zone, and an all-day event stays a date.
- **Playlists (.m3u, .m3u8, .pls, .xspf, .wpl, .asx):** title, location and length in seconds. A .m3u8 that is a streaming manifest rather than a playlist is refused, as QUILL's playlist reader taught; the two share a first line.
- **Feed lists (.opml):** title, feed, site and the group it sits in.
- **Subtitles (.srt, .vtt):** start, end and text, so one turns into the other.

Writing one, a table's field names are matched loosely: Email, E-mail and Email Address all fill the email. It is one short Python script that both languages run, as the SQLite engine is, and the kit's build fails if the two copies differ. The table is the third hub, after Markdown and a web page.

## Audio and Video

Audio (mp3, wav, flac, m4a, aac, ogg, opus, wma, aiff) and video (mp4, mkv, avi, mov, wmv, webm, flv, m4v, mpg, mpeg, ts, m2ts, 3gp, ogv) convert among themselves through ffmpeg; video to audio keeps the sound. Either becomes a transcript -- text, Markdown, a web page, Word, PDF, EPUB -- through Whisper, and a document becomes spoken audio or video through the kit's voices.

## .htm, Never .html

A web page a Homer app makes is .htm. Every Homer app reads .html as .htm, in C# and in Python alike, so the table has no html2 sections; four were removed in 1.90.0, since they could never be reached. A picker offers "htm" and never "html".

## Recognizing a File

Before converting, the kit works out what a file is, from its extension and from its first bytes:

- **A magic number settles it.** A file that starts like a PDF, a zip, a PNG, a JPEG, a program or a 1997 Office file is that, whatever its name.
- **A byte order mark or no zero bytes means text.** So a .inix, a .m3u, or a file with an extension nobody listed is read as text when its bytes are text.
- **The encoding comes from Ude** when Ude.dll is beside the program. Ude is the NuGet port of Mozilla's encoding detector. Without it, a strict UTF-8 test decides between UTF-8 and the Windows code page.
- **Zero bytes with no byte order mark mean binary.** So a binary file wearing a .txt name is not read aloud as gibberish.

Conversion.recognize returns what was found, and Conversion.describe turns it into one line a person hears, such as "M3U play list, text in UTF-8, 12 lines".

## The Best Engine for Each Conversion

This is the review of October 2026, across DbDo, EdSharp, FileDir, HomerScribe, HomerView and 2htm. Each choice is the best way any app had, with Office last.

- **csv, tsv and inix to md, htm or docx:** the table engine, from FileDir. Pandoc has no writer for csv or tsv.
- **doc, xls and ppt (the 1997 Office formats):** Office through COM, with the Alert box when it is missing. Recommended next: NPOI, a free NuGet package DbDo already uses, reads .xls without Office, so xls2csv and xls2md can move off COM.
- **docx2htm, docx2md, docx2epub and docx2odt:** Pandoc. 2htm used Word for docx2htm; Pandoc needs no Office and keeps the structure.
- **docx2txt and odt2txt:** zipxml, new in kit 1.74.0, since no program starts; then Pandoc.
- **md2docx, md2htm and md2epub:** Pandoc, with the page-break filter where the program ships it, as HomerScribe does.
- **pdf2md, pdf2docx and pdf2htm:** HomerScribe's reader is the best in the suite. It uses PdfPig's layout analysis and reading order, so a two-column page reads down each column. It uses the PDF's own tag tree when there is one, infers headings from type size, reads scanned pages with Tesseract above a confidence floor, and describes pictures with a local model. Since kit 1.75.0 it is the kit's PdfReader class, the pdfstructure and ocr engines in any app that compiles it; apps that do not yet still get pymupdf4llm.
- **pdf2txt:** pdftext, for speed. This is what FileDir's ? key uses. It replaces pymupdf4llm, which worked out the whole structure only to throw it away, and 2htm, which read PDFs through Word.
- **pptx2md and pptx2txt:** zipxml, with a heading for each slide in Markdown. PowerPoint only for the old .ppt.
- **xlsx2csv, xlsx2md and xlsx2txt:** the table engine, then zipxml. Excel only for the old .xls.
- **Audio, video and pictures:** ffmpeg and ImageMagick, in ConversionMedia.cs, moved from FileDir.

Every conversion is logged with its route and its time in milliseconds, so the order of the ways can be tuned from measurements over many test cycles.

## For an App

An app compiles Conversion.cs and Table.cs from the kit, and ConversionMedia.cs if it converts media. Its build copies exec\\conversions.inix beside the program, and its installer ships it. Then:

```
string sError;
string sText = Homer.Conversion.toText(sPath, out sError);
bool bMade = Homer.Conversion.convert(sSource, sTarget, out sError);
```

toText takes the quickest way and never uses OCR, for a key that must answer at once. convert takes the best way for the target.

## The Check

The shared check's conversion step scans an app's own C# for private conversion code: its own Pandoc finder, a 2htm call, an Office COM object or pymupdf4llm. An app listed in conversionsMoved, in data\\SuiteCommands.inix, fails on any such line; others get a warning that counts them until their move.

## Moves

- **DbDo:** moved in kit 1.77.1. Its Word export goes through the kit from Markdown; it reads .xls with NPOI, which it already used to write spreadsheets, so no Office is needed; Excel remains only for its native charts, marked as not conversions.
- **HomerView:** next. It still has 5 lines of its own conversion code.
- **EdSharp:** moved in kit 1.76.0. Import and Export offer and use the kit's routes first; its [Import] and [Export] sections serve only the targets the kit does not cover, such as MediaWiki, LaTeX and braille. Its Word conversion code is gone; Word remains only for its optional Word spelling, thesaurus and mail.
- **FileDir:** moved in kit 1.74.0. Its Convert.cs and Table.cs became the kit's Conversion.cs and Table.cs.
- **HomerScribe:** its PDF reader moved into the kit in 1.75.0 as PdfReader.cs, and HomerScribe calls it. Its Word version is still made by its own Pandoc call, which moves to Conversion when HomerScribe compiles it.
- **2htm:** becomes a thin command-line and dialog face over Conversion, keeping its own csv and json readers until they move into the kit too, and its Office converters as the last resort.

## Learnings from FRAME PDF Studio

FRAME PDF Studio (MIT licensed, by ripplelearning) is a browser tool for remediating PDFs by hand. It reads a PDF with pdf.js, recognizes scanned pages with tesseract.js, and writes a tagged PDF with pdf-lib. It was reviewed on 19 October 2026 for what the kit's PdfReader should learn.

### Taken into PdfReader (kit 1.77.5)

- **Drop caps.** A paragraph's first letter set large across several lines came out as a one-letter heading. It is now joined back to its word.
- **Form fields.** A fillable PDF's fields are listed at the end under Form fields, each with its label (its tooltip, else its name) and its value. Before, a filled form lost its answers.
- **Links.** A PDF's links to the web or to mail become Markdown links on the words they cover, in reading order. Any link whose words cannot be found is listed at the end under Links, so none is lost.

### Not taken, and why

- **Column order by clustering line centers.** PdfReader already uses PdfPig's Docstrum blocks and reading-order detector, which handle columns and full-width headings more reliably than a fixed 60-point cluster.
- **Headings by a fixed size ratio and list markers by pattern.** PdfReader already does both, with the body size measured by characters and a length test that FRAME's rule lacks.
- **Tables built by hand, and writing a tagged PDF.** These are remediation, making a better PDF, rather than conversion. They would suit a future pdf2pdf route, not pdf2md.
- **Its accessibility checker.** A list of a PDF's accessibility problems could become a kit report one day; it is not a conversion.

## Speech and text (kit 1.84.0)

- **Audio or video to a document:** a transcript, by Whisper on this computer, as plain text, Markdown, a web page, Word, PDF, OpenDocument, rich text, EPUB or Word 97. It needs ffmpeg and Whisper, both offered by the Homer installers.
- **A document to audio:** its words spoken by Windows' speech synthesis, as MP3, M4A, WAV, Ogg, FLAC or Opus. It needs ffmpeg.
- **A document to video:** the same speech over a plain black picture, as MP4, Matroska, WebM or QuickTime, since the kit makes no pictures of its own.
- **A video to a described document:** with HomerScribe installed, what is said and what can be seen, as one document with a heading for each; HomerScribe describes, as the kit's engine for it. Without HomerScribe, the transcript alone.

