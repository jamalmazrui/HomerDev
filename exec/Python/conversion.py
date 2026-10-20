"""conversion.py -- convert a file from one type to another, the one Homer way.

Every Homer program that converts a file calls this, not Pandoc or Office
directly. The routes are in conversions.inix, which C#'s Conversion.cs
reads too, so a route is decided once for both languages. Only approved
components: Pandoc, NuGet and PyPI packages, and Tesseract; Microsoft Office,
by COM, only as the last resort. No other converting program is looked for.

    convert(sSource, sTarget, dOptions=None)   -> dict: path, route, engine, ms
    toText(sSource)                            -> str, by the quickest route
    plan(sSource, sTargetType)                 -> the route that would be used, and why
    engineAvailable(sEngine)                   -> bool

sTarget is a path, or just a type such as "md", which writes beside the source.
Each conversion is logged with its route, its steps and its time.
"""
import glob
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET

try:
    import inix
except ImportError:
    inix = None
try:
    import log as homerLog
except ImportError:
    homerLog = None

sTableName = "conversions.inix"
iTimeoutSeconds = 600


def say(sText):
    if homerLog:
        try: homerLog.info("conversion: " + sText)
        except Exception: pass


# ---------- the table ----------

def tablePath():
    """conversions.inix beside this module, or in the folder above it (the kit's exec)."""
    sHere = os.path.dirname(os.path.abspath(__file__))
    for sDir in (sHere, os.path.dirname(sHere)):
        sPath = os.path.join(sDir, sTableName)
        if os.path.isfile(sPath): return sPath
    raise FileNotFoundError("no %s beside %s or above it" % (sTableName, sHere))


def loadTable():
    """{source type: {target type: [route, ...]}}, a route being [(engine, handsOnType), ...].

    Sections are named <source>2<target> (kit 1.74.0), e.g. [pdf2txt], each with a
    ways= line listing its routes best first, the same file C#'s Conversion.cs reads.
    """
    dRaw = inix.readInix(tablePath())
    dTable = {}
    for sName, dSection in dRaw.items():
        oMatch = re.match(r"^([a-z0-9]+?)2([a-z0-9]+)$", sName.strip().lower())
        if not oMatch or not isinstance(dSection, dict): continue
        sWays = next((v for k, v in dSection.items() if k.lower() == "ways"), "")
        lRoutes = []
        for sRoute in sWays.split(","):
            if not sRoute.strip(): continue
            lSteps = []
            for sStep in sRoute.split(">"):
                sEngine, _, sHands = sStep.strip().partition(":")
                lSteps.append((sEngine.strip().lower(), sHands.strip().lower()))
            lRoutes.append(lSteps)
        dTable.setdefault(oMatch.group(1), {})[oMatch.group(2)] = lRoutes
    return dTable


def typeOf(sPath):
    return os.path.splitext(sPath)[1].lstrip(".").lower()


# ---------- the engines: present or not ----------

def findProgram(sName, lsWindowsPaths=()):
    """The machine-wide install first, then the PATH, as Conversion.cs does (1.77.2). Asking the PATH first
    picked an old Pandoc 2.19.2 in c:\\bin over the machine-wide 3.12.1 on Jamal's computer, so the same
    conversion could differ between the C# and Python apps."""
    for sPattern in lsWindowsPaths:
        for sPath in glob.glob(os.path.expandvars(sPattern)):
            if os.path.isfile(sPath): return sPath
    sFound = shutil.which(sName)
    return sFound or ""


def programFor(sEngine):
    if sEngine == "pandoc": return findProgram("pandoc", [r"%ProgramFiles%\Pandoc\pandoc.exe", r"%LOCALAPPDATA%\Pandoc\pandoc.exe"])
    if sEngine == "tesseract": return findProgram("tesseract", [r"%ProgramFiles%\Tesseract-OCR\tesseract.exe"])
    return ""


def engineAvailable(sEngine):
    if sEngine in ("copy", "markdown", "zipxml"): return True
    if sEngine == "pandoc": return bool(programFor(sEngine))
    if sEngine == "ocr":
        try: import pypdfium2
        except ImportError: return False
        return bool(programFor("tesseract"))
    if sEngine == "pdftext":
        try: import pypdf; return True
        except ImportError: return False
    if sEngine == "pdfstructure":
        try: import pdfminer.high_level; return True
        except ImportError: return False
    if sEngine == "officecom":
        if os.name != "nt": return False
        try: import win32com.client; return True
        except ImportError: return False
    return False


