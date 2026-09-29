r"""elevate.py -- part of the shared Homer toolkit.

IS THERE A NEWER VERSION ON THE WEB, AND WOULD YOU LIKE IT?

THIS MODULE AND CSharp\Elevate.cs ARE THE SAME CLASS IN TWO LANGUAGES. Same
function names, same outcome numbers, same sentences: configure, check,
isNewer, describe, update and offer. "Elevate" is the Homer word for updating a
program to its newest release, and F11 is its key (elevate sounds like eleven).

AN APP CONFIGURES IT ONCE, at startup:

    import elevate
    elevate.configure("JamalMazrui", "urlCheck", sVersion)

and calls elevate.offer() from its F11 handler. offer checks, says what it
found, and on Yes fetches <repo>_setup.exe into the temporary folder and starts
it. The setup program asks for elevation itself.

NO WINDOW TOOLKIT IS ASSUMED. A Homer Python program may draw its windows with
wx (lbc), with WinForms through pythonnet (urlCheck), or have no window
at all. The questions here are Windows message boxes called through ctypes, so
every one of those programs gets the same box, owned by whatever window handle
it passes.

THE CHECK NEVER HANGS THE PROGRAM. Its own request, with an eight-second
timeout, because it runs from a key press on a machine that may be offline. A
failed check is an answer ("could not be checked"), not an exception.

WHAT COUNTS AS THE LATEST: the release GitHub marks latest. Its tag, with a
leading "v" removed, is the version; its asset named <repo>_setup.exe, in any
case, is what update fetches. When the API refuses (it limits callers who do
not sign in), the releases page is asked instead: it redirects to the tagged
release, and the setup program is then looked for at the usual download path.

VERSIONS ARE COMPARED AS NUMBERS. Compared as text, 1.11.0 sorts before 1.9.2,
and upgrades silently stop being offered. This module took over the version
comparison that lived in Python\homer\version.py, a name the kit could not
keep: every Homer build writes a version.py of its own, so .gitignore and the
checks treat that name as generated, and the module was never pushed.

Nothing here raises. Every function answers.
"""

import ctypes
import json
import os
import re
import subprocess
import tempfile
import urllib.request

# The outcome of a check, so callers can word themselves. The same numbers as
# Elevate.cs.
c_iCheckFailed = -1
c_iCurrent = 0
c_iNewer = 1
c_iNotConfigured = -2

c_iTimeoutSeconds = 8
c_sApiFormat = "https://api.github.com/repos/{0}/{1}/releases/latest"
c_sPageFormat = "https://github.com/{0}/{1}/releases/latest"
c_sUserAgent = "Homer (+version check)"

# Windows message box flags, named rather than numbered.
c_iMbDefButton2 = 0x100
c_iMbIconInformation = 0x40
c_iMbIconQuestion = 0x20
c_iMbOk = 0x0
c_iMbYesNo = 0x4
c_iIdYes = 6

sLatestFound = ""
sOwner = ""
sRepo = ""
sSetupUrlFound = ""
sThisVersion = ""


def configure(sOwnerIn, sRepoIn, sVersionIn):
    """Name the repository and this program's version. True when all three are given."""
    global sLatestFound, sOwner, sRepo, sSetupUrlFound, sThisVersion
    sOwner = (sOwnerIn or "").strip()
    sRepo = (sRepoIn or "").strip()
    sThisVersion = (sVersionIn or "").strip()
    sLatestFound = ""
    sSetupUrlFound = ""
    return isConfigured()


def isConfigured():
    return sOwner != "" and sRepo != "" and sThisVersion != ""


def thisVersion(): return sThisVersion
def latestVersion(): return sLatestFound
def setupUrl(): return sSetupUrlFound
def repoUrl(): return "https://github.com/%s/%s" % (sOwner, sRepo)


# --- comparing ----------------------------------------------------------------

def parse(sVersion):
    """A version as a tuple of numbers, ignoring any leading letter."""
    return tuple(int(s) for s in re.findall(r"\d+", str(sVersion or ""))) or (0,)


def compare(sLeft, sRight):
    """1, 0 or minus 1, comparing numerically rather than as text."""
    tLeft, tRight = parse(sLeft), parse(sRight)
    iLength = max(len(tLeft), len(tRight))
    tLeft += (0,) * (iLength - len(tLeft))
    tRight += (0,) * (iLength - len(tRight))
    return (tLeft > tRight) - (tLeft < tRight)


def isNewer(sRemote, sLocal):
    """True when sRemote is a later version than sLocal."""
    return compare(sRemote, sLocal) > 0


# --- asking the web -------------------------------------------------------------

