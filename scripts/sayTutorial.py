#!/usr/bin/env python3
r"""sayTutorial.py -- turn a Tutorial*.inix into an audio tutorial in two voices.

WHY TWO VOICES. A listener who cannot see the screen has no other way to tell
the teacher from the machine. The narration is one voice; what the screen reader
answers is another. A tutorial that reads both in one voice is a tutorial nobody
can follow, and that is the single thing this script exists to get right.

WHAT IT READS. Any Tutorial*.inix beside it, in the format makeTutorial.py uses:

    [about]
    Title = ...
    Setup = ...
    Intro = ...

    [step]
    Say  = the narration
    Key  = the keystroke, named the way a person says it
    Hear = what the screen reader answers   (repeat for several lines)
    Note = written version only; never spoken

WHAT IT WRITES, beside the source:

    <stem>.mp3      the whole tutorial, when ffmpeg is here
    <stem>\NNN-*.wav  one file per spoken line, always

The per-line files are kept whether or not they were joined. They are what lets
one sentence be re-recorded without redoing the tutorial, and they cost nothing.

HOW IT SPEAKS. Windows' own voices, through System.Speech from PowerShell.
Nothing is installed and nothing is uploaded. Two voices are chosen from what
this machine has: the first for narration, a different one for the screen
reader. Name them explicitly with --narrator and --reader when the automatic
choice is wrong.

    sayTutorial                         every Tutorial*.inix beside this script
    sayTutorial Tutorial_HomerDev.inix  one of them
    sayTutorial --list                  the voices this machine has
    sayTutorial --narrator "Microsoft David Desktop" --reader "Microsoft Zira Desktop"

A detailed log is written beside this script as sayTutorial.log.
"""

import argparse
import datetime
import glob
import os
import platform
import subprocess
import sys
import traceback

c_iKeyPauseMs = 400          # silence around a keystroke, so it lands separately
c_sLogName = "sayTutorial.log"

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sLogPath = os.path.join(sScriptDir, c_sLogName)
oLog = None


# --- saying things ----------------------------------------------------------

def logLine(sText):
    if oLog is None: return True
    oLog.write(sText + "\n")
    oLog.flush()
    return True


def sayLine(sText=""):
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def countNoun(iCount, sSingular, sPlural=None):
    """"1 step", "0 steps" -- the noun always matches the count."""
    if sPlural is None: sPlural = sSingular + "s"
    return "%d %s" % (iCount, sSingular if iCount == 1 else sPlural)


def runPowerShell(sCommand):
    """Run one PowerShell command; return (iCode, sOutput). Never raises."""
    lsArgs = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", sCommand]
    logLine("RUN: powershell -Command " + sCommand[:400])
    try:
        oResult = subprocess.run(lsArgs, capture_output=True, text=True)
    except Exception as oError:
        logLine("RUN FAILED: %s" % oError)
        return (1, str(oError))
    logLine("EXIT: %d" % oResult.returncode)
    if oResult.stdout: logLine("STDOUT:\n" + oResult.stdout.rstrip())
    if oResult.stderr: logLine("STDERR:\n" + oResult.stderr.rstrip())
    return (oResult.returncode, oResult.stdout or "")


# --- the voices -------------------------------------------------------------

def listVoices():
    """Every installed voice, in the order Windows reports them."""
    iCode, sOut = runPowerShell(
        "Add-Type -AssemblyName System.Speech;"
        "(New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices() |"
        " ForEach-Object { $_.VoiceInfo.Name }")
    if iCode != 0: return []
    return [s.strip() for s in sOut.splitlines() if s.strip()]


def chooseVoices(sNarrator, sReader):
    """Two different voices: the narrator, and the one the screen reader gets.

    Given names are taken as given. Otherwise the first installed voice narrates
    and the second answers, which on a stock Windows is a male and a female
    voice and is exactly the distinction wanted.
    """
    lsVoices = listVoices()
    logLine("Voices installed: " + ", ".join(lsVoices))
    if not lsVoices:
        return ("", "")
    if not sNarrator: sNarrator = lsVoices[0]
    if not sReader:
        lsOther = [s for s in lsVoices if s != sNarrator]
        sReader = lsOther[0] if lsOther else sNarrator
    if sReader == sNarrator:
        sayLine("Only 1 voice is installed, so the narrator and the screen reader")
        sayLine("will sound the same. Add a voice in Windows settings, under")
        sayLine("Time and language, Speech, to tell them apart.")
    return (sNarrator, sReader)