# ---------- planning ----------

def plan(sSource, sTargetType):
    """(route, lsSkipped): the first route whose engines are all present, and why each earlier one was passed over."""
    sFrom = typeOf(sSource); sTo = sTargetType.lstrip(".").lower()
    lRoutes = loadTable().get(sFrom, {}).get(sTo)
    if not lRoutes: return None, ["no route from %s to %s in %s" % (sFrom or "a file with no type", sTo, sTableName)]
    lsSkipped = []
    for lSteps in lRoutes:
        lsMissing = [sEngine for sEngine, _ in lSteps if not engineAvailable(sEngine)]
        if not lsMissing: return lSteps, lsSkipped
        lsSkipped.append("%s: %s not present" % (" > ".join(e for e, _ in lSteps), ", ".join(lsMissing)))
    return None, lsSkipped


# ---------- running each engine: (source path, target type, output path) ----------

def run(lsCommand, sWhat):
    oDone = subprocess.run(lsCommand, capture_output=True, timeout=iTimeoutSeconds)
    if oDone.returncode != 0:
        raise RuntimeError("%s failed (exit %d): %s" % (sWhat, oDone.returncode, oDone.stderr.decode("utf-8", "replace")[:400]))


def engineCopy(sSource, sTo, sOut):
    shutil.copyfile(sSource, sOut)


dPandocWriter = {"md": "markdown", "htm": "html5", "html": "html5", "txt": "plain", "docx": "docx", "epub": "epub",
                   "odt": "odt", "pptx": "pptx", "rtf": "rtf"}
dPandocReader = {"htm": "html", "md": "markdown", "txt": "markdown", "docx": "docx", "epub": "epub", "odt": "odt", "rtf": "rtf", "html": "html"}


def enginePandoc(sSource, sTo, sOut):
    lsCommand = [programFor("pandoc"), sSource, "-f", dPandocReader.get(typeOf(sSource), typeOf(sSource)),
                 "-t", dPandocWriter.get(sTo, sTo), "-o", sOut, "--wrap=none"]
    if sTo in ("htm", "html", "docx", "epub", "odt", "rtf"): lsCommand.append("--standalone")
    # Math as MathML (1.77.0), which screen readers read as math; a page without math is unchanged.
    if sTo in ("htm", "html"): lsCommand.append("--mathml")
    run(lsCommand, "Pandoc")


def enginePdfText(sSource, sTo, sOut):
    import pypdf
    oReader = pypdf.PdfReader(sSource)
    lsPages = [(oPage.extract_text() or "").strip() for oPage in oReader.pages]
    if not any(lsPages): raise RuntimeError("the PDF has no text layer; it needs recognition (ocr)")
    open(sOut, "w", encoding="utf-8-sig", newline="\r\n").write("\n\n".join(lsPages) + "\n")


def enginePdfStructure(sSource, sTo, sOut):
    """Lines with their type sizes; the commonest size is the body, and larger sizes
    become headings, the largest level 1. Nothing is guessed beyond the sizes."""
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTTextLine, LTChar
    lLines = []
    for oPage in extract_pages(sSource):
        for oBox in oPage:
            if not isinstance(oBox, LTTextContainer): continue
            for oLine in oBox:
                if not isinstance(oLine, LTTextLine): continue
                sText = oLine.get_text().strip()
                lnSizes = [round(o.size, 1) for o in oLine if isinstance(o, LTChar)]
                if sText and lnSizes: lLines.append((sText, max(set(lnSizes), key=lnSizes.count)))
        lLines.append(("", 0))
    if not any(s for s, _ in lLines): raise RuntimeError("the PDF has no text layer; it needs recognition (ocr)")
    dCount = {}
    for sText, nSize in lLines:
        if nSize: dCount[nSize] = dCount.get(nSize, 0) + len(sText)
    nBody = max(dCount, key=dCount.get)
    lnHeadings = sorted([n for n in dCount if n > nBody + 0.5], reverse=True)[:4]
    lsOut, lsPara = [], []
    def flush():
        if lsPara: lsOut.append(" ".join(lsPara)); lsOut.append(""); lsPara.clear()
    for sText, nSize in lLines:
        if not sText: flush(); continue
        if nSize in lnHeadings and len(sText) < 160:
            flush(); lsOut.append("#" * (lnHeadings.index(nSize) + 1) + " " + sText); lsOut.append("")
        else:
            lsPara.append(sText)
    flush()
    open(sOut, "w", encoding="utf-8-sig", newline="\r\n").write("\n".join(lsOut).strip() + "\n")


