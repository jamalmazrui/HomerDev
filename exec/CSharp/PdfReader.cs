// PdfReader.cs -- reading a PDF as an accessible document, for every Homer app.
//
// HOMERSCRIBE'S READER, MOVED INTO THE KIT (kit 1.75.0). It began as
// HomerScribe's PdfRead.cs and the PDF half of HomerScribe.cs, tuned over many
// runs on real documents. It is now one shared class in the Homer namespace, so
// HomerScribe calls it, and Conversion's pdfstructure and ocr engines call it
// through ConversionPdf.cs. One copy, one set of improvements.
//
// WHAT IT DOES, BEST SOURCE FIRST:
//   1. The PDF's own tags, where they carry the document: headings, lists and
//      figure descriptions as the author stated them.
//   2. Otherwise the text layer, in reading order (PdfPig's Docstrum blocks
//      and reading-order detector), with headings worked out from type sizes.
//   3. A text layer that cannot be trusted, or a scanned page, is read from
//      its picture: Tesseract first, above a confidence floor; an optional
//      picture model where Tesseract falters.
//   4. Running headers and footers are dropped, a page break is kept between
//      pages, and heading levels are closed so none is skipped.
//
// WHAT THE CALLER SUPPLIES, through Options: where to log and announce
// progress, Tesseract's path, and optionally a way to read a page or describe
// a picture with a model. Nothing here knows about any one app; HomerScribe's
// settings come in as plain values.
//
// REQUIRES: Log.cs.
// ASSEMBLIES: UglyToad.PdfPig.dll, UglyToad.PdfPig.DocumentLayoutAnalysis.dll
// (PdfPig from NuGet, with its other assemblies, referenced at compile time and
// shipped beside the program). An app that does not compile this file still
// reads PDFs through Conversion's other engines.
//
// NOT THREAD SAFE: the last document's tags are kept in static fields, as they
// were in HomerScribe. Read one PDF at a time.
//
// Copyright 2006-2026 by Jamal Mazrui. MIT License.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Text.RegularExpressions;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Content;
using UglyToad.PdfPig.DocumentLayoutAnalysis;
using UglyToad.PdfPig.DocumentLayoutAnalysis.PageSegmenter;
using UglyToad.PdfPig.DocumentLayoutAnalysis.ReadingOrderDetector;
using UglyToad.PdfPig.DocumentLayoutAnalysis.WordExtractor;

namespace Homer
{
    public static class PdfReader
    {
        // ---- what the caller supplies ------------------------------------

        public class Options
        {
            // Where pictures taken from the pages are written. Left empty, a
            // temporary folder is made and removed again when reading ends.
            public string sWorkDir = "";
            // The document's title, its level-1 heading; the file name if empty.
            public string sTitle = "";
            // Tesseract's path, or empty for no OCR (findTesseract finds it).
            public string sTesseract = "";
            // How sure Tesseract must be, out of a hundred, before its reading
            // of a page is kept rather than handed to the picture model.
            public int iOcrFloor = 70;
            // How much larger than body text a line must be to be a heading.
            public double nHeadingSize = 1.4;
            // How many pictures are described at most; 0 for no limit.
            public int iPictureLimit = 0;
            // The names of those settings in the calling app, for its messages.
            public string sHeadingSizeName = "the heading size setting";
            public string sPictureLimitName = "the picture limit";
            // The picture model's name, for messages.
            public string sModelName = "the picture model";
            // Log a line: text, level (INFO, ERROR, HINT), and what the console
            // should say (null for its default, "" for nothing). Log.cs if null.
            public Action<string, string, string> fnLog = null;
            // Announce progress: a kind ("Preparing", "Reading") and a phrase.
            public Action<string, string> fnProgress = null;
            // Turn a picture taken from a page into a PNG path, or "" to use it
            // as it is.
            public Func<string, string> fnToPng = null;
            // Read a scanned page's picture with a model, returning Markdown.
            public Func<string, string> fnReadPageByModel = null;
            // Describe a figure on a text page; null describes no pictures.
            public Func<string, string> fnDescribePicture = null;
        }

        public class Result
        {
            public bool bRead = false;          // false when no page could be read at all
            public string sTrouble = "";        // why, when nothing could be read
            public string sMarkdown = "";       // the document, levels closed, ready to write
            public string sLanguage = "";       // the document's stated language, or ""
            public bool bTagged = false;
            public bool bBuiltFromTags = false;
            public int iPages = 0;
            public int iWithText = 0;
            public int iScanned = 0;
            public int iFigures = 0;            // pictures found
            public int iDescribed = 0;          // pictures described
            public int iPassedOver = 0;         // pictures over the limit
            public int iByOcr = 0;
            public int iByModel = 0;
            public int iUnread = 0;             // scanned pages nothing could read
            public int iFurniture = 0;          // running header and footer lines dropped
        }

        // How much larger than the body a heading must be, for this document.
        static double nHeadingSize = 1.4;

        static void say(Options o, string sText, string sLevel, string sConsole)
        {
            if (o != null && o.fnLog != null) { o.fnLog(sText, sLevel, sConsole); return; }
            if (sLevel == "ERROR") Log.error(sText);
            else Log.info(sText);
        }

        static void say(Options o, string sText, string sLevel)
        {
            say(o, sText, sLevel, null);
        }

        static void progress(Options o, string sKind, string sContent)
        {
            if (o != null && o.fnProgress != null) o.fnProgress(sKind, sContent);
        }

        static string toPng(Options o, string sPath)
        {
            if (o == null || o.fnToPng == null) return sPath;
            string sPng = o.fnToPng(sPath);
            return sPng == null ? "" : sPng;
        }

        static string readByModel(Options o, string sPath)
        {
            if (o == null || o.fnReadPageByModel == null) return "";
            string sSaid = o.fnReadPageByModel(sPath);
            return sSaid == null ? "" : sSaid;
        }

        static string describe(Options o, string sPath)
        {
            if (o == null || o.fnDescribePicture == null) return "";
            string sSaid = o.fnDescribePicture(sPath);
            return sSaid == null ? "" : sSaid;
        }

        static string counted(int iHowMany, string sSingular, string sPlural)
        {
            return iHowMany.ToString() + " " + (iHowMany == 1 ? sSingular : sPlural);
        }

        static string num(double nValue)
        {
            return nValue.ToString("0.###", CultureInfo.InvariantCulture);
        }


        // ---- the whole document ------------------------------------------

        // read: a PDF as one Markdown document, with how it was read.
        //
        // This is what HomerScribe's readPdf did between opening the file and
        // writing described.md, moved here whole so every app reads a PDF the
        // same way. The caller writes the Markdown, makes any Word version, and
        // tidies its own working folder.
        public static Result read(string sPdfPath, Options o)
        {
            Result oResult = new Result();
            if (o == null) o = new Options();
            nHeadingSize = o.nHeadingSize;
            if (nHeadingSize < 1.05 || nHeadingSize > 4.0) nHeadingSize = 1.4;
            string sRoot = o.sTitle == null || o.sTitle.Trim() == ""
                         ? Path.GetFileNameWithoutExtension(sPdfPath) : o.sTitle.Trim();
            string sWorkDir = o.sWorkDir == null ? "" : o.sWorkDir;
            bool bOwnWorkDir = false;
            if (sWorkDir == "")
            {
                sWorkDir = Path.Combine(Path.GetTempPath(), "HomerPdf_" + Guid.NewGuid().ToString("N").Substring(0, 8));
                bOwnWorkDir = true;
            }
            try
            {
                if (!Directory.Exists(sWorkDir)) Directory.CreateDirectory(sWorkDir);
                oResult = readInto(sPdfPath, sRoot, sWorkDir, o);
            }
            catch (Exception oError)
            {
                oResult.bRead = false;
                if (oResult.sTrouble == "") oResult.sTrouble = oError.Message;
                say(o, "The PDF could not be read: " + oError.Message, "ERROR");
            }
            finally
            {
                if (bOwnWorkDir)
                {
                    try { Directory.Delete(sWorkDir, true); } catch (Exception) { }
                }
            }
            return oResult;
        }

