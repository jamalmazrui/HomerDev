# buildTutorials.ps1 -- write the tutorials and speak them, in one command.
#
#   buildTutorials                    every Tutorial*.inix: documents, then audio
#   buildTutorials Tutorial_Tagging   just that one
#   buildTutorials -docs              documents and feed only, no speaking
#   buildTutorials -sapi              use Windows voices; fetch nothing
#   buildTutorials -live              perform it now through JAWS, write no file
#
# WHAT IT DOES, IN ORDER
#
#   1. Makes sure there are two voices worth listening to (see below).
#   2. Runs makeTutorials.py: the sections of Tutorials.md and the feed.
#   3. Speaks each script into its own .mp3.
#   3a. Joins them into Tutorials.mkv, one chapter per tutorial, and writes
#       Tutorials.m3u beside it.
#   4. Runs makeTutorials.py again, so the feed picks up the audio just made.
#
# THE TWO VOICES, AND WHY THESE
#
# A walkthrough has two speakers and they must never be confused, because the
# whole point is knowing which words came from the program. So one voice should
# sound like a person and the other should sound like a screen reader.
#
# The narrator is PIPER, with the en_US-lessac-medium voice: a small neural
# engine from the Rhasspy project, free, MIT-licensed, entirely offline once
# fetched, and the best free English narration available for Windows. NVDA
# add-ons and other accessibility software use the same engine, so it is a
# known quantity rather than a novelty.
#
# The screen reader's stand-in is ESPEAK NG: free, tiny, and unmistakably
# synthetic -- the voice a listener recognises as a machine within two words.
# That is not a shortcoming here; it is the requirement.
#
# Neither is installed unless it is missing, both are fetched from their own
# projects, and -sapi skips all of it and uses the Windows voices instead. The
# log records every URL, every size and every exit code.
#
# THE SETTINGS, AND WHY THEY ARE NEARLY ALL DEFAULTS
#
# Narration is left at the voice's own rate and pitch. A narrator who sounds
# hurried is harder to follow than one who sounds ordinary, and a tutorial is
# listened to once by somebody who does not yet know the words.
#
# The screen reader's stand-in is the one thing set deliberately: FASTER than
# the narrator, because that is what a screen reader sounds like to the people
# this is for, and because the contrast does the work that a label would
# otherwise have to do. eSpeak runs at 260 words a minute here against a
# narrator near 150; with the Windows voices the same gap is rate 6 against
# rate 4.
#
# Volume stays equal. Making the reader quieter would suggest it matters less,
# and in a walkthrough it is the half that carries the answers. Pitch is left
# alone in both: two voices that already differ in engine and speed do not need
# a third difference, and pitch-shifted speech is tiring over three minutes.

$ErrorActionPreference = "Stop"
$sTool = Split-Path -Parent $MyInvocation.MyCommand.Path

