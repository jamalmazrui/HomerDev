r"""paths.py -- part of the shared Homer toolkit.

WHERE A HOMER APP PUTS ITS FILES, AND WHY THE NAMES ARE WHAT THEY ARE.

THIS MODULE AND CSharp\Paths.cs ARE THE SAME CLASS IN TWO LANGUAGES. Same
folder names, same fallback rule, same function names: start, appName,
installedFolder, userFolder, configs, data, jobs, logs, results, temp, the
shipped counterparts, configFile, clearTemp and tempFile.

A screen reader user moves through a folder listing by first letter. Nine
folders whose names all begin with the same letter cost nine keystrokes each
time; nine whose initials differ cost one. So every folder in the Homer layout
starts with a different letter, and the letter is the fast way in:

    c  configs     settings that decide how the program starts
    d  data        databases and seed data
    h  help        the documents: the guide, the tutorials, the history
    e  exec        the program itself: .exe, .dll, .py, .vbs
    j  jobs        scripts, add-ons and plugins that change behaviour later
    l  logs        one file per session
    r  results     what the program produced
    s  samples     examples that show what the program can do
    t  temp        scratch, deletable at the start of the next run
    t  templates   files a user copies and fills in

TWO t NAMES, AND THEY NEVER MEET. temp exists only in the per-user tree;
templates exists only in the installed tree. A listing therefore never holds
both, and first-letter navigation stays exact. A temp folder under Program Files
could not be written to anyway, which is the whole reason the per-user tree
exists.

THREE TREES, AND WHAT EACH HOLDS.

  The INSTALLED tree, C:\Program Files\<App>, read-only to the user:
      configs, data, exec, jobs, samples, templates, and the documents at its
      root where a person looking for the ReadMe expects them.

  The PER-USER tree, %LOCALAPPDATA%\<App>, which the program owns and writes:
      configs, data, jobs, logs, results, temp. No exec, no samples, no
      templates: those are shipped, not made.

  The DEVELOPMENT folder, C:\<App>, stays flat. It is a git repository, and
  every tool that reads one expects the source at the top. The structure is what
  the build SHIPS INTO, not what the developer works in.

Usage:

    from homer import paths
    paths.start("JobDo")
    sInix = paths.configFile("JobDo.inix")   # the user's, else the shipped one
    sOut = paths.results()                   # where output goes
    paths.clearTemp()                        # at startup, once

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
    try:
        sHere = os.path.dirname(os.path.abspath(sys.argv[0]))
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

def configs(): return _madeUnder(userFolder(), "configs")
def data(): return _madeUnder(userFolder(), "data")
def jobs(): return _madeUnder(userFolder(), "jobs")
def logs(): return _madeUnder(userFolder(), "logs")
def results(): return _madeUnder(userFolder(), "results")
def temp(): return _madeUnder(userFolder(), "temp")


# The shipped folders, read-only, never created here: a program that has to
# create its own samples folder has no samples.

def shippedConfigs(): return os.path.join(installedFolder(), "configs")
def shippedData(): return os.path.join(installedFolder(), "data")
def shippedExec(): return os.path.join(installedFolder(), "exec")
def shippedHelp(): return os.path.join(installedFolder(), "help")
def shippedJobs(): return os.path.join(installedFolder(), "jobs")
def shippedSamples(): return os.path.join(installedFolder(), "samples")
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


def clearTemp():
    """Empty the temp folder, at startup, once.

    Anything still in there is what a previous run could not clean up after
    itself, which is exactly what the folder is for: a crash leaves its
    half-written files somewhere known rather than somewhere shared.
    """
    iRemoved = 0
    try:
        sTemp = temp()
        for sName in os.listdir(sTemp):
            sPath = os.path.join(sTemp, sName)
            try:
                if os.path.isdir(sPath): shutil.rmtree(sPath)
                else: os.remove(sPath)
                iRemoved += 1
            except OSError:
                pass
    except Exception:
        pass
    return iRemoved


def tempFile(sExtension=".tmp"):
    """A name inside temp that nothing else is using."""
    if not sExtension.startswith("."): sExtension = "." + sExtension
    return os.path.join(temp(), "%s-%s%s" % (appName(),
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3], sExtension))