        static Result readInto(string sPdfPath, string sRoot, string sWorkDir, Options o)
        {
            Result oResult = new Result();
            oNow = o;
            progress(o, "Preparing", "Opening " + Path.GetFileName(sPdfPath));
            string sTrouble = "";
            List<PdfPage> lPages = pagesOfPdf(sPdfPath, sWorkDir, out sTrouble);
            oResult.sTrouble = sTrouble;
            oResult.iPages = lPages.Count;
            oResult.sLanguage = sDocumentLanguage;
            oResult.bTagged = bTaggedDocument;
            if (lPages.Count == 0)
            {
                say(o, "Nothing could be read out of " + Path.GetFileName(sPdfPath)
                    + (sTrouble == "" ? "." : ": " + sTrouble), "ERROR",
                    "Nothing could be read out of that PDF.");
                return oResult;
            }

            // What the PDF says about its own structure, before anything is
            // inferred about it.
            if (sTaggedSaid != "")
            {
                say(o, "About " + Path.GetFileName(sPdfPath) + ": " + sTaggedSaid + ".", "INFO", "");
                if (bTaggedDocument && sTagSummary != "")
                {
                    say(o, "  Reading its tags: " + sTagSummary + ".", "INFO", "");
                    // Matterhorn checkpoint 13-004: a Figure without Alt or
                    // ActualText. Worth saying plainly, because it is a fault in
                    // the SOURCE document rather than in this reading of it —
                    // somebody tagged that PDF and left a picture undescribed.
                    // Named apart from the iFigures counted from the picture
                    // layer above: these are figures the TAGS name, which is a
                    // different number about a different thing.
                    int iTaggedFigures = 0;
                    int iNoAlt = 0;
                    foreach (TaggedItem oItem in lTagged)
                    {
                        if (oItem.sKind != "Figure") continue;
                        iTaggedFigures = iTaggedFigures + 1;
                        if (oItem.sAlt == "") iNoAlt = iNoAlt + 1;
                    }
                    if (iNoAlt > 0)
                        say(o, "  " + counted(iNoAlt, "figure in the original carries no description",
                                                  "figures in the original carry no description")
                                   + ", which is a fault in that PDF rather than in this reading of it."
                                   + (o.fnDescribePicture != null ? " They are described here where possible." : ""), "INFO", "");
                }
            }
            int iScanned = 0;
            int iWithText = 0;
            int iFigures = 0;
            int iSkippedPictures = 0;
            foreach (PdfPage oPage in lPages) iSkippedPictures = iSkippedPictures + oPage.iSkippedPictures;
            foreach (PdfPage oPage in lPages)
            {
                if (oPage.bScanned) iScanned = iScanned + 1;
                else if (oPage.lLines.Count > 0) iWithText = iWithText + 1;
                iFigures = iFigures + oPage.lImages.Count;
            }
            // Say plainly when a document had no pictures at all, because
            // "0 pictures" can mean two very different things: a document that
            // genuinely has none, or a picture layer that failed to read them.
            // Four of his documents reported zero and there was no way to tell
            // which, so the count of pictures PASSED OVER is now reported too.
            if (iFigures == 0 && iSkippedPictures > 0)
                say(o, counted(iSkippedPictures, "picture was found but could not be read",
                                   "pictures were found but could not be read")
                           + ": stored without a JPEG, PNG or JPEG-2000 header, which is how a chart in a "
                           + "born-digital PDF is often kept. Those are passed over rather than written as a "
                           + "file nothing can open.", "INFO", "");
            say(o, counted(lPages.Count, "page", "pages") + " in " + Path.GetFileName(sPdfPath)
                       + ": " + counted(iWithText, "carries its own text", "carry their own text")
                       + ", " + counted(iScanned, "is a scan", "are scans")
                       + ", " + counted(iFigures, "picture", "pictures") + " in all.", "INFO",
                       counted(lPages.Count, "page", "pages") + " to read.");

            // THE TAGS FIRST, WHERE THEY CARRY THE DOCUMENT.
            //
            // Measured on his ten accessibility documents: against what the
            // tags say, the inference found 10 headings where there were 62,
            // and made 118 where there were 29. Four documents with tagged
            // lists produced no list items at all.
            //
            // So where the tags carry enough of the document, they are used and
            // nothing is guessed. "Enough" is judged by what came back: a tree
            // yielding a handful of words for a fifty-page document has not
            // been read properly, whatever it claims.
            bool bBuiltFromTags = false;
            if (lPieces.Count > 0)
            {
                int iTagHeadings = 0;
                int iTagList = 0;
                string sFromTags = markdownFromTags(lPieces, out iTagHeadings, out iTagList);
                int iTagWords = sFromTags.Split(new char[] { ' ', '\n' },
                                                StringSplitOptions.RemoveEmptyEntries).Length;
                // WORDS ALONE ARE NOT ENOUGH, and his Able Gamers Guidelines
                // proved it: its tags carry 1,374 words, 0 headings and 0
                // lists, and the pages themselves hold 25,995 words. It is a
                // SCANNED document that happens to be tagged, and its tags name
                // 141 figures and almost no text. Taken at its word, the
                // conversion lost 25,480 words.
                //
                // Two things are required now:
                //   the tags must carry some STRUCTURE, since a tree with no
                //   heading and no list is not describing a document; and
                //   they must not be plainly poorer than the pages, which is
                //   measured rather than assumed.
                int iPageWords = 0;
                foreach (PdfPage oPage in lPages)
                {
                    foreach (PageLine oLine in oPage.lLines)
                    {
                        if (oLine.sText == null) continue;
                        iPageWords = iPageWords + oLine.sText.Split(new char[] { ' ' },
                            StringSplitOptions.RemoveEmptyEntries).Length;
                    }
                }
                bool bHasShape = iTagHeadings > 0 || iTagList > 0;
                // FOUR FIFTHS, NOT A HALF.
                //
                // A half sounded cautious and is not. His 655-page handbook
                // passed it and still lost 39 per cent of its words: 42,938
                // from tags against 65,577 on the pages. Losing a third of a
                // textbook is not a trade worth making for better headings.
                //
                // Some loss is right — a tagged document marks its running
                // headers and footers as artifacts and they are correctly left
                // out — but that is a few words a page, not a third of the
                // document. Four fifths leaves room for the furniture and not
                // for a third of the text.
                bool bNotPoorer = iPageWords == 0 || iTagWords * 5 >= iPageWords * 4;
                if (!bHasShape)
                    say(o, "Its tags name no headings and no lists, so they do not describe the "
                               + "document. The layout is used instead.", "INFO", "");
                else if (!bNotPoorer)
                    say(o, "Its tags yield " + iTagWords.ToString() + " words where the pages hold "
                               + iPageWords.ToString() + ". The tags are not carrying the document, so the "
                               + "layout is used instead.", "INFO", "");
                if (bHasShape && bNotPoorer && iTagWords >= Math.Max(60, lPages.Count * 20))
                {
                    say(o, "Its own tags carry the document: "
                               + counted(iTagHeadings, "heading", "headings") + ", "
                               + counted(iTagList, "list item", "list items") + ", "
                               + counted(iTagWords, "word", "words")
                               + ". Nothing below is guessed from the layout.", "INFO",
                               "This PDF carries its own structure, so it is used rather than guessed.");
                    // PAC check 6, and a real fault in the source: "if the
                    // document has no assigned headings". A 23-page toolkit
                    // whose tags name 233 list items and no heading at all
                    // gives a reader nothing to move through, and that is worth
                    // saying about the original rather than passing on quietly.
                    if (iTagHeadings == 0)
                        say(o, "  But its tags name NO HEADINGS, only list items. That is a fault in the "
                                   + "original — a reader moving by heading has nothing to move through. The "
                                   + "words and lists below are its own; the headings it never had cannot be "
                                   + "supplied from them.", "ERROR");
                    // The pages are emptied and the tagged rendering put in
                    // place of them, so the rest of this function -- writing
                    // described.md, making the Word version, reading it back as
                    // a screen reader -- carries on unchanged. Better than a
                    // second copy of the write-out, which would drift from this
                    // one the first time either changed.
                    foreach (PdfPage oPage in lPages)
                    {
                        oPage.sMarkdown = "";
                        oPage.lLines.Clear();
                        oPage.bFromOcr = false;
                    }
                    if (lPages.Count > 0) lPages[0].sMarkdown = closedHeadingGaps(sFromTags);
                    bBuiltFromTags = true;
                }
                else
                    say(o, "Its tags were read but yielded only " + iTagWords.ToString()
                               + " words for " + counted(lPages.Count, "page", "pages")
                               + ", which is too little to be the document. The layout is used instead."
                               + (sPiecesTrouble == "" ? "" : " (" + sPiecesTrouble + ")"), "INFO", "");
            }
            else if (bTaggedDocument && sPiecesTrouble != "")
                say(o, "Its tags could not be joined to its words: " + sPiecesTrouble
                           + ". The layout is used instead.", "INFO", "");

            // A TEXT LAYER THAT CANNOT BE READ IS WORSE THAN NONE.
            //
            // PAC checks 8 and 14: a missing font translation table, or a
            // generator that never wrote the spaces. Either way the page looks
            // right and the text is nonsense — and nothing in the counts would
            // ever say so.
            //
            // The page is a picture too, so where the text fails this, the
            // pages are treated as scans and read instead.
            string sWhyBad = "";
            if (!bBuiltFromTags && iWithText > 0 && !textLayerIsSound(lPages, out sWhyBad))
            {
                say(o, "Its text layer cannot be trusted: " + sWhyBad + ". The pages will be read as "
                           + "pictures instead, which is slower and gives a usable document.", "INFO",
                           "The text in this PDF is not usable, so its pages will be read as pictures.");
                int iTurned = 0;
                foreach (PdfPage oPage in lPages)
                {
                    if (oPage.bScanned || oPage.lImages.Count == 0) continue;
                    oPage.bScanned = true;
                    oPage.lLines.Clear();
                    iTurned = iTurned + 1;
                }
                if (iTurned == 0)
                    say(o, "  But its pages hold no pictures either, so the text is all there is. "
                               + "The result will be poor and there is nothing better to use.", "ERROR");
                else
                {
                    iScanned = iScanned + iTurned;
                    iWithText = iWithText - iTurned;
                    say(o, "  " + counted(iTurned, "page will be read as a picture",
                                              "pages will be read as pictures") + ".", "INFO", "");
                }
            }

            // The heading structure, from font size alone. No model, and exact.
            double nBody = bodySizeOf(lPages);
            Dictionary<double, int> dLevel = headingLevels(lPages, nBody);
            if (nBody > 0.0)
                say(o, "Body text is set at " + num(nBody) + " point; "
                           + counted(dLevel.Count, "larger size becomes a heading level",
                                     "larger sizes become heading levels") + ".", "INFO", "");

            string sTesseract = o.sTesseract == null ? "" : o.sTesseract;
            int iOcrFloor = o.iOcrFloor;
            if (iOcrFloor < 1 || iOcrFloor > 100) iOcrFloor = 70;
            int iByOcr = 0;
            int iByModel = 0;
            int iUnread = 0;
            int iLimit = o.iPictureLimit;
            int iDescribed = 0;
            int iPassedOver = 0;
            int iTagAltUsed = 0;
            if (o.fnDescribePicture != null && iLimit > 0 && iFigures > iLimit)
                say(o, "This document holds " + counted(iFigures, "picture", "pictures")
                           + ". The largest " + iLimit.ToString() + " are described and the rest are named "
                           + "without one, which keeps the run to an evening rather than a day. Raise or "
                           + "clear " + o.sPictureLimitName + " to change that.", "INFO", "");
            for (int iAt = 0; bBuiltFromTags == false && iAt < lPages.Count; iAt = iAt + 1)
            {
                PdfPage oPage = lPages[iAt];
                if (iAt == 0) progress(o, "Reading", "Page 1 of " + lPages.Count.ToString());
                else progress(o, "Reading", "Page " + (iAt + 1).ToString() + ", "
                              + ((int)((iAt + 1) * 100.0 / lPages.Count)).ToString() + "%");

                if (oPage.bScanned)
                {
                    string sShow = toPng(o, oPage.lImages[0]);
                    if (sShow == "") sShow = oPage.lImages[0];
                    // TESSERACT FIRST, THE MODEL WHERE IT FALTERS.
                    //
                    // Tesseract reads clean print at least as well as the
                    // picture model, about twenty-five times faster, and cannot
                    // invent a word. Where its own confidence is poor the page
                    // is worth the model's slower look, and below that it is
                    // the model's job outright.
                    string sByOcr = "";
                    int iSure = 0;
                    List<double> lHeights = new List<double>();
                    if (sTesseract != "") sByOcr = tesseractRead(sTesseract, sShow, out iSure, lHeights);
                    if (sByOcr.Trim() != "" && iSure >= iOcrFloor)
                    {
                        // STRUCTURE, NOT JUST WORDS.
                        //
                        // His 511 KB of Markdown held 32 headings across 112
                        // pages and one list item, because a Tesseract page was
                        // handed straight through as plain lines. The words
                        // were right and the document had no shape.
                        //
                        // Tesseract gives each word's height, which does for a
                        // scan what point size does for a text page, so the
                        // same inference is used: the height most characters
                        // are set at is the body, anything markedly taller is a
                        // heading, and bullets and numbers become lists.
                        oPage.lLines.Clear();
                        string[] asByOcr = sByOcr.Replace("\r\n", "\n").Split('\n');
                        for (int iLine = 0; iLine < asByOcr.Length; iLine = iLine + 1)
                        {
                            if (asByOcr[iLine].Trim() == "") continue;
                            PageLine oOcrLine = new PageLine();
                            oOcrLine.sText = asByOcr[iLine];
                            oOcrLine.nSize = iLine < lHeights.Count ? lHeights[iLine] : 0.0;
                            oPage.lLines.Add(oOcrLine);
                        }
                        // Left as plain text for now. The heading levels cannot
                        // be known until every page has been read, because the
                        // body size is measured across the whole document --
                        // and on an all-scanned document there was nothing to
                        // measure until this loop had run. That is why his
                        // journal came out with 32 headings in 112 pages: the
                        // sizes arrived after the decision that needed them.
                        //
                        // A second pass below renders these pages properly.
                        oPage.sMarkdown = sByOcr;
                        oPage.bFromOcr = true;
                        iByOcr = iByOcr + 1;
                        say(o, "  Page " + oPage.iNumber.ToString() + " read by Tesseract, "
                                   + iSure.ToString() + " sure out of a hundred.", "INFO", "");
                    }
                    else if (o.fnReadPageByModel == null)
                    {
                        iUnread = iUnread + 1;
                        say(o, "  Page " + oPage.iNumber.ToString() + " could not be read: "
                                   + (sTesseract == "" ? "Tesseract is not available"
                                      : sByOcr.Trim() == "" ? "Tesseract found no words on it"
                                      : "Tesseract was only " + iSure.ToString() + " sure, under the floor of " + iOcrFloor.ToString())
                                   + ", and no picture model was given.", "INFO", "");
                    }
                    else
                    {
                        string[] asSaid = new string[] { "", readByModel(o, sShow) };
                        // THE MODEL WRITES ITS OWN MARKDOWN, and it writes a
                        // page title as "# Something". Twenty-two pages of his
                        // journal went to the model and produced 28 level-1
                        // headings, one per page — so a document with one title
                        // came out with twenty-nine.
                        //
                        // A page is not a document. Whatever the model calls a
                        // level 1, it is at best a level 2 here, and everything
                        // below it moves with it so the levels keep their
                        // shape.
                        oPage.sMarkdown = demotedHeadings(asSaid[1]);
                        iByModel = iByModel + 1;
                        say(o, "  Page " + oPage.iNumber.ToString() + " read by " + o.sModelName
                                   + (sByOcr.Trim() == ""
                                      ? ": Tesseract found no words on it."
                                      : ": Tesseract was only " + iSure.ToString() + " sure, under the floor of "
                                        + iOcrFloor.ToString() + "."), "INFO", "");
                    }
                }
                else
                {
                    // The text is exact; the sizes give the structure.
                    oPage.sMarkdown = pageAsMarkdown(oPage, nBody, dLevel);
                }

                // Any figure on the page becomes alt text, which is the part
                // no PDF reader does and the reason this belongs here.
                if (!oPage.bScanned && oPage.lImages.Count > 0 && o.fnDescribePicture != null)
                {
                    StringBuilder oAlt = new StringBuilder();
                    foreach (string sImage in oPage.lImages)
                    {
                        // A book of plates can carry two pictures on every
                        // page. One of his documents held 1,307, and asking
                        // about each is nine hours of work for a document
                        // nobody would read to the end. The largest are
                        // described -- they are the figures -- and the rest are
                        // named without one.
                        if (iLimit > 0 && iDescribed >= iLimit)
                        {
                            iPassedOver = iPassedOver + 1;
                            oAlt.AppendLine("![Picture on page " + oPage.iNumber.ToString()
                                            + ", not described: the limit of " + iLimit.ToString()
                                            + " was reached](page" + oPage.iNumber.ToString("000") + ".png)");
                            oAlt.AppendLine("");
                            continue;
                        }
                        string sShow = toPng(o, sImage);
                        if (sShow == "") sShow = sImage;
                        // THE AUTHOR'S OWN DESCRIPTION FIRST, where the PDF
                        // carries one.
                        //
                        // A tagged PDF's Figure elements hold the alt text
                        // somebody wrote for them. It is better than anything a
                        // model produces — it is what the author meant the
                        // picture to convey — and it costs nothing where the
                        // model costs about ninety seconds.
                        //
                        // The tree is the reading order, so the nth Figure
                        // describes the nth picture.
                        string sShown = "";
                        if (iTagAltUsed < lTaggedFigureAlt.Count
                            && lTaggedFigureAlt[iTagAltUsed].Trim() != "")
                        {
                            sShown = lTaggedFigureAlt[iTagAltUsed].Trim();
                            say(o, "  Page " + oPage.iNumber.ToString()
                                       + ": the PDF's own description is used, so the model was not asked.",
                                       "INFO", "");
                        }
                        if (iTagAltUsed < lTaggedFigureAlt.Count) iTagAltUsed = iTagAltUsed + 1;
                        if (sShown == "") sShown = describe(o, sShow);
                        if (sShown == "") continue;
                        say(o, "  Page " + oPage.iNumber.ToString() + " carries a picture: "
                                   + (sShown.Length > 120 ? sShown.Substring(0, 120) + "..." : sShown),
                                   "INFO", "");
                        iDescribed = iDescribed + 1;
                        oAlt.AppendLine("![" + sShown.TrimEnd('.').Replace("]", ")") + "](page"
                                        + oPage.iNumber.ToString("000") + ".png)");
                        oAlt.AppendLine("");
                    }
                    if (oAlt.Length > 0) oPage.sMarkdown = oAlt.ToString() + oPage.sMarkdown;
                }
            }

            // THE TAGS AS A CHECK ON THE INFERENCE.
            //
            // A tagged PDF states how many headings it has and how deep they
            // go. That is worth having even before the tags can be matched to
            // the text on the page, because it says whether the inference is
            // anywhere near right — and this project has just produced 4,336
            // headings for a document that should have had a few hundred.
            //
            // Matching a tag to the words it covers needs marked-content
            // identifiers and the page's content stream, which is a larger
            // piece of machinery. Counting is not, and it catches the failure
            // that actually happened.
            int iTaggedHeadings = 0;
            int iDeepestTag = 0;
            foreach (TaggedItem oItem in lTagged)
            {
                if (oItem.iLevel <= 0) continue;
                iTaggedHeadings = iTaggedHeadings + 1;
                if (oItem.iLevel > iDeepestTag) iDeepestTag = oItem.iLevel;
            }

            // THE SECOND PASS: now that every page has been read, the body
            // size can be measured and the OCR pages given their structure.
            //
            // Nothing to redo where the document carried its own text: those
            // pages had their sizes from the start.
            int iOcrPages = 0;
            foreach (PdfPage oPage in lPages) { if (oPage.bFromOcr) iOcrPages = iOcrPages + 1; }
            if (iOcrPages > 0)
            {
                double nOcrBody = bodySizeOf(lPages);
                // TIGHTEN UNTIL THE HEADINGS ARE A PLAUSIBLE PART OF THE
                // DOCUMENT.
                //
                // No setting can be right for every scan, because the noise in
                // a measured height depends on the scan. So the document
                // corrects the setting: if more than a tenth of its lines would
                // become headings, the bar goes up and it is tried again.
                //
                // ONE LINE IN TWENTY-FIVE. A tenth sounded safe and is not: his
                // journal's 1,769 headings in about 20,000 lines is 8.8 per
                // cent, which would have passed a tenth untouched. A well-made
                // document runs nearer a fiftieth, so twenty-five is still
                // generous and actually bites.
                //
                // This needs no tags, which most documents do not have.
                Dictionary<double, int> dOcrLevel = headingLevels(lPages, nOcrBody);
                int iLines = 0;
                foreach (PdfPage oPage in lPages) iLines = iLines + oPage.lLines.Count;
                double nBar = nHeadingSize;
                if (nBar < 1.05 || nBar > 4.0) nBar = 1.4;
                for (int iTry = 0; iTry < 6; iTry = iTry + 1)
                {
                    int iWouldBe = 0;
                    foreach (PdfPage oPage in lPages)
                    {
                        foreach (PageLine oLine in oPage.lLines)
                        {
                            double nAt = Math.Round(oLine.nSize * 2.0) / 2.0;
                            string sTrim = oLine.sText == null ? "" : oLine.sText.Trim();
                            if (dOcrLevel.ContainsKey(nAt) && sTrim.Length <= 100
                                && !Regex.IsMatch(sTrim, @"[.;,][""'\)]?$"))
                                iWouldBe = iWouldBe + 1;
                        }
                    }
                    if (iLines == 0 || iWouldBe * 25 <= iLines) break;
                    nBar = nBar * 1.15;
                    say(o, "  " + iWouldBe.ToString() + " of " + iLines.ToString()
                               + " lines would be headings, which is too many for one document. "
                               + "Trying a taller bar: " + num(nBar) + " times the body.", "INFO", "");
                    dOcrLevel = headingLevelsAt(lPages, nOcrBody, nBar);
                }
                // THE TAGS SET THE DEPTH, where the document has them.
                //
                // A tagged PDF states how deep its headings go. Inferring six
                // levels for a document whose author used three invents a
                // structure nobody wrote, so the inference is capped at what
                // the document says.
                if (iDeepestTag > 0)
                {
                    List<double> lKeys = new List<double>(dOcrLevel.Keys);
                    bool bCapped = false;
                    foreach (double nKey in lKeys)
                    {
                        if (dOcrLevel[nKey] <= iDeepestTag + 1) continue;
                        dOcrLevel[nKey] = iDeepestTag + 1;
                        bCapped = true;
                    }
                    if (bCapped)
                        say(o, "  Its tags go " + iDeepestTag.ToString()
                                   + " levels deep, so the inferred headings are kept within that.",
                                   "INFO", "");
                }
                foreach (PdfPage oPage in lPages)
                {
                    if (!oPage.bFromOcr) continue;
                    oPage.sMarkdown = pageAsMarkdown(oPage, nOcrBody, dOcrLevel);
                }
                say(o, "Reading finished, so the shape of the document could be measured: letters are "
                           + num(nOcrBody) + " tall in the body text, and "
                           + counted(dOcrLevel.Count, "taller size becomes a heading level",
                                     "taller sizes become heading levels") + " across "
                           + counted(iOcrPages, "page read by Tesseract", "pages read by Tesseract") + ".",
                           "INFO", "");
            }

            // Assembled in page order, with a running header or footer dropped:
            // a line that repeats on most pages is furniture, not content.
            Dictionary<string, int> dRepeats = new Dictionary<string, int>();
            foreach (PdfPage oPage in lPages)
            {
                foreach (string sLine in oPage.sMarkdown.Replace("\r\n", "\n").Split('\n'))
                {
                    string sBare = Regex.Replace(sLine.Trim().ToLower(), @"\d+", "#");
                    if (sBare.Length < 3 || sBare.Length > 70) continue;
                    if (!dRepeats.ContainsKey(sBare)) dRepeats[sBare] = 0;
                    dRepeats[sBare] = dRepeats[sBare] + 1;
                }
            }
            int iFurniture = 0;
            StringBuilder oWhole = new StringBuilder();
            oWhole.AppendLine("# " + sRoot);
            oWhole.AppendLine("");
            // Said in the document itself, since a reader deserves to know how
            // much of its shape was stated and how much was guessed.
            // The document's own language, where it states one. Pandoc turns
            // this into the docx's language, which is what decides how a screen
            // reader pronounces it.
            if (sTaggedSaid != "")
            {
                oWhole.AppendLine(bTaggedDocument && bBuiltFromTags
                    ? "The original is a tagged PDF, and its tags carry the document, so its headings and "
                      + "lists are its own rather than worked out from the layout."
                    : bTaggedDocument
                    ? "The original is a tagged PDF, but its tags do not carry the whole document, so its "
                      + "headings and lists have been worked out from the layout."
                    : "The original is not a tagged PDF, so its headings and lists have been worked out "
                      + "from the layout rather than read from the document.");
                oWhole.AppendLine("");
            }
            oWhole.AppendLine("Read from " + counted(lPages.Count, "page", "pages") + " of "
                            + Path.GetFileName(sPdfPath) + ". "
                            // "Every page carried its own text" was said whenever
                            // no page was a scan — including when no page was
                            // anything at all, which is how a document that
                            // yielded nothing described itself as exact.
                            + (iWithText == 0 && iScanned == 0
                               ? "Nothing could be read from it: no page carried text, and no page "
                                 + "yielded a picture that could be read either."
                               : iScanned == 0
                               ? "Every page carried its own text, so the words are exact."
                               : counted(iScanned, "page was read from a picture", "pages were read from pictures")
                                 + ", where the words are a reading rather than a certainty; anything unclear "
                                 + "is marked."));
            oWhole.AppendLine("");
            bool bFirstPage = true;
            foreach (PdfPage oPage in lPages)
            {
                // A HARD PAGE BREAK BETWEEN PAGES, so the docx paginates the
                // way the PDF does.
                //
                // The reason is a real one: a blind lawyer reading a converted
                // brief has to be on the same page as the colleague across the
                // table. If page 14 of the document is page 14 of the PDF,
                // "see the second paragraph on page 14" means the same thing to
                // both of them. Without it the conversion is readable and
                // useless for the argument.
                //
                // Pandoc has no native page break -- its issue 1934 is still
                // open -- so this writes the paragraph the pagebreak.lua filter
                // turns into one: a real break in Word, a styled div in a web
                // page, and a form feed where pages do not exist.
                if (!bFirstPage)
                {
                    oWhole.AppendLine("\\pagebreak");
                    oWhole.AppendLine("");
                }
                bFirstPage = false;
                // And the page's own number, as a comment, so a reader of the
                // Markdown can find it and nothing is shown that the PDF does
                // not show.
                oWhole.AppendLine("<!-- page " + oPage.iNumber.ToString() + " -->");
                oWhole.AppendLine("");
                foreach (string sLine in oPage.sMarkdown.Replace("\r\n", "\n").Split('\n'))
                {
                    string sBare = Regex.Replace(sLine.Trim().ToLower(), @"\d+", "#");
                    if (sBare != "" && dRepeats.ContainsKey(sBare)
                        && dRepeats[sBare] > Math.Max(2, lPages.Count / 2)
                        && !sLine.TrimStart().StartsWith("#"))
                    {
                        iFurniture = iFurniture + 1;
                        continue;
                    }
                    oWhole.AppendLine(sLine);
                }
            }
            if (iByOcr > 0 || iByModel > 0)
                say(o, counted(iByOcr, "page was read by Tesseract", "pages were read by Tesseract")
                           + " and " + counted(iByModel, "by the picture model", "by the picture model") + ".",
                           "INFO", "");
            if (iFurniture > 0)
                say(o, counted(iFurniture, "running header or footer line was dropped",
                                   "running header or footer lines were dropped")
                           + ": a line repeating on most pages is furniture, not content.", "INFO", "");

            // How the inference did against what the document itself says.
            if (iTaggedHeadings > 0)
            {
                int iMade = 0;
                int iDeepestMade = 0;
                foreach (Match oOne in Regex.Matches(oWhole.ToString(), @"(?m)^(#{1,6})\s+\S"))
                {
                    iMade = iMade + 1;
                    if (oOne.Groups[1].Value.Length > iDeepestMade)
                        iDeepestMade = oOne.Groups[1].Value.Length;
                }
                say(o, "The document's own tags name " + counted(iTaggedHeadings, "heading", "headings")
                           + ", " + iDeepestTag.ToString() + " levels deep. This reading made "
                           + counted(iMade, "heading", "headings") + ", " + iDeepestMade.ToString()
                           + " levels deep.", "INFO", "");
                // Three times as many is not a difference of judgement, it is a
                // fault. A tenth as many is the same fault the other way.
                if (iMade > iTaggedHeadings * 3)
                    say(o, "  That is far more than the document says it has, so the sizes are being "
                               + "read too generously. Raise " + o.sHeadingSizeName + " to tighten it.", "ERROR");
                else if (iMade * 3 < iTaggedHeadings)
                    say(o, "  That is far fewer than the document says it has, so the sizes are being "
                               + "read too strictly. Lower " + o.sHeadingSizeName + " to loosen it.", "ERROR");
                else
                    say(o, "  Those are close enough that the inference is working on this document.",
                               "INFO", "");
            }

            // Levels closed across the whole document, so what is returned is
            // what will be written, and the review reads that.
            oResult.sMarkdown = closedHeadingGaps(oWhole.ToString());
            oResult.sMarkdown = withLinksAndFields(oResult.sMarkdown, lPages, o);
            oResult.bRead = true;
            oResult.bBuiltFromTags = bBuiltFromTags;
            oResult.iWithText = iWithText;
            oResult.iScanned = iScanned;
            oResult.iFigures = iFigures;
            oResult.iDescribed = iDescribed;
            oResult.iPassedOver = iPassedOver;
            oResult.iByOcr = iByOcr;
            oResult.iByModel = iByModel;
            oResult.iUnread = iUnread;
            oResult.iFurniture = iFurniture;
            return oResult;
        }

