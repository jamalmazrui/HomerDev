r"""paths.py -- part of the shared Homer toolkit.

WHERE A HOMER APP PUTS ITS FILES, AND WHY THE NAMES ARE WHAT THEY ARE.

THIS MODULE AND CSharp\Paths.cs ARE THE SAME CLASS IN TWO LANGUAGES. Same
folder names, same fallback rule, same function names: start, appName,
installedFolder, userFolder, configs, data, logs, results, work, the
shipped counterparts, configFile, clearWork and workFile. The old names
temp, clearTemp and tempFile still work, as other names for the same three.

A screen reader user moves through a folder listing by first letter. Nine
folders whose names all begin with the same letter cost nine keystrokes each
time; nine whose initials differ cost one. So every folder in the Homer layout
starts with a different letter, and the letter is the fast way in:

    c  configs     settings that decide how the program starts
    d  data        databases and seed data
    h  help        the documents: the guide, the tutorials, the history
    e  exec        the program itself: .exe, .dll, .py, .vbs
    s  scripts     scripts, add-ons and plugins that change behaviour later
    l  logs        one file per session
    r  results     what the program produced
    t  templates   files a user copies and fills in
    w  work        scratch: what one run leaves, the next run deletes

ONE LETTER, ONE FOLDER (1.203.0, his ruling of 11 November 2026). The scratch
folder was called temp, which shared its t with templates; the rule had been
that the two never met in one tree. Now t means templates and nothing else, in
the installed tree and the per-user tree alike, and scratch is work: w was free.
Every new session of a Homer program or script may delete whatever a previous
session left in work, and clearWork does exactly that, once, at startup. A
temp folder an older version left in the per-user tree is deleted by clearWork
too, since it held only scratch.

THREE TREES, AND WHAT EACH HOLDS.

  The INSTALLED tree, %ProgramFiles%\<App>, read-only to the user:
      configs, data, exec, help, scripts, templates, and the documents at its
      root where a person looking for the ReadMe expects them.

  The PER-USER tree, %LOCALAPPDATA%\<App>, which the program owns and writes:
      configs, data, logs, results, scripts, work. No exec and no
      templates: those are shipped, not made.

  The DEVELOPMENT folder, <App> on any drive and at any depth, mirrors the installed tree (21 Sep 2026,
  superseding "stays flat"): sources, build files, ReadMe and License at the
  top, and configs, data, exec, help, logs, scripts and templates beneath, so
  a program run from the project's exec folder finds its files exactly as the
  installed copy does.

Usage:

    import paths
    paths.start("JobDo")
    sInix = paths.configFile("JobDo.inix")   # the user's, else the shipped one
    sOut = paths.results()                   # where output goes
    paths.clearWork()                        # at startup, once

Nothing here raises. A folder that cannot be made comes back as a path that does
not exist, and the caller's own error handling deals with it.
"""

import datetime
import os
import shutil
import sys

_sAppName = ""


# --- starting ---------------------------------------------------------------

def start(sAppNameGiven):
    """Name the app, which is all this module needs. Call it beside log.start."""
    global _sAppName
    _sAppName = (sAppNameGiven or "").strip()
    return _sAppName != ""


def appName():
    """The app's name, from start, or from the running program."""
    global _sAppName
    if _sAppName: return _sAppName
    try:
        _sAppName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    except Exception:
        pass
    if not _sAppName: _sAppName = "Homer"
    return _sAppName


# --- the two trees ----------------------------------------------------------

def installedFolder():
    """Where the program was installed: its own folder, or exec's parent."""
    # A FROZEN PROGRAM ASKS sys.executable (1.43.0). sys.argv[0] is what was
    # typed: "urlCheck" run through the PATH from another folder resolved
    # against that folder, and the guide was looked for in the wrong place.
    try:
        sHere = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]))
    except Exception:
        sHere = os.getcwd()
    if os.path.basename(sHere).lower() == "exec":
        return os.path.dirname(sHere)
    return sHere


def userFolder():
    """%LOCALAPPDATA%\\<App>, which the program owns."""
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), appName())


# --- the folders, by the letter a user types --------------------------------
#
# Each returns a path in the PER-USER tree and makes it when it is missing,
# because these are the ones a program writes to.

