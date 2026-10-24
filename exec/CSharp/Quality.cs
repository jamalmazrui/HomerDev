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
        topHeadings();
        return lsRows;
    }

    // MORE THAN ONE TOP HEADING (kit 1.92.2, from GLOW's MD-MULTIPLE-H1, and a Homer rule of its own: one
    // H1 per document). Front matter and fenced code are passed over.
    static void topHeadings() {
        int iTop = 0, iSecond = 0;
        bool bFence = false;
        for (int i = iYamlEndLine; i < aLines.Length; i++) {
            if (reFence.IsMatch(aLines[i].TrimStart())) { bFence = !bFence; continue; }
            if (bFence || !Regex.IsMatch(aLines[i], "^#[ \\t]+\\S")) continue;
            iTop++;
            if (iTop == 2) iSecond = i + 1;
        }
        if (iTop > 1) addRow("MultipleTopHeadings", "MSAC", "Heading issues", "Line " + iSecond, "(document)",
            "The document has " + iTop + " top-level headings; a document has one, its title.",
            "Keep one level-1 heading and make the others level 2.");
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

// =====================================================================
// OfficeCheck: extCheck's Word, Excel and PowerPoint rules, read from each file's own XML (kit 1.92.1).
//
// extCheck drives Word, Excel and PowerPoint through COM to judge their files; the kit does not depend on
// Office, so each rule here reads the file's XML instead, keeping extCheck's rule name, its wording and its
// threshold: an 18-point floor for slide text, 3 seconds for a slide that advances by itself, 20 paragraphs
// before a first heading, 5 blank rows in a row. The rules the kit's finishing step already fixes or
// reports -- title, author and language, alternative text for pictures, a table's header row, a default
// sheet name, merged cells, a frozen header row and a slide's title -- are not repeated here. Two rules need
// Office's rendering and stay in extCheck for now: ColorUsedAlone, and the help text Word gives a form
// field beyond what the file holds.
public static class OfficeCheck {
    static readonly string[] aBullets = { "\u2022", "\u25CF", "-", "*" };
    static readonly string[] aVague = { "click here", "here", "link", "read more", "more", "this", "url", "learn more", "continue", "details", "info", "information", "go" };
    const int iMaxParasBetweenHeadings = 20;
    const int iMaxConsecutiveEmptyRows = 5;
    const int iMaxSheetNameLength = 31;
    const int iSmallestFontHundredths = 1800;
    const int iShortestAdvanceMs = 3000;

    static List<string[]> lsRows = new List<string[]>();

    static string trunc(string s) { return s.Length > 60 ? s.Substring(0, 60) + "..." : s; }

    static void add(string sRule, string sCategory, string sLocation, string sContext, string sMessage, string sRemedy) {
        lsRows.Add(new string[] { sRule, "MSAC", sCategory, sLocation, trunc(sContext), sMessage, sRemedy });
    }

    static string text(string sXml, string sTag) {
        StringBuilder sb = new StringBuilder();
        foreach (Match m in Regex.Matches(sXml, "<" + sTag + "\\b[^>]*>(.*?)</" + sTag + ">", RegexOptions.Singleline)) sb.Append(System.Net.WebUtility.HtmlDecode(m.Groups[1].Value));
        return sb.ToString();
    }

    static bool vague(string s) {
        string sLower = s.Trim().ToLowerInvariant();
        if (sLower == "" || sLower.StartsWith("http") || sLower.StartsWith("www")) return true;
        return Array.IndexOf(aVague, sLower) >= 0;
    }

    // FAUX HEADINGS (kit 1.92.2, from GLOW's heading_detector.py): a paragraph without a heading style that
    // looks like one, scored by GLOW's signals and weights -- bold 20, large type 25 (22 points) or 20 (20
    // points), short 15, no closing punctuation 10, all capitals or title case 10, a single line 5, a
    // numbering pattern 5; a signature-like name -20, a callout such as "Note:" -15. GLOW treats 50 as a
    // candidate and 75 as certain. GLOW's signals that need the paragraphs around it (a blank before 10, body
    // after 5, a size unlike the body's 5) are left out here, so GLOW's 75 is this check's 55; the kit reports
    // from 60, and only for bold or large text, so a report is a likely heading, not a guess.
    const int iFauxHeadingThreshold = 60;

    static int fauxHeadingScore(string sXml, string sText, string sStyle) {
        if (sStyle.ToLowerInvariant().StartsWith("list") || sStyle.ToLowerInvariant() == "title" || sText.Length > 200) return 0;
        int iScore = 0;
        bool bBold = Regex.IsMatch(sXml, "<w:b/>|<w:b w:val=\"(?:1|true)\"/>");
        if (bBold) iScore += 20;
        Match oSize = Regex.Match(sXml, "<w:sz w:val=\"(\\d+)\"");
        if (oSize.Success) {
            double nPoints = int.Parse(oSize.Groups[1].Value) / 2.0;
            if (nPoints >= 22) iScore += 25; else if (nPoints >= 20) iScore += 20;
        }
        if (sText.Length <= 80) iScore += 15;
        if (!Regex.IsMatch(sText, "[.,;:!?]$")) iScore += 10;
        bool bCaps = sText == sText.ToUpperInvariant() && sText != sText.ToLowerInvariant();
        bool bTitleCase = !bCaps && Regex.IsMatch(sText, "^(?:[A-Z][a-z'\\-]*\\s*)+$");
        if (bCaps || bTitleCase) iScore += 10;
        if (sXml.IndexOf("<w:br/>", StringComparison.Ordinal) < 0) iScore += 5;
        if (Regex.IsMatch(sText, "^(?:\\d+(?:\\.\\d+)*\\.?|[IVXLC]+\\.|[A-Z]\\.)\\s")) iScore += 5;
        if (sText.Length <= 40 && Regex.IsMatch(sText, "^[A-Z][a-z]+(?:\\s+[A-Z]\\.?)?\\s+[A-Z][a-z]+$")) iScore -= 20;
        if (sText.Length <= 80 && Regex.IsMatch(sText, "^(?:Note|Please note|Dear|Hello|Hi|Thank you|Thanks|Sincerely|Regards)\\b", RegexOptions.IgnoreCase)) iScore -= 15;
        // Without bold or large type nothing marks it as a heading to a sighted reader either.
        if (!bBold && iScore < 100 && !(oSize.Success && int.Parse(oSize.Groups[1].Value) >= 40)) return 0;
        return iScore;
    }

    static bool allCaps(string s) { return s.Length > 4 && s == s.ToUpperInvariant() && s != s.ToLowerInvariant(); }

    static Dictionary<string, string> parts(string sPath) {
        Dictionary<string, string> d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        using (FileStream oFile = File.OpenRead(sPath))
        using (System.IO.Compression.ZipArchive zip = new System.IO.Compression.ZipArchive(oFile, System.IO.Compression.ZipArchiveMode.Read))
            foreach (System.IO.Compression.ZipArchiveEntry e in zip.Entries)
                if (e.FullName.EndsWith(".xml", StringComparison.OrdinalIgnoreCase) || e.FullName.EndsWith(".rels", StringComparison.OrdinalIgnoreCase))
                    using (StreamReader r = new StreamReader(e.Open(), Encoding.UTF8)) d[e.FullName] = r.ReadToEnd();
        return d;
    }

    // check: extCheck's rules for one Word, Excel or PowerPoint file; rows as MarkdownCheck gives them.
    public static List<string[]> check(string sPath) {
        lsRows = new List<string[]>();
        string sExt = Path.GetExtension(sPath).ToLowerInvariant();
        Dictionary<string, string> dParts = parts(sPath);
        if (sExt == ".docx") word(dParts);
        else if (sExt == ".xlsx") excel(dParts);
        else if (sExt == ".pptx") powerPoint(dParts);
        return lsRows;
    }

    static void word(Dictionary<string, string> d) {
        string sBody;
        if (!d.TryGetValue("word/document.xml", out sBody)) return;
        int iLast = 0, iBeforeFirst = 0;
        bool bLongFired = false;
        HashSet<string> hsHeadings = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (Match oPara in Regex.Matches(sBody, "<w:p\\b(?:(?!<w:p\\b).)*?</w:p>", RegexOptions.Singleline)) {
            string sXml = oPara.Value, sText = text(sXml, "w:t").Trim();
            Match oStyle = Regex.Match(sXml, "<w:pStyle w:val=\"([^\"]+)\"");
            string sStyle = oStyle.Success ? oStyle.Groups[1].Value : "";
            Match oLevel = Regex.Match(sStyle, "^[Hh]eading ?(\\d)$");
            if (oLevel.Success) {
                int iLevel = int.Parse(oLevel.Groups[1].Value);
                if (iLast > 0 && iLevel > iLast + 1) add("SkippedHeadingLevel", "Heading issues", "(Document)", sText, "Heading level " + iLevel + " follows level " + iLast + ", skipping a level.", "Use each heading level in turn.");
                if (sText != "" && !hsHeadings.Add(sText)) add("DuplicateHeadingText", "Heading issues", "(Document)", sText, "Two headings have the same text, so a list of headings cannot tell them apart.", "Make each heading distinct.");
                iLast = iLevel;
                continue;
            }
            if (sText == "") continue;
            int iScore = fauxHeadingScore(sXml, sText, sStyle);
            if (iScore >= iFauxHeadingThreshold) add("FauxHeading", "Heading issues", "(Document)", sText, "This paragraph looks like a heading -- " + iScore + " of 100 by GLOW's signals -- but has no heading style, so a screen reader cannot move to it.", "Apply the heading style for its level.");
            if (iLast == 0 && ++iBeforeFirst > iMaxParasBetweenHeadings && !bLongFired) {
                bLongFired = true;
                add("LongSectionWithoutHeading", "Heading issues", "(Document)", sText, "More than " + iMaxParasBetweenHeadings + " paragraphs come before the first heading.", "Add headings so a screen reader can move by them.");
            }
            if (sText.Contains("  ")) add("RepeatedBlankCharacters", "Formatting", "(Document)", sText, "Paragraph contains consecutive spaces likely used for visual layout.", "Remove repeated spaces. Use paragraph indentation or tab stops for layout instead.");
            if (allCaps(sText)) add("AllCapsText", "Formatting", "(Document)", sText, "Text is typed in capital letters, which some screen readers spell out.", "Type it in normal case; use the All Caps font setting if it must look so.");
            string sFirst = sText.Substring(0, 1);
            if (Array.IndexOf(aBullets, sFirst) >= 0 && sStyle.ToLowerInvariant().IndexOf("list", StringComparison.Ordinal) < 0 && sXml.IndexOf("<w:numPr>", StringComparison.Ordinal) < 0)
                add("FakeListBullet", "List not used correctly", "(Document)", sText, "Paragraph uses a manually typed bullet instead of a Word list style.", "Apply the 'List Bullet' built-in style from the Home tab Styles gallery.");
        }
        int iTable = 0;
        foreach (Match oTable in Regex.Matches(sBody, "<w:tbl>.*?</w:tbl>", RegexOptions.Singleline)) {
            iTable++;
            bool bHeader = oTable.Value.IndexOf("<w:tblHeader", StringComparison.Ordinal) >= 0;
            if (bHeader && Regex.IsMatch(oTable.Value, "<w:tblLook\\b[^>]*w:firstColumn=\"1\"")) add("ComplexTableHeaders", "Table issues", "Table " + iTable, "", "The table has both a header row and a header column.", "Split it into simpler tables, or describe it in a caption.");
            int iRow = 0;
            foreach (Match oRow in Regex.Matches(oTable.Value, "<w:tr\\b.*?</w:tr>", RegexOptions.Singleline)) {
                iRow++;
                foreach (Match oCell in Regex.Matches(oRow.Value, "<w:tc>.*?</w:tc>", RegexOptions.Singleline))
                    if (text(oCell.Value, "w:t").Trim() == "" && !(iRow == 1 && bHeader)) { add("EmptyTableCell", "Table issues", "Table " + iTable + " row " + iRow, "", "A table cell is empty, which a screen reader announces as blank.", "Fill it, or write a word such as none."); break; }
            }
        }
        foreach (Match oLink in Regex.Matches(sBody, "<w:hyperlink\\b.*?</w:hyperlink>", RegexOptions.Singleline)) {
            string sText = text(oLink.Value, "w:t").Trim();
            if (vague(sText)) add("NonDescriptiveHyperlinkText", "Link issues", "(Document)", sText, "Link text does not say where the link goes.", "Use words that name the destination.");
            if (oLink.Value.IndexOf("<w:u ", StringComparison.Ordinal) < 0 && oLink.Value.IndexOf("w:val=\"Hyperlink\"", StringComparison.Ordinal) < 0)
                add("HyperlinkNotUnderlined", "Link issues", "(Document)", sText, "A link is not underlined, so color alone marks it.", "Apply the Hyperlink character style.");
        }
        if (Regex.IsMatch(sBody, "<wp:anchor\\b(?:(?!</wp:anchor>).)*?(?:wps:txbx|v:textbox)", RegexOptions.Singleline)) add("FloatingTextBox", "Reading order", "(Document)", "", "A floating text box may be read out of order, or not at all.", "Put the text in the body, in line with the rest.");
        foreach (Match oField in Regex.Matches(sBody, "<w:ffData>.*?</w:ffData>", RegexOptions.Singleline))
            if (!Regex.IsMatch(oField.Value, "<w:(?:helpText|statusText)\\b[^>]*w:val=\"[^\"]+\"")) add("UnlabeledFormField", "Form issues", "(Document)", text(oField.Value, "w:name"), "A form field has no help text to say what it is for.", "Give it help text, through its Properties.");
    }

    static void excel(Dictionary<string, string> d) {
        string sBook;
        if (!d.TryGetValue("xl/workbook.xml", out sBook)) return;
        foreach (Match oSheet in Regex.Matches(sBook, "<sheet\\b[^>]*\\bname=\"([^\"]*)\"")) {
            string sName = System.Net.WebUtility.HtmlDecode(oSheet.Groups[1].Value);
            if (sName.Length > iMaxSheetNameLength) add("SheetNameTooLong", "Sheet issues", sName, sName, "The sheet name is longer than " + iMaxSheetNameLength + " characters.", "Shorten it.");
        }
        foreach (KeyValuePair<string, string> oPart in d) {
            if (Regex.IsMatch(oPart.Key, "^xl/worksheets/sheet\\d+\\.xml$")) {
                string sName = Path.GetFileNameWithoutExtension(oPart.Key);
                if (Regex.IsMatch(oPart.Value, "<col\\b[^>]*\\bhidden=\"(?:1|true)\"")) add("HiddenColumns", "Sheet issues", sName, "", "The sheet has hidden columns, which a screen reader user may not know are there.", "Show them, or say in the sheet that they are hidden.");
                if (Regex.IsMatch(oPart.Value, "<row\\b[^>]*\\bhidden=\"(?:1|true)\"")) add("HiddenRows", "Sheet issues", sName, "", "The sheet has hidden rows, which a screen reader user may not know are there.", "Show them, or say in the sheet that they are hidden.");
                List<int> lsUsed = new List<int>();
                foreach (Match oRow in Regex.Matches(oPart.Value, "<row\\b[^>]*\\br=\"(\\d+)\"[^>]*>(.*?)</row>", RegexOptions.Singleline))
                    if (Regex.IsMatch(oRow.Groups[2].Value, "<(?:v|t)\\b[^>]*>[^<]")) lsUsed.Add(int.Parse(oRow.Groups[1].Value));
                for (int i = 1; i < lsUsed.Count; i++)
                    if (lsUsed[i] - lsUsed[i - 1] - 1 >= iMaxConsecutiveEmptyRows) { add("BlankRowsUsedForLayout", "Sheet issues", sName, "", (lsUsed[i] - lsUsed[i - 1] - 1) + " blank rows in a row separate the data.", "Remove the blank rows, or put the parts on sheets of their own."); break; }
                foreach (Match oLink in Regex.Matches(oPart.Value, "<hyperlink\\b[^>]*\\bdisplay=\"([^\"]*)\""))
                    if (vague(System.Net.WebUtility.HtmlDecode(oLink.Groups[1].Value))) add("NonDescriptiveHyperlinkText", "Link issues", sName, oLink.Groups[1].Value, "Link text does not say where the link goes.", "Use words that name the destination.");
            }
            else if (Regex.IsMatch(oPart.Key, "^xl/tables/table\\d+\\.xml$")) {
                Match oName = Regex.Match(oPart.Value, "<table\\b[^>]*\\bdisplayName=\"([^\"]*)\"");
                if (oName.Success && Regex.IsMatch(oName.Groups[1].Value, "^Table\\d+$")) add("DefaultTableName", "Table issues", oName.Groups[1].Value, oName.Groups[1].Value, "The table keeps its default name.", "Name it for what it holds.");
                if (Regex.IsMatch(oPart.Value, "<table\\b[^>]*\\bheaderRowCount=\"0\"")) add("TableMissingHeaders", "Table issues", oName.Success ? oName.Groups[1].Value : "", "", "The table has no header row.", "Turn on its Header Row.");
            }
            else if (Regex.IsMatch(oPart.Key, "^xl/drawings/drawing\\d+\\.xml$")) {
                foreach (Match oFrame in Regex.Matches(oPart.Value, "<xdr:graphicFrame\\b.*?</xdr:graphicFrame>", RegexOptions.Singleline))
                    if (oFrame.Value.IndexOf("/chart\"", StringComparison.Ordinal) >= 0 && !Regex.IsMatch(oFrame.Value, "<xdr:cNvPr\\b[^>]*\\bdescr=\"[^\"]+\"")) add("ChartMissingAltText", "Missing alternative text", Path.GetFileNameWithoutExtension(oPart.Key), "", "A chart has no alternative text.", "Describe what the chart shows.");
                foreach (Match oPicture in Regex.Matches(oPart.Value, "<xdr:pic>.*?</xdr:pic>", RegexOptions.Singleline))
                    if (!Regex.IsMatch(oPicture.Value, "<xdr:cNvPr\\b[^>]*\\bdescr=\"[^\"]+\"")) add("MissingAltText", "Missing alternative text", Path.GetFileNameWithoutExtension(oPart.Key), "", "A picture has no alternative text.", "Describe the picture.");
            }
        }
    }

    static void powerPoint(Dictionary<string, string> d) {
        int iSlides = 0, iWithNotes = 0;
        List<string> lsSlides = new List<string>();
        foreach (string sKey in d.Keys) if (Regex.IsMatch(sKey, "^ppt/slides/slide\\d+\\.xml$")) lsSlides.Add(sKey);
        lsSlides.Sort(delegate(string a, string b) { return int.Parse(Regex.Match(a, "\\d+").Value).CompareTo(int.Parse(Regex.Match(b, "\\d+").Value)); });
        foreach (string sKey in lsSlides) {
            iSlides++;
            string sSlide = d[sKey], sLabel = "Slide " + Regex.Match(sKey, "\\d+").Value;
            // The notes, through the slide's relationships.
            string sRels, sNotes = "";
            if (d.TryGetValue("ppt/slides/_rels/" + Path.GetFileName(sKey) + ".rels", out sRels)) {
                Match oNotes = Regex.Match(sRels, "Target=\"\\.\\./notesSlides/([^\"]+)\"");
                string sNotesXml;
                if (oNotes.Success && d.TryGetValue("ppt/notesSlides/" + oNotes.Groups[1].Value, out sNotesXml)) {
                    foreach (Match oShape in Regex.Matches(sNotesXml, "<p:sp>.*?</p:sp>", RegexOptions.Singleline))
                        if (oShape.Value.IndexOf("type=\"body\"", StringComparison.Ordinal) >= 0) sNotes += text(oShape.Value, "a:t");
                }
            }
            if (sNotes.Trim() != "") iWithNotes++;
            else if (Regex.IsMatch(sSlide, "<p:pic>|<p:graphicFrame>")) add("VisualContentWithoutNotes", "Missing alternative text", sLabel, "", "The slide has a picture or chart and no speaker notes to describe it.", "Describe it in the notes.");
            Match oTransition = Regex.Match(sSlide, "<p:transition\\b[^>]*>");
            if (oTransition.Success) {
                Match oAdvance = Regex.Match(oTransition.Value, "\\badvTm=\"(\\d+)\"");
                if (oAdvance.Success && int.Parse(oAdvance.Groups[1].Value) > 0 && int.Parse(oAdvance.Groups[1].Value) < iShortestAdvanceMs) add("FastAutoAdvance", "Timing", sLabel, "", "The slide advances by itself in under 3 seconds.", "Advance on a click, or give it more time.");
                if (oTransition.Value.IndexOf("spd=\"fast\"", StringComparison.Ordinal) >= 0) add("FastTransitionSpeed", "Timing", sLabel, "", "The slide's transition is set to fast.", "Use a medium or slow transition, or none.");
            }
            if (Regex.IsMatch(sSlide, "\\brepeatCount=\"(?:indefinite|[2-9]\\d{3,}|\\d{5,})\"")) add("RepeatingAnimation", "Moving content", sLabel, "", "An animation repeats.", "Let it play once.");
            int iAuto = 0;
            foreach (Match oNode in Regex.Matches(sSlide, "<p:cTn\\b[^>]*\\bnodeType=\"(?:afterEffect|withEffect)\"[^>]*>(?:(?!</p:cTn>).)*?<p:cond\\b[^>]*\\bdelay=\"(\\d+)\"", RegexOptions.Singleline))
                if (int.Parse(oNode.Groups[1].Value) < 1000) iAuto++;
            if (iAuto > 3) add("RapidAutoAnimation", "Moving content", sLabel, "", iAuto + " animations start by themselves less than a second apart.", "Start them on a click, or space them out.");
            // Reading order: the title should be the first shape in the slide's shape tree.
            Match oFirst = Regex.Match(sSlide, "<p:spTree>.*?(<p:sp>.*?</p:sp>)", RegexOptions.Singleline);
            if (Regex.IsMatch(sSlide, "type=\"(?:ctrTitle|title)\"") && oFirst.Success && !Regex.IsMatch(oFirst.Groups[1].Value, "type=\"(?:ctrTitle|title)\""))
                add("TitleNotFirstInReadingOrder", "Reading order", sLabel, "", "The slide's title is not the first thing a screen reader reads.", "Move the title to the top of the Selection Pane's reading order.");
            foreach (Match oPara in Regex.Matches(sSlide, "<a:p>.*?</a:p>", RegexOptions.Singleline)) {
                string sText = text(oPara.Value, "a:t").Trim();
                if (sText == "") continue;
                if (allCaps(sText)) add("AllCapsText", "Formatting", sLabel, sText, "Text is typed in capital letters, which some screen readers spell out.", "Type it in normal case.");
                if (Array.IndexOf(aBullets, sText.Substring(0, 1)) >= 0 && oPara.Value.IndexOf("<a:buChar", StringComparison.Ordinal) < 0 && oPara.Value.IndexOf("<a:buAutoNum", StringComparison.Ordinal) < 0)
                    add("FakeListBullet", "List not used correctly", sLabel, sText, "Text uses a manually typed bullet instead of a PowerPoint list style.", "Apply a bullet list style from the Home tab Paragraph group.");
                Match oSize = Regex.Match(oPara.Value, "<a:rPr\\b[^>]*\\bsz=\"(\\d+)\"");
                if (oSize.Success && int.Parse(oSize.Groups[1].Value) < iSmallestFontHundredths) add("SmallFontSize", "Formatting", sLabel, sText, "Text is smaller than 18 points.", "Make it 18 points or larger.");
            }
        }
        if (iSlides > 0 && iWithNotes == 0) add("NoSpeakerNotes", "Missing alternative text", "(Presentation)", "", "No slide has speaker notes.", "Add notes that say what each slide shows.");
    }
}

// QualityCheck: the one door to every rule moved from extCheck, by the file's type. Conversion finds this
// class in the program at run time, so Quality.cs stays optional for an app (kit 1.92.1).
public static class QualityCheck {
    public static List<string[]> check(string sPath) {
        string sExt = Path.GetExtension(sPath).ToLowerInvariant();
        if (sExt == ".md" || sExt == ".markdown") return MarkdownCheck.check(sPath);
        if (sExt == ".docx" || sExt == ".xlsx" || sExt == ".pptx") return OfficeCheck.check(sPath);
        return new List<string[]>();
    }
}


} // namespace Homer (Quality.cs)