        // ---- links and form fields (19 October 2026) ----------------------
        //
        // LEARNED FROM FRAME PDF STUDIO (MIT, ripplelearning), a browser tool for
        // remediating PDFs, which reads a page's link annotations and its form
        // fields as well as its text. HomerScribe's reader read neither, so a
        // PDF's links became plain words and a filled form lost its answers.
        //
        // PdfPig's link and form readers are reached by reflection, so a PdfPig
        // without one simply gives nothing here rather than breaking a build.

        // The form fields of the document being read, each "label: value".
        public static List<string> lFormFields = new List<string>();

        static object propertyOf(object o, string sName)
        {
            if (o == null) return null;
            try
            {
                System.Reflection.PropertyInfo oProp = o.GetType().GetProperty(sName);
                return oProp == null ? null : oProp.GetValue(o, null);
            }
            catch (Exception) { return null; }
        }

        static string textOf(object o)
        {
            return o == null ? "" : Regex.Replace(o.ToString(), @"\s+", " ").Trim();
        }

        // linksOf: a page's links to the web or to mail, each {text, address}.
        static List<string[]> linksOf(Page oPage)
        {
            List<string[]> lLinks = new List<string[]>();
            try
            {
                System.Reflection.MethodInfo oMethod = oPage.GetType().GetMethod("GetHyperlinks", Type.EmptyTypes);
                if (oMethod == null) return lLinks;
                System.Collections.IEnumerable oAll = oMethod.Invoke(oPage, null) as System.Collections.IEnumerable;
                if (oAll == null) return lLinks;
                foreach (object oLink in oAll)
                {
                    string sUri = textOf(propertyOf(oLink, "Uri"));
                    if (!Regex.IsMatch(sUri, @"^(https?:|mailto:|ftp:)", RegexOptions.IgnoreCase)) continue;
                    lLinks.Add(new string[] { textOf(propertyOf(oLink, "Text")), sUri });
                }
            }
            catch (Exception) { }
            return lLinks;
        }

        // formFieldsOf: the document's form fields, as "label: value" or the label
        // alone when the field is empty. The label is the field's tooltip where it
        // has one, which is what its author wrote for a person, else its name.
        static List<string> formFieldsOf(PdfDocument oDoc)
        {
            List<string> lFields = new List<string>();
            try
            {
                System.Reflection.MethodInfo oMethod = oDoc.GetType().GetMethod("TryGetForm");
                if (oMethod == null) return lFields;
                object[] aArgs = new object[] { null };
                object oGot = oMethod.Invoke(oDoc, aArgs);
                if (!(oGot is bool) || !(bool) oGot || aArgs[0] == null) return lFields;
                System.Collections.IEnumerable oAll = propertyOf(aArgs[0], "Fields") as System.Collections.IEnumerable;
                if (oAll != null) foreach (object oField in oAll) addFormField(oField, "", lFields, 0);
            }
            catch (Exception) { }
            return lFields;
        }

        static void addFormField(object oField, string sParent, List<string> lFields, int iDepth)
        {
            if (oField == null || iDepth > 8 || lFields.Count > 2000) return;
            object oInfo = propertyOf(oField, "Information");
            string sLabel = textOf(propertyOf(oInfo, "AlternateName"));
            if (sLabel == "") sLabel = textOf(propertyOf(oInfo, "PartialName"));
            if (sLabel == "") sLabel = sParent;
            System.Collections.IEnumerable oChildren = propertyOf(oField, "Children") as System.Collections.IEnumerable;
            if (oChildren != null && !(oChildren is string))
            {
                foreach (object oChild in oChildren) addFormField(oChild, sLabel, lFields, iDepth + 1);
                return;
            }
            string sValue = "";
            object oValue = propertyOf(oField, "Value");
            object oChecked = propertyOf(oField, "IsChecked");
            object oOptions = propertyOf(oField, "SelectedOptions");
            // A radio button is one child of its group; only the chosen one is listed, under the group's label.
            object oSelected = propertyOf(oField, "IsSelected");
            if (oSelected is bool) { if (!(bool) oSelected) return; sValue = "selected"; }
            else if (oChecked is bool) sValue = (bool) oChecked ? "checked" : "not checked";
            else if (oOptions is System.Collections.IEnumerable && !(oOptions is string))
            {
                List<string> lPicked = new List<string>();
                foreach (object oPick in (System.Collections.IEnumerable) oOptions) { string sPick = textOf(oPick); if (sPick != "") lPicked.Add(sPick); }
                sValue = string.Join(", ", lPicked.ToArray());
            }
            else if (oValue != null && !(oValue is System.Collections.IEnumerable && !(oValue is string))) sValue = textOf(oValue);
            if (sLabel == "") return;
            lFields.Add(sValue == "" ? sLabel : sLabel + ": " + sValue);
        }

        // withLinksAndFields: each link's words made a Markdown link where they next
        // occur in reading order, matched across line breaks and Markdown's escapes;
        // a link whose words cannot be found is listed at the end so none is lost;
        // then the form fields, when the document has any.
        static string withLinksAndFields(string sMarkdown, List<PdfPage> lPages, Options o)
        {
            int iCursor = 0, iLinked = 0;
            List<string> lUnplaced = new List<string>();
            foreach (PdfPage oPage in lPages)
            {
                foreach (string[] aLink in oPage.lLinks)
                {
                    string sText = aLink[0], sUri = aLink[1];
                    if (sText.Length == 0 || sText.Length > 200) { lUnplaced.Add(sUri); continue; }
                    List<string> lWords = new List<string>();
                    foreach (string sWord in sText.Split(' ')) if (sWord != "") lWords.Add(Regex.Escape(escapedForMarkdown(sWord)).Replace(@"\\", @"\\?"));
                    Regex oFind = new Regex(@"(?<![\[\w])" + string.Join(@"\s+", lWords.ToArray()) + @"(?![\w\]])");
                    Match oHit = oFind.Match(sMarkdown, Math.Min(iCursor, sMarkdown.Length));
                    if (!oHit.Success) oHit = oFind.Match(sMarkdown);
                    if (!oHit.Success || sMarkdown.Substring(oHit.Index + oHit.Length).StartsWith("](")) { lUnplaced.Add(sText + " " + sUri); continue; }
                    string sLink = "[" + oHit.Value + "](" + sUri.Replace(")", "%29").Replace(" ", "%20") + ")";
                    sMarkdown = sMarkdown.Substring(0, oHit.Index) + sLink + sMarkdown.Substring(oHit.Index + oHit.Length);
                    iCursor = oHit.Index + sLink.Length;
                    iLinked++;
                }
            }
            StringBuilder oOut = new StringBuilder(sMarkdown.TrimEnd());
            oOut.Append("\r\n");
            if (lUnplaced.Count > 0)
            {
                oOut.Append("\r\n## Links\r\n\r\n");
                foreach (string sOne in lUnplaced)
                {
                    int iSpace = sOne.LastIndexOf(' ');
                    string sUri = iSpace < 0 ? sOne : sOne.Substring(iSpace + 1);
                    string sWords = iSpace < 0 ? sOne : sOne.Substring(0, iSpace);
                    oOut.Append("- [" + escapedForMarkdown(sWords) + "](" + sUri.Replace(")", "%29").Replace(" ", "%20") + ")\r\n");
                }
            }
            if (lFormFields.Count > 0)
            {
                oOut.Append("\r\n## Form fields\r\n\r\n");
                foreach (string sField in lFormFields) oOut.Append("- " + escapedForMarkdown(sField) + "\r\n");
            }
            int iAll = 0;
            foreach (PdfPage oPage in lPages) iAll += oPage.lLinks.Count;
            if (iAll > 0 || lFormFields.Count > 0)
                say(o, "Links: " + iLinked + " of " + iAll + " placed on their words" + (lUnplaced.Count > 0 ? ", " + lUnplaced.Count + " listed at the end" : "")
                       + "; form fields: " + lFormFields.Count + ".", "INFO", "");
            return oOut.ToString();
        }

        // ---- Tesseract ---------------------------------------------------