nOcrScale = 200 / 72   # pages drawn at 200 dots an inch, enough for Tesseract


def engineOcr(sSource, sTo, sOut):
    """A scanned PDF: each page drawn as a picture by pypdfium2, read by Tesseract."""
    import pypdfium2
    sDir = tempfile.mkdtemp(prefix="homerOcr-")
    try:
        oPdf = pypdfium2.PdfDocument(sSource)
        for iPage in range(len(oPdf)):
            oPdf[iPage].render(scale=nOcrScale).to_pil().save(os.path.join(sDir, "page%04d.png" % iPage))
        oPdf.close()
        lsText = []
        for sImage in sorted(glob.glob(os.path.join(sDir, "page*.png"))):
            oDone = subprocess.run([programFor("tesseract"), sImage, "stdout"], capture_output=True, timeout=iTimeoutSeconds)
            lsText.append(oDone.stdout.decode("utf-8", "replace").strip())
        open(sOut, "w", encoding="utf-8-sig", newline="\r\n").write("\n\n".join(lsText) + "\n")
    finally:
        shutil.rmtree(sDir, ignore_errors=True)


sW = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
sA = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
sS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
sTextNamespace = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"


def zipDocx(oZip, bMarkdown):
    oRoot = ET.fromstring(oZip.read("word/document.xml"))
    lsOut = []
    for oPara in oRoot.iter(sW + "p"):
        sText = "".join(o.text or "" for o in oPara.iter(sW + "t")).strip()
        if not sText: continue
        oStyle = oPara.find(sW + "pPr/" + sW + "pStyle")
        oMatch = re.match(r"(?i)heading\s*(\d)", oStyle.get(sW + "val", "")) if oStyle is not None else None
        lsOut.append(("#" * int(oMatch.group(1)) + " " + sText) if (bMarkdown and oMatch) else sText)
    return lsOut


def zipXlsx(oZip, bMarkdown, bCsv=False):
    lsShared = []
    if "xl/sharedStrings.xml" in oZip.namelist():
        for oItem in ET.fromstring(oZip.read("xl/sharedStrings.xml")).iter(sS + "si"):
            lsShared.append("".join(o.text or "" for o in oItem.iter(sS + "t")))
    oBook = ET.fromstring(oZip.read("xl/workbook.xml"))
    lsNames = [o.get("name") for o in oBook.iter(sS + "sheet")]
    lsOut = []
    for iSheet, sName in enumerate(lsNames, 1):
        sPath = "xl/worksheets/sheet%d.xml" % iSheet
        if sPath not in oZip.namelist(): continue
        llRows = []
        for oRow in ET.fromstring(oZip.read(sPath)).iter(sS + "row"):
            lsCells = []
            for oCell in oRow.iter(sS + "c"):
                oValue = oCell.find(sS + "v"); oInline = oCell.find(sS + "is")
                sValue = oValue.text if oValue is not None else ("".join(o.text or "" for o in oInline.iter(sS + "t")) if oInline is not None else "")
                if oCell.get("t") == "s" and sValue: sValue = lsShared[int(sValue)]
                lsCells.append(sValue or "")
            llRows.append(lsCells)
        if bCsv:
            import csv, io
            oBuffer = io.StringIO(); csv.writer(oBuffer, lineterminator="\n").writerows(llRows)
            return oBuffer.getvalue().rstrip("\n").split("\n")   # the first sheet, as a comma-separated file
        if bMarkdown:
            lsOut.append("## " + sName); lsOut.append("")
            if llRows:
                iWidth = max(len(r) for r in llRows)
                for i, lsRow in enumerate(llRows):
                    lsOut.append("| " + " | ".join((lsRow + [""] * iWidth)[:iWidth]).replace("\n", " ") + " |")
                    if i == 0: lsOut.append("|" + "---|" * iWidth)
            lsOut.append("")
        else:
            lsOut.append(sName); lsOut += ["\t".join(r) for r in llRows]; lsOut.append("")
    return lsOut