def moveFromRoaming():
    r"""A Homer app keeps nothing under %APPDATA% (1.43.49). Files an earlier
    version left in %APPDATA%\<App> -- the Roaming tree -- are moved to the same
    place under %LOCALAPPDATA%\<App>, unless a file is already there, in which
    case the Roaming copy is left and reported; the Roaming folder goes once it
    is empty. Returns one line per action, for the log. As Paths.moveFromRoaming
    in C#. Call it once, after log.start and before any setting is read."""
    lsLines = []
    try:
        sRoaming = os.path.join(os.environ.get("APPDATA", ""), appName())
        if not os.environ.get("APPDATA") or not os.path.isdir(sRoaming): return lsLines
        sLocal = userFolder()
        for sDir, lsDirs, lsFiles in os.walk(sRoaming):
            for sName in lsFiles:
                sFile = os.path.join(sDir, sName)
                sTarget = os.path.join(sLocal, os.path.relpath(sFile, sRoaming))
                try:
                    if os.path.exists(sTarget):
                        lsLines.append('roaming kept file=%s reason="a file of that name is already at %s"' % (sFile, sTarget))
                        continue
                    os.makedirs(os.path.dirname(sTarget), exist_ok=True)
                    shutil.move(sFile, sTarget)
                    lsLines.append("roaming moved file=%s to=%s" % (sFile, sTarget))
                except Exception as oError:
                    lsLines.append('roaming kept file=%s reason="%s"' % (sFile, oError))
        for sDir, lsDirs, lsFiles in sorted(os.walk(sRoaming, topdown=False), key=lambda t: -len(t[0])):
            try:
                if not os.listdir(sDir): os.rmdir(sDir)
            except Exception:
                pass
        if not os.path.isdir(sRoaming): lsLines.append("roaming removed folder=%s" % sRoaming)
    except Exception as oError:
        lsLines.append("roaming ERROR %s" % oError)
    return lsLines


def configs(): return _madeUnder(userFolder(), "configs")
def data(): return _madeUnder(userFolder(), "data")
def scripts(): return _madeUnder(userFolder(), "scripts")
def logs(): return _madeUnder(userFolder(), "logs")
def results(): return _madeUnder(userFolder(), "results")
def work(): return _madeUnder(userFolder(), "work")
def temp(): return work()   # the old name of work (1.203.0)


# The shipped folders, read-only, never created here: a program that has to
# create its own templates folder has no templates.

def shippedConfigs(): return os.path.join(installedFolder(), "configs")
def shippedData(): return os.path.join(installedFolder(), "data")
def shippedExec(): return os.path.join(installedFolder(), "exec")
def shippedHelp(): return os.path.join(installedFolder(), "help")
def shippedScripts(): return os.path.join(installedFolder(), "scripts")
def shippedTemplates(): return os.path.join(installedFolder(), "templates")


def _madeUnder(sParent, sChild):
    sPath = os.path.join(sParent, sChild)
    try:
        os.makedirs(sPath, exist_ok=True)
    except Exception:
        pass
    return sPath


# --- the pattern every app needs --------------------------------------------

def configFile(sFileName):
    """The user's copy of a settings file, falling back to the shipped one.

    This is the whole of "read the shipped default, write the user's change",
    written here once rather than in every app. The answer is a path in the
    per-user tree whenever one exists there, so a caller may write to it.
    """
    sUser = os.path.join(configs(), sFileName)
    if os.path.isfile(sUser): return sUser
    sShipped = os.path.join(shippedConfigs(), sFileName)
    if os.path.isfile(sShipped):
        try:
            shutil.copyfile(sShipped, sUser)
            return sUser
        except Exception:
            return sShipped
    return sUser


def clearWork():
    """Empty the work folder, at startup, once, and delete an older temp folder.

    Anything still in work is what a previous run could not clean up after
    itself, which is exactly what the folder is for: a crash leaves its
    half-written files somewhere known rather than somewhere shared. A temp
    folder beside it is where versions before 1.203.0 kept the same scratch.
    """
    iRemoved = 0
    try:
        sWork = work()
        lsPaths = [os.path.join(sWork, sName) for sName in os.listdir(sWork)]
        sOld = os.path.join(userFolder(), "temp")
        if os.path.isdir(sOld): lsPaths.append(sOld)
        for sPath in lsPaths:
            try:
                if os.path.isdir(sPath): shutil.rmtree(sPath)
                else: os.remove(sPath)
                iRemoved += 1
            except OSError:
                pass
    except Exception:
        pass
    return iRemoved


def clearTemp(): return clearWork()   # the old name of clearWork (1.203.0)


def workFile(sExtension=".tmp"):
    """A name inside work that nothing else is using."""
    if not sExtension.startswith("."): sExtension = "." + sExtension
    return os.path.join(work(), "%s-%s%s" % (appName(),
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3], sExtension))


def tempFile(sExtension=".tmp"): return workFile(sExtension)   # the old name of workFile (1.203.0)