def speakToFile(sText, sVoice, sPath, iRate):
    """One line of speech into one .wav file."""
    sSafeText = sText.replace("'", "''")
    sSafeVoice = sVoice.replace("'", "''")
    sSafePath = sPath.replace("'", "''")
    sCommand = ("Add-Type -AssemblyName System.Speech;"
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "try { $s.SelectVoice('%s') } catch { };"
                "$s.Rate = %d;"
                "$s.SetOutputToWaveFile('%s');"
                "$s.Speak('%s');"
                "$s.Dispose()" % (sSafeVoice, iRate, sSafePath, sSafeText))
    iCode, sOut = runPowerShell(sCommand)
    return os.path.isfile(sPath)


# --- reading the tutorial ---------------------------------------------------

def readSections(sPath):
    """The .inix as a list of sections, each a dict of field to list of values.

    A tolerant reader: a field may repeat, and repeats are kept in order, which
    is how a step carries several Hear lines.
    """
    lsSections = []
    dNow = None
    for sLine in open(sPath, "rb").read().decode("utf-8-sig").splitlines():
        sLine = sLine.strip()
        if not sLine or sLine.startswith(";") or sLine.startswith("#"): continue
        if sLine.startswith("[") and sLine.endswith("]"):
            dNow = {"_name": sLine[1:-1].strip().lower()}
            lsSections.append(dNow)
            continue
        if dNow is None or "=" not in sLine: continue
        sField, sValue = sLine.split("=", 1)
        dNow.setdefault(sField.strip(), []).append(sValue.strip())
    return lsSections


def firstOf(dSection, sField):
    lsValues = dSection.get(sField, [])
    return lsValues[0] if lsValues else ""


def linesToSpeak(lsSections):
    """The whole tutorial as (role, text) pairs, in the order they are heard."""
    lsLines = []
    for dSection in lsSections:
        if dSection["_name"] == "about":
            sTitle = firstOf(dSection, "Title")
            sIntro = firstOf(dSection, "Intro")
            sSetup = firstOf(dSection, "Setup")
            if sTitle: lsLines.append(("narrator", sTitle))
            if sIntro: lsLines.append(("narrator", sIntro))
            if sSetup: lsLines.append(("narrator", "What you need. " + sSetup))
        elif dSection["_name"] == "step":
            sSay = firstOf(dSection, "Say")
            sKey = firstOf(dSection, "Key")
            if sSay: lsLines.append(("narrator", sSay))
            if sKey: lsLines.append(("narrator", "Press " + sKey))
            for sHear in dSection.get("Hear", []):
                lsLines.append(("reader", sHear))
    return lsLines


# --- joining ----------------------------------------------------------------