def fetch(sUrl, sAccept="application/vnd.github+json"):
    """The body at sUrl and the address it ended at, or two empty strings."""
    try:
        request = urllib.request.Request(sUrl, headers={"Accept": sAccept, "User-Agent": c_sUserAgent})
        with urllib.request.urlopen(request, timeout=c_iTimeoutSeconds) as response:
            return response.read().decode("utf-8", errors="replace"), getattr(response, "url", "") or ""
    except Exception:
        return "", ""


def check():
    """Ask GitHub once. Returns one of the c_i outcomes.

    On c_iCurrent or c_iNewer, latestVersion() and setupUrl() are filled in.
    """
    global sLatestFound, sSetupUrlFound
    if not isConfigured(): return c_iNotConfigured
    sTag = ""
    sAsset = ""
    sBody, sFinal = fetch(c_sApiFormat.format(sOwner, sRepo))
    if sBody:
        try:
            dRelease = json.loads(sBody)
            sTag = str(dRelease.get("tag_name", "")).strip()
            for dAsset in dRelease.get("assets", []) or []:
                sName = str(dAsset.get("name", ""))
                if sName.lower() == (sRepo + "_setup.exe").lower():
                    sAsset = str(dAsset.get("browser_download_url", ""))
                    break
        except Exception:
            sTag = ""
    if not sTag:
        # The page fallback: no rate limit, and it redirects to /tag/<tag>.
        sBody, sFinal = fetch(c_sPageFormat.format(sOwner, sRepo), "text/html")
        match = re.search(r"/tag/([^/?#]+)/?$", sFinal or "")
        if match: sTag = match.group(1)
        if sTag:
            sAsset = "https://github.com/%s/%s/releases/download/%s/%s_setup.exe" % (sOwner, sRepo, sTag, sRepo)
    if not sTag: return c_iCheckFailed
    if sTag[:1] in ("v", "V"): sTag = sTag[1:]
    sLatestFound = sTag
    sSetupUrlFound = sAsset
    return c_iNewer if isNewer(sLatestFound, sThisVersion) else c_iCurrent


def describe(iOutcome):
    """The sentence a version box shows for an outcome of check()."""
    if iOutcome == c_iNotConfigured: return ""
    if iOutcome == c_iCheckFailed:
        return "This is version %s. The web could not be checked for a newer one." % sThisVersion
    if iOutcome == c_iNewer:
        return "This is version %s. Version %s is on the web." % (sThisVersion, sLatestFound)
    return "This is version %s, the newest on the web." % sThisVersion


def update():
    """Fetch the setup program found by check() and start it. False when nothing started."""
    if sSetupUrlFound == "" and check() < c_iCurrent: return False
    if sSetupUrlFound == "": return False
    sFile = os.path.join(tempfile.gettempdir(), sRepo + "_setup.exe")
    try:
        if os.path.exists(sFile): os.remove(sFile)
        request = urllib.request.Request(sSetupUrlFound, headers={"User-Agent": c_sUserAgent})
        with urllib.request.urlopen(request, timeout=120) as response, open(sFile, "wb") as fileOut:
            while True:
                binChunk = response.read(1024 * 256)
                if not binChunk: break
                fileOut.write(binChunk)
        if not os.path.exists(sFile) or os.path.getsize(sFile) == 0: return False
        os.startfile(sFile)
        return True
    except Exception:
        try:
            subprocess.Popen([sFile])
            return True
        except Exception:
            return False


# --- the conversation, for an F11 handler ---------------------------------------

def messageBox(hOwner, sText, sTitle, iFlags):
    """A Windows message box, whatever toolkit drew the owner. Returns the button id."""
    try:
        return int(ctypes.windll.user32.MessageBoxW(int(hOwner or 0), str(sText), str(sTitle), int(iFlags)))
    except Exception:
        print(sText)
        return 0


def offer(hOwner=0):
    """Check, say what was found, and update if the person says yes.

    hOwner is the window handle that owns the boxes: frm.Handle.ToInt64() in
    WinForms, frame.GetHandle() in wx, 0 for none. Returns True when the setup
    program was started. Yes is the default when a newer version exists and No
    when this one is current -- pressing Enter does the likely thing.
    """
    iOutcome = check()
    if iOutcome == c_iNotConfigured: return False
    if iOutcome == c_iCheckFailed:
        messageBox(hOwner, describe(iOutcome), "Version", c_iMbOk | c_iMbIconInformation)
        return False
    iFlags = c_iMbYesNo | c_iMbIconQuestion
    if iOutcome != c_iNewer: iFlags |= c_iMbDefButton2
    if messageBox(hOwner, describe(iOutcome) + "\r\n\r\nUpdate to it now?", "Version", iFlags) != c_iIdYes:
        return False
    if update(): return True
    messageBox(hOwner, "The setup program could not be fetched. It is at %s/releases." % repoUrl(),
               "Version", c_iMbOk | c_iMbIconInformation)
    return False