        static string sTesseractFound = null;

        // The options of the document being read, for messages from Tesseract.
        static Options oNow = null;

        // findTesseract: Tesseract's path, beside the program, in its machine-wide
        // folder, or on the PATH; "" when it is not on this computer. Found once
        // per session.
        public static string findTesseract()
        {
            if (sTesseractFound != null) return sTesseractFound;
            sTesseractFound = "";
            List<string> lsTry = new List<string>();
            lsTry.Add(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "tesseract.exe"));
            lsTry.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Tesseract-OCR\\tesseract.exe"));
            lsTry.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Tesseract-OCR\\tesseract.exe"));
            foreach (string sTry in lsTry)
            {
                try { if (File.Exists(sTry)) { sTesseractFound = sTry; return sTesseractFound; } } catch (Exception) { }
            }
            string sPath = Environment.GetEnvironmentVariable("PATH");
            if (sPath == null) sPath = "";
            foreach (string sFolder in sPath.Split(';'))
            {
                if (sFolder.Trim() == "") continue;
                try
                {
                    string sTry = Path.Combine(sFolder.Trim().Trim('"'), "tesseract.exe");
                    if (File.Exists(sTry)) { sTesseractFound = sTry; return sTesseractFound; }
                }
                catch (Exception) { }
            }
            return sTesseractFound;
        }

        // runUtf8: a program's output, read as UTF-8, which is what Tesseract
        // writes. Read as a code page, a right single quote became three letters
        // ninety-eight times in one of his documents. Waits at most iSeconds.
        static int runUtf8(string sProgram, string sArgs, int iSeconds, out string sOut, out string sErr)
        {
            sOut = "";
            sErr = "";
            ProcessStartInfo oStart = new ProcessStartInfo(sProgram, sArgs);
            oStart.UseShellExecute = false;
            oStart.CreateNoWindow = true;
            oStart.RedirectStandardOutput = true;
            oStart.RedirectStandardError = true;
            oStart.StandardOutputEncoding = Encoding.UTF8;
            oStart.StandardErrorEncoding = Encoding.UTF8;
            StringBuilder oOut = new StringBuilder();
            StringBuilder oErr = new StringBuilder();
            using (Process oRun = new Process())
            {
                oRun.StartInfo = oStart;
                oRun.OutputDataReceived += delegate(object oSender, DataReceivedEventArgs oArgs)
                { if (oArgs.Data != null) lock (oOut) oOut.AppendLine(oArgs.Data); };
                oRun.ErrorDataReceived += delegate(object oSender, DataReceivedEventArgs oArgs)
                { if (oArgs.Data != null) lock (oErr) oErr.AppendLine(oArgs.Data); };
                oRun.Start();
                oRun.BeginOutputReadLine();
                oRun.BeginErrorReadLine();
                if (!oRun.WaitForExit(iSeconds * 1000))
                {
                    try { oRun.Kill(); } catch (Exception) { }
                    sErr = "it took longer than " + iSeconds.ToString() + " seconds and was stopped";
                    return -1;
                }
                oRun.WaitForExit();
                lock (oOut) sOut = oOut.ToString();
                lock (oErr) sErr = oErr.ToString();
                return oRun.ExitCode;
            }
        }

        static string quoted(string sPath)
        {
            return "\"" + sPath + "\"";
        }

        static string tail(string sText, int iKeep)
        {
            if (sText == null) return "";
            sText = sText.Trim();
            return sText.Length <= iKeep ? sText : "..." + sText.Substring(sText.Length - iKeep);
        }

        // A scanned page read by Tesseract, with how sure it was.
        //
        // WHY THIS AND NOT THE MODEL. Tesseract cannot hallucinate: where it
        // fails it produces visible nonsense rather than fluent wrong text, and
        // it gives a confidence for every word, which no language model can. On
        // clean print its accuracy is at least as good, and it is roughly
        // twenty-five times faster. The model keeps the two jobs it is
        // genuinely better at -- describing pictures, and telling a heading
        // from a paragraph.
        //
        // The TSV output is asked for rather than plain text because it carries
        // the confidence and the line numbering in the same pass.
        public static string tesseractRead(string sTesseract, string sImagePath, out int iSure,
                                    List<double> lHeights)
        {
            iSure = 0;
            double nLineHigh = 0.0;
            int iHighWords = 0;
            string sOut = "";
            string sErr = "";
            // UTF-8, BECAUSE THAT IS WHAT TESSERACT WRITES.
            //
            // His 511 KB of Markdown carries "ΓÇÖ" ninety-eight times: a right
            // single quote, written as UTF-8 and read back as a code page. The
            // words were recognised correctly and mangled on the way in.
            int iCode = runUtf8(sTesseract, quoted(sImagePath) + " stdout tsv", 300, out sOut, out sErr);
            say(oNow, "  tesseract " + Path.GetFileName(sImagePath) + " stdout tsv: exit code " + iCode.ToString(), "INFO", "");
            if (iCode != 0 || sOut.Trim() == "")
            {
                say(oNow, "  Tesseract read nothing from " + Path.GetFileName(sImagePath)
                           + (sErr.Trim() == "" ? "." : ": " + tail(sErr, 120)), "INFO", "");
                return "";
            }
            StringBuilder oText = new StringBuilder();
            StringBuilder oLine = new StringBuilder();
            int iLastLine = -1;
            int iTotal = 0;
            int iWords = 0;
            bool bFirst = true;
            foreach (string sRow in sOut.Replace("\r\n", "\n").Split('\n'))
            {
                if (bFirst) { bFirst = false; continue; }          // the header row
                string[] asBit = sRow.Split('\t');
                if (asBit.Length < 12) continue;
                string sWord = asBit[11].Trim();
                if (sWord == "") continue;
                // TESSERACT 5 WRITES CONFIDENCE AS A FLOAT: "96.5", not "96".
                //
                // int.TryParse("96.5") fails and leaves zero, so every word
                // scored nothing, every page came out "0 sure", every page
                // fell under the floor of 70, and every page went to the
                // picture model. Tesseract was installed, found and read
                // correctly, and did no work at all -- which is exactly why
                // there was no speed gain.
                //
                // Parsed as a number now, and with the invariant culture,
                // since a machine set to a comma decimal would fail the same
                // way on the same string.
                double nConf = 0.0;
                double.TryParse(asBit[10], NumberStyles.Any, CultureInfo.InvariantCulture, out nConf);
                int iConf = (int)Math.Round(nConf);
                if (iConf < 0) continue;
                iTotal = iTotal + iConf;
                iWords = iWords + 1;
                int iLine = 0;
                int.TryParse(asBit[4], out iLine);
                int iBlock = 0;
                int.TryParse(asBit[2], out iBlock);
                int iWhich = iBlock * 1000 + iLine;
                if (iWhich != iLastLine && iLastLine >= 0)
                {
                    oText.AppendLine(oLine.ToString().Trim());
                    lHeights.Add(iHighWords == 0 ? 0.0 : nLineHigh / iHighWords);
                    oLine.Length = 0;
                    nLineHigh = 0.0;
                    iHighWords = 0;
                }
                iLastLine = iWhich;
                oLine.Append(sWord + " ");
                // The TSV carries each word's HEIGHT, which does for a scanned
                // page exactly what point size does for a text one: the height
                // most of the characters are set at is the body, and anything
                // markedly taller is a heading.
                int iHigh = 0;
                int.TryParse(asBit[9], out iHigh);
                if (iHigh > 0)
                {
                    nLineHigh = nLineHigh + iHigh;
                    iHighWords = iHighWords + 1;
                }
            }
            if (oLine.Length > 0)
            {
                oText.AppendLine(oLine.ToString().Trim());
                lHeights.Add(iHighWords == 0 ? 0.0 : nLineHigh / iHighWords);
            }
            iSure = iWords == 0 ? 0 : iTotal / iWords;
            return oText.ToString();
        }

        // ---- file to file, for Conversion -------------------------------

        // True when the last toFile failed because its pages are scans, so
        // Conversion tries OCR next rather than a reader that cannot see them.
        public static bool bLastWasScans = false;

        // toFile: a PDF written as Markdown (.md) or plain text (.txt and any
        // other target), for Conversion's pdfstructure and ocr engines. bOcr
        // reads scanned pages with Tesseract; without it a document of scans
        // fails, so the next way in conversions.inix is tried.
        public static bool toFile(string sSource, string sTarget, bool bOcr, out string sError)
        {
            sError = "";
            bLastWasScans = false;
            Options o = new Options();
            if (bOcr)
            {
                o.sTesseract = findTesseract();
                if (o.sTesseract == "") { sError = "Tesseract is not installed"; return false; }
            }
            Result oResult = read(sSource, o);
            if (!oResult.bRead)
            {
                sError = oResult.sTrouble == "" ? "nothing could be read from it" : oResult.sTrouble;
                return false;
            }
            if (oResult.iWithText == 0 && oResult.iByOcr == 0 && !oResult.bBuiltFromTags)
            {
                bLastWasScans = oResult.iScanned > 0;
                sError = oResult.iScanned > 0
                       ? "its pages are scans, which only OCR can read" + (bOcr ? ", and Tesseract read none of them" : "")
                       : "no page carries text";
                return false;
            }
            string sText = oResult.sMarkdown;
            if (!Path.GetExtension(sTarget).Equals(".md", StringComparison.OrdinalIgnoreCase)) sText = plainFrom(sText);
            File.WriteAllText(sTarget, sText, new UTF8Encoding(true));
            return true;
        }

        // plainFrom: the Markdown this class writes, as plain text. Heading marks
        // and the page comments go; a page break becomes a form feed, the plain
        // text page break.
        public static string plainFrom(string sMarkdown)
        {
            StringBuilder oOut = new StringBuilder();
            foreach (string sLine in sMarkdown.Replace("\r\n", "\n").Split('\n'))
            {
                string sTrim = sLine.Trim();
                if (Regex.IsMatch(sTrim, @"^<!-- page \d+ -->$")) continue;
                if (sTrim == "\\pagebreak") { oOut.Append("\f"); continue; }
                string sPlain = Regex.Replace(sLine, @"^\s{0,3}#{1,6}\s+", "");
                sPlain = Regex.Replace(sPlain, @"\*\*([^*]+)\*\*", "$1");
                sPlain = Regex.Replace(sPlain, @"(?<![*\w])\*([^*\s][^*]*)\*(?![*\w])", "$1");
                sPlain = Regex.Replace(sPlain, @"\\([\\`*_{}\[\]()#+\-.!|>])", "$1");
                oOut.Append(sPlain + "\r\n");
            }
            return oOut.ToString();
        }


        // ---- the reader proper, from HomerScribe's PdfRead.cs ------------

        // Every page's lines and pictures, taken out of the file.
        //
        // Letters are grouped into lines by their vertical position, because
        // PdfPig gives letters and a line is what a reader needs. Two letters
        // within a third of their own height are on the same line; that
        // tolerance is what keeps a subscript with its paragraph and a
        // superscript off its own line.

        // Words, grouped into blocks, put in the order a person reads them.
        //
        // PdfPig's own layout analysis: NearestNeighbourWordExtractor builds
        // words from letters by spacing, DocstrumBoundingBoxes groups them into
        // blocks, and UnsupervisedReadingOrderDetector orders the blocks. All
        // three are better tested than anything written here, and the last is
        // the one that makes a two-column page read down each column rather
        // than across the gutter.
        static bool readInOrder(Page oPage, PdfPage oOut)
        {
            try
            {
                // GetWords hands back an IEnumerable, not a list. The compiler
                // said so plainly:
                //   error CS0266: Cannot implicitly convert type
                //   'IEnumerable<Word>' to 'IReadOnlyList<Word>'
                // Taking a list of it once is better than leaving it lazy,
                // since it is walked more than once below.
                List<Word> lWords = new List<Word>(oPage.GetWords(NearestNeighbourWordExtractor.Instance));
                if (lWords.Count == 0) return false;
                List<TextBlock> lBlocks = new List<TextBlock>(DocstrumBoundingBoxes.Instance.GetBlocks(lWords));
                if (lBlocks.Count == 0) return false;
                IEnumerable<TextBlock> lOrdered =
                    UnsupervisedReadingOrderDetector.Instance.Get(lBlocks);
                if (lOrdered == null) return false;
                foreach (TextBlock oBlock in lOrdered)
                {
                    foreach (TextLine oTextLine in oBlock.TextLines)
                    {
                        PageLine oLine = new PageLine();
                        oLine.sText = oTextLine.Text;
                        oLine.nTop = oTextLine.BoundingBox.Bottom;
                        double nSize = 0.0;
                        int iCount = 0;
                        string sFont = "";
                        bool bSawBold = false;
                        bool bSawItalic = false;
                        foreach (Word oWord in oTextLine.Words)
                        {
                            foreach (Letter oLetter in oWord.Letters)
                            {
                                nSize = nSize + oLetter.PointSize;
                                iCount = iCount + 1;
                                // FontDetails, not Font: the older name is obsolete, and this
                                // one carries IsBold and IsItalic outright rather than
                                // leaving them to be read out of the typeface name.
                                if (sFont == "" && oLetter.FontDetails != null)
                                {
                                    sFont = oLetter.FontDetails.Name;
                                    if (oLetter.FontDetails.IsBold) bSawBold = true;
                                    if (oLetter.FontDetails.IsItalic) bSawItalic = true;
                                }
                            }
                        }
                        oLine.nSize = iCount == 0 ? 0.0 : nSize / iCount;
                        if (sFont == null) sFont = "";
                        sFont = sFont.ToLower();
                        // The font's own flags first, since it states what the
                        // name only implies; the name is still read, because
                        // plenty of PDFs set neither flag and say "Times-Bold".
                        oLine.bBold = bSawBold || sFont.Contains("bold") || sFont.Contains("black")
                                    || sFont.Contains("heavy") || sFont.Contains("semibold");
                        oLine.bItalic = bSawItalic || sFont.Contains("italic") || sFont.Contains("oblique");
                        if (oLine.sText != null && oLine.sText.Trim() != "") oOut.lLines.Add(oLine);
                    }
                }
                return oOut.lLines.Count > 0;
            }
            catch (Exception)
            {
                // A page the analysis cannot handle falls back below rather
                // than taking the whole document down.
                return false;
            }
        }