def joinWithFfmpeg(lsWavs, sMp3):
    """One file out of many, when ffmpeg is on the PATH. Silent when it is not."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except Exception:
        logLine("ffmpeg is not here, so the parts were not joined.")
        return False
    sList = os.path.join(os.path.dirname(lsWavs[0]), "parts.txt")
    with open(sList, "w", encoding="utf-8") as oFile:
        for sWav in lsWavs:
            oFile.write("file '%s'\n" % sWav.replace("\\", "/"))
    lsArgs = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", sList,
              "-codec:a", "libmp3lame", "-qscale:a", "4", sMp3]
    logLine("RUN: " + " ".join(lsArgs))
    try:
        oResult = subprocess.run(lsArgs, capture_output=True, text=True)
        logLine("EXIT: %d" % oResult.returncode)
        if oResult.stderr: logLine("STDERR:\n" + oResult.stderr[-4000:])
        return os.path.isfile(sMp3)
    except Exception as oError:
        logLine("JOIN FAILED: %s" % oError)
        return False


# --- the work ---------------------------------------------------------------

def sayTutorial(sSource, sNarrator, sReader, iRate):
    sStem = os.path.splitext(os.path.basename(sSource))[0]
    sFolder = os.path.join(os.path.dirname(sSource), sStem)
    os.makedirs(sFolder, exist_ok=True)

    lsSections = readSections(sSource)
    lsLines = linesToSpeak(lsSections)
    logLine("%s: %s, %s" % (os.path.basename(sSource),
                            countNoun(len(lsSections), "section"),
                            countNoun(len(lsLines), "spoken line")))
    if not lsLines:
        sayLine("%s holds 0 spoken lines." % os.path.basename(sSource))
        return False

    lsWavs = []
    iNumber = 0
    for sRole, sText in lsLines:
        iNumber += 1
        sVoice = sNarrator if sRole == "narrator" else sReader
        sWav = os.path.join(sFolder, "%03d-%s.wav" % (iNumber, sRole))
        logLine("%03d  %-8s  %s" % (iNumber, sRole, sText[:120]))
        if speakToFile(sText, sVoice, sWav, iRate):
            lsWavs.append(sWav)
        else:
            sayLine("Line %d could not be spoken. The log has why." % iNumber)

    sayLine("%s spoken into %s." % (countNoun(len(lsWavs), "line"), sFolder))
    sMp3 = os.path.join(os.path.dirname(sSource), sStem + ".mp3")
    if lsWavs and joinWithFfmpeg(lsWavs, sMp3):
        sayLine("Joined into %s." % os.path.basename(sMp3))
    else:
        sayLine("The parts were not joined; install ffmpeg to get one file.")
    return True


def main():
    global oLog
    oParser = argparse.ArgumentParser(description="Speak a Tutorial inix in two voices.")
    oParser.add_argument("source", nargs="?", default="",
                         help="one Tutorial*.inix; all of them by default")
    oParser.add_argument("--list", action="store_true", help="list this machine's voices and stop")
    oParser.add_argument("--narrator", default="", help="the narrator's voice")
    oParser.add_argument("--rate", type=int, default=0, help="speaking rate, -10 to 10")
    oParser.add_argument("--reader", default="", help="the screen reader's voice")
    dArguments = oParser.parse_args()

    oLog = open(sLogPath, "w", encoding="utf-8")
    logLine("sayTutorial started %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    logLine("Script: %s" % os.path.abspath(__file__))
    logLine("Python: %s" % sys.version.replace("\n", " "))
    logLine("Platform: %s" % platform.platform())
    logLine("Working directory: %s" % os.getcwd())
    logLine("Command line: %s" % " ".join(sys.argv))

    if dArguments.list:
        lsVoices = listVoices()
        sayLine("%s installed:" % countNoun(len(lsVoices), "voice"))
        for sVoice in lsVoices: sayLine("  " + sVoice)
        return 0

    sNarrator, sReader = chooseVoices(dArguments.narrator, dArguments.reader)
    if not sNarrator:
        sayLine("No speech voice was found on this machine, so nothing was spoken.")
        return 1
    sayLine("Narrator: %s" % sNarrator)
    sayLine("Screen reader: %s" % sReader)
    logLine("Rate: %d" % dArguments.rate)

    # Tutorial scripts live in help, which is where the Homer layout puts
    # documents; a copy beside this script works too.
    lsSources = ([os.path.abspath(dArguments.source)] if dArguments.source
                 else sorted(glob.glob(os.path.join(sScriptDir, "Tutorial*.inix")) +
                             glob.glob(os.path.join(sScriptDir, "..", "help", "Tutorial*.inix"))))
    if not lsSources:
        sayLine("There is no Tutorial inix file here, so there is nothing to speak.")
        return 1

    for sSource in lsSources:
        sayTutorial(sSource, sNarrator, sReader, dArguments.rate)
    logLine("Finished %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    return 0


if __name__ == "__main__":
    iCode = 1
    try:
        iCode = main()
    except Exception:
        try:
            logLine("TRACEBACK:\n" + traceback.format_exc())
        except Exception:
            pass
        print("Something went wrong. The details are in %s." % sLogPath)
    finally:
        if oLog is not None: oLog.close()
    sys.exit(iCode)
