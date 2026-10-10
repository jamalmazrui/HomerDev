"""
toHomerEncoding.py -- put text files into the Homer encoding.

Usage:
    python toHomerEncoding.py <file-folder-or-wildcard> [...]

The Homer encoding is UTF-8 with a byte order mark and CRLF line endings,
except .cmd and .bat files, version.txt and a skill's SKILL.md, which take
CRLF and no mark. Pandoc and most converters write UTF-8 with no mark and bare line
feeds, so run this on what they write. A file is read in the first encoding
that decodes it cleanly (UTF-8 with or without a mark, UTF-16 with a mark,
then Windows-1252); binary files are left alone. A Pandoc page whose
title is repeated as its first heading keeps one of the two. A folder is walked
recursively. Each file changed is reported, and a count at the end.

Exit code 0 when every file was read, 1 when one could not be, 2 for no
arguments.
"""

import glob, html, os, re, sys

c_lsNoMark = (".bat", ".cmd")
# The same rules as the kit's scripts\\fixEncoding.py, their authoritative home;
# the kit's build fails if the two ever differ (1.64.0, don't repeat yourself).
c_lsTextExt = (".bat", ".cmd", ".cs", ".css", ".csv", ".htm", ".html", ".inix", ".iss", ".js", ".json", ".lua",
               ".m3u", ".md", ".ps1", ".py", ".spec", ".tsv", ".txt", ".xml")


def decode(binData):
    """The text of a file, or None when it is not text."""
    if binData.startswith(b"\xff\xfe") or binData.startswith(b"\xfe\xff"):
        return binData.decode("utf-16")
    if b"\x00" in binData: return None
    for sEncoding in ("utf-8-sig", "cp1252"):
        try:
            return binData.decode(sEncoding)
        except UnicodeDecodeError:
            continue
    return None


def plainText(sHtml):
    """A heading's words, as a screen reader says them: no tags, entities read, spacing and case ignored."""
    sText = html.unescape(re.sub(r"<[^>]+>", "", sHtml))
    return " ".join(sText.split()).casefold()


def dropRepeatedTitle(sText):
    """ONE TITLE, SAID ONCE (8 October 2026): Pandoc's standalone page puts the title
    in a header block as a top-level heading, and a Markdown file that also opens with
    the same # heading gave every page two -- a screen reader said the title twice
    before anything else. When the header's heading says exactly what the first body
    heading says, the header's is removed, and the header with it if nothing else is
    in it. A title that differs from the first heading is left as it is."""
    oHeader = re.search(r'<header id="title-block-header">(.*?)</header>\s*', sText, re.S)
    if not oHeader: return sText
    oTitle = re.search(r'<h1 class="title">(.*?)</h1>\s*', oHeader.group(1), re.S)
    oFirst = re.search(r"<h1(?: [^>]*)?>(.*?)</h1>", sText[oHeader.end():], re.S)
    if not oTitle or not oFirst or plainText(oTitle.group(1)) != plainText(oFirst.group(1)): return sText
    sInside = oHeader.group(1)[:oTitle.start()] + oHeader.group(1)[oTitle.end():]
    sHeader = "" if not sInside.strip() else '<header id="title-block-header">' + sInside + "</header>\n"
    return sText[:oHeader.start()] + sHeader + sText[oHeader.end():]


def kitHeadingRule():
    """fixEncoding's oneTitleHeading, the authoritative rule (9 October 2026): from the kit this skill sits in, or the
    kit wherever it is (the HomerDev variable, then C:\\HomerDev). None for a copy uploaded without the kit, which then
    keeps its own narrower rule, dropRepeatedTitle."""
    lsPlaces = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "scripts")]
    for sKit in (os.environ.get("HomerDev", ""), r"C:\HomerDev"):
        if sKit: lsPlaces.append(os.path.join(sKit, "scripts"))
    for sPlace in lsPlaces:
        if os.path.isfile(os.path.join(sPlace, "fixEncoding.py")):
            try:
                import importlib.util
                oSpec = importlib.util.spec_from_file_location("homerFixEncoding", os.path.join(sPlace, "fixEncoding.py"))
                oModule = importlib.util.module_from_spec(oSpec); oSpec.loader.exec_module(oModule)
                return oModule.oneTitleHeading
            except Exception:
                continue
    return None


def convert(sPath):
    """Rewrite one file in the Homer encoding. Returns "changed", "same" or a problem."""
    binData = open(sPath, "rb").read()
    sText = decode(binData)
    if sText is None: return "not text"
    if sPath.lower().endswith((".htm", ".html")):
        # ONE LEVEL-ONE HEADING (9 October 2026): the kit's rule handles a repeated title, sections at level one, and
        # a page with none; without the kit, the repeated title alone is put right.
        fnRule = kitHeadingRule()
        sText = fnRule(sText.replace("\r\n", "\n")) if fnRule else dropRepeatedTitle(sText)
    sText = sText.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    sName = os.path.basename(sPath)
    # version.txt is read by build scripts and Inno, which want the number alone.
    bMark = not (sName.lower().endswith(c_lsNoMark) or sName in ("SKILL.md", "version.txt"))
    binNew = (b"\xef\xbb\xbf" if bMark else b"") + sText.encode("utf-8")
    if binNew == binData: return "same"
    open(sPath, "wb").write(binNew)
    return "changed"


def expand(sArgument):
    """The text files an argument names."""
    if os.path.isdir(sArgument):
        lsPaths = []
        for sDir, lsDirs, lsFiles in os.walk(sArgument):
            lsDirs[:] = [s for s in lsDirs if s not in (".git", "__pycache__")]
            lsPaths += [os.path.join(sDir, s) for s in lsFiles if s.lower().endswith(c_lsTextExt)]
        return sorted(lsPaths)
    return sorted(glob.glob(sArgument)) or [sArgument]


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    iChanged = 0
    bProblem = False
    for sArgument in sys.argv[1:]:
        for sPath in expand(sArgument):
            try:
                sOutcome = convert(sPath)
            except Exception as oError:
                sOutcome = "could not be read: %s" % oError
            if sOutcome == "changed":
                iChanged += 1
                print("changed: " + sPath)
            elif sOutcome not in ("same", "not text"):
                bProblem = True
                print("%s: %s" % (sPath, sOutcome))
    print("%d file%s changed." % (iChanged, "" if iChanged == 1 else "s"))
    return 1 if bProblem else 0


if __name__ == "__main__":
    sys.exit(main())