        // The older way: letters sorted by position and grouped into lines.
        // Kept because a page read badly beats a page not read at all.
        static bool readByPosition(Page oPage, PdfPage oOut)
        {
            List<Letter> lLetters = new List<Letter>();
            foreach (Letter oLetter in oPage.Letters) lLetters.Add(oLetter);
            lLetters.Sort(delegate(Letter oLeft, Letter oRight)
            {
                int iSame = oRight.BoundingBox.Bottom.CompareTo(oLeft.BoundingBox.Bottom);
                if (iSame != 0) return iSame;
                return oLeft.BoundingBox.Left.CompareTo(oRight.BoundingBox.Left);
            });
            PageLine oLine = null;
            double nLastBottom = double.NaN;
            foreach (Letter oLetter in lLetters)
            {
                double nBottom = oLetter.BoundingBox.Bottom;
                double nHeight = Math.Max(1.0, oLetter.BoundingBox.Height);
                bool bNewLine = oLine == null
                              || double.IsNaN(nLastBottom)
                              || Math.Abs(nBottom - nLastBottom) > nHeight / 3.0;
                if (bNewLine)
                {
                    if (oLine != null && oLine.sText.Trim() != "") oOut.lLines.Add(oLine);
                    oLine = new PageLine();
                    oLine.nTop = nBottom;
                    oLine.nSize = oLetter.PointSize;
                    // Bold and italic, taken from the font's own name.
                    //
                    // He wants emphasis kept and font CHOICES and SIZES discarded: a
                    // size decides a heading level and then has no further business
                    // in the Markdown, and a typeface name has none at any point. A
                    // PDF names its fonts "Times-BoldItalic" or "Arial,Bold", so the
                    // name carries the emphasis and nothing else is needed.
                    string sFont = "";
                    try
                    {
                        if (oLetter.FontDetails != null)
                            {
                                sFont = oLetter.FontDetails.Name;
                                if (oLetter.FontDetails.IsBold) oLine.bBold = true;
                                if (oLetter.FontDetails.IsItalic) oLine.bItalic = true;
                            }
                    }
                    catch (Exception)
                    {
                    }
                    if (sFont == null) sFont = "";
                    sFont = sFont.ToLower();
                    oLine.bBold = sFont.Contains("bold") || sFont.Contains("black")
                                || sFont.Contains("heavy") || sFont.Contains("semibold");
                    oLine.bItalic = sFont.Contains("italic") || sFont.Contains("oblique");
                }
                oLine.sText = oLine.sText + oLetter.Value;
                // The size of a line is the size of most of it, so
                // a capital dropped cap does not make a heading of
                // a paragraph.
                if (oLetter.PointSize > 0 && oLine.sText.Length > 3)
                    oLine.nSize = (oLine.nSize * 3.0 + oLetter.PointSize) / 4.0;
                nLastBottom = nBottom;
            }
            if (oLine != null && oLine.sText.Trim() != "") oOut.lLines.Add(oLine);


            return oOut.lLines.Count > 0;
        }

        // Do these bytes already begin like a picture?
        static bool looksLikeAnImage(byte[] aBytes)
        {
            if (aBytes == null || aBytes.Length < 12) return false;
            if (aBytes[0] == 0xFF && aBytes[1] == 0xD8 && aBytes[2] == 0xFF) return true;          // JPEG
            if (aBytes[0] == 0x89 && aBytes[1] == 0x50 && aBytes[2] == 0x4E && aBytes[3] == 0x47)  // PNG
                return true;
            if (aBytes[4] == 0x6A && aBytes[5] == 0x50) return true;                               // JPEG 2000
            return false;
        }

        // An ASCII85 stream, decoded. The bytes back unchanged if it was not one.
        //
        // ASCII85 packs four bytes into five printable characters, "z" stands
        // for four zero bytes, and "~>" ends it. Whitespace is ignored, which
        // matters because a PDF wraps these streams at 80 characters.
        static byte[] unAscii85(byte[] aBytes)
        {
            if (aBytes == null || aBytes.Length < 8) return aBytes;
            try
            {
                List<byte> lOut = new List<byte>();
                uint iGroup = 0;
                int iHave = 0;
                foreach (byte iAt in aBytes)
                {
                    char cAt = (char)iAt;
                    if (cAt == '~') break;
                    if (char.IsWhiteSpace(cAt)) continue;
                    if (cAt == 'z' && iHave == 0)
                    {
                        lOut.Add(0); lOut.Add(0); lOut.Add(0); lOut.Add(0);
                        continue;
                    }
                    if (cAt < '!' || cAt > 'u') return aBytes;      // not ASCII85 at all
                    iGroup = iGroup * 85 + (uint)(cAt - '!');
                    iHave = iHave + 1;
                    if (iHave != 5) continue;
                    lOut.Add((byte)(iGroup >> 24)); lOut.Add((byte)(iGroup >> 16));
                    lOut.Add((byte)(iGroup >> 8)); lOut.Add((byte)iGroup);
                    iGroup = 0;
                    iHave = 0;
                }
                if (iHave > 1)
                {
                    // A part group is padded with 'u' and the padding dropped.
                    for (int iPad = iHave; iPad < 5; iPad = iPad + 1) iGroup = iGroup * 85 + 84;
                    byte[] aTail = new byte[] { (byte)(iGroup >> 24), (byte)(iGroup >> 16),
                                                (byte)(iGroup >> 8), (byte)iGroup };
                    for (int iAdd = 0; iAdd < iHave - 1; iAdd = iAdd + 1) lOut.Add(aTail[iAdd]);
                }
                byte[] aGot = lOut.ToArray();
                return aGot.Length > 8 ? aGot : aBytes;
            }
            catch (Exception)
            {
                return aBytes;
            }
        }

        // A deflated stream, inflated. Empty where it was not one.
        static byte[] inflated(byte[] aBytes)
        {
            if (aBytes == null || aBytes.Length < 3) return aBytes;
            // A zlib stream starts 0x78; raw deflate does not. Try both, since
            // a PDF may carry either.
            int[] aSkip = aBytes[0] == 0x78 ? new int[] { 2, 0 } : new int[] { 0, 2 };
            foreach (int iSkip in aSkip)
            {
                try
                {
                    using (MemoryStream oIn = new MemoryStream(aBytes, iSkip, aBytes.Length - iSkip))
                    using (DeflateStream oOut = new DeflateStream(oIn, CompressionMode.Decompress))
                    using (MemoryStream oGot = new MemoryStream())
                    {
                        byte[] aChunk = new byte[65536];
                        int iRead = 0;
                        while ((iRead = oOut.Read(aChunk, 0, aChunk.Length)) > 0)
                            oGot.Write(aChunk, 0, iRead);
                        byte[] aOut = oGot.ToArray();
                        if (aOut.Length > 0 && looksLikeAnImage(aOut)) return aOut;
                    }
                }
                catch (Exception)
                {
                }
            }
            return aBytes;
        }

        // IS THIS PDF TAGGED?
        //
        // A tagged PDF carries its own structure: real headings with real
        // levels, lists that know they are lists, tables that mark which cells
        // are headers, alt text on every figure, and a reading order the author
        // set rather than one inferred from where the ink fell.
        //
        // Everything HomerScribe infers -- font size into heading level, length
        // into heading or paragraph, word height on a scan -- is a
        // reconstruction of what a tagged PDF simply states. Where the tags are
        // there, they beat the inference every time, because they are what the
        // author meant rather than what the layout suggests.
        //
        // This only REPORTS it so far. Reading the tags is the next piece of
        // work, and saying whether they exist is worth having on its own: a
        // lawyer handed a brief can be told whether it was made accessible or
        // merely printed to PDF.
        public static bool bTaggedDocument = false;
        public static string sTaggedSaid = "";

