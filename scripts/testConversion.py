"""testConversion.py -- prove the shared conversion routes on real files, before any app relies on them.

    testConversion          every route in exec\\conversions.inix that a sample can test

Sample files are made here at test time, with approved tools only -- Pandoc,
Python, pypdfium2 and Pillow -- so no binary sample is stored: Word,
OpenDocument, PowerPoint, EPUB, HTML, RTF, Excel, a PDF with a larger-type
heading, and a scanned PDF of a picture only. Each
route is run and its output must exist and hold the document's marker word;
a Markdown result must keep a heading. A route whose engines are not on this
computer is reported as not tested, never as passed. Exit 1 when a route fails.
The log is logs\\HomerDev-testConversion-<stamp>.log.
"""
import datetime, glob, os, shutil, subprocess, sys, tempfile
sKit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(sKit, "exec", "Python"))
import conversion

c_sMarker = "Harborlight"
c_sSample = """# The Harborlight Report

## First findings

The Harborlight survey found three things worth telling.

- Tides rose early.
- Boats came back late.

| Pier | Boats |
|------|-------|
| North | 12 |
| South | 9 |
"""
lsLog = []
def logLine(s): lsLog.append(datetime.datetime.now().strftime("%H:%M:%S ") + s)

def makePdf(sPath):
    """A one-page PDF written by hand: the title in 24 point type, the rest in 12,
    so the structure route has a heading to find. Only Python is needed."""
    lsLines = [(24, "The Harborlight Report"), (16, "First findings"),
               (12, "The Harborlight survey found three things worth telling."),
               (12, "Tides rose early."), (12, "Boats came back late.")]
    sStream, iY = "", 760
    for iSize, sText in lsLines:
        sStream += "BT /F1 %d Tf 72 %d Td (%s) Tj ET\n" % (iSize, iY, sText); iY -= iSize + 14
    lsObjects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                 "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
                 "<< /Length %d >>\nstream\n%sendstream" % (len(sStream), sStream),
                 "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    sOut, liOffsets = "%PDF-1.4\n", []
    for i, sObject in enumerate(lsObjects, 1):
        liOffsets.append(len(sOut)); sOut += "%d 0 obj\n%s\nendobj\n" % (i, sObject)
    iXref = len(sOut)
    sOut += "xref\n0 %d\n0000000000 65535 f \n" % (len(lsObjects) + 1) + "".join("%010d 00000 n \n" % n for n in liOffsets)
    sOut += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(lsObjects) + 1, iXref)
    open(sPath, "wb").write(sOut.encode("latin-1"))


def makeXlsx(sPath):
    """A one-sheet workbook written as its XML, with the marker word in a cell."""
    import zipfile
    llRows = [["Pier", "Boats"], ["North", "12"], ["South", "9"], [c_sMarker, "1"]]
    sRows = ""
    for i, lsRow in enumerate(llRows, 1):
        sRows += '<row r="%d">' % i + "".join('<c t="inlineStr"><is><t>%s</t></is></c>' % s for s in lsRow) + "</row>"
    with zipfile.ZipFile(sPath, "w") as oZip:
        oZip.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        oZip.writestr("xl/workbook.xml", '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Piers" sheetId="1"/></sheets></workbook>')
        oZip.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>' % sRows)


