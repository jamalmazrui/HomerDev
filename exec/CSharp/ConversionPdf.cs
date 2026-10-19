// ConversionPdf.cs -- the PDF reader's half of the kit's Conversion class (kit 1.75.0).
//
// A separate file because PdfReader.cs needs PdfPig at compile time, and an app
// that does not ship PdfPig should not have to compile it. When this file and
// PdfReader.cs are left out, Conversion.cs's partial methods compile to
// nothing: pdfstructure falls back to pymupdf4llm and ocr is reported missing.
//
// REQUIRES: Conversion.cs, PdfReader.cs.
//
// To use it, an app compiles PdfReader.cs and this file, references PdfPig's
// assemblies, and ships them beside its executable, as HomerScribe does.
//
// Copyright 2006-2026 by Jamal Mazrui. MIT License.

using System;
using System.IO;

namespace Homer {

public static partial class Conversion {

static partial void readerState(ref bool bReader, ref bool bTesseract) {
bReader = true;
bTesseract = PdfReader.findTesseract() != "";
} // readerState method

static partial void readerConvert(string sSource, string sTarget, bool bOcr, ref bool bMade, ref bool bScans, ref string sError) {
string sWhy;
bMade = PdfReader.toFile(sSource, sTarget, bOcr, out sWhy);
bScans = !bMade && PdfReader.bLastWasScans;
sError = bMade ? "" : sWhy;
} // readerConvert method

} // Conversion class

} // Homer namespace