        static bool documentIsTagged(PdfDocument oDoc, out string sHow)
        {
            sHow = "";
            try
            {
                // /MarkInfo /Marked true in the catalogue is the declaration,
                // and /StructTreeRoot is the tree itself. A document can claim
                // one without the other, so both are looked for and reported.
                bool bMarked = false;
                bool bHasTree = false;
                UglyToad.PdfPig.Tokens.DictionaryToken oCatalog = oDoc.Structure.Catalog.CatalogDictionary;
                if (oCatalog != null)
                {
                    UglyToad.PdfPig.Tokens.IToken oMarkInfo;
                    if (oCatalog.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("MarkInfo"), out oMarkInfo))
                    {
                        UglyToad.PdfPig.Tokens.DictionaryToken oMark =
                            oMarkInfo as UglyToad.PdfPig.Tokens.DictionaryToken;
                        UglyToad.PdfPig.Tokens.IToken oIsMarked;
                        if (oMark != null
                            && oMark.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("Marked"), out oIsMarked))
                        {
                            UglyToad.PdfPig.Tokens.BooleanToken oBool =
                                oIsMarked as UglyToad.PdfPig.Tokens.BooleanToken;
                            if (oBool != null) bMarked = oBool.Data;
                        }
                    }
                    UglyToad.PdfPig.Tokens.IToken oTree;
                    if (oCatalog.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("StructTreeRoot"), out oTree))
                        bHasTree = oTree != null;
                }
                if (bMarked && bHasTree) sHow = "it is tagged: it declares itself marked and carries a structure tree";
                else if (bHasTree) sHow = "it carries a structure tree but does not declare itself marked";
                else if (bMarked) sHow = "it declares itself marked but carries no structure tree, so there is nothing to read";
                else sHow = "it is not tagged, so its structure has to be inferred from the layout";
                return bHasTree;
            }
            catch (Exception oError)
            {
                sHow = "whether it is tagged could not be determined: " + oError.Message;
                return false;
            }
        }

        // ---- reading a tagged PDF's own structure ------------------------
        //
        // A structure tree is a dictionary tree and PdfPig hands over the
        // tokens, which is all that is needed. No library reads these on .NET
        // Framework: PdfPig says accessibility tagging is out of scope, iText
        // does it but is AGPL and would force HomerScribe off its MIT licence,
        // and VellumPdf is .NET 10 and writes rather than reads.
        //
        //   /StructTreeRoot   /K kids, /RoleMap custom name -> standard name
        //   each element      /S the type (H1..H6, P, L, LI, Table, Figure),
        //                     /Alt alternative text, /ActualText replacement
        //                     text, /Lang, and /K its own kids
        //
        // ROLE MAPPING IS APPLIED FIRST. Matterhorn checkpoint 02: only
        // standard PDF 1.7 tags may be used, and a custom tag must carry a role
        // map entry saying which standard tag it stands for. A document using
        // "Heading1" for "H1" is perfectly valid, and without the role map it
        // would look untagged.

        // public, because lTagged is public and a public field cannot hold a
        // less accessible type:
        //   error CS0052: Inconsistent accessibility: field type
        //   'List<HomerScribe.TaggedItem>' is less accessible than field
        //   'HomerScribe.lTagged'
        // The class was written before the field that exposes it, and its
        // default accessibility was never revisited.
        public class TaggedItem
        {
            public string sKind = "";      // the standard tag, after role mapping
            public string sAlt = "";       // alternative text, where the tag carries one
            public int iLevel;             // 1 to 6 for a heading, 0 otherwise
        }

        // The document's stated language, from the catalogue's /Lang.
        public static string sDocumentLanguage = "";

        // A language tag, or nothing.
        //
        // His ADA Checklist carries a /Lang of binary rubbish — an undecoded
        // byte string, not a language — and HomerScribe wrote it straight into
        // the Markdown's YAML front matter, where Pandoc choked:
        //
        //   Pandoc could not make the Word version: YAML parse exception at
        //   line 0, column 0
        //
        // So that document got no Word version at all, and the only sign was
        // one line in its log. A value read out of a file is data, not a fact,
        // and this one was neither checked nor escaped.
        //
        // A language tag looks like "en" or "en-US": letters, digits and
        // hyphens, and short. Anything else is not one.
        static string languageOnly(string sSaid)
        {
            if (sSaid == null) return "";
            sSaid = sSaid.Trim();
            if (sSaid.Length < 2 || sSaid.Length > 16) return "";
            if (!Regex.IsMatch(sSaid, @"^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8})*$")) return "";
            return sSaid;
        }

        // Figure descriptions the author wrote, in reading order.
        public static List<string> lTaggedFigureAlt = new List<string>();

        static Dictionary<string, string> dRoleMap = new Dictionary<string, string>();

        // The standard tag a name stands for, following the role map.
        static string standardTag(string sName)
        {
            if (sName == null) return "";
            string sAt = sName;
            // A role map can point at another custom name, so it is followed --
            // with a limit, since a broken document can point in a circle.
            for (int iHop = 0; iHop < 8; iHop = iHop + 1)
            {
                string sNext;
                if (!dRoleMap.TryGetValue(sAt, out sNext)) break;
                if (sNext == null || sNext == sAt) break;
                sAt = sNext;
            }
            return sAt;
        }

        // ---- the tag reader proper --------------------------------------
        //
        // His ten accessibility documents made the case with numbers. Nine are
        // tagged, and against what the tags say the inference is wrong in both
        // directions: 62 tagged headings where it found 10, 29 where it made
        // 118. Lists are worse — four documents with 6, 23, 32 and 65 tagged
        // lists produced NO list items at all.
        //
        // HOW A TAG FINDS ITS WORDS. A structure element's /K holds marked
        // content identifiers — numbers — and the page's content stream marks
        // each run of text with the matching identifier. PdfPig hands over
        // those runs through GetMarkedContents(), so the join is: element -> id
        // -> run of letters -> words.
        //
        // Where anything about this fails, the inference still runs. A tagged
        // document that cannot be read this way is no worse off than an
        // untagged one.

        // public, for the same reason TaggedItem is: lPieces is public and a
        // public field cannot hold a less accessible type. I made this exact
        // mistake on TaggedItem six builds ago and repeated it verbatim.
        public class TaggedPiece
        {
            public string sKind = "";
            public int iLevel;
            public string sText = "";
            public string sAlt = "";
            public int iPage;
            // Inside a list, however deeply. A tagged list puts its words in a
            // P inside an LBody inside an LI, so the piece that CARRIES the
            // text is a paragraph and only its ancestors say it is a list item.
            // Asking the piece alone gave his German checklist nine plain
            // paragraphs where nine list items were tagged.
            public bool bInList;
        }

        // An identifier's words, wherever on the document they sit.
        //
        // THE LOOP THIS REPLACES SEARCHED PAGES 1 TO iPage+2, and iPage only
        // advanced when something matched — so on a document whose first
        // elements did not match, it never looked past page three. His
        // 655-page handbook yielded 5,228 words against 65,577 on the pages;
        // two others came out at about a tenth as well. The tags were fine and
        // the lookup was blind.
        //
        // Every page is searched now, starting at the one we think we are on,
        // since that is nearly always right and makes the search cost nothing
        // in the ordinary case.
        static string wordsForMark(Dictionary<string, string> dText, int iId, int iFrom, int iPages,
                                   out int iFoundOn)
        {
            iFoundOn = 0;
            string sSaid;
            if (iFrom < 1) iFrom = 1;
            for (int iAt = iFrom; iAt <= iPages; iAt = iAt + 1)
            {
                if (!dText.TryGetValue(iAt.ToString() + ":" + iId.ToString(), out sSaid)) continue;
                iFoundOn = iAt;
                return sSaid;
            }
            for (int iAt = 1; iAt < iFrom; iAt = iAt + 1)
            {
                if (!dText.TryGetValue(iAt.ToString() + ":" + iId.ToString(), out sSaid)) continue;
                iFoundOn = iAt;
                return sSaid;
            }
            return "";
        }

        // Every marked run of text on every page, by page and identifier.
        static Dictionary<string, string> textByMark(PdfDocument oDoc)
        {
            Dictionary<string, string> dText = new Dictionary<string, string>();
            int iPage = 0;
            foreach (Page oPage in oDoc.GetPages())
            {
                iPage = iPage + 1;
                try
                {
                    foreach (MarkedContentElement oMark in oPage.GetMarkedContents())
                        gatherMark(oMark, iPage, dText);
                }
                catch (Exception)
                {
                }
            }
            return dText;
        }

        static void gatherMark(MarkedContentElement oMark, int iPage, Dictionary<string, string> dText)
        {
            if (oMark == null) return;
            try
            {
                if (oMark.MarkedContentIdentifier >= 0)
                {
                    StringBuilder oSaid = new StringBuilder();
                    foreach (Letter oLetter in oMark.Letters) oSaid.Append(oLetter.Value);
                    string sSaid = oSaid.ToString().Trim();
                    if (sSaid != "")
                    {
                        string sKey = iPage.ToString() + ":" + oMark.MarkedContentIdentifier.ToString();
                        if (dText.ContainsKey(sKey)) dText[sKey] = dText[sKey] + " " + sSaid;
                        else dText[sKey] = sSaid;
                    }
                }
                foreach (MarkedContentElement oChild in oMark.Children) gatherMark(oChild, iPage, dText);
            }
            catch (Exception)
            {
            }
        }

        // Everything the tree says, in the order the tree says it.
        //
        // The order matters as much as the content: the structure tree IS the
        // document's logical reading order, stated by whoever made it, which is
        // better than any inference from where the ink fell on the page.
        static List<TaggedItem> itemsFromTree(PdfDocument oDoc, out string sTrouble)
        {
            List<TaggedItem> lItems = new List<TaggedItem>();
            sTrouble = "";
            dRoleMap = new Dictionary<string, string>();
            try
            {
                UglyToad.PdfPig.Tokens.DictionaryToken oCatalog = oDoc.Structure.Catalog.CatalogDictionary;
                if (oCatalog == null) return lItems;
                UglyToad.PdfPig.Tokens.IToken oRootToken;
                if (!oCatalog.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("StructTreeRoot"), out oRootToken))
                    return lItems;
                UglyToad.PdfPig.Tokens.DictionaryToken oRoot =
                    resolved(oDoc, oRootToken) as UglyToad.PdfPig.Tokens.DictionaryToken;
                if (oRoot == null) return lItems;

                // The role map first, so every tag below can be translated.
                UglyToad.PdfPig.Tokens.IToken oRoleToken;
                if (oRoot.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("RoleMap"), out oRoleToken))
                {
                    UglyToad.PdfPig.Tokens.DictionaryToken oRoles =
                        resolved(oDoc, oRoleToken) as UglyToad.PdfPig.Tokens.DictionaryToken;
                    if (oRoles != null)
                    {
                        // DictionaryToken.Data is keyed by STRING, not by
                        // NameToken. The compiler said so exactly:
                        //   error CS0030: Cannot convert
                        //   KeyValuePair<string, IToken> to
                        //   KeyValuePair<NameToken, IToken>
                        foreach (KeyValuePair<string,
                                              UglyToad.PdfPig.Tokens.IToken> oPair in oRoles.Data)
                        {
                            UglyToad.PdfPig.Tokens.NameToken oTo =
                                oPair.Value as UglyToad.PdfPig.Tokens.NameToken;
                            if (oTo != null) dRoleMap[oPair.Key] = oTo.Data;
                        }
                    }
                }

                UglyToad.PdfPig.Tokens.IToken oKids;
                if (oRoot.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("K"), out oKids))
                    walkTree(oDoc, oKids, lItems, 0);
            }
            catch (Exception oError)
            {
                sTrouble = oError.Message;
            }
            return lItems;
        }

        // Whatever a token points at, or the token itself.
        //
        // Every other reader here went through asDictionary, which returns null
        // for anything that is not a dictionary — including an array, which is
        // what /K usually holds.
        static UglyToad.PdfPig.Tokens.IToken resolved(PdfDocument oDoc,
                                                      UglyToad.PdfPig.Tokens.IToken oToken)
        {
            try
            {
                for (int iHop = 0; iHop < 8; iHop = iHop + 1)
                {
                    UglyToad.PdfPig.Tokens.IndirectReferenceToken oRef =
                        oToken as UglyToad.PdfPig.Tokens.IndirectReferenceToken;
                    if (oRef == null) return oToken;
                    oToken = oDoc.Structure.TokenScanner.Get(oRef.Data).Data;
                }
                return oToken;
            }
            catch (Exception)
            {
                return oToken;
            }
        }

        static void walkTree(PdfDocument oDoc, UglyToad.PdfPig.Tokens.IToken oToken,
                             List<TaggedItem> lItems, int iDepth)
        {
            // A tree can be deep, and a broken one can be circular.
            if (iDepth > 40 || lItems.Count > 200000) return;
            try
            {
                // RESOLVE FIRST, THEN ASK WHAT IT IS.
                //
                // /K is very often an indirect reference to an array, and this
                // asked "is it an array?" of the reference itself, which it is
                // not — so the whole tree was dropped at the first hop and his
                // tagged document reported "no headings, lists, tables or
                // figures" from a tree that plainly has them.
                oToken = resolved(oDoc, oToken);
                UglyToad.PdfPig.Tokens.ArrayToken oArray = oToken as UglyToad.PdfPig.Tokens.ArrayToken;
                if (oArray != null)
                {
                    foreach (UglyToad.PdfPig.Tokens.IToken oOne in oArray.Data)
                        walkTree(oDoc, oOne, lItems, iDepth + 1);
                    return;
                }
                UglyToad.PdfPig.Tokens.DictionaryToken oNode =
                    oToken as UglyToad.PdfPig.Tokens.DictionaryToken;
                if (oNode == null) return;

                UglyToad.PdfPig.Tokens.IToken oType;
                if (oNode.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("S"), out oType))
                {
                    UglyToad.PdfPig.Tokens.NameToken oName = oType as UglyToad.PdfPig.Tokens.NameToken;
                    if (oName != null)
                    {
                        TaggedItem oItem = new TaggedItem();
                        oItem.sKind = standardTag(oName.Data);
                        Match oHead = Regex.Match(oItem.sKind, @"^H([1-9])$");
                        if (oHead.Success) oItem.iLevel = int.Parse(oHead.Groups[1].Value);
                        oItem.sAlt = stringFrom(oNode, "Alt");
                        if (oItem.sAlt == "") oItem.sAlt = stringFrom(oNode, "ActualText");
                        lItems.Add(oItem);
                    }
                }

                UglyToad.PdfPig.Tokens.IToken oKids;
                if (oNode.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("K"), out oKids))
                    walkTree(oDoc, oKids, lItems, iDepth + 1);
            }
            catch (Exception)
            {
            }
        }

        // MATCHED BY ORDER, NOT BY PAGE NUMBER.
        //
        // A structure element names its page with /Pg, an indirect reference to
        // the page object — and PdfPig does not expose a page's object number,
        // so that reference cannot be turned into a page number without going
        // round the library.
        //
        // It does not need to be. The structure tree IS the reading order, so
        // the figures in it come in the same order as the figures on the pages.
        // The nth Figure element describes the nth picture. That is exact for a
        // well-made document and no worse than nothing for a bad one.
        //
        // A stub returning zero was written here first. It would have compiled,
        // run, and quietly matched nothing.
        static List<string> figureDescriptionsInOrder(List<TaggedItem> lItems)
        {
            List<string> lAlt = new List<string>();
            foreach (TaggedItem oItem in lItems)
            {
                if (oItem.sKind != "Figure") continue;
                lAlt.Add(oItem.sAlt);
            }
            return lAlt;
        }

        static string stringFrom(UglyToad.PdfPig.Tokens.DictionaryToken oNode, string sKey)
        {
            try
            {
                UglyToad.PdfPig.Tokens.IToken oToken;
                if (!oNode.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create(sKey), out oToken)) return "";
                UglyToad.PdfPig.Tokens.StringToken oText = oToken as UglyToad.PdfPig.Tokens.StringToken;
                if (oText != null) return oText.Data == null ? "" : oText.Data.Trim();
                UglyToad.PdfPig.Tokens.HexToken oHex = oToken as UglyToad.PdfPig.Tokens.HexToken;
                if (oHex != null) return oHex.Data == null ? "" : oHex.Data.Trim();
                return "";
            }
            catch (Exception)
            {
                return "";
            }
        }

        public static List<TaggedPiece> lPieces = new List<TaggedPiece>();
        public static string sPiecesTrouble = "";
        static int iMarkPages = 0;

        // The document as its own tags describe it, in the order they give.
        static List<TaggedPiece> piecesFromTree(PdfDocument oDoc, out string sTrouble)
        {
            List<TaggedPiece> lOut = new List<TaggedPiece>();
            sTrouble = "";
            try
            {
                Dictionary<string, string> dText = textByMark(oDoc);
                iMarkPages = oDoc.NumberOfPages;
                if (dText.Count == 0)
                {
                    sTrouble = "the pages carry no marked content, so the tags cannot be joined to the words";
                    return lOut;
                }
                UglyToad.PdfPig.Tokens.DictionaryToken oCatalog = oDoc.Structure.Catalog.CatalogDictionary;
                if (oCatalog == null) return lOut;
                UglyToad.PdfPig.Tokens.IToken oRootToken;
                if (!oCatalog.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("StructTreeRoot"), out oRootToken))
                    return lOut;
                UglyToad.PdfPig.Tokens.DictionaryToken oRoot =
                    resolved(oDoc, oRootToken) as UglyToad.PdfPig.Tokens.DictionaryToken;
                if (oRoot == null) return lOut;
                UglyToad.PdfPig.Tokens.IToken oKids;
                if (oRoot.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("K"), out oKids))
                    walkForPieces(oDoc, oKids, lOut, dText, 0, 1);
            }
            catch (Exception oError)
            {
                sTrouble = oError.Message;
            }
            return lOut;
        }

        static void walkForPieces(PdfDocument oDoc, UglyToad.PdfPig.Tokens.IToken oToken,
                                  List<TaggedPiece> lOut, Dictionary<string, string> dText,
                                  int iDepth, int iPage)
        {
            walkForPieces(oDoc, oToken, lOut, dText, iDepth, iPage, false);
        }

        static void walkForPieces(PdfDocument oDoc, UglyToad.PdfPig.Tokens.IToken oToken,
                                  List<TaggedPiece> lOut, Dictionary<string, string> dText,
                                  int iDepth, int iPage, bool bInList)
        {
            if (iDepth > 40 || lOut.Count > 200000) return;
            try
            {
                oToken = resolved(oDoc, oToken);
                UglyToad.PdfPig.Tokens.ArrayToken oArray = oToken as UglyToad.PdfPig.Tokens.ArrayToken;
                if (oArray != null)
                {
                    foreach (UglyToad.PdfPig.Tokens.IToken oOne in oArray.Data)
                        walkForPieces(oDoc, oOne, lOut, dText, iDepth + 1, iPage, bInList);
                    return;
                }
                // A bare number is a marked content identifier: the words
                // belonging to whichever element we are inside.
                UglyToad.PdfPig.Tokens.NumericToken oNumber = oToken as UglyToad.PdfPig.Tokens.NumericToken;
                if (oNumber != null)
                {
                    if (lOut.Count > 0)
                    {
                        int iFoundOn = 0;
                        string sSaid = wordsForMark(dText, oNumber.Int, iPage, iMarkPages, out iFoundOn);
                        if (sSaid != "")
                        {
                            TaggedPiece oLast = lOut[lOut.Count - 1];
                            oLast.sText = (oLast.sText + " " + sSaid).Trim();
                            oLast.iPage = iFoundOn;
                        }
                    }
                    return;
                }
                UglyToad.PdfPig.Tokens.DictionaryToken oNode =
                    oToken as UglyToad.PdfPig.Tokens.DictionaryToken;
                if (oNode == null) return;

                UglyToad.PdfPig.Tokens.IToken oType;
                if (oNode.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("S"), out oType))
                {
                    UglyToad.PdfPig.Tokens.NameToken oName = oType as UglyToad.PdfPig.Tokens.NameToken;
                    if (oName != null)
                    {
                        TaggedPiece oPiece = new TaggedPiece();
                        oPiece.sKind = standardTag(oName.Data);
                        Match oHead = Regex.Match(oPiece.sKind, @"^H([1-9])$");
                        if (oHead.Success) oPiece.iLevel = int.Parse(oHead.Groups[1].Value);
                        else if (oPiece.sKind == "H") oPiece.iLevel = 1;
                        // A list anywhere above makes this a list item, even
                        // where the tag on this piece is only P.
                        if (oPiece.sKind == "L" || oPiece.sKind == "LI"
                            || oPiece.sKind == "LBody" || oPiece.sKind == "Lbl") bInList = true;
                        oPiece.bInList = bInList;
                        oPiece.sAlt = stringFrom(oNode, "Alt");
                        if (oPiece.sAlt == "") oPiece.sAlt = stringFrom(oNode, "ActualText");
                        lOut.Add(oPiece);
                    }
                }
                // An MCR dictionary names an identifier and sometimes its page.
                UglyToad.PdfPig.Tokens.IToken oMcid;
                if (oNode.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("MCID"), out oMcid))
                {
                    UglyToad.PdfPig.Tokens.NumericToken oId = oMcid as UglyToad.PdfPig.Tokens.NumericToken;
                    if (oId != null && lOut.Count > 0)
                    {
                        int iFoundOn = 0;
                        string sSaid = wordsForMark(dText, oId.Int, iPage, iMarkPages, out iFoundOn);
                        if (sSaid != "")
                        {
                            TaggedPiece oLast = lOut[lOut.Count - 1];
                            oLast.sText = (oLast.sText + " " + sSaid).Trim();
                            oLast.iPage = iFoundOn;
                        }
                    }
                }

                UglyToad.PdfPig.Tokens.IToken oKids;
                if (oNode.TryGet(UglyToad.PdfPig.Tokens.NameToken.Create("K"), out oKids))
                    walkForPieces(oDoc, oKids, lOut, dText, iDepth + 1,
                                  lOut.Count > 0 ? lOut[lOut.Count - 1].iPage : iPage, bInList);
            }
            catch (Exception)
            {
            }
        }

        public static List<TaggedItem> lTagged = new List<TaggedItem>();
        public static string sTagSummary = "";

        // What was found in the tree, in a sentence somebody would read.
        static string summaryOfTags(List<TaggedItem> lItems, string sTrouble)
        {
            if (sTrouble != "") return "its structure tree could not be read: " + sTrouble;
            if (lItems.Count == 0) return "its structure tree holds nothing that could be read";
            int iHeadings = 0;
            int iFigures = 0;
            int iWithAlt = 0;
            int iTables = 0;
            int iLists = 0;
            foreach (TaggedItem oItem in lItems)
            {
                if (oItem.iLevel > 0) iHeadings = iHeadings + 1;
                else if (oItem.sKind == "Figure")
                {
                    iFigures = iFigures + 1;
                    if (oItem.sAlt != "") iWithAlt = iWithAlt + 1;
                }
                else if (oItem.sKind == "Table") iTables = iTables + 1;
                else if (oItem.sKind == "L") iLists = iLists + 1;
            }
            List<string> lSaid = new List<string>();
            if (iHeadings > 0) lSaid.Add(iHeadings.ToString() + " headings");
            if (iLists > 0) lSaid.Add(iLists.ToString() + " lists");
            if (iTables > 0) lSaid.Add(iTables.ToString() + " tables");
            if (iFigures > 0)
                lSaid.Add(iFigures.ToString() + " figures, " + iWithAlt.ToString() + " with alternative text");
            if (lSaid.Count == 0) return "its structure tree names no headings, lists, tables or figures";
            return "its structure tree names " + string.Join(", ", lSaid.ToArray());
        }

        // EVERYTHING THIS FILE REMEMBERS, FORGOTTEN.
        //
        // Ten documents in one run reported identical tag counts in pairs: the
        // 63-page iOS guide and the 76-page Toolkit both "96 headings, 313 list
        // items"; the 15-page Training guide and the 46-page Charts guide both
        // "6 headings, 0 list items". The second document of each pair was
        // being described by the first document's tags.
        //
        // These are static because one document is read at a time — which is
        // true, and says nothing about what happens when the NEXT one starts.
        // Nothing cleared them, so a document whose own tree was unreadable
        // silently inherited its predecessor's.
        //
        // Cleared here, at the one place that cannot be forgotten: the moment a
        // PDF is opened.
        static void forgetTheLastDocument()
        {
            bTaggedDocument = false;
            sTaggedSaid = "";
            sTagSummary = "";
            sDocumentLanguage = "";
            sPiecesTrouble = "";
            iMarkPages = 0;
            lTagged = new List<TaggedItem>();
            lPieces = new List<TaggedPiece>();
            lTaggedFigureAlt = new List<string>();
            dRoleMap = new Dictionary<string, string>();
        }

        public static List<PdfPage> pagesOfPdf(string sPath, string sWorkDir, out string sTrouble)
        {
            List<PdfPage> lPages = new List<PdfPage>();
            sTrouble = "";
            forgetTheLastDocument();
            try
            {
                using (PdfDocument oDoc = PdfDocument.Open(sPath))
                {
                    lFormFields = formFieldsOf(oDoc);
                    // The document's stated language, which a screen reader
                    // uses to decide how to pronounce it.
                    sDocumentLanguage = "";
                    try
                    {
                        UglyToad.PdfPig.Tokens.DictionaryToken oCat =
                            oDoc.Structure.Catalog.CatalogDictionary;
                        if (oCat != null) sDocumentLanguage = languageOnly(stringFrom(oCat, "Lang"));
                    }
                    catch (Exception)
                    {
                    }
                    string sTagged = "";
                    bTaggedDocument = documentIsTagged(oDoc, out sTagged);
                    sTaggedSaid = sTagged;
                    // What the document says about itself, read before anything
                    // is inferred about it.
                    lTagged = new List<TaggedItem>();
                    if (bTaggedDocument)
                    {
                        string sTreeTrouble = "";
                        lTagged = itemsFromTree(oDoc, out sTreeTrouble);
                        sTagSummary = summaryOfTags(lTagged, sTreeTrouble);
                        lTaggedFigureAlt = figureDescriptionsInOrder(lTagged);
                        // And the document as the tags actually describe it.
                        string sPieceTrouble = "";
                        lPieces = piecesFromTree(oDoc, out sPieceTrouble);
                        sPiecesTrouble = sPieceTrouble;
                    }
                    int iAt = 0;
                    foreach (Page oPage in oDoc.GetPages())
                    {
                        iAt = iAt + 1;
                        PdfPage oOut = new PdfPage();
                        oOut.iNumber = iAt;
                        oOut.lLinks = linksOf(oPage);

                        // ---- the text layer, IN READING ORDER ----
                        //
                        // PdfPig ships this and HomerScribe was not using it.
                        // Words are assembled spatially, grouped into blocks by
                        // Docstrum, and the blocks put in the order a person
                        // would read them. Sorting letters top to bottom, which
                        // is what this did before, reads a two-column page
                        // straight across the gutter and produces nonsense --
                        // and a lawyer's brief is very often two columns.
                        //
                        // The old sorting is kept as a fallback: where the
                        // analysis throws, a page read badly beats a page not
                        // read at all.
                        if (readInOrder(oPage, oOut)) { }
                        else { oOut.lLines.Clear(); readByPosition(oPage, oOut); }
                        // ---- the picture layer ----
                        //
                        // Written out biggest first. On a scanned page the
                        // biggest IS the page; on a text page it is a figure
                        // that wants alt text.
                        List<IPdfImage> lFound = new List<IPdfImage>();
                        try
                        {
                            foreach (IPdfImage oImage in oPage.GetImages()) lFound.Add(oImage);
                        }
                        catch (Exception)
                        {
                        }
                        lFound.Sort(delegate(IPdfImage oLeft, IPdfImage oRight)
                        { return (oRight.WidthInSamples * oRight.HeightInSamples)
                                 .CompareTo(oLeft.WidthInSamples * oLeft.HeightInSamples); });
                        int iImage = 0;
                        foreach (IPdfImage oImage in lFound)
                        {
                            // Anything smaller than this is a rule, a bullet or
                            // a logo, not something worth describing.
                            if (oImage.WidthInSamples < 64 || oImage.HeightInSamples < 64) continue;
                            iImage = iImage + 1;
                            if (iImage > 6) break;
                            // RawBytes ONLY, and the extension chosen from what
                            // the bytes actually are.
                            //
                            // TryGetBytes does not exist on IPdfImage, and
                            // TryGetPng's shape varies between versions --
                            // guessing at either is what produced
                            //   error CS1061: IPdfImage does not contain a
                            //   definition for TryGetBytes
                            // The raw stream is always there, and for a scanned
                            // page it IS a JPEG. So: take the bytes, look at
                            // their first few, and name the file accordingly.
                            byte[] aBytes = null;
                            try
                            {
                                aBytes = oImage.RawBytes.ToArray();
                            }
                            catch (Exception)
                            {
                                aBytes = null;
                            }
                            if (aBytes == null || aBytes.Length < 512) continue;
                            // FLATE FIRST, WHERE THE BYTES ARE NOT AN IMAGE YET.
                            //
                            // His journal stores 101 of its 112 pages as
                            // /Filter [/FlateDecode /DCTDecode] -- a JPEG,
                            // deflated. RawBytes hands back the raw stream, so
                            // those do not begin FF D8 FF and were all passed
                            // over: the run read 11 pages and skipped 101.
                            //
                            // Inflating is the whole of the fix, and .NET has
                            // had it all along. A zlib stream begins 78 and a
                            // check byte; DeflateStream wants the two header
                            // bytes gone.
                            // ASCII85 FIRST, THEN FLATE.
                            //
                            // A PDF may wrap an image in more than one filter,
                            // and the order matters: /Filter [/ASCII85Decode
                            // /DCTDecode] means the bytes are a JPEG, printed
                            // as ASCII85 text. The inflater only knew about
                            // Flate, so those bytes never looked like a picture
                            // and every page was passed over — a purpose-built
                            // two-page scan reported "0 pictures in all".
                            if (!looksLikeAnImage(aBytes)) aBytes = unAscii85(aBytes);
                            if (!looksLikeAnImage(aBytes)) aBytes = inflated(aBytes);
                            if (aBytes == null || aBytes.Length < 512) continue;
                            string sKind = ".bin";
                            if (aBytes.Length > 3 && aBytes[0] == 0xFF && aBytes[1] == 0xD8 && aBytes[2] == 0xFF)
                                sKind = ".jpg";
                            else if (aBytes.Length > 8 && aBytes[0] == 0x89 && aBytes[1] == 0x50
                                     && aBytes[2] == 0x4E && aBytes[3] == 0x47)
                                sKind = ".png";
                            else if (aBytes.Length > 12 && aBytes[4] == 0x6A && aBytes[5] == 0x50)
                                sKind = ".jp2";
                            // Anything else is a raw bitmap with no header, and
                            // ffmpeg cannot open one without being told its
                            // shape. Those are passed over rather than written
                            // as a file nothing can read.
                            if (sKind == ".bin")
                            {
                                // Counted, not silently dropped. A chart in a
                                // born-digital PDF is often Flate-compressed
                                // raw samples with no header, and four of his
                                // documents reported "0 pictures" with no way
                                // to tell whether they had none or whether
                                // these were being discarded.
                                oOut.iSkippedPictures = oOut.iSkippedPictures + 1;
                                continue;
                            }
                            string sOut = Path.Combine(sWorkDir, "page" + iAt.ToString("000")
                                                     + "_" + iImage.ToString() + sKind);
                            try
                            {
                                File.WriteAllBytes(sOut, aBytes);
                                oOut.lImages.Add(sOut);
                            }
                            catch (Exception)
                            {
                            }
                        }

                        // A page with almost no text and a big picture is a
                        // scan, whatever else it claims.
                        int iChars = 0;
                        foreach (PageLine oOne in oOut.lLines) iChars = iChars + oOne.sText.Trim().Length;
                        oOut.bScanned = iChars < 40 && oOut.lImages.Count > 0;
                        lPages.Add(oOut);
                    }
                }
            }
            catch (Exception oError)
            {
                sTrouble = oError.Message;
            }
            return lPages;
        }

        // ---- a PDF made into accessible Markdown -------------------------
        //
        // BOTH LAYERS, because a PDF often has both and they know different
        // things. The text layer is EXACT where a reading of a picture is a
        // guess. The picture knows what the text cannot say: which lines look
        // like headings, what a figure shows, where a table's columns lie.
        //
        // Taken from the research he asked for:
        //
        //   Equalify Iris runs extract, assemble, review -- and reviews in TWO
        //   VIEWS, the marked-up text and a flattened screen-reader view,
        //   looping until a round changes nothing. The two-view review is the
        //   cleverest part of it and costs almost nothing.
        //
        //   OpenDataLoader-pdf, built with the PDF Association and the veraPDF
        //   people, does layout analysis for headings, tables, lists and
        //   reading order and emits Markdown with those preserved. It is close
        //   to the reference implementation of this -- in Java.
        //
        //   iTagPDF found its errors clustered where two regions were
        //   semantically alike: a caption merged with a table, a header with
        //   the title. Worth knowing where to look when this goes wrong.
        //
        //   PdfPig (Apache 2.0, .NET Standard, works back to .NET 4.5) is what
        //   makes it possible in C#. It hands back letters WITH POSITIONS AND
        //   FONT SIZES, not a string, which is what the heading inference
        //   below needs.

        public class PageLine
        {
            public string sText = "";
            public double nSize;
            public double nTop;
            // Emphasis is kept; the typeface and its size are not. A size
            // decides a heading level and then has no further business in the
            // Markdown, and a font name has none at any point.
            public bool bBold;
            public bool bItalic;
        }

        public class PdfPage
        {
            public int iNumber;
            public List<PageLine> lLines = new List<PageLine>();
            public List<string> lImages = new List<string>();
            public bool bScanned;
            public bool bFromOcr;      // read by Tesseract, so its lines have heights but no Markdown yet
            public int iSkippedPictures;   // found, but stored in a form nothing can open
            public List<string[]> lLinks = new List<string[]>();   // each {text, address}, from the page's link annotations
            public string sMarkdown = "";
        }

        // The body text size: the one the most CHARACTERS are set in.
        //
        // Not the average, which a few large headings drag upwards, and not
        // the commonest LINE size, since a page of headings would win. Rounded
        // to the half point so 11.04 and 11.0 count as one size.
        public static double bodySizeOf(List<PdfPage> lPages)
        {
            Dictionary<double, int> dSeen = new Dictionary<double, int>();
            foreach (PdfPage oPage in lPages)
            {
                foreach (PageLine oLine in oPage.lLines)
                {
                    double nAt = Math.Round(oLine.nSize * 2.0) / 2.0;
                    if (nAt <= 0.0) continue;
                    if (!dSeen.ContainsKey(nAt)) dSeen[nAt] = 0;
                    dSeen[nAt] = dSeen[nAt] + oLine.sText.Length;
                }
            }
            double nBody = 0.0;
            int iMost = 0;
            foreach (KeyValuePair<double, int> oPair in dSeen)
            {
                if (oPair.Value <= iMost) continue;
                iMost = oPair.Value;
                nBody = oPair.Key;
            }
            return nBody;
        }

        // Which heading level a size means, or nothing for body text.
        //
        // Sizes larger than the body are ranked biggest first and capped at
        // five, leaving h1 for the document's own title. A tenth above the
        // body is noise; a sixth is a heading.
        // Sizes grouped into BANDS relative to the body, not taken as exact
        // values.
        //
        // Taking the five largest distinct sizes works for a text PDF, where
        // sizes are a designer's small set. It fails on a scan, where a
        // measured pixel height is noisy: his journal produced dozens of
        // distinct heights, the five largest were rare outliers on a title
        // page, and the common subheadings a fifth above the body got no level
        // at all — 38 headings in 112 pages, with one solitary h5.
        //
        // A band is a RATIO to the body size, so the same rule serves a point
        // size and a pixel height, and heights of 13 and 14 land together
        // instead of competing for one of five places.
        public static Dictionary<double, int> headingLevels(List<PdfPage> lPages, double nBody)
        {
            double nAsked = nHeadingSize;
            if (nAsked < 1.05 || nAsked > 4.0) nAsked = 1.4;
            return headingLevelsAt(lPages, nBody, nAsked);
        }

        public static Dictionary<double, int> headingLevelsAt(List<PdfPage> lPages, double nBody, double nLowest)
        {
            if (nBody <= 0.0) return new Dictionary<double, int>();
            if (nLowest < 1.05 || nLowest > 8.0) nLowest = 1.4;
            // How much of the document is set at each size, so a size used once
            // on a cover cannot outrank one used on forty subheadings.
            Dictionary<double, int> dWeight = new Dictionary<double, int>();
            foreach (PdfPage oPage in lPages)
            {
                foreach (PageLine oLine in oPage.lLines)
                {
                    double nAt = Math.Round(oLine.nSize * 2.0) / 2.0;
                    if (nAt < nBody * nLowest) continue;
                    if (!dWeight.ContainsKey(nAt)) dWeight[nAt] = 0;
                    dWeight[nAt] = dWeight[nAt] + 1;
                }
            }
            // The bands: a fifth larger, a half larger, twice, and so on. Five
            // of them, which is what Markdown has room for below the title.
            // The lowest band is 1.4, not 1.16, BECAUSE A MEASURED LINE HEIGHT
            // IS NOISY IN A WAY A POINT SIZE IS NOT.
            //
            // A line of "Migration" measures taller than a line of "was more"
            // in the same font, because capitals and ascenders reach higher
            // than lowercase. Ordinary text therefore wanders over a range of
            // two or three pixels, and at 1.16 above a 9-pixel body every line
            // with a capital in it qualified: his journal produced 2,416 level
            // 6 headings.
            //
            // A real heading is set noticeably larger, not a sixth larger. At
            // 1.4 the wandering of ordinary text falls below the bar and a
            // heading still clears it comfortably.
            double[] anBand = new double[] { nLowest, nLowest * 1.21, nLowest * 1.5,
                                             nLowest * 1.86, nLowest * 2.29 };
            Dictionary<double, int> dLevel = new Dictionary<double, int>();
            foreach (KeyValuePair<double, int> oPair in dWeight)
            {
                double nRatio = oPair.Key / nBody;
                int iLevel = 6;
                for (int iBand = anBand.Length - 1; iBand >= 0; iBand = iBand - 1)
                {
                    if (nRatio >= anBand[iBand]) { iLevel = 2 + (anBand.Length - 1 - iBand); break; }
                }
                dLevel[oPair.Key] = iLevel;
            }

            // LEVELS MUST NOT SKIP.
            //
            // The bands run 2 to 6, but a document uses only the sizes it uses.
            // One with two heading sizes came out as h2 and h6, and his
            // screen-reader review caught it: "Heading level jumps from 2 to 6".
            //
            // That is Matterhorn checkpoint 14-003 and it matters to a reader
            // moving by heading, who cannot tell whether a level was skipped or
            // something was missed. So the levels actually used are squeezed
            // onto consecutive numbers, largest size first, keeping their order
            // and losing the gaps.
            List<int> lUsed = new List<int>();
            foreach (KeyValuePair<double, int> oPair in dLevel)
            {
                if (!lUsed.Contains(oPair.Value)) lUsed.Add(oPair.Value);
            }
            lUsed.Sort();
            Dictionary<int, int> dSqueezed = new Dictionary<int, int>();
            for (int iAt = 0; iAt < lUsed.Count; iAt = iAt + 1)
                dSqueezed[lUsed[iAt]] = Math.Min(6, iAt + 2);
            List<double> lSizes = new List<double>(dLevel.Keys);
            foreach (double nSize in lSizes) dLevel[nSize] = dSqueezed[dLevel[nSize]];
            return dLevel;
        }

        // A page's headings pushed down one level, so the document keeps one
        // title.
        //
        // The model is asked for a page and answers with a document, complete
        // with its own level 1. Six levels exist and the model rarely uses more
        // than three, so pushing everything down one costs nothing and leaves
        // the document's own title alone at the top.
        // Heading levels walked through once, so none skips.
        //
        // Matterhorn 14-003: a level that jumps leaves a reader moving by
        // heading unsure whether something was missed. His screen-reader review
        // caught five such jumps — 1 to 6, 2 to 5, 2 to 6 three times.
        //
        // Each heading may be at most one deeper than the one before it. Going
        // back up is always fine: that is how a document returns to a higher
        // section.
        //
        // This runs over the WHOLE document, because the inferred pages squeeze
        // their own levels and a model-written page has its own, and a document
        // made of both can still skip where the two meet. A reader meets the
        // document, not the pages it was made from.
        public static string closedHeadingGaps(string sMarkdown)
        {
            if (sMarkdown == null || sMarkdown == "") return sMarkdown;
            StringBuilder oOut = new StringBuilder();
            int iLast = 0;
            foreach (string sLine in sMarkdown.Replace("\r\n", "\n").Split('\n'))
            {
                Match oHead = Regex.Match(sLine, @"^(#{1,6})(\s+\S.*)$");
                if (!oHead.Success)
                {
                    oOut.AppendLine(sLine);
                    continue;
                }
                int iLevel = oHead.Groups[1].Value.Length;
                if (iLast > 0 && iLevel > iLast + 1) iLevel = iLast + 1;
                iLast = iLevel;
                oOut.AppendLine(new string('#', iLevel) + oHead.Groups[2].Value);
            }
            return oOut.ToString();
        }

        public static string demotedHeadings(string sMarkdown)
        {
            if (sMarkdown == null || sMarkdown == "") return sMarkdown;
            StringBuilder oOut = new StringBuilder();
            foreach (string sLine in sMarkdown.Replace("\r\n", "\n").Split('\n'))
            {
                Match oHead = Regex.Match(sLine, @"^(#{1,5})(\s+\S.*)$");
                if (oHead.Success) oOut.AppendLine("#" + oHead.Groups[1].Value + oHead.Groups[2].Value);
                else oOut.AppendLine(sLine);
            }
            return oOut.ToString();
        }

        // Text that is not meant as markup, kept from becoming markup.
        //
        // His journal came out with 28 level-1 headings, one of them reading
        // "# Haven. Three such sites produced about average counts" -- body
        // text from the middle of a sentence. Tesseract had read some mark on
        // the page as a "#", and because the line was written into the Markdown
        // untouched, it became a heading.
        //
        // Only the characters that START a line matter, since that is where
        // Markdown looks: a hash, a greater-than, a pipe. Anything inside the
        // line is harmless and escaping it would litter the text with
        // backslashes.
        public static string escapedForMarkdown(string sSaid)
        {
            if (sSaid == null || sSaid == "") return sSaid;
            // A line the reader is meant to see as a heading has already been
            // written as one above; anything reaching here is prose.
            if (Regex.IsMatch(sSaid, @"^\s*(#|>|\||=|\+)"))
                return "\\" + sSaid.TrimStart();
            return sSaid;
        }

        // The document written from its own tags.
        //
        // Headings keep the level the author gave them. A list is a list
        // because the tag says L, not because a line begins with a bullet. A
        // figure carries the author's own description. Nothing here is guessed.
        public static string markdownFromTags(List<TaggedPiece> lPieces, out int iHeadings, out int iListItems)
        {
            iHeadings = 0;
            iListItems = 0;
            StringBuilder oOut = new StringBuilder();
            int iPageAt = 0;
            bool bFirst = true;
            foreach (TaggedPiece oPiece in lPieces)
            {
                // A page break wherever the tags move to a new page, so the
                // Word version still paginates like the original.
                if (oPiece.iPage > 0 && oPiece.iPage != iPageAt)
                {
                    iPageAt = oPiece.iPage;
                    if (!bFirst)
                    {
                        oOut.AppendLine("\\pagebreak");
                        oOut.AppendLine("");
                    }
                    oOut.AppendLine("<!-- page " + iPageAt.ToString() + " -->");
                    oOut.AppendLine("");
                }
                bFirst = false;
                string sSaid = oPiece.sText == null ? "" : oPiece.sText.Trim();
                sSaid = Regex.Replace(sSaid, @"\s+", " ");

                if (oPiece.sKind == "Figure")
                {
                    string sAlt = oPiece.sAlt.Trim();
                    if (sAlt == "") sAlt = sSaid;
                    oOut.AppendLine(sAlt == ""
                        ? "![A picture the original does not describe](figure.png)"
                        : "![" + sAlt.Replace("]", ")") + "](figure.png)");
                    oOut.AppendLine("");
                    continue;
                }
                if (sSaid == "") continue;
                if (oPiece.iLevel > 0)
                {
                    // The author's level, moved down one so the document's own
                    // title keeps level 1.
                    int iLevel = Math.Min(6, oPiece.iLevel + 1);
                    oOut.AppendLine(new string('#', iLevel) + " " + sSaid);
                    oOut.AppendLine("");
                    iHeadings = iHeadings + 1;
                    continue;
                }
                // bInList, not the tag on this piece: a tagged list puts its
                // words in a P inside an LBody inside an LI, so asking this
                // piece alone gave nine plain paragraphs where nine list items
                // were tagged.
                if (oPiece.bInList)
                {
                    oOut.AppendLine("- " + sSaid);
                    iListItems = iListItems + 1;
                    continue;
                }
                if (oPiece.sKind == "TH" || oPiece.sKind == "TD")
                {
                    // Tables are not built yet, so a cell is written as its own
                    // line rather than silently dropped. A reader gets the
                    // words; what is lost is which column they were in.
                    oOut.AppendLine(escapedForMarkdown(sSaid));
                    continue;
                }
                oOut.AppendLine(escapedForMarkdown(sSaid));
                oOut.AppendLine("");
            }
            return oOut.ToString();
        }

        // IS THIS TEXT LAYER ACTUALLY USABLE?
        //
        // Two of PAC's fourteen checks describe ways a PDF can carry a text
        // layer that is worthless, and HomerScribe trusted every text layer
        // absolutely:
        //
        //   Check 8, accessible font encodings. "If a translation table is
        //   missing for a certain font, non-interpretable characters are passed
        //   to the assistive technology." The page looks perfect and the text
        //   extracts as gibberish.
        //
        //   Check 14, spaces existent. "Some PDF Generators think it not
        //   necessary to include invisible spaces to be passed into the PDF
        //   document." The words run together with nothing between them.
        //
        // Both produce a document that reads as nonsense while every count in
        // the log looks healthy — the worst kind of failure, because nothing
        // reports it. And both have the same remedy: the page is a picture too,
        // so read the picture instead.
        //
        // Three signs, each cheap:
        //   almost no spaces      "Thewordsrunttogetherlikethis"
        //   few letters at all    a page of replacement characters or boxes
        //   absurd word lengths   a mean word length no language has
        public static bool textLayerIsSound(List<PdfPage> lPages, out string sWhy)
        {
            sWhy = "";
            StringBuilder oAll = new StringBuilder();
            foreach (PdfPage oPage in lPages)
            {
                foreach (PageLine oLine in oPage.lLines)
                {
                    oAll.Append(oLine.sText);
                    oAll.Append(" ");
                }
                if (oAll.Length > 40000) break;
            }
            string sText = oAll.ToString();
            if (sText.Trim().Length < 40) return true;   // too little to judge

            int iLetters = 0;
            int iSpaces = 0;
            int iOdd = 0;
            foreach (char cAt in sText)
            {
                if (char.IsLetter(cAt)) iLetters = iLetters + 1;
                else if (cAt == ' ') iSpaces = iSpaces + 1;
                else if (cAt == '\uFFFD' || cAt == '\u25A1' || cAt == '\u0000') iOdd = iOdd + 1;
            }
            // DIGITS ARE NOT A FAULT. A page of counts and totals is
            // legitimately mostly numbers — his journal is full of them — and
            // an earlier version of this test rejected exactly that. Only
            // characters that are neither letters nor digits nor ordinary
            // punctuation count against it.
            int iJunk = 0;
            foreach (char cAt in sText)
            {
                if (char.IsLetterOrDigit(cAt) || char.IsWhiteSpace(cAt)) continue;
                if (char.IsPunctuation(cAt) || char.IsSymbol(cAt)) continue;
                iJunk = iJunk + 1;
            }
            if (iJunk > sText.Length / 10)
            {
                sWhy = "more than a tenth of its characters are neither letters, digits nor punctuation";
                return false;
            }
            if (iOdd > sText.Length / 50)
            {
                sWhy = "it is full of replacement characters, so a font has no translation table";
                return false;
            }
            // A space every five or six characters is ordinary English. One
            // every twenty-five means the spaces were never written.
            if (iSpaces > 0 && iLetters / iSpaces > 20)
            {
                sWhy = "its words run together, with a space only every "
                       + (iLetters / iSpaces).ToString() + " letters";
                return false;
            }
            if (iSpaces == 0)
            {
                sWhy = "it contains no spaces at all";
                return false;
            }
            return true;
        }

        // A line wrapped in Markdown emphasis where its font carried some.
        //
        // A whole line in bold that is not large enough to be a heading is
        // usually a run-in heading or a defined term, and marking it keeps
        // that. Nothing is done for a line already set as a heading: a
        // heading is emphatic by being one.
        static string emphasised(string sSaid, PageLine oLine)
        {
            if (sSaid == "" || oLine == null) return sSaid;
            if (!oLine.bBold && !oLine.bItalic) return sSaid;
            // Never wrap something that is already marked, or that is only
            // punctuation.
            if (!Regex.IsMatch(sSaid, @"[A-Za-z0-9]")) return sSaid;
            if (sSaid.StartsWith("*") || sSaid.StartsWith("_")) return sSaid;
            string sMark = oLine.bBold && oLine.bItalic ? "***" : (oLine.bBold ? "**" : "*");
            return sMark + sSaid + sMark;
        }

        // A page's lines turned into Markdown, using the sizes for structure.
        public static string pageAsMarkdown(PdfPage oPage, double nBody, Dictionary<double, int> dLevel)
        {
            StringBuilder oOut = new StringBuilder();
            StringBuilder oPara = new StringBuilder();
            bool bMarkerSeen = false;
            string sDropCap = "";
            foreach (PageLine oLine in oPage.lLines)
            {
                string sSaid = oLine.sText.Trim();
                if (sSaid == "") continue;
                // A DROP CAP IS THE FIRST LETTER OF A WORD (19 October 2026, a learning from
                // FRAME PDF Studio's findDropCaps). A paragraph's opening letter set large
                // across several lines is a line of one letter in a big size, which the
                // heading test below would make "# T". It is held and joined to the start
                // of the next line instead, so "T" and "he story began" read "The story began".
                if (sSaid.Length == 1 && char.IsLetter(sSaid[0]) && oLine.nSize >= nBody * 1.5)
                {
                    sDropCap = sSaid;
                    continue;
                }
                if (sDropCap != "")
                {
                    sSaid = sDropCap + sSaid;
                    sDropCap = "";
                }
                double nAt = Math.Round(oLine.nSize * 2.0) / 2.0;
                // A HEADING IS SHORT, whatever size it is set in.
                //
                // His GAC document came out with 130 headings in six pages:
                // every paragraph of body text became an h6, because the size
                // most CHARACTERS were set in was the small print, and ordinary
                // prose sat a sixth above it. Size alone cannot tell a heading
                // from a paragraph.
                //
                // Length can. A heading names what follows; it does not run to
                // two hundred characters and it does not end in a full stop.
                // That test costs nothing and no real heading fails it.
                bool bShortEnough = sSaid.Length <= 100
                                    && !Regex.IsMatch(sSaid, @"[.;,][""'\)]?$");
                if (dLevel.ContainsKey(nAt) && bShortEnough)
                {
                    if (oPara.Length > 0)
                    {
                        oOut.AppendLine(oPara.ToString().Trim());
                        oOut.AppendLine("");
                        oPara.Length = 0;
                    }
                    oOut.AppendLine(new string('#', dLevel[nAt]) + " " + sSaid);
                    oOut.AppendLine("");
                    continue;
                }
                // A bullet or a number at the start of a line is a list item,
                // and a list item is the one thing a screen reader user
                // navigates by that a paragraph cannot stand in for.
                //
                // PyMuPDF4LLM -- the reader EdSharp and FileDir settled on --
                // does exactly three things to make a PDF rich: font sizes
                // become heading levels, BULLET RUNS BECOME LISTS, and ruled
                // areas become tables. The first was already here and this is
                // the second. Tables are the one still missing.
                // A BULLET IS OFTEN ITS OWN LINE.
                //
                // In a PDF the marker and the text are separate runs at
                // different positions, so the reading order may deliver
                // "\u2022" and then "Inner item two" as two lines — and
                // matching "bullet, space, text" finds neither. His 03-lists
                // test came out as one paragraph with the bullets embedded in
                // the middle of it.
                //
                // So a line that is ONLY a marker turns the next line into a
                // list item.
                if (Regex.IsMatch(sSaid, @"^\s*([\u2022\u2023\u25AA\u25CF\u00B7\u2013\-\*]|\d{1,3}[.)]|[a-z][.)])\s*$"))
                {
                    bMarkerSeen = true;
                    continue;
                }
                if (bMarkerSeen)
                {
                    bMarkerSeen = false;
                    if (oPara.Length > 0)
                    {
                        oOut.AppendLine(oPara.ToString().Trim());
                        oOut.AppendLine("");
                        oPara.Length = 0;
                    }
                    oOut.AppendLine("- " + escapedForMarkdown(sSaid));
                    continue;
                }
                Match oBullet = Regex.Match(sSaid, @"^\s*([\u2022\u2023\u25AA\u25CF\u00B7\-\*\u2013])\s+(.+)$");
                Match oNumber = Regex.Match(sSaid, @"^\s*(\d{1,3})[.)]\s+(.+)$");
                if (oBullet.Success || oNumber.Success)
                {
                    if (oPara.Length > 0)
                    {
                        oOut.AppendLine(oPara.ToString().Trim());
                        oOut.AppendLine("");
                        oPara.Length = 0;
                    }
                    oOut.AppendLine(oBullet.Success
                                    ? "- " + oBullet.Groups[2].Value.Trim()
                                    : oNumber.Groups[1].Value + ". " + oNumber.Groups[2].Value.Trim());
                    continue;
                }
                // A PDF breaks its lines where the page ends, not where the
                // sentence does, so lines are joined back into paragraphs and a
                // line ending in a full stop closes one.
                oPara.Append(emphasised(escapedForMarkdown(sSaid), oLine) + " ");
                if (Regex.IsMatch(sSaid, @"[.!?][""'\)]?$"))
                {
                    oOut.AppendLine(oPara.ToString().Trim());
                    oOut.AppendLine("");
                    oPara.Length = 0;
                }
            }
            if (oPara.Length > 0)
            {
                oOut.AppendLine(oPara.ToString().Trim());
                oOut.AppendLine("");
            }
            return oOut.ToString();
        }
    }
}
