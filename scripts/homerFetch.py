r"""homerFetch.py -- fetches a web resource politely and keeps the last good copy, for any Homer script that gathers
from the web. Part of the HomerDev kit (1.292.0). A module to import, not a command.

    import homerFetch
    oCache = homerFetch.Cache(r"C:\DbDo\data\BrailleForum", fLog=log)
    dResult = oCache.fetch("https://www.acb.org/sites/default/files/bf112023.txt")
    oCache.save()

WHY A KIT MODULE. Every Homer harvester fetched its own way: makeDescribedFilms, harvestShows, helpFido. An archive
built from a magazine's issues, such as DbDo's BrailleForum template, asks the same server for the same hundreds of
files every time it is rebuilt. This module asks once, then asks again only "has it changed?", so a rebuild costs the
server almost nothing and works offline from the copies already kept.

WHAT ONE FETCH DOES.
  - Asks with If-None-Match and If-Modified-Since when it holds a copy, so an unchanged file comes back as 304 and
    is read from the cache.
  - Waits between requests (nDelay seconds), times out (iTimeout), and retries a failure (iRetries), waiting longer
    each time.
  - Stores the body under its SHA-256 hash, so a changed file never overwrites the copy it replaces, and the same
    body fetched from two addresses is kept once.
  - Keeps the last good copy when a fetch fails, and says so in the result.

THE MANIFEST, manifest.inix in the cache folder, has one section per address: its etag, last-modified, hash, file,
size, the time it was last fetched and last changed, and its last status. UTF-8 with a byte order mark and Windows
line endings, so EdSharp and the screen reader read it like any other Homer settings file.

THE RESULT of fetch is a dictionary: status ("new", "changed", "unchanged", "kept" when bTrustKept let the kept copy
stand without asking, "cached" when the fetch failed and the last good copy was used, "missing" when it failed with no copy, or "skipped" when bOffline), body (bytes or None),
hash, path, code (the HTTP status, or 0), and error (text, or "").
"""

import datetime, hashlib, io, os, time, urllib.error, urllib.request

sVersion = "1.292.0"