def zipPptx(oZip, bMarkdown):
    lsSlides = sorted([s for s in oZip.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", s)], key=lambda s: int(re.findall(r"\d+", s)[-1]))
    lsOut = []
    sP = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
    for iSlide, sSlide in enumerate(lsSlides, 1):
        oRoot = ET.fromstring(oZip.read(sSlide))
        sTitle, lsBody = "", []
        for oShape in oRoot.iter(sP + "sp"):
            oPh = oShape.find(".//" + sP + "ph")
            lsParas = ["".join(o.text or "" for o in oPara.iter(sA + "t")).strip() for oPara in oShape.iter(sA + "p")]
            lsParas = [s for s in lsParas if s]
            if oPh is not None and oPh.get("type") in ("title", "ctrTitle") and not sTitle: sTitle = " ".join(lsParas)
            else: lsBody += lsParas
        if bMarkdown:
            lsOut.append("## " + (sTitle or "Slide %d" % iSlide)); lsOut.append("")
            lsOut += ["- " + s for s in lsBody]; lsOut.append("")
        else:
            lsOut += ([sTitle] if sTitle else []) + lsBody + [""]
    return lsOut


def zipOdf(oZip, bMarkdown):
    oRoot = ET.fromstring(oZip.read("content.xml"))
    lsOut = []
    for oNode in oRoot.iter():
        if oNode.tag in (sTextNamespace + "p", sTextNamespace + "h"):
            sText = "".join(oNode.itertext()).strip()
            if not sText: continue
            if bMarkdown and oNode.tag == sTextNamespace + "h":
                sText = "#" * int(oNode.get(sTextNamespace + "outline-level", "1")) + " " + sText
            lsOut.append(sText)
    return lsOut


sDraw = "{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}"
sPres = "{urn:oasis:names:tc:opendocument:xmlns:presentation:1.0}"


def zipOdp(oZip, bMarkdown):
    """OpenDocument slides: each draw:page is a slide, its title the frame of class title."""
    oRoot = ET.fromstring(oZip.read("content.xml"))
    lsOut = []
    for iSlide, oPage in enumerate(oRoot.iter(sDraw + "page"), 1):
        sTitle, lsBody = "", []
        for oFrame in oPage.iter(sDraw + "frame"):
            lsParas = [s for s in ("".join(o.itertext()).strip() for o in oFrame.iter(sTextNamespace + "p")) if s]
            if oFrame.get(sPres + "class") == "title" and not sTitle: sTitle = " ".join(lsParas)
            else: lsBody += lsParas
        if bMarkdown:
            lsOut.append("## " + (sTitle or "Slide %d" % iSlide)); lsOut.append("")
            lsOut += ["- " + s for s in lsBody]; lsOut.append("")
        else:
            lsOut += ([sTitle] if sTitle else []) + lsBody + [""]
    return lsOut


def engineZipXml(sSource, sTo, sOut):
    sFrom = typeOf(sSource); bMarkdown = (sTo == "md")
    with zipfile.ZipFile(sSource) as oZip:
        if sFrom == "docx": lsOut = zipDocx(oZip, bMarkdown)
        elif sFrom == "xlsx": lsOut = zipXlsx(oZip, bMarkdown, sTo == "csv")
        elif sFrom == "pptx": lsOut = zipPptx(oZip, bMarkdown)
        elif sFrom == "odp": lsOut = zipOdp(oZip, bMarkdown)
        elif sFrom in ("odt", "ods"): lsOut = zipOdf(oZip, bMarkdown)
        else: raise RuntimeError("zipxml does not read .%s" % sFrom)
    sJoin = "\n\n" if (bMarkdown and sFrom in ("docx", "odt")) else "\n"
    open(sOut, "w", encoding="utf-8-sig", newline="\r\n").write(sJoin.join(lsOut).strip() + "\n")


dOfficeFormat = {("word", "doc"): 0, ("word", "docx"): 16, ("word", "odt"): 23, ("word", "pdf"): 17, ("word", "htm"): 10,
                   ("word", "rtf"): 6, ("word", "txt"): 7,
                   ("excel", "xlsx"): 51, ("excel", "csv"): 6, ("excel", "htm"): 44,
                   ("powerpoint", "pptx"): 24, ("powerpoint", "pdf"): 32}


def engineOfficeCom(sSource, sTo, sOut):
    """The last resort: Microsoft Office by COM, Windows only, and logged as such."""
    import win32com.client
    sFrom = typeOf(sSource)
    sApp = "word" if sFrom in ("doc", "docx", "rtf", "odt", "htm", "html", "txt") else ("excel" if sFrom in ("xls", "xlsx", "ods", "csv") else "powerpoint")
    iFormat = dOfficeFormat.get((sApp, sTo))
    if iFormat is None: raise RuntimeError("Office cannot write .%s from .%s here" % (sTo, sFrom))
    say("officecom: the last resort, for %s" % os.path.basename(sSource))
    # OFFICE WRITES ITS OWN NAME (9 October 2026): the engine hands every route a target ending in .part, renamed
    # when the route succeeds. Word saves under exactly that name, but PowerPoint adds the extension of the format
    # it saves, so sample.pdf.part came out as sample.pdf.part.pdf and the rename failed with "cannot find the file
    # specified" -- the kit's pptx > pdf test failed on every build. Office now saves into a folder of its own under
    # a name with the right extension, and the result is moved to the target.
    sOfficeDir = tempfile.mkdtemp(prefix="homerOffice-")
    sFinal = sOut
    sOut = os.path.join(sOfficeDir, "converted." + sTo)
    try:
        engineOfficeComSave(sApp, sSource, sOut, iFormat)
        if not os.path.isfile(sOut):
            lsMade = [s for s in os.listdir(sOfficeDir) if s.lower().startswith("converted")]
            if not lsMade: raise RuntimeError("Office reported success but wrote no file")
            sOut = os.path.join(sOfficeDir, lsMade[0])
        # WORD'S TEXT IN THE HOMER ENCODING (1.76.1): UTF-8 with a byte order mark, whatever Word chose to write.
        if sApp == "word" and sTo == "txt":
            sText = decodeText(open(sOut, "rb").read())
            open(sOut, "w", encoding="utf-8-sig", newline="").write(sText)
        os.replace(sOut, sFinal)
    finally:
        shutil.rmtree(sOfficeDir, ignore_errors=True)


def engineOfficeComSave(sApp, sSource, sOut, iFormat):
    """Opens sSource in the Office application sApp and saves it to sOut in format iFormat."""
    import win32com.client
    if sApp == "word":
        oApp = win32com.client.DispatchEx("Word.Application"); oApp.Visible = False
        try:
            oDoc = oApp.Documents.Open(os.path.abspath(sSource), ReadOnly=True); oDoc.SaveAs2(os.path.abspath(sOut), FileFormat=iFormat); oDoc.Close(False)
        finally: oApp.Quit()
    elif sApp == "excel":
        oApp = win32com.client.DispatchEx("Excel.Application"); oApp.Visible = False; oApp.DisplayAlerts = False
        try:
            oBook = oApp.Workbooks.Open(os.path.abspath(sSource), ReadOnly=True); oBook.SaveAs(os.path.abspath(sOut), FileFormat=iFormat); oBook.Close(False)
        finally: oApp.Quit()
    else:
        oApp = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            oShow = oApp.Presentations.Open(os.path.abspath(sSource), ReadOnly=True, WithWindow=False); oShow.SaveAs(os.path.abspath(sOut), iFormat); oShow.Close()
        finally: oApp.Quit()


def engineMarkdown(sSource, sTo, sOut):
    """The kit's own writer of Markdown as an accessible web page (1.82.1), as Conversion.cs's markdown
    engine does, line for line: a second way after Pandoc for md2htm and pdf2htm, so a computer without
    Pandoc still gets a page. Headings, paragraphs, bullet and numbered lists, pipe tables, quotes,
    fenced code, rules; inline links, images with their alt text, bold, italic and code; lang and title
    from front matter, else the first heading, else the file name; the body inside main."""
    if sTo not in ("htm", "html"): raise ValueError("the markdown engine writes web pages only")
    sText = decodeText(open(sSource, "rb").read()).replace("\r\n", "\n").replace("\r", "\n")
    lsLines = sText.split("\n")
    sTitle, sLang, iAt = "", "en", 0
    if lsLines and lsLines[0].strip() == "---":
        iAt = 1
        while iAt < len(lsLines) and lsLines[iAt].strip() != "---":
            oMeta = re.match(r'^\s*(title|lang)\s*:\s*"?(.*?)"?\s*$', lsLines[iAt], re.I)
            if oMeta:
                if oMeta.group(1).lower() == "title": sTitle = oMeta.group(2)
                else: sLang = oMeta.group(2)
            iAt += 1
        iAt += 1
    lsBody, lsPara, dList = [], [], {"kind": ""}
    def closeList():
        if dList["kind"]: lsBody.append("</%s>" % dList["kind"]); dList["kind"] = ""
    def flush():
        if lsPara: lsBody.append("<p>" + markdownInline(" ".join(lsPara)) + "</p>"); del lsPara[:]
    i = iAt
    while i < len(lsLines):
        sLine = lsLines[i]; sTrim = sLine.strip()
        if sTrim.startswith("```"):
            flush(); closeList(); lsCode = []; i += 1
            while i < len(lsLines) and not lsLines[i].strip().startswith("```"): lsCode.append(htmlEscape(lsLines[i])); i += 1
            lsBody.append("<pre><code>" + "\r\n".join(lsCode) + "\r\n</code></pre>"); i += 1; continue
        if sTrim == "": flush(); closeList(); i += 1; continue
        oHead = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", sTrim)
        if oHead:
            flush(); closeList(); iLevel = len(oHead.group(1))
            if not sTitle and iLevel == 1: sTitle = re.sub(r"[*_`]", "", oHead.group(2))
            lsBody.append("<h%d>%s</h%d>" % (iLevel, markdownInline(oHead.group(2)), iLevel)); i += 1; continue
        if re.match(r"^(\*\s*\*\s*\*|-\s*-\s*-|_\s*_\s*_)[\s*_-]*$", sTrim): flush(); closeList(); lsBody.append("<hr>"); i += 1; continue
        if sTrim.startswith("|") and i + 1 < len(lsLines) and re.match(r"^\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?$", lsLines[i + 1].strip()):
            flush(); closeList()
            lsBody.append("<table>\r\n<thead><tr>" + "".join('<th scope="col">%s</th>' % markdownInline(c) for c in markdownCells(sTrim)) + "</tr></thead>\r\n<tbody>")
            i += 2
            while i < len(lsLines) and lsLines[i].strip().startswith("|"):
                lsBody.append("<tr>" + "".join("<td>%s</td>" % markdownInline(c) for c in markdownCells(lsLines[i].strip())) + "</tr>"); i += 1
            lsBody.append("</tbody>\r\n</table>"); continue
        oBullet = re.match(r"^\s*[-*+]\s+(.*)$", sLine); oNumber = re.match(r"^\s*\d+[.)]\s+(.*)$", sLine)
        if oBullet or oNumber:
            flush(); sKind = "ul" if oBullet else "ol"
            if dList["kind"] != sKind: closeList(); lsBody.append("<%s>" % sKind); dList["kind"] = sKind
            lsBody.append("<li>" + markdownInline((oBullet or oNumber).group(1)) + "</li>"); i += 1; continue
        if sTrim.startswith(">"): flush(); closeList(); lsBody.append("<blockquote><p>" + markdownInline(sTrim.lstrip(">").strip()) + "</p></blockquote>"); i += 1; continue
        closeList(); lsPara.append(sTrim); i += 1
    flush(); closeList()
    if not sTitle: sTitle = os.path.splitext(os.path.basename(sSource))[0]
    sPage = ('<!DOCTYPE html>\r\n<html lang="%s">\r\n<head>\r\n<meta charset="utf-8">\r\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1">\r\n<title>%s</title>\r\n</head>\r\n<body>\r\n<main>\r\n'
             % (htmlEscape(sLang), htmlEscape(sTitle))) + "".join(s + "\r\n" for s in lsBody) + "</main>\r\n</body>\r\n</html>\r\n"
    open(sOut, "w", encoding="utf-8-sig", newline="").write(sPage)


def markdownCells(sRow):
    s = sRow.strip()
    if s.startswith("|"): s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"): s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def markdownInline(sText):
    """Code spans and escaped characters set aside first, so neither becomes emphasis; then images,
    links, bold and italic -- the order Conversion.cs uses."""
    lsCode, lsEscaped = [], []
    def keepCode(m): lsCode.append(m.group(1)); return "\x01%d\x02" % (len(lsCode) - 1)
    def keepEscaped(m): lsEscaped.append(m.group(1)); return "\x03%d\x04" % (len(lsEscaped) - 1)
    s = re.sub(r"`([^`]+)`", keepCode, sText)
    s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>])", keepEscaped, s)
    s = htmlEscape(s)
    s = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)', r'<img src="\2" alt="\1">', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", r"<strong>\2</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])", r"<em>\1</em>", s)
    s = re.sub("\x03(\\d+)\x04", lambda m: htmlEscape(lsEscaped[int(m.group(1))]), s)
    s = re.sub("\x01(\\d+)\x02", lambda m: "<code>" + htmlEscape(lsCode[int(m.group(1))]) + "</code>", s)
    return s