def make(sDir):
    """The sample files this computer can make, by type, with approved tools only:
    Pandoc, Python, and the PyPI packages pypdfium2 and Pillow for the scanned page."""
    dMade = {}
    sMd = os.path.join(sDir, "sample.md"); open(sMd, "w", encoding="utf-8").write(c_sSample); dMade["md"] = sMd
    sTxt = os.path.join(sDir, "sample.txt"); open(sTxt, "w", encoding="utf-8").write(c_sSample); dMade["txt"] = sTxt
    for sTo in ("docx", "odt", "pptx", "epub", "htm", "rtf"):
        try:
            sOut = os.path.join(sDir, "sample." + sTo); conversion.convert(sMd, sOut); dMade[sTo] = sOut
        except Exception as oError: logLine("could not make sample .%s: %s" % (sTo, oError))
    if "htm" in dMade: dMade["html"] = shutil.copy(dMade["htm"], os.path.join(sDir, "sample2.html"))
    try:
        sXlsx = os.path.join(sDir, "sheet.xlsx"); makeXlsx(sXlsx); dMade["xlsx"] = sXlsx
    except Exception as oError: logLine("could not make sample .xlsx: %s" % oError)
    try:
        sPdf = os.path.join(sDir, "sample.pdf"); makePdf(sPdf); dMade["pdf"] = sPdf
    except Exception as oError: logLine("could not make sample .pdf: %s" % oError)
    if "pdf" in dMade:
        try:
            import pypdfium2
            oPdf = pypdfium2.PdfDocument(dMade["pdf"])
            oImage = oPdf[0].render(scale=150 / 72).to_pil().convert("RGB"); oPdf.close()
            sScan = os.path.join(sDir, "scanned.pdf"); oImage.save(sScan, "PDF", resolution=150); dMade["scanned"] = sScan
        except Exception as oError: logLine("could not make the scanned sample: %s" % oError)
    return dMade

def main():
    sDir = tempfile.mkdtemp(prefix="homerTestConversion-")
    iPass = iFail = iUntested = 0
    try:
        dMade = make(sDir)
        logLine("samples: " + ", ".join(sorted(dMade)))
        dTable = conversion.loadTable()
        for sFrom in sorted(dTable):
            for sTo in sorted(dTable[sFrom]):
                sSource = dMade.get(sFrom)
                if not sSource: iUntested += 1; logLine("NOT TESTED %s > %s: no sample here" % (sFrom, sTo)); continue
                lRoute, lsSkipped = conversion.plan(sSource, sTo)
                if lRoute is None: iUntested += 1; logLine("NOT TESTED %s > %s: %s" % (sFrom, sTo, "; ".join(lsSkipped))); continue
                sOut = os.path.join(sDir, "out-%s-to.%s" % (sFrom, sTo))
                try:
                    dDone = conversion.convert(sSource, sOut)
                    sText = conversion.toText(sOut) if sTo not in ("txt", "md", "htm", "html", "csv") else open(sOut, encoding="utf-8-sig", errors="replace").read()
                    lsWrong = []
                    if c_sMarker.lower() not in sText.lower(): lsWrong.append("no marker word")
                    if sTo == "md" and sFrom not in ("xlsx", "ods", "xls") and "#" not in sText: lsWrong.append("no heading")
                    if lsWrong: iFail += 1; logLine("FAIL %s > %s by %s: %s" % (sFrom, sTo, dDone["route"], ", ".join(lsWrong)))
                    else: iPass += 1; logLine("pass %s > %s by %s, %d ms" % (sFrom, sTo, dDone["route"], dDone["ms"]))
                except Exception as oError:
                    iFail += 1; logLine("FAIL %s > %s: %s" % (sFrom, sTo, oError))
        if "scanned" in dMade:
            try:
                sText = conversion.toText(dMade["scanned"])
                if c_sMarker.lower() in sText.lower(): iPass += 1; logLine("pass scanned pdf > txt, falling back to recognition")
                else: iFail += 1; logLine("FAIL scanned pdf > txt: the marker word was not recognised")
            except Exception as oError: iFail += 1; logLine("FAIL scanned pdf > txt: %s" % oError)
    finally:
        shutil.rmtree(sDir, ignore_errors=True)
    sSummary = "%d routes passed, %d failed, %d not tested here." % (iPass, iFail, iUntested)
    logLine(sSummary)
    sLogs = os.path.join(sKit, "logs"); os.makedirs(sLogs, exist_ok=True)
    sLog = os.path.join(sLogs, "HomerDev-testConversion-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    open(sLog, "w", encoding="utf-8-sig", newline="\r\n").write("\n".join(lsLog) + "\n")
    for s in lsLog:
        if s[9:].startswith("FAIL"): print(s[9:])
    print(sSummary + " The log is " + sLog)
    return 1 if iFail else 0

if __name__ == "__main__":
    sys.exit(main())