def stamp():
    """Now, as SQLite writes times: yyyy-MM-dd HH:mm:ss."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def readInix(sPath):
    """{section: {key: value}} from an .inix file; comments and blank lines set aside."""
    dSections, sSection = {}, ""
    if not os.path.isfile(sPath): return dSections
    for sLine in io.open(sPath, encoding="utf-8-sig"):
        sLine = sLine.strip()
        if not sLine or sLine.startswith(";"): continue
        if sLine.startswith("[") and sLine.endswith("]"):
            sSection = sLine[1:-1]
            dSections.setdefault(sSection, {})
            continue
        if "=" in sLine and sSection:
            sKey, sValue = sLine.split("=", 1)
            dSections[sSection][sKey.strip()] = sValue.strip()
    return dSections


def writeInix(sPath, dSections, sHeader):
    """Writes {section: {key: value}} as .inix, sections in alphabetical order, UTF-8 with BOM and CRLF."""
    lsLines = [";" + s if s else ";" for s in sHeader.splitlines()] + [""]
    for sSection in sorted(dSections, key=str.lower):
        lsLines.append("[%s]" % sSection)
        for sKey in sorted(dSections[sSection]):
            lsLines.append("%s = %s" % (sKey, dSections[sSection][sKey]))
        lsLines.append("")
    sTemp = sPath + ".new"
    with io.open(sTemp, "w", encoding="utf-8-sig", newline="\r\n") as fOut: fOut.write("\n".join(lsLines))
    os.replace(sTemp, sPath)
    return True


class Cache:
    """A folder of fetched bodies with its manifest."""

    def __init__(self, sFolder, fLog=None, nDelay=1.0, iTimeout=60, iRetries=3, sUserAgent="", bOffline=False):
        self.sFolder = os.path.abspath(sFolder)
        self.sFiles = os.path.join(self.sFolder, "files")
        os.makedirs(self.sFiles, exist_ok=True)
        self.sManifest = os.path.join(self.sFolder, "manifest.inix")
        self.dManifest = readInix(self.sManifest)
        self.fLog = fLog or (lambda sText: True)
        self.nDelay, self.iTimeout, self.iRetries, self.bOffline = nDelay, iTimeout, iRetries, bOffline
        self.sUserAgent = sUserAgent or "HomerDev homerFetch/%s (+https://github.com/JamalMazrui/HomerDev)" % sVersion
        self.nLast = 0.0
        self.dCounts = {}
        self.bTrustKept = False   # True: a kept copy is used without asking the server, as for an old issue that will not change
        self.fLog("homerFetch %s: cache %s; %d addresses known; delay %.1f s; timeout %d s; retries %d; offline %s"
                  % (sVersion, self.sFolder, len(self.dManifest), nDelay, iTimeout, iRetries, bOffline))

    def known(self, sUrl):
        """The manifest entry for an address, or {}."""
        return self.dManifest.get(sUrl, {})

    def body(self, sUrl):
        """The kept body of an address, or None. A DAMAGED COPY IS NO COPY (26 November 2026, from ChatGPT's plan for
        BrailleMonitor: "retry unconditionally when a 304 refers to missing or damaged cached bytes"). A kept file
        whose bytes no longer match the hash the manifest recorded is set aside, so the address is fetched afresh,
        without If-None-Match, rather than a 304 confirming bytes that are gone or changed."""
        dEntry = self.known(sUrl)
        sFile = dEntry.get("file", "")
        sPath = os.path.join(self.sFiles, sFile) if sFile else ""
        if not (sPath and os.path.isfile(sPath)): return None
        binBody = io.open(sPath, "rb").read()
        if dEntry.get("hash") and hashlib.sha256(binBody).hexdigest() != dEntry["hash"]:
            self.fLog("FETCH damaged %s: the kept file %s no longer matches its recorded hash, so it is fetched afresh" % (sUrl, sFile))
            return None
        return binBody

    def wait(self):
        """Keeps nDelay seconds between requests to the server."""
        nGap = self.nDelay - (time.time() - self.nLast)
        if nGap > 0: time.sleep(nGap)
        self.nLast = time.time()
        return True

    def count(self, sStatus):
        self.dCounts[sStatus] = self.dCounts.get(sStatus, 0) + 1
        return self.dCounts[sStatus]

    def result(self, sUrl, sStatus, binBody, iCode, sError):
        dEntry = self.known(sUrl)
        sFile = dEntry.get("file", "")
        self.count(sStatus)
        self.fLog("FETCH %s %s code %d%s" % (sStatus, sUrl, iCode, "; " + sError if sError else ""))
        return {"status": sStatus, "body": binBody, "hash": dEntry.get("hash", ""), "path": os.path.join(self.sFiles, sFile) if sFile else "",
                "code": iCode, "error": sError}

    def keep(self, sUrl, binBody, oHeaders, iCode):
        """Stores a body under its hash and records it; returns new, changed or unchanged."""
        sHash = hashlib.sha256(binBody).hexdigest()
        dOld = self.known(sUrl)
        sExt = os.path.splitext(sUrl.split("?")[0])[1].lower()
        sExt = sExt if 1 < len(sExt) <= 6 else ".bin"
        sFile = sHash[:16] + sExt
        sPath = os.path.join(self.sFiles, sFile)
        if not os.path.isfile(sPath):
            with io.open(sPath + ".new", "wb") as fOut: fOut.write(binBody)
            os.replace(sPath + ".new", sPath)
        sStatus = "new" if not dOld else ("unchanged" if dOld.get("hash") == sHash else "changed")
        dNew = dict(dOld)
        dNew.update({"etag": (oHeaders.get("ETag") or "").strip(), "modified": (oHeaders.get("Last-Modified") or "").strip(),
                     "hash": sHash, "file": sFile, "size": str(len(binBody)), "fetched": stamp(), "status": str(iCode)})
        if sStatus != "unchanged": dNew["changed"] = stamp()
        self.dManifest[sUrl] = dNew
        return sStatus

    def fetch(self, sUrl):
        """One address, as the module's notes describe."""
        dOld = self.known(sUrl)
        binKept = self.body(sUrl)
        if self.bTrustKept and binKept is not None: return self.result(sUrl, "kept", binKept, 0, "")
        if self.bOffline:
            return self.result(sUrl, "cached" if binKept is not None else "skipped", binKept, 0, "" if binKept is not None else "offline, and no copy is kept")
        dHeaders = {"User-Agent": self.sUserAgent, "Accept-Encoding": "identity"}
        if binKept is not None and dOld.get("etag"): dHeaders["If-None-Match"] = dOld["etag"]
        if binKept is not None and dOld.get("modified"): dHeaders["If-Modified-Since"] = dOld["modified"]
        sError, iCode = "", 0
        for iTry in range(1, self.iRetries + 1):
            self.wait()
            try:
                oResponse = urllib.request.urlopen(urllib.request.Request(sUrl, headers=dHeaders), timeout=self.iTimeout)
                iCode = oResponse.getcode() or 200
                binBody = oResponse.read()
                sStatus = self.keep(sUrl, binBody, oResponse.headers, iCode)
                return self.result(sUrl, sStatus, binBody, iCode, "")
            except urllib.error.HTTPError as oError:
                iCode = oError.code
                if iCode == 304 and binKept is not None:
                    self.dManifest[sUrl]["fetched"] = stamp()
                    self.dManifest[sUrl]["status"] = "304"
                    return self.result(sUrl, "unchanged", binKept, 304, "")
                sError = "HTTP %d %s" % (iCode, oError.reason)
                if iCode in (400, 401, 403, 404, 410): break   # asking again will not change the answer
            except Exception as oError:
                sError = "%s: %s" % (type(oError).__name__, oError)
            self.fLog("RETRY %d of %d for %s: %s" % (iTry, self.iRetries, sUrl, sError))
            time.sleep(self.nDelay * iTry * 2)
        if dOld: self.dManifest[sUrl]["status"] = str(iCode or "failed")
        if binKept is not None: return self.result(sUrl, "cached", binKept, iCode, sError + "; the last good copy is used")
        return self.result(sUrl, "missing", None, iCode, sError)

    def save(self):
        """Writes the manifest."""
        writeInix(self.sManifest, self.dManifest,
                  " manifest.inix -- what homerFetch (HomerDev %s) holds for each address, written %s.\n"
                  " One section per address: etag and modified as the server sent them, the body's SHA-256 hash and the\n"
                  " file in files\\ that holds it, its size, when it was last fetched and last changed, and the last status.\n"
                  " Written by the program; edit only to make it forget an address (delete its section)." % (sVersion, stamp()))
        self.fLog("MANIFEST %s: %d addresses; this run %s" % (self.sManifest, len(self.dManifest),
                  ", ".join("%s %d" % (s, self.dCounts[s]) for s in sorted(self.dCounts)) or "fetched nothing"))
        return True
