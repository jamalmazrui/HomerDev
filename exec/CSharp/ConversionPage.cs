// ConversionPage.cs -- the Homer web page: 2htm's accessible page form, as kit engines.
//
// MOVED FROM 2htm (kit 1.87.0, the author's rule that every conversion is one shared
// technique): 2htm's htmlWriter, its HTML clean-up and its JSON converter, so the kit
// makes web pages as 2htm always has, and 2htm can become a face over Conversion.convert.
//   PageWriter  the page form: the base stylesheet, a head with title and language, main
//               labelled by the title, headings shifted and clamped under the one H1,
//               images inlined or removed, tables with headers, escaping.
//   PageHtml    a web page cleaned into that form (styles, scripts and comments removed),
//               or its text.
//   PageJson    a JSON file as a readable page of nested lists and tables, or its text.
// Engines: page (htm to htm or txt) and json (json to htm or txt). An app that compiles
// this file has them; one that does not is told so by engineMissing, and uses another way.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace Homer
{

public static partial class Conversion
{
    static partial void pageState(ref bool bPage) { bPage = true; }

    // pageFinish: a page another engine made, put in the Homer form in place. The body's first H1
    // becomes the page's title first, since the writer makes the title the one H1 and moves the
    // body's headings down a level; otherwise a Pandoc page, titled by its file name, would read
    // H1 the file name, H2 the real title. The working copy sits beside the page, so the
    // writer finds its pictures where the page points to them.
    static partial void pageFinish(string sPath, ref string sError)
    {
        string sWork = sPath + ".homerpage.htm";
        try
        {
            string sHtml = decodeText(File.ReadAllBytes(sPath));
            Match oH1 = Regex.Match(sHtml, @"<h1\b[^>]*>(?<t>.*?)</h1>", RegexOptions.Singleline | RegexOptions.IgnoreCase);
            if (oH1.Success)
            {
                string sTitle = Regex.Replace(oH1.Groups["t"].Value, "<[^>]+>", "").Trim();
                if (sTitle.Length > 0)
                {
                    sHtml = sHtml.Remove(oH1.Index, oH1.Length);
                    string sTitleTag = "<title>" + PageWriter.escape(System.Net.WebUtility.HtmlDecode(sTitle)) + "</title>";
                    if (Regex.IsMatch(sHtml, @"<title[^>]*>.*?</title>", RegexOptions.Singleline | RegexOptions.IgnoreCase))
                        sHtml = Regex.Replace(sHtml, @"<title[^>]*>.*?</title>", sTitleTag, RegexOptions.Singleline | RegexOptions.IgnoreCase);
                    else sHtml = Regex.Replace(sHtml, @"<head[^>]*>", "$0" + sTitleTag, RegexOptions.IgnoreCase);
                }
            }
            File.WriteAllText(sWork, sHtml, new UTF8Encoding(false));
            PageHtml.convert(sWork, sPath);
        }
        catch (Exception oError) { sError = oError.Message; }
        finally { try { File.Delete(sWork); } catch (Exception) { } }
    }

    static partial void pageConvert(string sEngine, string sSource, string sTarget, ref bool bMade, ref string sError)
    {
        string sTo = typeOf(sTarget);
        try
        {
            if (sEngine == "page")
            {
                if (sTo == "txt") PageHtml.convertToText(sSource, sTarget); else PageHtml.convert(sSource, sTarget);
            }
            else
            {
                if (sTo == "txt") PageJson.convertToText(sSource, sTarget); else PageJson.convert(sSource, sTarget);
            }
            bMade = File.Exists(sTarget);
            if (!bMade) sError = "the " + sEngine + " engine wrote nothing";
        }
        catch (Exception oError) { sError = oError.Message; bMade = false; }
    }
}

    public static class PageWriter
    {
        public const string sDefaultDocType = "<!DOCTYPE html>";
        public const string sDefaultCharset = "utf-8";
        public const string sGeneratorName = "Homer";
        // Images are removed rather than kept, when an app sets this (2htm's --strip-images).
        public static bool bStripImages = false;

        public const string sBaseCss =
            "html{font-size:100%}" +
            "body{font-family:sans-serif;max-width:80ch;margin:1em auto;padding:0 1em;" +
                "line-height:1.6;color:#000;text-align:left}" +
            "p{margin:1em 0}" +
            "h1,h2,h3,h4,h5,h6{line-height:1.3;margin-top:1.5em}" +
            "a{color:#00529b;text-decoration:underline}" +
            "a:hover,a:focus{text-decoration:underline;text-decoration-thickness:2px}" +
            "*:focus{outline:3px solid #00529b;outline-offset:2px}" +
            ".visually-hidden{position:absolute !important;clip:rect(1px,1px,1px,1px);" +
                "width:1px;height:1px;overflow:hidden;white-space:nowrap}" +
            "table{border-collapse:collapse;margin:1em 0}" +
            "th,td{border:1px solid #595959;padding:.4em .6em;text-align:left;vertical-align:top}" +
            "th{background:#e8e8e8}" +
            "td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}" +
            "caption{caption-side:top;font-weight:bold;text-align:left;padding:.25em 0;font-size:1.05em}" +
            "nav ol{list-style:decimal;padding-left:2em}" +
            "figure{margin:1em 0}" +
            "img{max-width:100%;height:auto}" +
            "aside.slide-notes{border-left:4px solid #595959;padding-left:1em;margin:1em 0}" +
            ".byline{font-style:italic;color:#333;margin:0 0 1em 0}" +
            "p.subtitle{font-style:italic;color:#333;margin:0 0 1em 0}" +
            "pre{background:#f4f4f4;border:1px solid #595959;padding:.5em;overflow-x:auto;" +
                "font-family:monospace;white-space:pre-wrap;word-break:break-word}" +
            "code{font-family:monospace;background:#f4f4f4;padding:0 .2em;border:1px solid #d0d0d0}" +
            "pre code{background:transparent;border:0;padding:0}" +
            ".json-value{font-family:monospace}" +
            ".json-value.num{color:#004d00}" +
            ".json-value.str::before{content:'\"'}" +
            ".json-value.str::after{content:'\"'}" +
            ".json-value.null,.json-value.bool{font-style:italic}" +
            "dl.json-obj{margin-left:1.5em;border-left:2px solid #d0d0d0;padding-left:1em}" +
            "ol.json-arr{margin-left:1.5em}";

        public static string escape(string sIn)
        {
            if (string.IsNullOrEmpty(sIn)) return "";
            var sb = new StringBuilder(sIn.Length);
            foreach (char c in sIn) {
                switch (c) {
                    case '&': sb.Append("&amp;"); break;
                    case '<': sb.Append("&lt;"); break;
                    case '>': sb.Append("&gt;"); break;
                    case '"': sb.Append("&quot;"); break;
                    default:  sb.Append(c); break;
                }
            }
            return sb.ToString();
        }

        public static void writeHead(TextWriter writer, Dictionary<string, string> dMeta,
            string sDocTitle = null)
        {
            string sL;
            string sLang = dMeta.TryGetValue("language", out sL) && !string.IsNullOrWhiteSpace(sL)
                ? sL : "en";
            string sT;
            string sMetaTitle = dMeta.TryGetValue("title", out sT) && !string.IsNullOrWhiteSpace(sT)
                ? sT : "Converted document";

            // If a subtitle is present, combine it into the visible
            // title as "Title: Subtitle" (the conventional book
            // style). This affects both the <title> element in the
            // head and the <h1> emitted below. If an explicit
            // sDocTitle was supplied by the caller (e.g., the
            // Word/Excel converters), it overrides the derived title.
            string sSub;
            if (dMeta.TryGetValue("subtitle", out sSub) && !string.IsNullOrWhiteSpace(sSub)) {
                sMetaTitle = sMetaTitle + ": " + sSub;
            }
            if (string.IsNullOrWhiteSpace(sDocTitle)) sDocTitle = sMetaTitle;

            writer.WriteLine(sDefaultDocType);
            writer.WriteLine("<html lang=\"" + escape(sLang) + "\">");
            writer.WriteLine("<head>");
            writer.WriteLine("<meta charset=\"" + sDefaultCharset + "\">");
            writer.WriteLine("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">");
            writer.WriteLine("<meta name=\"generator\" content=\"" + escape(sGeneratorName) + "\">");
            writer.WriteLine("<title>" + escape(sMetaTitle) + "</title>");

            writeMetaTag(writer, "author", dMeta);
            writeMetaTag(writer, "description", dMeta);
            writeMetaTag(writer, "keywords", dMeta);

            writeDc(writer, "DC.title", dMeta, "title");
            writeDc(writer, "DC.creator", dMeta, "author");
            writeDc(writer, "DC.subject", dMeta, "subject");
            writeDc(writer, "DC.description", dMeta, "description");
            writeDc(writer, "DC.date.created", dMeta, "created");
            writeDc(writer, "DC.date.modified", dMeta, "modified");
            writeDc(writer, "DC.language", dMeta, "language");

            writer.WriteLine("<style>" + sBaseCss + "</style>");
            writer.WriteLine("</head>");
            writer.WriteLine("<body>");

            writer.WriteLine("<h1 id=\"doc-title\">" + escape(sDocTitle) + "</h1>");
            writeMetaHeader(writer, dMeta);
        }

        private static void writeMetaHeader(TextWriter writer, Dictionary<string, string> dMeta)
        {
            // Author and Created date render as a visible byline
            // paragraph ("By Author \u2014 Date"). This reads naturally
            // as an opening line and is what most documents want.
            // The byline fields are NOT repeated in any subsequent
            // properties block.
            bool bAuthor  = hasVal(dMeta, "author");
            bool bCreated = hasVal(dMeta, "created");
            bool bByline  = bAuthor || bCreated;

            if (bByline) writeByline(writer, dMeta, bAuthor, bCreated);

            // The remaining document properties (subject, keywords,
            // description, last-modified date) are rendered as plain
            // paragraphs, one per property, in natural English rather
            // than wrapped in a labeled "Document properties" section.
            // A reader will see "Subject: ...", "Last modified: ...",
            // etc., which is readable by itself and does not require
            // the extra structural chrome.
            writeMetaParagraph(writer, dMeta, "subject",     "Subject");
            writeMetaParagraph(writer, dMeta, "description", "Description");
            writeMetaParagraph(writer, dMeta, "keywords",    "Keywords");
            writeMetaDateParagraph(writer, dMeta, "modified", "Last modified");
        }

        private static void writeMetaParagraph(TextWriter writer, Dictionary<string, string> d,
            string sKey, string sLabel)
        {
            if (!hasVal(d, sKey)) return;
            writer.WriteLine("<p>" + escape(sLabel) + ": " + escape(d[sKey]) + ".</p>");
        }

        private static void writeMetaDateParagraph(TextWriter writer, Dictionary<string, string> d,
            string sKey, string sLabel)
        {
            if (!hasVal(d, sKey)) return;
            string sIso = d[sKey];
            string sDisplay = formatIsoDateForDisplay(sIso);
            writer.WriteLine("<p>" + escape(sLabel) + ": " +
                "<time datetime=\"" + escape(sIso) + "\">" + escape(sDisplay) + "</time>.</p>");
        }

        // Converts an ISO 8601 datetime (e.g., "2022-05-19T08:49:58")
        // to a human-friendly date ("2022-05-19"). The datetime= attr
        // on the <time> element still gets the full ISO string for
        // machine consumption; this helper governs only what's read
        // aloud or displayed to a human. If parsing fails, returns
        // the input unchanged.
        public static string formatIsoDateForDisplay(string sIso)
        {
            if (string.IsNullOrWhiteSpace(sIso)) return sIso;
            // If the string has a 'T' (ISO datetime), take just the
            // date portion. Otherwise return as-is.
            int iT = sIso.IndexOf('T');
            return (iT > 0) ? sIso.Substring(0, iT) : sIso;
        }

        // Emits a byline paragraph combining author and date.
        private static void writeByline(TextWriter writer, Dictionary<string, string> dMeta,
            bool bAuthor, bool bCreated)
        {
            var sb = new StringBuilder();
            sb.Append("<p class=\"byline\">");
            if (bAuthor) {
                sb.Append("By ");
                sb.Append(escape(dMeta["author"]));
                if (bCreated) sb.Append(" \u2014 ");
            }
            if (bCreated) {
                string sIso = dMeta["created"];
                string sDisplay = formatIsoDateForDisplay(sIso);
                sb.Append("<time datetime=\"").Append(escape(sIso)).Append("\">");
                sb.Append(escape(sDisplay));
                sb.Append("</time>");
            }
            sb.Append("</p>");
            writer.WriteLine(sb.ToString());
        }

        private static bool hasVal(Dictionary<string, string> d, string sKey)
        {
            string sV;
            return d.TryGetValue(sKey, out sV) && !string.IsNullOrWhiteSpace(sV);
        }

        public static void writeFoot(TextWriter writer)
        {
            writer.WriteLine("</body>");
            writer.WriteLine("</html>");
        }

        private static void writeMetaTag(TextWriter writer, string sName, Dictionary<string, string> dMeta)
        {
            string sVal;
            if (dMeta.TryGetValue(sName, out sVal) && !string.IsNullOrWhiteSpace(sVal))
                writer.WriteLine("<meta name=\"" + sName + "\" content=\"" + escape(sVal) + "\">");
        }

        private static void writeDc(TextWriter writer, string sDcName, Dictionary<string, string> dMeta,
            string sKey)
        {
            string sVal;
            if (dMeta.TryGetValue(sKey, out sVal) && !string.IsNullOrWhiteSpace(sVal))
                writer.WriteLine("<meta name=\"" + sDcName + "\" content=\"" + escape(sVal) + "\">");
        }

        public static string shiftAndClampHeadings(string sHtmlFragment, int iTargetMin)
        {
            if (string.IsNullOrEmpty(sHtmlFragment)) return sHtmlFragment;

            var regexHead = new Regex(@"<(?<slash>/?)h(?<level>[1-6])(?<rest>[^>]*)>",
                RegexOptions.IgnoreCase);
            var matches = regexHead.Matches(sHtmlFragment);
            if (matches.Count == 0) return sHtmlFragment;

            int iMin = 6;
            foreach (Match m in matches) {
                int iLvl = int.Parse(m.Groups["level"].Value);
                if (iLvl < iMin) iMin = iLvl;
            }

            int iShift = iTargetMin - iMin;

            return regexHead.Replace(sHtmlFragment, m => {
                int iLvl = int.Parse(m.Groups["level"].Value);
                int iNew = iLvl + iShift;
                if (iNew < iTargetMin) iNew = iTargetMin;
                if (iNew > 6) iNew = 6;
                return "<" + m.Groups["slash"].Value + "h" + iNew + m.Groups["rest"].Value + ">";
            });
        }

        // Handles <img> tags in a body HTML fragment. Word's filtered
        // HTML writes images to a sibling folder and references them
        // by relative path; this method either embeds those images as
        // base64 data URLs (portable, self-contained) or strips the
        // tags entirely (when --strip-images is active, or when a
        // referenced file is missing or is an unsupported format).
        //
        // The base directory for resolving relative paths is sBaseDir
        // (typically the temp folder where Word wrote its output).
        // The method never throws on per-image failures; broken
        // references are silently removed because the user asked for
        // no broken links under any circumstance.
        public static string inlineOrStripImages(string sHtmlFragment, string sBaseDir)
        {
            if (string.IsNullOrEmpty(sHtmlFragment)) return sHtmlFragment;

            var regexImg = new Regex(@"<img\b[^>]*>", RegexOptions.IgnoreCase);
            var regexSrc = new Regex(@"\bsrc\s*=\s*(?:""([^""]*)""|'([^']*)')",
                RegexOptions.IgnoreCase);

            return regexImg.Replace(sHtmlFragment, m => {
                string sTag = m.Value;

                // When --strip-images is active, strip every <img> tag
                // regardless of whether its file exists.
                if (PageWriter.bStripImages) return "";

                var matchSrc = regexSrc.Match(sTag);
                if (!matchSrc.Success) return ""; // no src at all
                string sRel = matchSrc.Groups[1].Success
                    ? matchSrc.Groups[1].Value
                    : matchSrc.Groups[2].Value;
                if (string.IsNullOrWhiteSpace(sRel)) return "";

                // If the src is already a data URL, keep the tag as-is.
                if (sRel.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
                    return sTag;

                // If the src is absolute (http:, https:, file:, etc.),
                // strip rather than embed. We do not fetch external
                // resources; a document that relies on them would
                // produce broken output in offline scenarios.
                if (Regex.IsMatch(sRel, @"^[a-zA-Z][a-zA-Z0-9+\-.]*:"))
                    return "";

                // Decode URL-encoded characters that Word may have
                // produced (spaces as %20, etc.).
                string sDecoded;
                try { sDecoded = Uri.UnescapeDataString(sRel); }
                catch { return ""; }

                string sFull = Path.Combine(sBaseDir, sDecoded);
                if (!File.Exists(sFull)) return "";

                string sMime = mimeForExtension(Path.GetExtension(sFull));
                if (sMime == null) return ""; // unsupported format

                byte[] binBytes;
                try { binBytes = File.ReadAllBytes(sFull); }
                catch { return ""; }

                string sB64 = Convert.ToBase64String(binBytes);
                string sNewSrc = "data:" + sMime + ";base64," + sB64;

                // Replace just the src attribute value; preserve
                // everything else (alt, width, height, etc.).
                string sResult = regexSrc.Replace(sTag,
                    mm => {
                        string sQuote = mm.Value.Contains("\"") ? "\"" : "'";
                        return "src=" + sQuote + sNewSrc + sQuote;
                    },
                    1);
                return sResult;
            });
        }

        // Maps a file extension (including the leading dot) to an
        // IANA MIME type suitable for a data URL. Returns null for
        // anything not in the whitelist; unknown types get stripped
        // rather than embedded with a guessed type.
        private static string mimeForExtension(string sExt)
        {
            if (string.IsNullOrEmpty(sExt)) return null;
            switch (sExt.ToLowerInvariant()) {
                case ".png":  return "image/png";
                case ".jpg":
                case ".jpeg": return "image/jpeg";
                case ".gif":  return "image/gif";
                case ".bmp":  return "image/bmp";
                case ".svg":  return "image/svg+xml";
                case ".webp": return "image/webp";
                default:      return null;
            }
        }

        // Writes a 2-D value array as an HTML <table>, with header
        // markup appropriate to the detected structure.
        //
        //   bColHeaders  first row is a header row; those cells get
        //                <th scope="col">
        //   bRowHeaders  first column is a header column; those cells
        //                get <th scope="row">
        //
        // When both flags are true and the top-left cell is a corner
        // (row 1, column 1), the corner gets <th> with no scope (the
        // WCAG-recommended pattern for a corner cell between both
        // header axes).
        //
        // When neither flag is true, writeTable is the wrong tool —
        // callers should emit paragraphs instead. We still produce a
        // valid table in that case (role="presentation" so screen
        // readers do not apply tabular semantics to it).
        public static void writeTable(TextWriter writer, object[,] aValues,
            string sCaption, string sSummaryId, string sSummaryText,
            bool bColHeaders, bool bRowHeaders)
        {
            int iR0 = aValues.GetLowerBound(0);
            int iC0 = aValues.GetLowerBound(1);
            int iRows = aValues.GetLength(0);
            int iCols = aValues.GetLength(1);

            bool[] abColIsNumeric = new bool[iCols];
            int iBodyStart = bColHeaders ? 1 : 0;
            for (int c = 0; c < iCols; c++)
                abColIsNumeric[c] = isColumnNumeric(aValues, iRows, iR0, iC0, c, iBodyStart);

            if (!string.IsNullOrEmpty(sSummaryId)) {
                writer.WriteLine("<p id=\"" + sSummaryId + "\" class=\"visually-hidden\">" +
                    escape(sSummaryText) + "</p>");
            }

            string sTableAttrs = string.IsNullOrEmpty(sSummaryId) ? "" :
                " aria-describedby=\"" + sSummaryId + "\"";
            if (!bColHeaders && !bRowHeaders)
                sTableAttrs += " role=\"presentation\"";
            writer.WriteLine("<table" + sTableAttrs + ">");
            if (!string.IsNullOrEmpty(sCaption))
                writer.WriteLine("<caption>" + escape(sCaption) + "</caption>");

            if (bColHeaders) {
                writer.WriteLine("<thead><tr>");
                for (int c = 0; c < iCols; c++) {
                    object oVal = aValues[iR0, iC0 + c];
                    string sCls = abColIsNumeric[c] ? " class=\"num\"" : "";
                    // If both axes have headers, the top-left cell is
                    // a corner between them; WCAG recommends emitting
                    // it as a bare <th> with no scope.
                    if (c == 0 && bRowHeaders)
                        writer.WriteLine("<th" + sCls + ">" + cellToHtml(oVal) + "</th>");
                    else
                        writer.WriteLine("<th scope=\"col\"" + sCls + ">" + cellToHtml(oVal) + "</th>");
                }
                writer.WriteLine("</tr></thead>");
            }

            writer.WriteLine("<tbody>");
            for (int r = iBodyStart; r < iRows; r++) {
                writer.WriteLine("<tr>");
                for (int c = 0; c < iCols; c++) {
                    object oVal = aValues[iR0 + r, iC0 + c];
                    bool bNum = abColIsNumeric[c] && isNumeric(oVal);
                    string sCls = bNum ? " class=\"num\"" : "";
                    if (c == 0 && bRowHeaders)
                        writer.WriteLine("<th scope=\"row\"" + sCls + ">" + cellToHtml(oVal) + "</th>");
                    else
                        writer.WriteLine("<td" + sCls + ">" + cellToHtml(oVal) + "</td>");
                }
                writer.WriteLine("</tr>");
            }
            writer.WriteLine("</tbody>");
            writer.WriteLine("</table>");
        }

        private static bool isColumnNumeric(object[,] aValues, int iRows, int iR0, int iC0,
            int iCol, int iBodyStart)
        {
            int iNum = 0, iNonEmpty = 0;
            for (int r = iBodyStart; r < iRows; r++) {
                object oVal = aValues[iR0 + r, iC0 + iCol];
                if (oVal == null) continue;
                iNonEmpty++;
                if (isNumeric(oVal)) iNum++;
            }
            if (iNonEmpty == 0) return false;
            return iNum * 2 >= iNonEmpty;
        }

        public static bool isNumeric(object oVal)
        {
            if (oVal == null) return false;
            if (oVal is double || oVal is int || oVal is long ||
                oVal is decimal || oVal is float || oVal is short) return true;
            if (oVal is string)
            {
                double nIgnored;
                return double.TryParse((string)oVal, NumberStyles.Any, CultureInfo.InvariantCulture, out nIgnored);
            }
            return false;
        }

        public static string cellToHtml(object oVal)
        {
            if (oVal == null) return "";
            if (oVal is DateTime) {
                DateTime dt = (DateTime)oVal;
                string sIso = dt.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
                return "<time datetime=\"" + sIso + "\">" + escape(sIso) + "</time>";
            }
            if (oVal is double)
                return escape(((double)oVal).ToString("R", CultureInfo.InvariantCulture));
            return escape(Convert.ToString(oVal, CultureInfo.InvariantCulture));
        }
    }

    public static class PageHtml
    {
        public static void convert(string sInPath, string sOutPath)
        {
            string sRaw = File.ReadAllText(sInPath, detectEncoding(sInPath));

            var dMeta = extractMeta(sRaw);
            if (!dMeta.ContainsKey("title") || string.IsNullOrWhiteSpace(dMeta["title"]))
                dMeta["title"] = Path.GetFileNameWithoutExtension(sInPath);

            string sBody = extractBody(sRaw);
            sBody = Regex.Replace(sBody, @"<style.*?</style>", "", RegexOptions.Singleline | RegexOptions.IgnoreCase);
            sBody = Regex.Replace(sBody, @"<script.*?</script>", "", RegexOptions.Singleline | RegexOptions.IgnoreCase);
            sBody = Regex.Replace(sBody, @"<!--.*?-->", "", RegexOptions.Singleline);
            sBody = PageWriter.inlineOrStripImages(sBody, Path.GetDirectoryName(sInPath) ?? "");
            sBody = PageWriter.shiftAndClampHeadings(sBody, 2);

            using (var writer = new StreamWriter(sOutPath, false, new UTF8Encoding(false))) {
                PageWriter.writeHead(writer, dMeta);
                writer.WriteLine("<main aria-labelledby=\"doc-title\">");
                writer.WriteLine(sBody);
                writer.WriteLine("</main>");
                PageWriter.writeFoot(writer);
            }
        }

        private static Encoding detectEncoding(string sPath)
        {
            try {
                byte[] binHead = new byte[Math.Min(2048, (int)new FileInfo(sPath).Length)];
                using (var fileStream = File.OpenRead(sPath)) fileStream.Read(binHead, 0, binHead.Length);
                if (binHead.Length >= 3 && binHead[0] == 0xEF && binHead[1] == 0xBB && binHead[2] == 0xBF)
                    return Encoding.UTF8;
                if (binHead.Length >= 2 && binHead[0] == 0xFF && binHead[1] == 0xFE)
                    return Encoding.Unicode;
                if (binHead.Length >= 2 && binHead[0] == 0xFE && binHead[1] == 0xFF)
                    return Encoding.BigEndianUnicode;
                string sHead = Encoding.ASCII.GetString(binHead);
                Match m = Regex.Match(sHead,
                    @"<meta[^>]+charset\s*=\s*['""]?(?<cs>[A-Za-z0-9_\-]+)",
                    RegexOptions.IgnoreCase);
                if (m.Success) {
                    try { return Encoding.GetEncoding(m.Groups["cs"].Value); } catch { }
                }
            } catch { }
            return Encoding.UTF8;
        }

        private static Dictionary<string, string> extractMeta(string sHtml)
        {
            var d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

            Match oTitle = Regex.Match(sHtml, @"<title[^>]*>(?<t>.*?)</title>",
                RegexOptions.Singleline | RegexOptions.IgnoreCase);
            if (oTitle.Success) {
                string sT = htmlToText(oTitle.Groups["t"].Value).Trim();
                if (!string.IsNullOrWhiteSpace(sT)) d["title"] = sT;
            }

            Match matchLang = Regex.Match(sHtml, @"<html[^>]+lang\s*=\s*['""]?(?<l>[A-Za-z\-]+)",
                RegexOptions.IgnoreCase);
            if (matchLang.Success) d["language"] = matchLang.Groups["l"].Value;

            foreach (Match m in Regex.Matches(sHtml, @"<meta\s+(?<attrs>[^>]*)>",
                RegexOptions.IgnoreCase)) {
                string sAttrs = m.Groups["attrs"].Value;
                string sName = attrVal(sAttrs, "name");
                string sContent = attrVal(sAttrs, "content");
                if (string.IsNullOrWhiteSpace(sName) || string.IsNullOrWhiteSpace(sContent))
                    continue;
                switch (sName.ToLowerInvariant()) {
                    case "author":       d["author"]      = sContent; break;
                    case "description":  d["description"] = sContent; break;
                    case "keywords":     d["keywords"]    = sContent; break;
                    case "dc.title":     if (!d.ContainsKey("title"))       d["title"]       = sContent; break;
                    case "dc.creator":   if (!d.ContainsKey("author"))      d["author"]      = sContent; break;
                    case "dc.subject":   if (!d.ContainsKey("subject"))     d["subject"]     = sContent; break;
                    case "dc.description": if (!d.ContainsKey("description")) d["description"] = sContent; break;
                    case "dc.language":  if (!d.ContainsKey("language"))    d["language"]    = sContent; break;
                }
            }
            return d;
        }

        private static string attrVal(string sAttrs, string sAttrName)
        {
            Match m = Regex.Match(sAttrs,
                sAttrName + @"\s*=\s*(?:""(?<v>[^""]*)""|'(?<v>[^']*)'|(?<v>[^\s>]+))",
                RegexOptions.IgnoreCase);
            return m.Success ? m.Groups["v"].Value : "";
        }

        private static string extractBody(string sHtml)
        {
            Match m = Regex.Match(sHtml, @"<body[^>]*>(?<b>.*?)</body>",
                RegexOptions.Singleline | RegexOptions.IgnoreCase);
            return m.Success ? m.Groups["b"].Value : sHtml;
        }

        private static string htmlToText(string sHtml)
        {
            string s = Regex.Replace(sHtml, @"<[^>]+>", "");
            s = s.Replace("&amp;", "&").Replace("&lt;", "<").Replace("&gt;", ">")
                 .Replace("&quot;", "\"").Replace("&#39;", "'").Replace("&nbsp;", " ");
            return s;
        }

        // Plain-text conversion. Strips markup while preserving the
        // line structure implied by block-level tags (paragraphs,
        // headings, list items, line breaks). Images are dropped
        // regardless of --strip-images; plain text has no image
        // concept.
        public static void convertToText(string sInPath, string sOutPath)
        {
            string sRaw = File.ReadAllText(sInPath, detectEncoding(sInPath));
            string sBody = extractBody(sRaw);

            // Remove style/script/comment content before tag stripping
            // so their contents don't leak into the text.
            sBody = Regex.Replace(sBody, @"<style.*?</style>", "",
                RegexOptions.Singleline | RegexOptions.IgnoreCase);
            sBody = Regex.Replace(sBody, @"<script.*?</script>", "",
                RegexOptions.Singleline | RegexOptions.IgnoreCase);
            sBody = Regex.Replace(sBody, @"<!--.*?-->", "", RegexOptions.Singleline);

            string sText = htmlBlocksToText(sBody);
            File.WriteAllText(sOutPath, sText, new UTF8Encoding(true));
        }

        // Replace block-level closing tags and <br> with newlines so
        // the visual structure survives the tag strip. Collapses
        // runs of blank lines to at most two. Decodes common named
        // entities.
        // Converts an HTML body fragment to plain text, preserving
        // paragraph boundaries but NOT wrapping within paragraphs.
        // The resulting text has one line per logical paragraph
        // (headings, list items, table rows, etc.), not one line per
        // source-line-of-HTML. This is the Pandoc "--wrap=none"
        // style and lets editors and screen readers apply their own
        // natural word-wrapping without fighting embedded hard
        // returns at an arbitrary column.
        public static string htmlBlocksToText(string sHtml)
        {
            // Strip entire <figure>...</figure> blocks before
            // processing anything else. A figure contains an image
            // and optionally a <figcaption>; keeping the caption
            // without the image would violate the "no orphan
            // image references or captions" rule.
            string s = Regex.Replace(sHtml, @"<figure\b[^>]*>.*?</figure>", "",
                RegexOptions.Singleline | RegexOptions.IgnoreCase);

            // We need to distinguish "paragraph boundary" (which
            // becomes a real newline in the output) from "any other
            // whitespace, including source-file newlines inside a
            // paragraph" (which should be collapsed to a single
            // space). We use a rare sentinel character — U+E000,
            // the start of the Private Use Area — as the marker
            // for real paragraph breaks, and then normalize all
            // other whitespace before converting the marker back.
            const string sBreakSentinel = "\uE000";

            // Place the sentinel at the boundaries of block-level
            // elements. Double sentinels signal a stronger break
            // (blank line in output).
            s = Regex.Replace(s, @"<br\s*/?>", sBreakSentinel, RegexOptions.IgnoreCase);
            s = Regex.Replace(s,
                @"</(p|div|blockquote|pre|section|article|header|footer|nav|aside|figcaption)\s*>",
                sBreakSentinel + sBreakSentinel, RegexOptions.IgnoreCase);
            s = Regex.Replace(s, @"</(li|dt|dd|tr)\s*>", sBreakSentinel, RegexOptions.IgnoreCase);
            s = Regex.Replace(s, @"</(h[1-6])\s*>", sBreakSentinel + sBreakSentinel, RegexOptions.IgnoreCase);
            s = Regex.Replace(s, @"<(h[1-6])\b[^>]*>", sBreakSentinel, RegexOptions.IgnoreCase);
            s = Regex.Replace(s, @"<li\b[^>]*>", sBreakSentinel + "- ", RegexOptions.IgnoreCase);

            // Strip remaining tags.
            s = Regex.Replace(s, @"<[^>]+>", "");

            // Decode common entities.
            s = s.Replace("&amp;", "&").Replace("&lt;", "<").Replace("&gt;", ">")
                 .Replace("&quot;", "\"").Replace("&apos;", "'").Replace("&#39;", "'")
                 .Replace("&nbsp;", " ").Replace("&mdash;", "\u2014")
                 .Replace("&ndash;", "\u2013").Replace("&hellip;", "\u2026");
            // Numeric character references (decimal only; hex is rarer).
            s = Regex.Replace(s, @"&#(\d+);", m => {
                int iCode;
                if (int.TryParse(m.Groups[1].Value, out iCode) && iCode > 0 && iCode <= 0x10FFFF)
                    return char.ConvertFromUtf32(iCode);
                return m.Value;
            });

            // Collapse ALL runs of whitespace (including literal
            // newlines from the HTML source) into a single space.
            // This is what removes intra-paragraph hard returns.
            s = Regex.Replace(s, @"[ \t\r\n\f\v]+", " ");

            // Replace sentinels with newlines. A double sentinel
            // (which was used for stronger boundaries like
            // paragraph and heading ends) becomes a blank line.
            // Collapse runs of sentinels to at most two so we never
            // emit more than one blank line in a row.
            s = Regex.Replace(s, sBreakSentinel + "+", m => {
                return m.Length >= 2 ? "\n\n" : "\n";
            });

            // Trim leading/trailing whitespace on each line and the
            // whole document.
            var sbOut = new StringBuilder();
            bool bSawAnyText = false;
            int iBlank = 0;
            foreach (var sLine in s.Split('\n')) {
                string t = sLine.Trim();
                if (t.Length == 0) {
                    if (bSawAnyText) iBlank++;
                    continue;
                }
                if (iBlank > 0) sbOut.AppendLine();
                sbOut.AppendLine(t);
                bSawAnyText = true;
                iBlank = 0;
            }
            return sbOut.ToString();
        }
    }

    public static class PageJson
    {
        public static void convert(string sInPath, string sOutPath)
        {
            string sJson = File.ReadAllText(sInPath, Encoding.UTF8);
            var dMeta = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
                { "title", Path.GetFileNameWithoutExtension(sInPath) }
            };

            object vRoot;
            try {
                var jsonParserInst = new jsonParser(sJson);
                vRoot = jsonParserInst.parseValue();
                jsonParserInst.skipWhitespace();
                if (!jsonParserInst.isAtEnd())
                    throw new FormatException("Unexpected content after root value at position " + jsonParserInst.pos);
            } catch (Exception ex) {
                using (var writer = new StreamWriter(sOutPath, false, new UTF8Encoding(false))) {
                    PageWriter.writeHead(writer, dMeta);
                    writer.WriteLine("<main aria-labelledby=\"doc-title\">");
                    writer.WriteLine("<h2>Parse error</h2>");
                    writer.WriteLine("<p>" + PageWriter.escape(ex.Message) + "</p>");
                    writer.WriteLine("<h2>Raw content</h2>");
                    writer.WriteLine("<pre>" + PageWriter.escape(sJson) + "</pre>");
                    writer.WriteLine("</main>");
                    PageWriter.writeFoot(writer);
                }
                return;
            }

            using (var writer = new StreamWriter(sOutPath, false, new UTF8Encoding(false))) {
                PageWriter.writeHead(writer, dMeta);
                writer.WriteLine("<main aria-labelledby=\"doc-title\">");
                renderValue(writer, vRoot);
                writer.WriteLine("</main>");
                PageWriter.writeFoot(writer);
            }
        }

        private static void renderValue(TextWriter writer, object oVal)
        {
            if (oVal == null) {
                writer.WriteLine("<span class=\"json-value null\">null</span>");
            } else if (oVal is bool) {
                bool b = (bool)oVal;
                writer.WriteLine("<span class=\"json-value bool\">" + (b ? "true" : "false") + "</span>");
            } else if (oVal is double) {
                double nD = (double)oVal;
                writer.WriteLine("<span class=\"json-value num\">" +
                    PageWriter.escape(nD.ToString("R", CultureInfo.InvariantCulture)) + "</span>");
            } else if (oVal is long) {
                long nL = (long)oVal;
                writer.WriteLine("<span class=\"json-value num\">" + nL + "</span>");
            } else if (oVal is string) {
                string s = (string)oVal;
                writer.WriteLine("<span class=\"json-value str\">" + PageWriter.escape(s) + "</span>");
            } else if (oVal is List<KeyValuePair<string, object>>) {
                List<KeyValuePair<string, object>> lObj = (List<KeyValuePair<string, object>>)oVal;
                renderObject(writer, lObj);
            } else if (oVal is List<object>) {
                List<object> lArr = (List<object>)oVal;
                renderArray(writer, lArr);
            } else {
                writer.WriteLine("<span class=\"json-value\">" +
                    PageWriter.escape(Convert.ToString(oVal, CultureInfo.InvariantCulture)) + "</span>");
            }
        }

        private static void renderObject(TextWriter writer, List<KeyValuePair<string, object>> lObj)
        {
            if (lObj.Count == 0) {
                writer.WriteLine("<span class=\"json-value\">{} <em>(empty object)</em></span>");
                return;
            }
            writer.WriteLine("<dl class=\"json-obj\">");
            foreach (var kv in lObj) {
                writer.WriteLine("<dt>" + PageWriter.escape(kv.Key) + ":</dt>");
                writer.WriteLine("<dd>");
                renderValue(writer, kv.Value);
                writer.WriteLine("</dd>");
            }
            writer.WriteLine("</dl>");
        }

        private static void renderArray(TextWriter writer, List<object> lArr)
        {
            if (lArr.Count == 0) {
                writer.WriteLine("<span class=\"json-value\">[] <em>(empty array)</em></span>");
                return;
            }
            writer.WriteLine("<ol class=\"json-arr\">");
            foreach (var v in lArr) {
                writer.WriteLine("<li>");
                renderValue(writer, v);
                writer.WriteLine("</li>");
            }
            writer.WriteLine("</ol>");
        }

        public class jsonParser
        {
            private readonly string src;
            public int pos;

            public jsonParser(string sSrc) { src = sSrc; pos = 0; }

            public bool isAtEnd() { return pos >= src.Length; }

            public void skipWhitespace()
            {
                while (pos < src.Length && char.IsWhiteSpace(src[pos])) pos++;
            }

            public object parseValue()
            {
                skipWhitespace();
                if (isAtEnd()) throw new FormatException("Unexpected end of input");
                char c = src[pos];
                if (c == '{') return parseObject();
                if (c == '[') return parseArray();
                if (c == '"') return parseString();
                if (c == '-' || (c >= '0' && c <= '9')) return parseNumber();
                if (c == 't' || c == 'f') return parseBool();
                if (c == 'n') { parseLiteral("null"); return null; }
                throw new FormatException("Unexpected character '" + c + "' at position " + pos);
            }

            private List<KeyValuePair<string, object>> parseObject()
            {
                var l = new List<KeyValuePair<string, object>>();
                pos++;
                skipWhitespace();
                if (pos < src.Length && src[pos] == '}') { pos++; return l; }
                while (true) {
                    skipWhitespace();
                    if (pos >= src.Length || src[pos] != '"')
                        throw new FormatException("Expected string key at position " + pos);
                    string sKey = parseString();
                    skipWhitespace();
                    if (pos >= src.Length || src[pos] != ':')
                        throw new FormatException("Expected ':' at position " + pos);
                    pos++;
                    object oVal = parseValue();
                    l.Add(new KeyValuePair<string, object>(sKey, oVal));
                    skipWhitespace();
                    if (pos < src.Length && src[pos] == ',') { pos++; continue; }
                    if (pos < src.Length && src[pos] == '}') { pos++; return l; }
                    throw new FormatException("Expected ',' or '}' at position " + pos);
                }
            }

            private List<object> parseArray()
            {
                var l = new List<object>();
                pos++;
                skipWhitespace();
                if (pos < src.Length && src[pos] == ']') { pos++; return l; }
                while (true) {
                    l.Add(parseValue());
                    skipWhitespace();
                    if (pos < src.Length && src[pos] == ',') { pos++; continue; }
                    if (pos < src.Length && src[pos] == ']') { pos++; return l; }
                    throw new FormatException("Expected ',' or ']' at position " + pos);
                }
            }

            private string parseString()
            {
                pos++;
                var sb = new StringBuilder();
                while (pos < src.Length) {
                    char c = src[pos++];
                    if (c == '"') return sb.ToString();
                    if (c == '\\') {
                        if (pos >= src.Length) throw new FormatException("Unterminated escape");
                        char e = src[pos++];
                        switch (e) {
                            case '"':  sb.Append('"'); break;
                            case '\\': sb.Append('\\'); break;
                            case '/':  sb.Append('/'); break;
                            case 'b':  sb.Append('\b'); break;
                            case 'f':  sb.Append('\f'); break;
                            case 'n':  sb.Append('\n'); break;
                            case 'r':  sb.Append('\r'); break;
                            case 't':  sb.Append('\t'); break;
                            case 'u':
                                if (pos + 4 > src.Length)
                                    throw new FormatException("Bad \\u escape at position " + pos);
                                string sHex = src.Substring(pos, 4);
                                pos += 4;
                                sb.Append((char)int.Parse(sHex, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                                break;
                            default: throw new FormatException("Unknown escape \\" + e + " at position " + (pos - 1));
                        }
                    } else sb.Append(c);
                }
                throw new FormatException("Unterminated string starting near position " + pos);
            }

            private object parseNumber()
            {
                int iStart = pos;
                if (src[pos] == '-') pos++;
                while (pos < src.Length && src[pos] >= '0' && src[pos] <= '9') pos++;
                bool bFrac = false;
                if (pos < src.Length && src[pos] == '.') {
                    bFrac = true;
                    pos++;
                    while (pos < src.Length && src[pos] >= '0' && src[pos] <= '9') pos++;
                }
                if (pos < src.Length && (src[pos] == 'e' || src[pos] == 'E')) {
                    bFrac = true;
                    pos++;
                    if (pos < src.Length && (src[pos] == '+' || src[pos] == '-')) pos++;
                    while (pos < src.Length && src[pos] >= '0' && src[pos] <= '9') pos++;
                }
                string sNum = src.Substring(iStart, pos - iStart);
                if (bFrac)
                    return double.Parse(sNum, CultureInfo.InvariantCulture);
                long nL;
                if (long.TryParse(sNum, NumberStyles.Integer, CultureInfo.InvariantCulture, out nL))
                    return nL;
                return double.Parse(sNum, CultureInfo.InvariantCulture);
            }

            private bool parseBool()
            {
                if (src[pos] == 't') { parseLiteral("true"); return true; }
                parseLiteral("false"); return false;
            }

            private void parseLiteral(string sExpected)
            {
                if (pos + sExpected.Length > src.Length ||
                    src.Substring(pos, sExpected.Length) != sExpected)
                    throw new FormatException("Expected literal '" + sExpected + "' at position " + pos);
                pos += sExpected.Length;
            }
        }

        // Plain-text conversion. JSON is already human-readable in
        // its source form; we simply copy the content as UTF-8
        // without BOM so it matches the output-encoding convention
        // used elsewhere.
        public static void convertToText(string sInPath, string sOutPath)
        {
            File.Copy(sInPath, sOutPath, true);
        }
    }

} // namespace Homer
