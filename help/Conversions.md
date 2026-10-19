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
- **ocr** (outside): Tesseract reads a scanned page. In C#, the kit's PdfReader runs it, so a scanned page gets headings and lists too; in Python, pypdfium2 draws each page for it. Never used for a quick read, since it can take minutes.
- **officecom** (outside, last resort): Microsoft Office through COM. Used only where nothing free will do. When Office is needed and missing, an Alert box says so once per session, and says how to avoid it.
- **pandoc** (outside): Pandoc, for the markup and document formats it reads and writes.
- **pdfstructure** (internal where it can be): a PDF's headings, lists and reading order. In C#, the kit's PdfReader, HomerScribe's reader, in an app that compiles PdfReader.cs and ConversionPdf.cs with PdfPig; otherwise pymupdf4llm through Python. A document of scans fails it, so OCR reads it next.
- **pdftext** (internal when it can be): a PDF's text layer. PdfPig in-process when PdfPig is beside the program; otherwise PyMuPDF's plain text through Python.
- **table** (internal): rows and columns, through the kit's Table class, with cells placed by their references.
- **zipxml** (internal): the text inside a Word, Excel, PowerPoint or OpenDocument file, read straight from its XML.

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

- **DbDo, EdSharp and HomerView:** next. Each still has its own Pandoc finder, 2htm calls or Office COM code: 13 lines in DbDo, 6 in EdSharp and 5 in HomerView.
- **FileDir:** moved in kit 1.74.0. Its Convert.cs and Table.cs became the kit's Conversion.cs and Table.cs.
- **HomerScribe:** its PDF reader moved into the kit in 1.75.0 as PdfReader.cs, and HomerScribe calls it. Its Word version is still made by its own Pandoc call, which moves to Conversion when HomerScribe compiles it.
- **2htm:** becomes a thin command-line and dialog face over Conversion, keeping its own csv and json readers until they move into the kit too, and its Office converters as the last resort.
