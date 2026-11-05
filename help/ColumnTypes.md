# Column Types

A Homer database says what a column holds through its declared type. The names follow two sets of rules at once: SQLite's rules for storing data, and the web's de facto conventions for naming formats.

## How a name is built

- **The prefix states storage.** SQLite decides how to store a value from words inside its column's declared type. A name beginning TEXT stores UTF-8 text; a name beginning BLOB keeps bytes exactly as given.
- **The rest names the format,** by its usual file extension: the convention of downloads, and the one Windows uses to choose a program. So it is BLOBJPG, not BLOBJPEG, though BLOBJPEG is accepted and read as BLOBJPG.
- **Each type records its MIME type,** such as image/png or application/json, for exporting and for web headers.
- **Text formats are TEXT, whatever MIME's first word says.** JSON is application/json, yet it is text, so TEXTJSON; an SVG drawing is image/svg+xml, yet text, so TEXTSVG. A zip file is binary, so BLOBZIP.
- **Value types name one value with a natural action,** after HTML's input types: TEXTURL opens in the browser, TEXTEMAIL writes with mailto, TEXTPHONE calls with tel, and TEXTPATH opens a file or folder.

## Three traps, proven on 5 November 2026

SQLite reads a declared type by looking for words in it, in this order, and the first match wins:

- **INT anywhere means a number.** TEXTPOINT, TEXTPRINT and BLOBPOINT all turned the text 123 into the number 123. No Homer type contains INT.
- **CHAR, CLOB or TEXT anywhere means text,** even after BLOB: BLOBTEXT and BLOBCHART store text. No BLOB type contains them.
- **BLOB comes before REAL,** so BLOBFLOAT would still keep bytes; Homer has no such type, but the order is safe.

A STRICT table refuses all of these names, so a Homer table is never STRICT.

## The types

Each type below gives its extension, its MIME type where it has one, and what it holds.

### Binary formats

- **BLOBDOCX** (.docx, application/vnd.openxmlformats-officedocument.wordprocessingml.document): A Word document. Shown with the default program for its format.
- **BLOBEPUB** (.epub, application/epub+zip): An EPUB book. Shown with the default program for its format.
- **BLOBGIF** (.gif, image/gif): A GIF picture. Shown with the default program for its format.
- **BLOBJPG** (.jpg, image/jpeg): A JPEG photo. Shown with the default program for its format.
- **BLOBM4A** (.m4a, audio/mp4): AAC audio. Shown with the default program for its format.
- **BLOBMP3** (.mp3, audio/mpeg): MP3 audio. Shown with the default program for its format.
- **BLOBMP4** (.mp4, video/mp4): MP4 video. Shown with the default program for its format.
- **BLOBOGG** (.ogg, audio/ogg): Ogg audio. Shown with the default program for its format.
- **BLOBPDF** (.pdf, application/pdf): A PDF document. Shown with the default program for its format.
- **BLOBPNG** (.png, image/png): A PNG picture. Shown with the default program for its format.
- **BLOBPPTX** (.pptx, application/vnd.openxmlformats-officedocument.presentationml.presentation): A PowerPoint deck. Shown with the default program for its format.
- **BLOBWAV** (.wav, audio/wav): WAV audio. Shown with the default program for its format.
- **BLOBWEBM** (.webm, video/webm): WebM video. Shown with the default program for its format.
- **BLOBWEBP** (.webp, image/webp): A WebP picture. Shown with the default program for its format.
- **BLOBXLSX** (.xlsx, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet): An Excel workbook. Shown with the default program for its format.
- **BLOBZIP** (.zip, application/zip): A zip archive. Shown with the default program for its format.

### Text formats

- **TEXTCSV** (.csv, text/csv): Comma-separated values.
- **TEXTDBDO** (.dbdo, text/x-dbdo): A DbDo routine of dot-prompt commands.
- **TEXTHTML** (.htm, text/html): A web page.
- **TEXTICS** (.ics, text/calendar): ICalendar events.
- **TEXTINIX** (.inix, text/x-inix): Homer settings, in sections of key = value lines.
- **TEXTJSCRIPT** (.js, text/javascript): A JScript .NET program.
- **TEXTJSON** (.json, application/json): JSON data.
- **TEXTM3U** (.m3u, audio/x-mpegurl): A playlist.
- **TEXTMARKDOWN** (.md, text/markdown): Markdown.
- **TEXTMEMO** (.txt, text/plain): Lines of plain text.
- **TEXTSQL** (.sql, application/sql): SQL statements.
- **TEXTSRT** (.srt, application/x-subrip): SubRip captions.
- **TEXTSVG** (.svg, image/svg+xml): An SVG drawing, which is text.
- **TEXTTSV** (.tsv, text/tab-separated-values): Tab-separated values.
- **TEXTVCAL** (.vcs, text/x-vcalendar): VCalendar events.
- **TEXTVCARD** (.vcf, text/vcard): VCard contacts.
- **TEXTVTT** (.vtt, text/vtt): WebVTT captions.
- **TEXTXML** (.xml, application/xml): XML.

### Single values

- **TEXTEMAIL**: An email address, written to with mailto. Written to with the default mail program.
- **TEXTLINE** (text/plain): One line of plain text.
- **TEXTPATH**: The path of a file or folder, opened by Windows. Opened by Windows.
- **TEXTPHONE**: A phone number, called with tel. Called with the default phone program.
- **TEXTTIME**: A date and time, as YYYY-MM-DD HH:MM:SS.
- **TEXTURL**: A web address, opened in the default browser. Opened in the default browser.

### Aliases

These names are read as the type after them: BLOBJPEG as BLOBJPG, TEXTJAVASCRIPT as TEXTJSCRIPT, TEXTJS as TEXTJSCRIPT, TEXTMD as TEXTMARKDOWN, TEXTPLAIN as TEXTMEMO, TEXTTEL as TEXTPHONE, TEXTTXT as TEXTMEMO. These extensions are read as the type after them: .html as TEXTHTML, .ini as TEXTINIX, .jpeg as BLOBJPG, .m3u8 as TEXTM3U, .markdown as TEXTMARKDOWN, .text as TEXTMEMO. A file whose extension is not listed is TEXTMEMO.

## Where the vocabulary lives

The kit keeps it in two twins: Homer.ColumnTypes in exec\Schema.cs, for programs, and scripts\columnTypes.py, for scripts. The kit's build runs scripts\checkTypes.py, which proves that the twins agree and that a real SQLite gives every name the storage it says. On Windows it also logs how the SQLite ODBC driver reports each type to ADO, which is how DbDo reads a database. The conversion to DbDo format seeds every type into each database's defs, as rows with src DbDo and fld type, so a database describes its own types.

## One column, many formats

When one column holds rows of different formats, as DbDo's files table does, the column is declared for what they share, and a kind column names each row's format in this same vocabulary. Both ways speak one language: the declared type when a column has one format, kind when each row has its own.
