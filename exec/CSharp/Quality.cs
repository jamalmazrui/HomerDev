// Quality.cs -- part of the shared Homer toolkit (HomerDev), kit 1.92.0.
//
// EXTCHECK'S RULES IN THE KIT (the author's rule of 24 October 2026: every file a Homer app makes passes
// extCheck's quality checks, and those checks live in HomerDev). This file starts with extCheck's whole
// Markdown module, moved here word for word but for its two calls out -- results.add and shared.trunc --
// which now fill a list of rows. Markdown first because every two-step conversion passes through it and
// the module needs no Office. extCheck compiles this file and runs its Markdown checks from it; the kit's
// Conversion finds it in the program at run time and runs it on every .md it makes, so this file stands
// alone -- extCheck compiles it without Conversion -- and an app that does not compile it still builds and
// converts, with the short checks Conversion.cs has of its own.
//
// It needs nothing but the .NET Framework: an app adds Quality to its homerModules.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace Homer
{

public static class MarkdownCheck {
    const int iMaxParasBetweenHeadings = 20;
    const int iMaxHeadingLength        = 120;
    const int iMinAltTextLength        = 3;

    static string[] aLines;
    static Dictionary<string, string> dMeta;
    static int iYamlEndLine;
    static Regex reFence = new Regex(@"^(`{3,}|~{3,})");

    // The rows found, each: rule, source, category, location, context, message, remediation -- the
    // columns of an extCheck report.
    static List<string[]> lsRows = new List<string[]>();
    static readonly string[] aVague = { "click here", "here", "link", "read more", "more", "this", "url", "learn more", "continue", "details", "info", "information", "go" };

    static string trunc(string s) { return s.Length > 60 ? s.Substring(0, 60) + "..." : s; }

    static void addRow(string sRule, string sSource, string sCategory, string sLocation, string sContext, string sMessage, string sRemediation) {
        lsRows.Add(new string[] { sRule, sSource, sCategory, sLocation, sContext, sMessage, sRemediation });
    }

    // check: every Markdown rule extCheck has, on one file. The one entry point; extCheck and
    // the kit's finishing step both call it, so a Markdown file is judged the same everywhere.
    public static List<string[]> check(string sPath) {
        lsRows = new List<string[]>();
        open(sPath);
        checkAll(sPath);
        return lsRows;
    }

    public static bool open(string sPath) {
        aLines       = File.ReadAllText(sPath, Encoding.UTF8).Split(new[] { "\r\n", "\n" }, StringSplitOptions.None);
        dMeta        = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        iYamlEndLine = 0;
        parseYaml();
        return true;
    }

    public static void quit() {}  // no COM to release

    public static void checkAll(string sFilePath) {
        metadata(sFilePath);
        headings();
        images();
        links();
        tables();
        lists();
        emphasis();
        codeBlocks();
        rawHtml();
        lineIssues();
    }

    static void parseYaml() {
        if (aLines.Length < 2 || aLines[0].Trim() != "---") {
            return;
        }
        for (int i = 1; i < aLines.Length; i++) {
            string sT = aLines[i].Trim();
            if (sT == "---" || sT == "...") {
                iYamlEndLine = i + 1;
                break;
            }
            int iC = aLines[i].IndexOf(':');
            if (iC > 0) {
                string sKey = aLines[i].Substring(0, iC).Trim().ToLower();
                string sVal = aLines[i].Substring(iC + 1).Trim().Trim('"').Trim('\'');
                if (!dMeta.ContainsKey(sKey)) {
                    dMeta[sKey] = sVal;
                }
            }
        }
    }

    static bool inYaml(int iLn)      { return iLn <= iYamlEndLine; }
    static bool hasMeta(string sKey) { return dMeta.ContainsKey(sKey) && dMeta[sKey] != ""; }

    static void metadata(string sFilePath) {
        if (iYamlEndLine == 0) {
            add("NoYamlFrontMatter", 1, "MSAC", "Missing document properties", sFilePath,
                "The file has no YAML front matter block. Without front matter, Pandoc cannot set document title, language, or author.",
                "Add a YAML front matter block at the very top starting and ending with ---. Include at minimum: title and lang.");
            return;
        }
        if (!hasMeta("title")) {
            add("MissingTitle", 1, "MSAC", "Missing document properties", sFilePath,
                "No 'title' field found in YAML front matter.",
                "Add 'title: \"My Document Title\"' to the YAML front matter.");
        }
        if (!hasMeta("lang")) {
            add("MissingLanguage", 1, "MSAC", "Missing document language", sFilePath,
                "No 'lang' field in YAML front matter. Screen readers use this to select the correct TTS voice.",
                "Add 'lang: en-US' (or appropriate BCP 47 tag) to the YAML front matter.");
        }
        if (!hasMeta("author")) {
            add("MissingAuthor", 1, "AXE", "Missing document properties", sFilePath,
                "No 'author' field in YAML front matter.",
                "Add 'author: \"Name\"' to the YAML front matter.");
        }
        if (!hasMeta("description")) {
            add("MissingDescription", 1, "AXE", "Missing document properties", sFilePath,
                "No 'description' field in YAML front matter.",
                "Add 'description: \"Brief summary\"' to the YAML front matter.");
        }
    }

    // Convenience overload for MD: location is the line number as a string
    static void add(string ruleId, int iLn, string source, string category, string context, string message, string remediation) {
        addRow(ruleId, source, category, "Line " + iLn, context, message, remediation);
    }

    static void headings() {
        int iLastLv      = 0;
        int iParasSince  = 0;
        bool bLongFired  = false;
        bool bFoundFirst = false;
        var lHdgs = new List<string>();
        bool bInFence = false;
        var reAtx  = new Regex(@"^(#{1,6})\s+(.+)$");
        var reH1ul = new Regex(@"^=+\s*$");
        var reH2ul = new Regex(@"^-+\s*$");

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            string sT    = sLine.Trim();
            if (reFence.IsMatch(sT)) {
                bInFence = !bInFence;
                continue;
            }
            if (bInFence) {
                continue;
            }

            int iSetextLv = 0;
            if (i > 0 && sT.Length > 0) {
                if (reH1ul.IsMatch(sT) && aLines[i-1].Trim().Length > 0) {
                    iSetextLv = 1;
                } else if (reH2ul.IsMatch(sT) && aLines[i-1].Trim().Length > 0) {
                    iSetextLv = 2;
                }
            }

            var mAtx    = reAtx.Match(sLine);
            bool bIsHdg = mAtx.Success || iSetextLv > 0;
            int iLv     = 0;
            string sHText = "";

            if (mAtx.Success) {
                iLv    = mAtx.Groups[1].Value.Length;
                sHText = Regex.Replace(mAtx.Groups[2].Value.Trim(), @"\s+#+\s*$", "").Trim();
            } else if (iSetextLv > 0) {
                iLv    = iSetextLv;
                sHText = aLines[i-1].Trim();
            }

            if (bIsHdg) {
                bFoundFirst = true;
                if (iLastLv > 0 && iLv > iLastLv + 1) {
                    add("SkippedHeadingLevel", iLn, "MSAC", "Heading issues", trunc(sHText),
                        "Heading jumps from H" + iLastLv + " to H" + iLv + ", skipping a level.",
                        "Change this heading to H" + (iLastLv + 1) + " so levels are sequential.");
                }
                if (sHText == "") {
                    add("EmptyHeading", iLn, "MSAC", "Heading issues", "(empty)",
                        "Heading marker is present but contains no text.",
                        "Add descriptive text after the heading marker, or remove the marker.");
                }
                string sKey = iLv + "|" + sHText.ToLower().Trim();
                if (lHdgs.Contains(sKey)) {
                    add("DuplicateHeadingText", iLn, "AXE", "Heading issues", trunc(sHText),
                        "Two H" + iLv + " headings share identical text, creating ambiguous navigation.",
                        "Make each heading uniquely descriptive of its section.");
                } else {
                    lHdgs.Add(sKey);
                }
                if (sHText.Length > iMaxHeadingLength) {
                    add("HeadingTooLong", iLn, "MSAC", "Object has no title or name", trunc(sHText) + "...",
                        "Heading is " + sHText.Length + " characters, which is unusually long for a navigation landmark.",
                        "Shorten the heading to under 80 characters.");
                }
                if (sHText.Length > 0) {
                    char cLast = sHText[sHText.Length - 1];
                    if (cLast == '.' || cLast == ';' || cLast == ':') {
                        add("HeadingEndsWithPunctuation", iLn, "MSAC", "Object has no title or name", trunc(sHText),
                            "Heading ends with '" + cLast + "', causing TTS to insert an unnatural pause.",
                            "Remove the trailing punctuation from the heading.");
                    }
                }
                iLastLv     = iLv;
                iParasSince = 0;
                bLongFired  = false;
            } else {
                if (sT.Length > 0 && !sT.StartsWith("|") && !sT.StartsWith("    ")) {
                    iParasSince++;
                    if (iParasSince > iMaxParasBetweenHeadings && !bLongFired && iLastLv == 0) {
                        add("LongSectionWithoutHeading", iLn, "MSAC", "Heading issues", "(document start)",
                            "More than " + iMaxParasBetweenHeadings + " content lines appear before any heading.",
                            "Add a top-level heading near the start of the document and headings throughout to mark major sections.");
                        bLongFired = true;
                    }
                }
            }
        }

        if (!bFoundFirst && aLines.Length > 30) {
            addRow("NoHeadings", "MSAC", "Heading issues", "Line 1", "(document)",
                "Document has no headings. Screen reader users navigate long documents primarily by heading list.",
                "Add ATX-style headings (# H1, ## H2) to mark major sections.");
        }
    }

    static void images() {
        var reImg     = new Regex(@"!\[([^\]]*)\]\(([^)]*)\)");
        var reImgRef  = new Regex(@"!\[([^\]]*)\]\[([^\]]*)\]");
        var reHtmlImg = new Regex(@"<img\b[^>]*>", RegexOptions.IgnoreCase);
        var reAlt     = new Regex(@"\balt\s*=\s*(?:""([^""]*)""|'([^']*)'|(\S+))", RegexOptions.IgnoreCase);
        bool bInFence = false;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            string sT    = sLine.Trim();
            if (reFence.IsMatch(sT)) {
                bInFence = !bInFence;
                continue;
            }
            if (bInFence) {
                continue;
            }

            foreach (Match m in reImg.Matches(sLine)) {
                string sAlt = m.Groups[1].Value.Trim();
                string sUrl = m.Groups[2].Value.Trim();
                int iTs     = sUrl.IndexOf('"');
                if (iTs > 0) {
                    sUrl = sUrl.Substring(0, iTs).Trim();
                }
                if (sAlt == "") {
                    add("MissingAltText", iLn, "MSAC", "Missing alternative text", trunc(sUrl),
                        "Image has empty alt text.",
                        "Add descriptive alt text inside the square brackets: ![A description](url).");
                } else if (sAlt.Length < iMinAltTextLength) {
                    add("AltTextTooShort", iLn, "MSAC", "Missing alternative text", trunc(sAlt),
                        "Image alt text is very short (\"" + sAlt + "\") and unlikely to convey meaningful information.",
                        "Expand the alt text to describe the image content and its purpose.");
                } else if (Regex.IsMatch(sAlt, @"\.[a-zA-Z]{2,4}$") && !sAlt.Contains(" ")) {
                    add("AltTextIsFilename", iLn, "MSAC", "Missing alternative text", trunc(sAlt),
                        "Image alt text appears to be a filename rather than a meaningful description.",
                        "Replace the filename with a description of what the image shows.");
                } else if (sAlt.ToLower().StartsWith("image of") || sAlt.ToLower().StartsWith("picture of") || sAlt.ToLower().StartsWith("photo of")) {
                    add("AltTextRedundantPrefix", iLn, "MSAC", "Missing alternative text", trunc(sAlt),
                        "Alt text begins with a redundant phrase. Screen readers already announce the element is an image.",
                        "Remove the redundant prefix and begin the alt text with the actual description.");
                }
            }

            foreach (Match m in reImgRef.Matches(sLine)) {
                if (m.Groups[1].Value.Trim() == "") {
                    add("MissingAltText", iLn, "MSAC", "Missing alternative text", "ref: " + m.Groups[2].Value.Trim(),
                        "Reference-style image has empty alt text.",
                        "Add descriptive alt text: ![A description][ref]");
                }
            }

            foreach (Match m in reHtmlImg.Matches(sLine)) {
                var mAlt    = reAlt.Match(m.Value);
                string sAlt = mAlt.Success
                    ? (mAlt.Groups[1].Value + mAlt.Groups[2].Value + mAlt.Groups[3].Value).Trim()
                    : "";
                if (!mAlt.Success || sAlt == "") {
                    add("MissingAltText", iLn, "MSAC", "Missing alternative text", trunc(m.Value),
                        "Raw HTML img tag is missing an alt attribute or has empty alt.",
                        "Add alt=\"A description\" to the img tag. Use alt=\"\" only for decorative images.");
                }
            }
        }
    }

    static void links() {
        var reLink    = new Regex(@"\[([^\]]*)\]\(([^)]*)\)");
        var reLinkRef = new Regex(@"(?<!!)\[([^\]]+)\]\[([^\]]*)\]");
        var reBareUrl = new Regex(@"(?<![(\[<])(https?://\S+)", RegexOptions.IgnoreCase);
        bool bInFence = false;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            string sT    = sLine.Trim();
            if (reFence.IsMatch(sT)) {
                bInFence = !bInFence;
                continue;
            }
            if (bInFence) {
                continue;
            }

            foreach (Match m in reLink.Matches(sLine)) {
                if (m.Index > 0 && sLine[m.Index - 1] == '!') {
                    continue;
                }
                string sText = m.Groups[1].Value.Trim();
                string sUrl  = m.Groups[2].Value.Trim();
                int iTs      = sUrl.IndexOf('"');
                if (iTs > 0) {
                    sUrl = sUrl.Substring(0, iTs).Trim();
                }
                checkLinkText(sText, sUrl, iLn);
            }

            foreach (Match m in reLinkRef.Matches(sLine)) {
                checkLinkText(m.Groups[1].Value.Trim(), "[" + m.Groups[2].Value.Trim() + "]", iLn);
            }

            foreach (Match m in reBareUrl.Matches(sLine)) {
                bool bInside = false;
                int idx      = m.Index;
                for (int j = idx - 1; j >= 0 && j >= idx - 3; j--) {
                    if (sLine[j] == '(' || sLine[j] == '[') {
                        bInside = true;
                        break;
                    }
                }
                if (!bInside) {
                    add("BareUrl", iLn, "AXE", "Hyperlink", trunc(m.Value),
                        "A bare URL appears in text without descriptive link text. Screen readers read the URL character by character.",
                        "Wrap the URL in a Markdown link: [Descriptive text](https://url).");
                }
            }
        }
    }

    static void checkLinkText(string sText, string sTarget, int iLn) {
        if (sText == "") {
            add("EmptyLinkText", iLn, "AXE", "Hyperlink", trunc(sTarget),
                "Link has no visible text. Screen readers read the raw URL or produce no output.",
                "Add descriptive text between the square brackets.");
            return;
        }
        foreach (string v in aVague) {
            if (sText.ToLower() == v) {
                add("NonDescriptiveLinkText", iLn, "AXE", "Hyperlink", "\"" + sText + "\"",
                    "Link text \"" + sText + "\" is non-descriptive and does not indicate the destination.",
                    "Replace with text that describes where the link goes.");
                return;
            }
        }
        if (sText.StartsWith("http://") || sText.StartsWith("https://") || sText.StartsWith("www.")) {
            add("UrlAsLinkText", iLn, "AXE", "Hyperlink", trunc(sText),
                "Link text is a raw URL, which screen readers read character by character.",
                "Replace the URL with a description of the link destination.");
        }
    }

    static void tables() {
        var reSep     = new Regex(@"^\|?[\s\-:]+(\|[\s\-:]+)+\|?\s*$");
        var reRow     = new Regex(@"^\|.+\|?\s*$");
        bool bInFence = false;
        int iTableStart = -1;
        int iTableNum   = 0;
        int iColCount   = 0;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            string sT    = sLine.Trim();
            if (reFence.IsMatch(sT)) {
                bInFence = !bInFence;
                continue;
            }
            if (bInFence) {
                continue;
            }

            bool bIsRow = reRow.IsMatch(sT);
            bool bIsSep = reSep.IsMatch(sT);

            if (bIsRow && iTableStart < 0 && i + 1 < aLines.Length && reSep.IsMatch(aLines[i+1].Trim())) {
                iTableStart = iLn;
                iTableNum++;
                string[] aCells = sT.Trim('|').Split('|');
                iColCount = aCells.Length;
                int iCol  = 0;
                foreach (string sCell in aCells) {
                    iCol++;
                    if (stripMd(sCell).Trim() == "") {
                        add("BlankTableHeader", iLn, "MSAC", "Missing table header", "Table " + iTableNum + " Col " + iCol,
                            "Table column header cell is blank.",
                            "Add a descriptive label to each column header cell.");
                    }
                }
                continue;
            }

            if (iTableStart > 0 && bIsSep) {
                continue;
            }

            if (iTableStart > 0 && bIsRow) {
                string[] aCells = sT.Trim('|').Split('|');
                int iCol        = 0;
                foreach (string sCell in aCells) {
                    iCol++;
                    if (stripMd(sCell).Trim() == "") {
                        add("EmptyTableCell", iLn, "MSAC", "Blank cells used for formatting", "Table " + iTableNum + " Col " + iCol,
                            "Table data cell is empty.",
                            "Add content, or use a dash or N/A to indicate intentionally missing data.");
                    }
                }
                if (aCells.Length != iColCount) {
                    add("TableColumnCountMismatch", iLn, "AXE", "Complex table", "Table " + iTableNum + " row at line " + iLn,
                        "Row has " + aCells.Length + " cells but the header has " + iColCount + " columns.",
                        "Ensure every row has the same number of pipe-delimited cells as the header row.");
                }
                continue;
            }

            if (iTableStart > 0 && !bIsRow) {
                iTableStart = -1;
                iColCount   = 0;
            }
        }
    }

    static void lists() {
        // NUMBERING MARKDOWN DOES NOT MAKE A LIST (8 October 2026, from an audit by another
        // AI): the pattern was Markdown's own ordered-list syntax, "1." or "1)", so every
        // real numbered list was reported as fake. A fake one is "(1) text", "1 - text",
        // "1: text" or a dash after the number, which Markdown leaves as plain paragraphs.
        var reFakeNum       = new Regex(@"^\s{0,3}(\(\d+\)\s+\S|\d+\s*[-:\u2013\u2014]\s+\S)");
        var reFakeMidBullet = new Regex(@"\s[•·‣⁃]\s");
        bool bInFence = false;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            string sT    = sLine.Trim();
            if (reFence.IsMatch(sT)) {
                bInFence = !bInFence;
                continue;
            }
            if (bInFence) {
                continue;
            }

            if (reFakeMidBullet.IsMatch(sLine)) {
                add("FakeInlineBullet", iLn, "MSAC", "List not used correctly", trunc(sT),
                    "Line contains a Unicode bullet character used as an inline list marker.",
                    "Use proper Markdown list items: start each item on its own line with - or * followed by a space.");
            }

            if (reFakeNum.IsMatch(sLine) && i > 0 && reFakeNum.IsMatch(aLines[i-1])) {
                add("FakeNumberedList", iLn, "MSAC", "List not used correctly", trunc(sT),
                    "Lines are numbered in a way Markdown does not make a list, such as (1) or 1 -, so they read as plain paragraphs.",
                    "Use Markdown ordered list syntax: start each item with '1.' followed by a space.");
            }
        }
    }

    static void emphasis() {
        var reAllCaps  = new Regex(@"(?<![`\w])[A-Z]{7,}(?![`\w])");
        var reCodeSpan = new Regex(@"`[^`]+`");
        var reFullBold = new Regex(@"^\*{2}.{10,}\*{2}$|^_{2}.{10,}_{2}$");
        bool bInFence  = false;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            string sT    = sLine.Trim();
            if (reFence.IsMatch(sT)) {
                bInFence = !bInFence;
                continue;
            }
            if (bInFence) {
                continue;
            }

            string sNoCode = reCodeSpan.Replace(sLine, " ");
            foreach (Match m in reAllCaps.Matches(sNoCode)) {
                add("AllCapsText", iLn, "MSAC", "Text", "\"" + m.Value + "\"",
                    "Long all-caps sequence \"" + m.Value + "\" may cause TTS to read each letter individually.",
                    "Use mixed case. Reserve all-caps for true acronyms of six characters or fewer.");
            }

            if (reFullBold.IsMatch(sT) && sT.Length > 20) {
                add("EntireLineBolded", iLn, "AXE", "Text", trunc(sT),
                    "The entire line is bold. Bolding long passages reduces the emphasis signal for screen reader users.",
                    "Use bold sparingly for key terms. If the intent is a heading, use a heading marker instead.");
            }
        }
    }

    static void codeBlocks() {
        var reFenceOpen = new Regex(@"^(`{3,}|~{3,})(\w*)");
        bool bInFence   = false;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sT = aLines[i].Trim();
            var mF    = reFenceOpen.Match(sT);
            if (mF.Success) {
                if (!bInFence) {
                    bInFence = true;
                    if (mF.Groups[2].Value.Trim() == "") {
                        add("CodeBlockMissingLanguage", iLn, "AXE", "Code", "Fenced block at line " + iLn,
                            "Fenced code block has no language specifier. Screen reader users receive no cue about what kind of code they are reading.",
                            "Add a language identifier after the opening fence: ```python, ```bash, ```json, etc.");
                    }
                } else {
                    bInFence = false;
                }
                continue;
            }

            if (!bInFence && aLines[i].StartsWith("    ") && aLines[i].Trim().Length > 0) {
                if (i > 0 && !aLines[i-1].StartsWith("    ") && aLines[i-1].Trim().Length > 0) {
                    add("IndentedCodeBlock", iLn, "AXE", "Code", trunc(aLines[i].Trim()),
                        "Indented code block (4-space indent) cannot carry a language specifier.",
                        "Convert to a fenced code block using ``` with a language identifier.");
                }
            }
        }
    }

    static void rawHtml() {
        var reTag = new Regex(@"<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>", RegexOptions.IgnoreCase);
        bool bInFence = false;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            if (reFence.IsMatch(sLine.Trim())) {
                bInFence = !bInFence;
                continue;
            }
            if (bInFence) {
                continue;
            }

            foreach (Match m in reTag.Matches(sLine)) {
                string sTag = m.Groups[1].Value.ToLower();
                if (sTag == "table") {
                    add("RawHtmlTable", iLn, "MSAC", "Missing table header", trunc(m.Value),
                        "Raw HTML table used. HTML tables require explicit th scope headers and a caption to be accessible.",
                        "Use Pandoc pipe table syntax, or ensure the HTML table includes th scope headers and a caption.");
                } else if (sTag == "font" || sTag == "center") {
                    add("RawHtmlPresentational", iLn, "MSAC", "Use of color alone", trunc(m.Value),
                        "Raw HTML presentational element <" + sTag + "> conveys no semantics and is not supported in non-HTML Pandoc output formats.",
                        "Replace with Markdown formatting or a Pandoc-native span/div.");
                } else if (sTag == "marquee" || sTag == "blink") {
                    add("MovingContent", iLn, "AXE", "Motion", trunc(m.Value),
                        "Raw HTML <" + sTag + "> causes moving or blinking content, violating WCAG 2.2.2.",
                        "Remove the element entirely. Moving and blinking text has no accessible equivalent.");
                } else if (sTag == "div" || sTag == "span") {
                    add("RawHtmlGenericContainer", iLn, "AXE", "Use of color alone", trunc(m.Value),
                        "Raw HTML <" + sTag + "> container is silently ignored by Pandoc when converting to non-HTML formats.",
                        "Use Pandoc's native fenced div (::: {.class}) or bracketed span ([text]{.class}) syntax instead.");
                }
            }
        }
    }

    static void lineIssues() {
        bool bInFence     = false;
        var reTrail       = new Regex(@"  +$");
        int iConsecBlanks = 0;

        for (int i = 0; i < aLines.Length; i++) {
            int iLn = i + 1;
            if (inYaml(iLn)) {
                continue;
            }
            string sLine = aLines[i];
            string sT    = sLine.Trim();
            if (reFence.IsMatch(sT)) {
                bInFence      = !bInFence;
                iConsecBlanks = 0;
                continue;
            }
            if (bInFence) {
                iConsecBlanks = 0;
                continue;
            }

            if (sT == "") {
                iConsecBlanks++;
                if (iConsecBlanks == 3) {
                    add("ExcessiveBlankLines", iLn, "MSAC", "Repeated blank characters", "Line " + iLn,
                        "Three or more consecutive blank lines used for visual spacing.",
                        "Remove extra blank lines. Use a single blank line to separate paragraphs.");
                }
            } else {
                iConsecBlanks = 0;
            }

            if (reTrail.IsMatch(sLine)) {
                string sTr = sLine.Substring(sLine.TrimEnd().Length);
                if (sTr.Length > 2) {
                    add("ExcessiveTrailingSpaces", iLn, "MSAC", "Repeated blank characters",
                        "Line " + iLn + " (" + sTr.Length + " trailing spaces)",
                        "Line has " + sTr.Length + " trailing spaces. Exactly two trailing spaces are an intentional hard line break; more than two is almost always unintentional.",
                        "Remove the extra trailing spaces.");
                }
            }

            if (Regex.IsMatch(sLine, @"<br\s*/?>", RegexOptions.IgnoreCase)) {
                add("RawBrTag", iLn, "MSAC", "Repeated blank characters", trunc(sT),
                    "Raw HTML br tag used for a line break, reducing portability to non-HTML Pandoc output formats.",
                    "End the line with two trailing spaces or a backslash for a portable hard line break.");
            }
        }
    }

    static string stripMd(string s) {
        s = Regex.Replace(s, @"`[^`]+`", "");
        s = Regex.Replace(s, @"\*{1,2}([^*]+)\*{1,2}", "$1");
        s = Regex.Replace(s, @"_{1,2}([^_]+)_{1,2}", "$1");
        s = Regex.Replace(s, @"\[([^\]]+)\]\([^)]+\)", "$1");
        return s;
    }
}

} // namespace Homer (Quality.cs)