# THE SCRIPTS LIVE IN help, THE TOOLING IN scripts.
#
# FileDir keeps both in one folder; the Homer layout does not, and this script
# was copied without noticing. $sHere is therefore the folder holding the
# tutorial scripts -- help -- and the audio, the playlist and Tutorials.mkv are
# written beside them, where a person looking for a tutorial looks. The tools,
# the voices and the log stay in scripts.
$sHere = Join-Path (Split-Path -Parent $sTool) "help"
if (-not (Test-Path -LiteralPath $sHere)) { $sHere = $sTool }
$sLogDir = Join-Path (Split-Path -Parent $sTool) "logs"
if (-not (Test-Path -LiteralPath $sLogDir)) { New-Item -ItemType Directory -Path $sLogDir | Out-Null }
$sLog = Join-Path $sLogDir ((Split-Path -Leaf (Split-Path -Parent $sTool)) + "-tutorials-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
$sTools = Join-Path $sTool "voices"

trap {
  $sWhere = ""
  try { $sWhere = " at line " + $_.InvocationInfo.ScriptLineNumber } catch { }
  try {
    Add-Content -LiteralPath $sLog -Value ((Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "  UNEXPECTED: " + $_.Exception.Message + $sWhere)
    Add-Content -LiteralPath $sLog -Value ($_.ScriptStackTrace)
  } catch { }
  Write-Host "Something unexpected stopped the script. The log has it."
  exit 1
}

function note([string] $sText) {
  Add-Content -LiteralPath $sLog -Value ((Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "  " + $sText)
}

function say([string] $sText) {
  Write-Host $sText
  note $sText
}

if (Test-Path -LiteralPath $sLog) { Remove-Item -LiteralPath $sLog -Force }
note "buildTutorials starting"
note ("script: " + $MyInvocation.MyCommand.Path)
note ("PowerShell: " + $PSVersionTable.PSVersion.ToString())
note ("platform: " + [Environment]::OSVersion.VersionString)
note ("working directory: " + (Get-Location).Path)
note ("command line: " + [Environment]::CommandLine)

# ---- what was asked for ----

$bDocsOnly = $false
$bSapi = $false
$bLive = $false
$sOnly = ""
foreach ($sArg in $args) {
  $sTrimmed = ("" + $sArg).Trim()
  if ($sTrimmed.Length -eq 0) { continue }
  if ($sTrimmed -eq "-docs") { $bDocsOnly = $true; continue }
  if ($sTrimmed -eq "-sapi") { $bSapi = $true; continue }
  if ($sTrimmed -eq "-live") { $bLive = $true; continue }
  if ($sTrimmed.StartsWith("-")) { note ("ignoring unknown switch " + $sTrimmed); continue }
  $sOnly = [System.IO.Path]::GetFileNameWithoutExtension($sTrimmed)
}
note ("docs only: " + $bDocsOnly + ", Windows voices: " + $bSapi + ", live: " + $bLive + ", only: " + $sOnly)

# ---- the scripts to build ----

$lsScripts = @()
if ($sOnly -ne "") {
  $sOne = Join-Path $sHere ($sOnly + ".inix")
  if (-not (Test-Path -LiteralPath $sOne)) { say ($sOnly + ".inix is not here."); exit 1 }
  $lsScripts = @($sOne)
}
else {
  $lsScripts = @(Get-ChildItem -LiteralPath $sHere -Filter "Tutorial*.inix" | Sort-Object Name | ForEach-Object { $_.FullName })
}
if ($lsScripts.Count -eq 0) { say "0 tutorial scripts here."; exit 1 }
note ("scripts: " + (($lsScripts | ForEach-Object { [System.IO.Path]::GetFileName($_) }) -join ", "))

# ---- running a voice, without its chatter ending the run ----
#
# THIS IS WHAT KILLED THE FIRST REAL RUN:
#
#   UNEXPECTED: [piper] [info] Loaded voice in 0.29 second(s)
#
# Not an error -- piper says it every time, on standard error, because that is
# where command-line tools put progress. But $ErrorActionPreference is "Stop",
# and PowerShell 5 turns a native program's standard error into a terminating
# error when it is piped. So the narrator announcing that it had loaded
# successfully ended the build.
#
# runVoice takes the whole thing back to what it should be: standard error goes
# to the log as text, the exit code decides whether anything went wrong, and
# nothing a tool says can stop the script.
function runVoice([string] $sExe, [string[]] $lsArgs, [object] $oInput, [string] $sLabel) {
  # NOTHING TO SAY MEANS NOTHING TO RUN.
  #
  # This is what hung the build partway through the eighth tutorial. Steps that
  # only explain something carry an empty Hear line, and piper reads its text
  # from standard input: handed nothing, it waits for input that never comes,
  # with no output and no exit.
  #
  # THE PARAMETER IS [object], NOT [string], AND THAT MATTERS. PowerShell
  # converts $null to "" when a parameter is typed [string], so the callers that
  # pass $null -- python, ffmpeg, everything that reads no standard input --
  # arrived here indistinguishable from an empty line of speech. The guard then
  # skipped them all, and the very next build wrote no documents at all:
  #
  #     makeTutorial skipped: nothing to say
  #     The documents could not be written.
  #
  # With [object] a null stays a null, and only a genuinely empty string is
  # treated as nothing to say.
  $sInput = $null
  if ($oInput -is [string]) { $sInput = [string] $oInput }
  if ($null -ne $sInput -and $sInput.Trim() -eq "") {
    note ("  " + $sLabel + " skipped: nothing to say")
    return 0
  }
  $sOut = ""
  $sPrevious = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    if ($null -eq $sInput) { $sOut = (& $sExe @lsArgs 2>&1 | Out-String) }
    else { $sOut = ($sInput | & $sExe @lsArgs 2>&1 | Out-String) }
  }
  catch {
    note (("  " + $sLabel + " threw: " + $_.Exception.Message))
  }
  finally { $ErrorActionPreference = $sPrevious }
  foreach ($sLine in ($sOut -split "`r?`n")) {
    if ($sLine.Trim() -ne "") { note ("  " + $sLabel + " | " + $sLine.Trim()) }
  }
  return $LASTEXITCODE
}

# ---- step 1 of 4: the documents ----

function runMake() {
  $sPython = ""
  foreach ($sTry in @("python.exe", "py.exe")) {
    $oFound = Get-Command $sTry -ErrorAction SilentlyContinue
    if ($oFound -and $sPython -eq "") { $sPython = $oFound.Source }
  }
  if ($sPython -eq "") { say "Python was not found, so the documents cannot be written."; return $false }
  note ("Python: " + $sPython)
  # Take the code runVoice RETURNS. $LASTEXITCODE is whatever the last native
  # command in this session set, which after a skipped or wrapped call is
  # nothing at all -- the log showed "exit code: " with a blank after it.
  $iExit = runVoice $sPython @((Join-Path $sTool "makeTutorials.py")) $null "makeTutorial"
  note ("makeTutorials.py exit code: " + $iExit)
  return ($iExit -eq 0)
}

say "Writing the tutorials into Tutorials.md ..."
if (-not (runMake)) { say "The documents could not be written. The log has why."; exit 1 }
if ($bDocsOnly) { say "Documents only, as asked. Nothing was spoken."; exit 0 }

# ---- step 2 of 4: the voices ----

$sFfmpeg = Join-Path $sTool "ffmpeg.exe"
if (-not (Test-Path -LiteralPath $sFfmpeg)) {
  $oFound = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
  if ($oFound) { $sFfmpeg = $oFound.Source }
}
note ("ffmpeg: " + $sFfmpeg)
if (-not $bLive -and -not (Test-Path -LiteralPath $sFfmpeg)) {
  say "ffmpeg was not found, and it is what joins the pieces into one file."
  say "Run installMediaTools.cmd in this folder."
  exit 1
}

function fetchTo([string] $sUrl, [string] $sPath) {
  # One download, with the whole story in the log: where from, where to, and
  # how big it turned out to be.
  note ("fetching " + $sUrl)
  note ("      to " + $sPath)
  try {
    $oOld = $ProgressPreference
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $sUrl -OutFile $sPath -UseBasicParsing
    $ProgressPreference = $oOld
    note ("fetched " + (Get-Item -LiteralPath $sPath).Length + " bytes")
    return $true
  }
  catch {
    note ("fetch failed: " + $_.Exception.Message)
    return $false
  }
}

$sPiper = ""
$sPiperVoice = ""
$sEspeak = ""

if (-not $bSapi -and -not $bLive) {
  New-Item -ItemType Directory -Path $sTools -Force | Out-Null

  # PIPER: the narrator. A release zip and one voice, both fetched once.
  $sPiper = Join-Path $sTools "piper\piper.exe"
  if (-not (Test-Path -LiteralPath $sPiper)) {
    say "Fetching the narrator voice. This happens once."
    $sZip = Join-Path $sTools "piper.zip"
    if (fetchTo "https://github.com/rhasspy/piper/releases/latest/download/piper_windows_amd64.zip" $sZip) {
      try {
        Expand-Archive -LiteralPath $sZip -DestinationPath $sTools -Force
        # THE DOWNLOAD GOES ONCE IT IS UNPACKED. 22 MB of it, sitting beside the
        # 63 MB voice model and the unpacked copy of itself, in a folder nobody
        # thinks to look in. A tool that fetches something should leave behind
        # only the thing it needed.
        try { Remove-Item -LiteralPath $sZip -Force; note ("removed " + $sZip) } catch { }
      }
      catch { note ("could not unpack piper: " + $_.Exception.Message) }
    }
  }
  if (-not (Test-Path -LiteralPath $sPiper)) {
    $oFound = Get-ChildItem -LiteralPath $sTools -Filter "piper.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($oFound) { $sPiper = $oFound.FullName }
  }
  note ("piper: " + $sPiper + ", present: " + (Test-Path -LiteralPath $sPiper))

  # TWO NEURAL VOICES, ONE ENGINE.
  #
  # fetchVoice takes a piper voice name -- speaker and quality -- and brings back
  # the model and its settings file, once.
  function fetchVoice([string] $sSpeaker, [string] $sQuality) {
    $sName = "en_US-" + $sSpeaker + "-" + $sQuality
    $sModel = Join-Path $sTools ($sName + ".onnx")
    $sJson = $sModel + ".json"
    $sBase = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/" + $sSpeaker + "/" + $sQuality + "/"
    if (-not (Test-Path -LiteralPath $sModel)) {
      if (-not (fetchTo ($sBase + $sName + ".onnx") $sModel)) { return "" }
    }
    if (-not (Test-Path -LiteralPath $sJson)) {
      if (-not (fetchTo ($sBase + $sName + ".onnx.json") $sJson)) { return "" }
    }
    return $sModel
  }

  if (Test-Path -LiteralPath $sPiper) {
    # THE VOICES ARE CHOSEN BY LICENCE FIRST, THEN BY SOUND.
    #
    # The audio these produce is published in DbDo's repository under MIT, so
    # the training data behind each voice matters as much as the voice does.
    # Most of piper's best-known English voices cannot be used that way:
    #
    #   lessac     Blizzard 2013 corpus -- research purposes only, and the
    #              licence explicitly excludes commercial use of anything
    #              derived from it.
    #   ryan       RyanSpeech, CC BY-NC-SA 4.0: non-commercial AND share-alike,
    #              which fights an MIT repository. It is also fine-tuned FROM
    #              lessac, so it carries that restriction too.
    #   hfc_male,  CC BY-NC-SA 4.0.
    #   hfc_female
    #   libritts_r CC BY 4.0 on the data, but fine-tuned from lessac.
    #
    # Bryce Beattie trained a set of voices for exactly this reason -- his
    # stated goal was voices without restrictive licences -- and those are the
    # ones used here. Both are public domain at the source, trained from scratch
    # or from each other, with no restricted ancestor anywhere in the lineage.
    #
    # THE NARRATOR: kristin, a US English female voice trained from scratch on
    # the LJ Speech dataset, which is public domain.
    $sPiperVoice = fetchVoice "kristin" "medium"

    # SR: john, a US English male voice built from LibriVox recordings, public
    # domain, fine-tuned from kristin. Same family, different sex, which is part
    # of why the two sit together well.
    $sReaderVoice = fetchVoice "john" "medium"
    if ($sReaderVoice -eq "") { $sReaderVoice = $sPiperVoice }
  }
  else { $sPiper = ""; $sReaderVoice = "" }

  # ESPEAK NG: the screen reader's stand-in. Already on the machine more often
  # than not, since other accessibility software carries it.
  $oFound = Get-Command espeak-ng.exe -ErrorAction SilentlyContinue
  if ($oFound) { $sEspeak = $oFound.Source }
  if ($sEspeak -eq "") {
    foreach ($sTry in @("$env:ProgramFiles\eSpeak NG\espeak-ng.exe",
                        "${env:ProgramFiles(x86)}\eSpeak NG\espeak-ng.exe")) {
      if ($sEspeak -eq "" -and (Test-Path -LiteralPath $sTry)) { $sEspeak = $sTry }
    }
  }
  if ($sEspeak -eq "" -and (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
    # Already here? Then nothing is fetched. winget knows about packages it
    # installed; an espeak on the PATH or in its usual folder counts too.
    foreach ($sTry in @("$env:ProgramFiles\eSpeak NG\espeak-ng.exe",
                        "${env:ProgramFiles(x86)}\eSpeak NG\espeak-ng.exe")) {
      if ($sEspeak -eq "" -and (Test-Path -LiteralPath $sTry)) { $sEspeak = $sTry }
    }
    $oOnPath = Get-Command espeak-ng.exe -ErrorAction SilentlyContinue
    if ($sEspeak -eq "" -and $oOnPath) { $sEspeak = $oOnPath.Source }
    if ($sEspeak -ne "") { note ("espeak-ng already installed: " + $sEspeak) }
    if ($sEspeak -eq "") {
    say "Fetching the screen reader voice. This happens once, and takes a minute or two."
    # A FETCH THAT CANNOT FINISH MUST NOT BECOME A HANG.
    #
    # eSpeak NG installs from an MSI, and msiexec can sit waiting for something
    # nobody can see -- an elevation prompt on another desktop, a repair, another
    # installer holding the lock. On Jamal's machine it reached "Starting package
    # install..." and stopped there, with no way to tell a slow install from a
    # stuck one.
    #
    # So it runs as a job with a time limit. If the limit passes, the job is
    # stopped, the log says so, and the build carries on with the Windows voices
    # rather than waiting for something that is not coming. --disable-interactivity
    # tells winget not to ask anything it would otherwise ask.
    # WINDOWS MAY BE ASKING FOR PERMISSION IN A WINDOW YOU CANNOT SEE.
    #
    # This is what actually happened: the install reached "Starting package
    # install..." and stopped, and the reason was a User Account Control prompt
    # that had opened behind everything and taken no focus. Nothing was stuck --
    # it was waiting for an answer nobody knew it had asked for.
    #
    # A script that shells out to an installer has to say so. This one says it
    # before the wait begins, and again as soon as the UAC process appears, and
    # names the keystroke that finds the window.
    say "Windows may ask for permission in a window behind this one. If nothing happens, press Alt+Tab and look for User Account Control."
    $iWaitSeconds = 300
    $oJob = Start-Job -ScriptBlock {
      & winget.exe install --id eSpeak-NG.eSpeak-NG --accept-package-agreements `
        --accept-source-agreements --disable-interactivity --silent 2>&1
    }
    $bToldAgain = $false
    $iWaited = 0
    while ($oJob.State -eq "Running" -and $iWaited -lt $iWaitSeconds) {
      Start-Sleep -Seconds 2
      $iWaited = $iWaited + 2
      # consent.exe IS the User Account Control prompt. If it is running, the
      # answer is one Alt+Tab away rather than minutes away.
      if (-not $bToldAgain -and (Get-Process -Name "consent" -ErrorAction SilentlyContinue)) {
        say "Windows is asking for permission now. Press Alt+Tab to reach the User Account Control window and answer Yes."
        note "consent.exe seen: a UAC prompt is open"
        $bToldAgain = $true
      }
    }
    if ($oJob.State -eq "Running") {
      Stop-Job $oJob
      say ("The screen reader voice did not install within " + [int]($iWaitSeconds / 60) + " minutes, so the Windows voices will be used.")
      note ("winget timed out after " + $iWaitSeconds + " seconds; continuing without espeak")
    }
    else {
      Receive-Job $oJob | ForEach-Object { note ("  | " + $_) }
      note ("winget finished")
    }
    Remove-Job $oJob -Force -ErrorAction SilentlyContinue
    foreach ($sTry in @("$env:ProgramFiles\eSpeak NG\espeak-ng.exe",
                        "${env:ProgramFiles(x86)}\eSpeak NG\espeak-ng.exe")) {
      if ($sEspeak -eq "" -and (Test-Path -LiteralPath $sTry)) { $sEspeak = $sTry }
    }
    }
  }
  note ("espeak-ng: " + $sEspeak)
}

$bWindowsVoices = ($sPiper -eq "" -or $sPiperVoice -eq "")
if ($bWindowsVoices -and -not $bLive) {
  if (-not $bSapi) { say "Falling back to the Windows voices; the log says which fetch fell short." }
  note ("using Windows voices: piper=" + $sPiper + " voice=" + $sPiperVoice + " espeak=" + $sEspeak)
}

# Windows voices are needed for the fallback and for the live narration.
Add-Type -AssemblyName System.Speech
$oSpeaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$lsVoices = @($oSpeaker.GetInstalledVoices() | Where-Object { $_.Enabled } | ForEach-Object { $_.VoiceInfo.Name })
note ("Windows voices: " + ($lsVoices -join ", "))
$sSapiNarrator = if ($lsVoices.Count -gt 0) { $lsVoices[0] } else { "" }
$sSapiReader = ""
foreach ($sWanted in @("eloquence", "eti-eloquence", "ibmtts")) {
  foreach ($sVoice in $lsVoices) { if ($sSapiReader -eq "" -and $sVoice.ToLower().Contains($sWanted)) { $sSapiReader = $sVoice } }
}
if ($sSapiReader -eq "" -and $lsVoices.Count -gt 1) { $sSapiReader = $lsVoices[1] }
if ($sSapiReader -eq "") { $sSapiReader = $sSapiNarrator }
note ("Windows narrator: " + $sSapiNarrator + ", Windows reader: " + $sSapiReader)

$oJaws = $null
if ($bLive) {
  try { $oJaws = New-Object -ComObject FreedomSci.JawsApi; note "JAWS COM server attached" }
  catch {
    note ("JAWS COM server not available: " + $_.Exception.Message)
    say "JAWS is not running, or its COM server is not available."
    exit 1
  }
}

# SPEED. A screen reader user listens faster than a first-time listener. Piper
# takes a length scale, where less is quicker; eSpeak takes words a minute.
# length_scale is duration: less is quicker. The narrator sits just inside
# natural; SR runs noticeably faster, the way a screen reader does for somebody
# who listens all day. The gap is what tells them apart, along with the speaker.
# TWO VOICES, TOLD APART THREE WAYS: who is speaking, how fast, and how flat.
#
# The narrator is female, high quality, and keeps her natural variation -- the
# register is a colleague explaining something she likes, at a clip an
# experienced listener is comfortable with.
#
# SR is male, high quality, and deliberately even: same clarity, none of the
# expression, the way a screen reader sounds when it is doing its job.
#
# Faster than natural, both of them, because an experienced screen reader user
# listens above the rate a narrator would choose and a tutorial that dawdles is
# one nobody finishes.
# THE NARRATOR, TUNED FOR LISTENERS OF EVERY AGE.
#
# Hearing changes with age, and blind listeners are no exception. A beta tester
# found the narrator hard to follow at 0.72. Two things are known to matter:
#
#   Rate. Older listeners' hearing recovers more slowly between sounds, so
#   speech that is fast for a young ear runs sounds together for an older one.
#   0.80 is one step back from 0.72 -- still brisker than natural (1.0), since
#   slow speech tries the patience of the many listeners who hear well.
#
#   Pitch. Age-related hearing loss takes the high frequencies first, and a
#   woman's voice sits about an octave above a man's -- roughly 224 Hz against
#   132. So the narrator is lowered two semitones, to about 200 Hz: easier on an
#   older ear, still clearly a woman's voice, and still well apart from the
#   screen reader's. Keeping the two voices apart in pitch is itself an aid:
#   a difference in pitch is how any listener tells two voices apart.
#
# Both are [global] settings, NarratorScale and NarratorPitch, in semitones;
# 0 leaves the pitch alone.
$dNarratorScale = 0.80
$dNarratorPitch = -2
$dReaderScale = 0.56
$dReaderNoise = 0.333
# Silence before the first word of a script, and after each passage. The lead-in
# exists because the screen reader is usually still announcing that a program
# opened when the audio starts.
$dLeadIn = 2.0
$dGap = 0.3
$iEspeakRate = 260
$iSapiNarratorRate = 4
$iSapiReaderRate = 6

# ---- reading a SPEAK script ----

function readScript([string] $sPath) {
  $lsSections = New-Object System.Collections.Generic.List[hashtable]
  $dNow = $null
  foreach ($sRaw in (Get-Content -LiteralPath $sPath -Encoding UTF8)) {
    $sLine = $sRaw.Trim()
    if ($sLine.Length -eq 0 -or $sLine.StartsWith(";") -or $sLine.StartsWith("#")) { continue }
    if ($sLine.StartsWith("[") -and $sLine.EndsWith("]")) {
      $dNow = @{ "_name" = $sLine.Substring(1, $sLine.Length - 2).Trim().ToLower() }
      $lsSections.Add($dNow)
      continue
    }
    if ($null -eq $dNow) { continue }
    $iAt = $sLine.IndexOf("=")
    if ($iAt -lt 1) { continue }
    $sField = $sLine.Substring(0, $iAt).Trim()
    $sValue = $sLine.Substring($iAt + 1).Trim()
    if ($sValue.Length -eq 0) { continue }
    if (-not $dNow.ContainsKey($sField)) { $dNow[$sField] = New-Object System.Collections.Generic.List[string] }
    $dNow[$sField].Add($sValue)
  }
  return $lsSections
}

# ---- speaking one tutorial ----

# ---- [global]: the settings a whole demo script runs under ----
#
# A DEMO SCRIPT is an .inix whose sections are speech passages. Its FIRST
# section is [global], and what it holds applies to every passage after it: the
# voices, how fast each speaks, how flat the screen reader is, the silence
# before the first word and between passages, and where the engines live when
# they are somewhere unusual.
#
# Script 00 sets the series defaults. A later script may carry its own [global]
# to override any of them for itself.
#
# Every key is optional, so a demo script with no [global] behaves as before.
function resolveVoice([string] $sName) {
  # "kristin medium", "john medium" or "en_US-john-medium" all resolve.
  $lsParts = $sName -split "[\s\-]+" | Where-Object { $_ -ne "" -and $_ -ne "en" -and $_ -ne "US" -and $_ -ne "en_US" }
  if ($lsParts.Count -ge 2) {
    $sPath = fetchVoice $lsParts[$lsParts.Count - 2] $lsParts[$lsParts.Count - 1]
    if ($sPath -ne "") { return $sPath }
  }
  note ("[global] named a voice that could not be fetched: " + $sName)
  return ""
}

function applyGlobal($dGlobal) {
  if ($null -eq $dGlobal) { return }
  foreach ($sKey in @("NarratorVoice", "ReaderVoice", "NarratorPitch", "NarratorScale", "ReaderScale",
                      "ReaderFlatness", "LeadIn", "Gap", "VoiceFolder", "PiperPath", "FfmpegPath")) {
    if (-not $dGlobal.ContainsKey($sKey)) { continue }
    $sValue = ([string] $dGlobal[$sKey][0]).Trim()
    if ($sValue -eq "") { continue }
    switch ($sKey) {
      "NarratorVoice"  { $sFound = resolveVoice $sValue; if ($sFound -ne "") { $script:sPiperVoice = $sFound } }
      "ReaderVoice"    { $sFound = resolveVoice $sValue; if ($sFound -ne "") { $script:sReaderVoice = $sFound } }
      "NarratorScale"  { $script:dNarratorScale = [double] $sValue }
      "NarratorPitch"  { $script:dNarratorPitch = [double] $sValue }
      "ReaderScale"    { $script:dReaderScale = [double] $sValue }
      "ReaderFlatness" { $script:dReaderNoise = [double] $sValue }
      "LeadIn"         { $script:dLeadIn = [double] $sValue }
      "Gap"            { $script:dGap = [double] $sValue }
      "VoiceFolder"    { if (Test-Path -LiteralPath $sValue) { $script:sTools = $sValue } }
      "PiperPath"      { if (Test-Path -LiteralPath $sValue) { $script:sPiper = $sValue } }
      "FfmpegPath"     { if (Test-Path -LiteralPath $sValue) { $script:sFfmpeg = $sValue } }
    }
    note ("[global] " + $sKey + " = " + $sValue)
  }
}

function buildOne([string] $sScript) {
  $sStem = [System.IO.Path]::GetFileNameWithoutExtension($sScript)
  $sOut = Join-Path $sHere ($sStem + ".mp3")
  $sWork = Join-Path $env:TEMP ("buildTutorial_" + [Guid]::NewGuid().ToString("N"))
  $script:iPiece = 0
  $script:lsPieces = New-Object System.Collections.Generic.List[string]
  if (-not $bLive) { New-Item -ItemType Directory -Path $sWork -Force | Out-Null }
  note ("building " + $sStem + ", work folder " + $sWork)

  function pieceFile() {
    $script:iPiece = $script:iPiece + 1
    return (Join-Path $sWork ("piece_{0:D4}.wav" -f $script:iPiece))
  }

  function speakNarrator([string] $sText) {
    if ($bLive) {
      $oSpeaker.SelectVoice($sSapiNarrator)
      $oSpeaker.Rate = $iSapiNarratorRate
      $oSpeaker.SetOutputToDefaultAudioDevice()
      $oSpeaker.Speak($sText)
      note ("live narrator: " + $sText)
      return
    }
    $sFile = pieceFile
    if (-not $bWindowsVoices) {
      # Piper reads its text from standard input and writes one wave file.
      # The narrator keeps piper's own variation, which is what makes a voice
      # sound like somebody rather than something, and a half-second between
      # sentences so a point lands before the next one starts.
      runVoice $sPiper @("-m", $sPiperVoice, "--length_scale", "$dNarratorScale",
                         "--sentence_silence", "0.5", "-f", $sFile) $sText "piper" | Out-Null
      # Lower the pitch without changing the length: play it slower by the pitch
      # ratio, then speed the tempo back up by the same ratio. The voice models
      # speak at 22050 Hz.
      if ($dNarratorPitch -ne 0 -and (Test-Path -LiteralPath $sFile)) {
        $dRatio = [Math]::Pow(2.0, $dNarratorPitch / 12.0)
        $sInv = [System.Globalization.CultureInfo]::InvariantCulture
        $sRate = [string]::Format($sInv, "{0:0}", 22050 * $dRatio)
        $sTempo = [string]::Format($sInv, "{0:0.0000}", 1.0 / $dRatio)
        $sLowered = $sFile + ".low.wav"
        runVoice $sFfmpeg @("-y", "-loglevel", "error", "-i", $sFile,
                            "-af", ("asetrate=" + $sRate + ",aresample=22050,atempo=" + $sTempo),
                            $sLowered) $null "ffmpeg-pitch" | Out-Null
        if (Test-Path -LiteralPath $sLowered) { Move-Item -LiteralPath $sLowered -Destination $sFile -Force }
      }
    }
    else {
      $oSpeaker.SelectVoice($sSapiNarrator)
      $oSpeaker.Rate = $iSapiNarratorRate
      $oSpeaker.SetOutputToWaveFile($sFile)
      $oSpeaker.Speak($sText)
      $oSpeaker.SetOutputToNull()
    }
    if (Test-Path -LiteralPath $sFile) { $script:lsPieces.Add($sFile) }
    else { note ("no audio made for: " + $sText) }
    note ("narrator: " + $sText)
  }

  function speakReader([string] $sText) {
    if ($bLive) {
      $oJaws.SayString($sText, $true) | Out-Null
      Start-Sleep -Milliseconds ([Math]::Max(400, $sText.Length * 38))
      note ("live JAWS: " + $sText)
      return
    }
    $sFile = pieceFile
    if (-not $bWindowsVoices) {
      # SR SPEAKS THROUGH THE SAME NEURAL ENGINE, faster and in another voice.
      #
      # eSpeak was the wrong choice and the research says why: NVDA's default on
      # Windows 10 and 11 is Windows OneCore -- "responsive, natural-sounding" --
      # and eSpeak is the default only on Windows 8.1 and earlier. Meanwhile the
      # Sonata add-on gives NVDA piper voices, so a piper voice IS a contemporary
      # screen reader voice rather than a stand-in for one.
      #
      # It stays distinguishable by speaker and speed, not by sounding broken.
      if ($sReaderVoice -ne "") {
        # NEUTRAL BY SETTING, NOT BY QUALITY.
        #
        # noise_scale is how much the voice varies in tone, noise_w how much it
        # varies in timing. Piper's defaults -- 0.667 and 0.8 -- are what make a
        # narrator sound alive. Lowering both flattens the delivery into the
        # even, unhurried sameness of a screen reader, using the same
        # high-quality model, so SR is clear AND neutral rather than clear OR
        # neutral.
        #
        # sentence_silence is cut to a fifth of a second: a screen reader does
        # not pause to let a sentence land.
        runVoice $sPiper @("-m", $sReaderVoice, "--length_scale", "$dReaderScale",
                           "--noise_scale", "$dReaderNoise", "--noise_w", "$dReaderNoise",
                           "--sentence_silence", "0.2", "-f", $sFile) $sText "piper-sr" | Out-Null
      }
      else {
        runVoice $sEspeak @("-v", "en-us", "-s", "$iEspeakRate", "-w", $sFile, $sText) $null "espeak" | Out-Null
      }
    }
    else {
      $oSpeaker.SelectVoice($sSapiReader)
      $oSpeaker.Rate = $iSapiReaderRate
      $oSpeaker.SetOutputToWaveFile($sFile)
      $oSpeaker.Speak($sText)
      $oSpeaker.SetOutputToNull()
    }
    if (Test-Path -LiteralPath $sFile) { $script:lsPieces.Add($sFile) }
    else { note ("no audio made for: " + $sText) }
    note ("reader: " + $sText)
  }

  function gap([double] $dSeconds) {
    if ($bLive) { Start-Sleep -Milliseconds ([int]($dSeconds * 1000)); return }
    $sFile = pieceFile
    runVoice $sFfmpeg @("-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
                        "-t", "$dSeconds", $sFile) $null "ffmpeg" | Out-Null
    if (Test-Path -LiteralPath $sFile) { $script:lsPieces.Add($sFile) }
  }

  $lsSections = readScript $sScript
  $dAbout = $lsSections | Where-Object { $_["_name"] -eq "about" } | Select-Object -First 1
  # [global] first, so everything spoken below runs under it.
  applyGlobal ($lsSections | Where-Object { $_["_name"] -eq "global" } | Select-Object -First 1)
  $lsSteps = @($lsSections | Where-Object { $_["_name"] -eq "step" })
  if ($lsSteps.Count -eq 0) { say ($sStem + " holds 0 steps."); return $false }
  note ($sStem + ": steps " + $lsSteps.Count)

  # A BEAT BEFORE ANYTHING IS SAID.
  #
  # The screen reader is usually still announcing that a program has opened when
  # the audio starts, so the first sentence lands underneath it and is lost.
  # Two seconds of nothing costs nothing and saves the opening line.
  gap $dLeadIn
  # The opening: what this is, in one sentence, with no names and no apology.
  # The voices are named once because they are somebody's work and public
  # domain -- and never again.
  # NO FIXED OPENING. It used to say which voices these are at the top of every
  # walkthrough -- fourteen times the same sentence. The introductions belong to
  # the first script only, where they are written as its first step.
  if ($dAbout -and $dAbout.ContainsKey("Title")) { speakNarrator $dAbout["Title"][0]; gap 0.35 }
  # SETUP IS WRITTEN, NOT SPOKEN. It used to be read aloud after the title, which
  # put three narrator sentences -- title, setup, first step -- before the screen
  # reader said anything. The listener hears the reader within one sentence now,
  # and the starting state is in the transcript for anybody who wants it.

  foreach ($dStep in $lsSteps) {
    # Pause= is the one piece of timing a script can set for itself: seconds of
    # silence before the step is spoken. SSML calls this <break time="2s"/>; our
    # key is the same idea with the angle brackets left off. Everything else --
    # which voice, how fast, how flat -- stays in this script, because it is the
    # same for every passage and belongs in one place rather than in nine files.
    if ($dStep.ContainsKey("Pause")) {
      $dWait = 0.0
      if ([double]::TryParse($dStep["Pause"][0], [ref] $dWait)) { gap $dWait }
    }
    if ($dStep.ContainsKey("Say")) { speakNarrator $dStep["Say"][0]; gap 0.3 }
    if ($dStep.ContainsKey("Key")) { speakNarrator ("Press " + $dStep["Key"][0]); gap 0.35 }
    if ($dStep.ContainsKey("Hear")) {
      foreach ($sHeard in $dStep["Hear"]) { speakReader $sHeard }
      gap 0.4
    }
  }
  speakNarrator "End of the walk."
  if ($dAbout -and $dAbout.ContainsKey("Homework")) {
    gap 0.35
    speakNarrator ("Something to try. " + $dAbout["Homework"][0])
  }

  if ($bLive) { say ($sStem + " was spoken live. No file was written."); return $true }

  note ("pieces: " + $script:lsPieces.Count)
  $sList = Join-Path $sWork "pieces.txt"
  $lsLines = $script:lsPieces | ForEach-Object { "file '" + $_.Replace("'", "'\''") + "'" }
  Set-Content -LiteralPath $sList -Value $lsLines -Encoding ASCII
  runVoice $sFfmpeg @("-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", $sList,
                      "-ar", "22050", "-ac", "1", "-codec:a", "libmp3lame", "-q:a", "4", $sOut) $null "ffmpeg" | Out-Null
  $iExit = $LASTEXITCODE
  note ("ffmpeg exit code: " + $iExit)
  try { Remove-Item -LiteralPath $sWork -Recurse -Force } catch { note ("could not clear " + $sWork) }
  if ($iExit -ne 0 -or -not (Test-Path -LiteralPath $sOut)) { say ($sStem + " could not be joined."); return $false }
  say ("Wrote " + [System.IO.Path]::GetFileName($sOut))
  return $true
}

# ---- step 3 of 4: speak them ----

$iDone = 0
foreach ($sScript in $lsScripts) {
  if (buildOne $sScript) { $iDone = $iDone + 1 }
}
$oSpeaker.Dispose()

# ---- step 4 of 5: one file with a chapter for each tutorial ----
#
# The separate .mp3 files are what a feed wants. One file with a chapter per
# tutorial is what a person wants who is going to sit and listen through them,
# and what the Homer Player in FileDir opens as a set of tracks. Matroska holds
# both the audio and the chapter names, so the tracks are called what the
# tutorials are called rather than "track 3".
#
# Tutorials.m3u is written beside it: a plain playlist of the same files, in the
# same order, for any player that reads a list rather than a container.

function buildOneFile() {
  # ONE TRACK PER TUTORIAL.
  #
  # Chapters gave the Player "1 track", which is literally what a chaptered file
  # is: one continuous recording with marks in it. A track list needs tracks, so
  # Tutorials.mkv carries nine audio streams, each titled with its tutorial's
  # name, and the Player lists nine.
  #
  # The trade-off, stated because it is real: a container's audio streams are
  # ALTERNATIVES by convention -- the way a film holds English and French -- so a
  # player that follows the convention plays one and waits rather than running
  # on to the next. Moving between tracks is a keystroke; automatic advance is
  # what Tutorials.m3u is for, since a playlist of nine files advances by itself
  # in any player that reads one.
  #
  # Both are written every run. Whichever the Player prefers is there.
  $lsParts = @()
  $lsTitles = @()
  foreach ($sScript in $lsScripts) {
    $sStem = [System.IO.Path]::GetFileNameWithoutExtension($sScript)
    $sMp3 = Join-Path $sHere ($sStem + ".mp3")
    if (-not (Test-Path -LiteralPath $sMp3)) { continue }
    $lsParts += $sMp3
    $sTitle = $sStem
    foreach ($sLine in (Get-Content -LiteralPath $sScript)) {
      if ($sLine -match "^\s*Title\s*=\s*(.+?)\s*$") { $sTitle = $matches[1]; break }
    }
    $lsTitles += $sTitle
  }
  if ($lsParts.Count -eq 0) { say "No audio to join."; return $false }

  $sM3u = Join-Path $sHere "Tutorials.m3u"
  $lsM3u = @("#EXTM3U")
  for ($i = 0; $i -lt $lsParts.Count; $i++) {
    $lsM3u += ("#EXTINF:-1," + $lsTitles[$i])
    $lsM3u += [System.IO.Path]::GetFileName($lsParts[$i])
  }
  [System.IO.File]::WriteAllLines($sM3u, $lsM3u, (New-Object System.Text.UTF8Encoding($false)))
  note ("wrote " + $sM3u)

  # ONE RECORDING, MARKED OFF INTO TUTORIALS.
  #
  # FileDir's Control+Shift+L is a play list BUILDER: it writes an .m3u naming
  # the items you have tagged. One .mkv is one item, so it reports one track,
  # and no arrangement of audio streams inside the file changes that -- a
  # container's streams are alternatives, not a sequence, which is also why only
  # the first played when it held nine.
  #
  # So the file distributed in the repository is one continuous recording with a
  # CHAPTER at the start of each tutorial: it plays through by itself, and a
  # player that reads chapters lists them by name. The .m3u beside it names the
  # nine .mp3 files for anybody who keeps them.
  $sList = Join-Path $env:TEMP ("tutorials_" + [guid]::NewGuid().ToString("N") + ".txt")
  $sMeta = Join-Path $env:TEMP ("chapters_" + [guid]::NewGuid().ToString("N") + ".txt")
  $lsList = @()
  $lsMeta = @(";FFMETADATA1", "title=DbDo Walkthroughs", "artist=Jamal Mazrui",
              "album=DbDo Walkthroughs", "genre=Speech", "comment=Simulated walkthroughs of DbDo using the JobTrail sample database. Speech synthesised with piper, voices kristin and john, both trained on public domain recordings.")
  $dStart = 0.0
  for ($i = 0; $i -lt $lsParts.Count; $i++) {
    $sPart = $lsParts[$i]
    $lsList += ("file '" + $sPart.Replace("'", "'\''") + "'")
    $sPrevious = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $sProbe = (& $sFfmpeg -i $sPart 2>&1 | Out-String) | Select-String -Pattern "Duration: (\d+):(\d+):([\d.]+)"
    $ErrorActionPreference = $sPrevious
    $dSeconds = 0.0
    if ($sProbe) {
      $oM = $sProbe.Matches[0]
      $dSeconds = ([double]$oM.Groups[1].Value) * 3600 + ([double]$oM.Groups[2].Value) * 60 + [double]$oM.Groups[3].Value
    }
    $dEnd = $dStart + $dSeconds
    $sTitle = $lsTitles[$i]
    foreach ($sCh in @("\", "=", ";", "#")) { $sTitle = $sTitle.Replace($sCh, "\" + $sCh) }
    $lsMeta += @("[CHAPTER]", "TIMEBASE=1/1000", ("START=" + [int]($dStart * 1000)),
                 ("END=" + [int]($dEnd * 1000)), ("title=" + $sTitle))
    $dStart = $dEnd
  }
  [System.IO.File]::WriteAllLines($sList, $lsList, (New-Object System.Text.ASCIIEncoding))
  # No byte order mark: ffmetadata must begin with ";FFMETADATA1".
  [System.IO.File]::WriteAllLines($sMeta, $lsMeta, (New-Object System.Text.UTF8Encoding($false)))
  $sOut = Join-Path $sHere "Tutorials.mkv"
  $iExit = runVoice $sFfmpeg @("-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                               "-i", $sList, "-f", "ffmetadata", "-i", $sMeta, "-map_metadata", "1",
                               "-map", "0:a", "-c:a", "libmp3lame", "-q:a", "4",
                               "-ar", "22050", "-ac", "1", $sOut) $null "ffmpeg"
  note ("ffmpeg exit code (one file): " + $iExit)
  try { Remove-Item -LiteralPath $sList, $sMeta -Force } catch { }
  if ($iExit -ne 0 -or -not (Test-Path -LiteralPath $sOut)) { say "Tutorials.mkv could not be written."; return $false }
  say ("Wrote Tutorials.mkv: one recording, " + $lsParts.Count + " chapters, with title and credits. Tutorials.m3u names the same " + $lsParts.Count + " files.")
  return $true
}

if (-not $bLive -and $iDone -gt 0) { buildOneFile | Out-Null }

# ---- step 5 of 5: the feed, now that the audio exists ----

if (-not $bLive -and $iDone -gt 0) {
  say "Writing the feed ..."
  runMake | Out-Null
}

say ($iDone.ToString() + " of " + $lsScripts.Count + " tutorials built.")
if ($iDone -lt $lsScripts.Count) { exit 1 }
exit 0