def htmlEscape(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


dEngines = {"copy": engineCopy, "markdown": engineMarkdown, "ocr": engineOcr, "officecom": engineOfficeCom,
              "pandoc": enginePandoc, "pdfstructure": enginePdfStructure, "pdftext": enginePdfText, "zipxml": engineZipXml}


# ---------- converting ----------

def convert(sSource, sTarget, dOptions=None):
    """Convert sSource; sTarget is a path, or a type such as "md" for a file beside the source.
    Returns {path, route, ms, skipped}. Raises with every route's reason when none works."""
    if not os.path.isfile(sSource): raise FileNotFoundError(sSource)
    if os.path.splitext(sTarget)[1] or os.sep in sTarget or "/" in sTarget:
        sOut = sTarget; sTo = typeOf(sTarget)
    else:
        sTo = sTarget.lstrip(".").lower(); sOut = os.path.splitext(sSource)[0] + "." + sTo
    dTable = loadTable()
    lRoutes = dTable.get(typeOf(sSource), {}).get(sTo)
    if not lRoutes: raise ValueError("no route from .%s to .%s" % (typeOf(sSource), sTo))
    lsTried = []
    for lSteps in lRoutes:
        sName = " > ".join(e for e, _ in lSteps)
        lsMissing = [e for e, _ in lSteps if not engineAvailable(e)]
        if lsMissing: lsTried.append("%s: %s not present" % (sName, ", ".join(lsMissing))); continue
        dtStart = time.time()
        sDir = tempfile.mkdtemp(prefix="homerRoute-")
        try:
            sCurrent = sSource
            for i, (sEngine, sHands) in enumerate(lSteps):
                sStepTo = sHands if (i < len(lSteps) - 1 and sHands) else sTo
                sStepOut = os.path.join(sDir, "step%d.%s" % (i, sStepTo)) if i < len(lSteps) - 1 else sOut + ".part"
                dEngines[sEngine](sCurrent, sStepTo, sStepOut)
                sCurrent = sStepOut
            os.replace(sOut + ".part", sOut)
            # Text in the Homer encoding (1.80.0), as Conversion.cs does: UTF-8 with a byte order mark and CRLF.
            if typeOf(sOut) in ("csv", "htm", "html", "inix", "md", "tsv", "txt"):
                sMade = decodeText(open(sOut, "rb").read()).replace("\r\n", "\n").replace("\r", "\n")
                open(sOut, "w", encoding="utf-8-sig", newline="\r\n").write(sMade)
            iMs = int((time.time() - dtStart) * 1000)
            say("%s -> %s by %s in %d ms" % (sSource, sOut, sName, iMs))
            return {"path": sOut, "route": sName, "ms": iMs, "skipped": lsTried}
        except Exception as oError:
            lsTried.append("%s: %s" % (sName, oError))
            try: os.remove(sOut + ".part")
            except OSError: pass
        finally:
            shutil.rmtree(sDir, ignore_errors=True)
    raise RuntimeError("could not convert %s to .%s: %s" % (sSource, sTo, "; ".join(lsTried)))


def decodeText(abText):
    """Text from bytes whose encoding is not promised (1.76.1): the byte order mark first, then UTF-8, then the
    Windows code page. Word's text output was the case that needed it: UTF-16 from some documents and the code
    page from others, so a bullet (0x95) or a UTF-16 mark (0xFF) failed a UTF-8 read."""
    if abText[:2] in (b"\xff\xfe", b"\xfe\xff"): return abText.decode("utf-16")
    if abText[:3] == b"\xef\xbb\xbf": return abText[3:].decode("utf-8", "replace")
    try: return abText.decode("utf-8")
    except UnicodeDecodeError: return abText.decode("cp1252", "replace")


def toText(sSource):
    """The text of a file, by the quickest route the table offers for plain text."""
    sDir = tempfile.mkdtemp(prefix="homerText-")
    try:
        sOut = os.path.join(sDir, "text.txt")
        convert(sSource, sOut)
        return decodeText(open(sOut, "rb").read())
    finally:
        shutil.rmtree(sDir, ignore_errors=True)
