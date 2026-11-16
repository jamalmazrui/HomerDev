# auditionVoices.ps1 -- hear candidate screen reader voices for the tutorials, side by side (HomerDev 1.237.0).
#
#   auditionVoices          render every candidate, then join them into one recording
#
# WHY (15 November 2026). Jamal found the tutorials' screen reader voice "too grumpy"; the narrator is fine. The
# reader is piper's john, flattened on purpose (noise 0.333) and sped up (length scale 0.70): buildTutorials.ps1 has
# put the reader on piper since 25 September, because piper speaks a line in a second where Kokoro takes twenty.
# ChatGPT's review of voices for Homer (Homer_Voices_ChatGPT.md) proposed an audition by ear before any change, and
# Claude agreed: a voice is chosen by listening, not by a model card.
#
# WHAT IT MAKES. The same short exchange -- narrator lines in today's narrator, Kokoro's af_sarah, and reader lines in
# each candidate -- one mp3 per candidate and all of them joined, in the kit's results\voiceAudition folder. Before
# each, the narrator says the candidate's number and name, so "reader 6" is all an answer needs. The reader lines
# are rendered with no context pitch change, so each voice is heard as it is.
#
# THE CANDIDATES, every one free to publish beside MIT code:
#   1, 2      piper john, as today, then with its natural variation      (public domain, Bryce Beattie)
#   3         piper norman, another of Bryce Beattie's LibriVox voices     (public domain)
#   4, 5      Kokoro am_michael and am_adam, the English pack the tutorials already use (Apache 2.0)
#   6 to 10   Kokoro v1.0: am_puck, am_echo, am_liam, am_eric, am_fenrir  (Apache 2.0)
#   11 to 16  Phonon 31m: Easton, Micah, Trevor, Preston, Miles, Russell  (Apache 2.0; the 40m models are
#             non-commercial and are never fetched)
# Anything it cannot fetch or run is skipped, said on screen, and written in the log with the reason.
#
# WHERE THE ENGINES LIVE: the same voices folder buildTutorials uses -- HOMER_VOICES, else the kit's exec folder.
# Kokoro v1.0 (about 330 MB) and Phonon's ptts.exe are fetched once, beside the engines already there. The log is
# logs\HomerDev-auditionVoices-yyyyMMdd-HHmmss.log, with every command, exit code and file size.

$ErrorActionPreference = "Stop"
$sTool = Split-Path -Parent $MyInvocation.MyCommand.Path
$sRoot = Split-Path -Parent $sTool
$sLogDir = Join-Path $sRoot "logs"
if (-not (Test-Path -LiteralPath $sLogDir)) { New-Item -ItemType Directory -Path $sLogDir | Out-Null }
$sLog = Join-Path $sLogDir ("HomerDev-auditionVoices-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
$sOut = Join-Path $sRoot "results\voiceAudition"
$sWork = Join-Path $sOut "pieces"
$sInv = [System.Globalization.CultureInfo]::InvariantCulture

function note([string] $sText) {
  Add-Content -LiteralPath $sLog -Value ((Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "  " + $sText)
  return $true
}

function say([string] $sText) {
  Write-Host $sText
  note $sText | Out-Null
  return $true
}

trap {
  $sWhere = ""
  try { $sWhere = " at line " + $_.InvocationInfo.ScriptLineNumber } catch { }
  try { note ("UNEXPECTED: " + $_.Exception.Message + $sWhere) | Out-Null; note ($_.ScriptStackTrace) | Out-Null } catch { }
  Write-Host ("auditionVoices stopped: " + $_.Exception.Message + ". The log is " + $sLog)
  exit 1
}

note ("auditionVoices " + $MyInvocation.MyCommand.Path) | Out-Null
note ("powershell " + $PSVersionTable.PSVersion + ", " + [Environment]::OSVersion.VersionString + ", cwd " + (Get-Location).Path) | Out-Null
note ("arguments: " + ($args -join " ")) | Out-Null

# ---- the voices folder, as buildTutorials finds it ----

$sTools = ""
if ($env:HOMER_VOICES -and (Test-Path -LiteralPath $env:HOMER_VOICES)) { $sTools = $env:HOMER_VOICES }
if ($sTools -eq "") { $sTools = Join-Path $sRoot "exec" }
note ("voices folder: " + $sTools) | Out-Null

function runTool([string] $sExe, [string[]] $lsArgs, [object] $oInput, [string] $sLabel) {
  if ([System.IO.Path]::GetFileNameWithoutExtension($sExe) -ieq "ffmpeg") { $lsArgs = @("-nostdin") + $lsArgs }
  note ("run " + $sLabel + ": " + $sExe + " " + ($lsArgs -join " ")) | Out-Null
  $sText = ""
  $sPrevious = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    if ($null -eq $oInput) { $sText = (& $sExe @lsArgs 2>&1 | Out-String) }
    else { $sText = ([string] $oInput | & $sExe @lsArgs 2>&1 | Out-String) }
  }
  catch { note ("  " + $sLabel + " threw: " + $_.Exception.Message) | Out-Null }
  finally { $ErrorActionPreference = $sPrevious }
  $iExit = $LASTEXITCODE
  if ($null -eq $iExit) { $iExit = 0 }
  foreach ($sLine in ($sText -split "`r?`n")) { if ($sLine.Trim() -ne "" -and $sLine -match "error|fail|not found|cannot|unable|Elapsed|RTF") { note ("  | " + $sLine.Trim()) | Out-Null } }
  note ("  " + $sLabel + " exit code " + $iExit) | Out-Null
  return $iExit
}

function fetchTo([string] $sUrl, [string] $sPath) {
  note ("fetching " + $sUrl + " to " + $sPath) | Out-Null
  try {
    $oOld = $ProgressPreference
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $sUrl -OutFile $sPath -UseBasicParsing -Headers @{ "User-Agent" = "HomerDev-auditionVoices" }
    $ProgressPreference = $oOld
    note ("fetched " + (Get-Item -LiteralPath $sPath).Length + " bytes") | Out-Null
    return $true
  }
  catch { note ("fetch failed: " + $_.Exception.Message) | Out-Null; return $false }
}

function findFile([string] $sFolder, [string] $sName) {
  if (-not (Test-Path -LiteralPath $sFolder)) { return "" }
  $oFound = Get-ChildItem -LiteralPath $sFolder -Filter $sName -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($oFound) { return $oFound.FullName }
  return ""
}

# ---- the engines ----

$sFfmpeg = findFile $sTools "ffmpeg.exe"
if ($sFfmpeg -eq "") { $oFound = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue; if ($oFound) { $sFfmpeg = $oFound.Source } }
if ($sFfmpeg -eq "") { say "ffmpeg was not found, and it joins the pieces. Run the kit's installFfmpeg.cmd, then this again." | Out-Null; exit 1 }
$sPiper = findFile $sTools "piper.exe"
$sSherpa = findFile $sTools "sherpa-onnx-offline-tts.exe"
note ("ffmpeg " + $sFfmpeg + "; piper " + $sPiper + "; sherpa-onnx " + $sSherpa) | Out-Null
if ($sSherpa -eq "") { say "The Kokoro engine is not in the voices folder. Build a Homer app's tutorials once, so buildTutorials fetches it, then run this again." | Out-Null; exit 1 }

function piperVoice([string] $sSpeaker) {
  $sName = "en_US-" + $sSpeaker + "-medium.onnx"
  $sFound = findFile $sTools $sName
  if ($sFound -ne "") { return $sFound }
  $sBase = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/" + $sSpeaker + "/medium/"
  $sDir = Join-Path $sTools "piper"
  New-Item -ItemType Directory -Path $sDir -Force | Out-Null
  $sModel = Join-Path $sDir $sName
  if ((fetchTo ($sBase + $sName) $sModel) -and (fetchTo ($sBase + $sName + ".json") ($sModel + ".json"))) { return $sModel }
  return ""
}

$sKokoroOld = Join-Path $sTools "kokoro-int8-en-v0_19"
$sKokoroNew = Join-Path $sTools "kokoro-multi-lang-v1_0"
if (-not (Test-Path -LiteralPath (Join-Path $sKokoroNew "voices.bin"))) {
  say "Fetching Kokoro v1.0, about 330 MB, for five more male voices. This happens once." | Out-Null
  $sTar = Join-Path $sTools "kokoro-multi-lang-v1_0.tar.bz2"
  if (fetchTo "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2" $sTar) {
    runTool "tar.exe" @("-xf", $sTar, "-C", $sTools) $null "tar-kokoro-v1" | Out-Null
    try { Remove-Item -LiteralPath $sTar -Force } catch { }
  }
}

$sPtts = findFile $sTools "ptts.exe"
if ($sPtts -eq "") {
  say "Fetching Phonon's ptts engine. This happens once; its 31m model downloads on first use." | Out-Null
  try {
    $lsReleases = @(Invoke-RestMethod -Uri "https://api.github.com/repos/gradium-ai/xn-ptts/releases" -Headers @{ "User-Agent" = "HomerDev-auditionVoices" } -UseBasicParsing)
    $oAsset = $null
    foreach ($oRelease in $lsReleases) {
      $oAsset = $oRelease.assets | Where-Object { $_.name -match "x86_64-pc-windows-msvc\.zip$" } | Select-Object -First 1
      if ($oAsset) { note ("ptts release " + $oRelease.tag_name + ", asset " + $oAsset.name) | Out-Null; break }
    }
    if ($oAsset) {
      $sZip = Join-Path $sTools $oAsset.name
      if (fetchTo $oAsset.browser_download_url $sZip) {
        Expand-Archive -LiteralPath $sZip -DestinationPath (Join-Path $sTools "ptts") -Force
        try { Remove-Item -LiteralPath $sZip -Force } catch { }
      }
    }
    else { note "no Windows x64 ptts archive among the releases" | Out-Null }
  }
  catch { note ("the ptts releases could not be read: " + $_.Exception.Message) | Out-Null }
  $sPtts = findFile $sTools "ptts.exe"
}
note ("ptts: " + $sPtts) | Out-Null

# ---- rendering ----

if (Test-Path -LiteralPath $sWork) { Remove-Item -LiteralPath $sWork -Recurse -Force }
New-Item -ItemType Directory -Path $sWork -Force | Out-Null
$script:iPiece = 0
function pieceFile() { $script:iPiece++; return (Join-Path $sWork ("p" + $script:iPiece.ToString("0000") + ".wav")) }

function evenOut([string] $sFile, [double] $dTempo) {
  # One loudness for every piece, as buildTutorials does, and one sample rate, so a louder voice does not win by
  # being louder. A tempo other than 1 speeds an engine with no rate control of its own to the reader's pace.
  if (-not (Test-Path -LiteralPath $sFile)) { return $false }
  $sFilter = "loudnorm=I=-16:TP=-1.5:LRA=11"
  if ($dTempo -ne 1.0) { $sFilter = "atempo=" + [string]::Format($sInv, "{0:0.00}", $dTempo) + "," + $sFilter }
  $sEven = $sFile + ".even.wav"
  runTool $sFfmpeg @("-y", "-loglevel", "error", "-i", $sFile, "-af", $sFilter, "-ar", "24000", "-ac", "1", $sEven) $null "ffmpeg-even" | Out-Null
  if (Test-Path -LiteralPath $sEven) { Move-Item -LiteralPath $sEven -Destination $sFile -Force }
  return (Test-Path -LiteralPath $sFile)
}

function kokoroArgs([string] $sDir) {
  $lsArgs = @(("--kokoro-model=" + (findFile $sDir "model*.onnx")), ("--kokoro-voices=" + (Join-Path $sDir "voices.bin")),
              ("--kokoro-tokens=" + (Join-Path $sDir "tokens.txt")), ("--kokoro-data-dir=" + (Join-Path $sDir "espeak-ng-data")))
  # Kokoro v1.0 carries lexicons; the English pack does not.
  $lsLexicons = @(@("lexicon-us-en.txt", "lexicon-zh.txt") | ForEach-Object { Join-Path $sDir $_ } | Where-Object { Test-Path -LiteralPath $_ })
  if ($lsLexicons.Count -gt 0) { $lsArgs += ("--kokoro-lexicon=" + ($lsLexicons -join ",")) }
  if (Test-Path -LiteralPath (Join-Path $sDir "dict")) { $lsArgs += ("--kokoro-dict-dir=" + (Join-Path $sDir "dict")) }
  return $lsArgs
}

function speak([hashtable] $dVoice, [string] $sText) {
  $sFile = pieceFile
  $sRaw = $sFile + ".raw.wav"
  $dTempo = 1.0
  switch ($dVoice.engine) {
    "piper" {
      runTool $sPiper @("-m", $dVoice.model, "--length_scale", $dVoice.scale, "--noise_scale", $dVoice.noise,
                        "--noise_w", $dVoice.noisew, "--sentence_silence", "0.2", "-f", $sRaw) $sText "piper" | Out-Null
    }
    "kokoro" {
      runTool $sSherpa ((kokoroArgs $dVoice.dir) + @(("--kokoro-length-scale=" + $dVoice.scale), "--num-threads=2",
                        ("--sid=" + $dVoice.sid), ("--output-filename=" + $sRaw), $sText)) $null "kokoro" | Out-Null
    }
    "phonon" {
      runTool $sPtts @("--lang", "en", "--voice", $dVoice.voice, $sText, "-o", $sRaw) $null "ptts" | Out-Null
      $dTempo = 1.3   # ptts has no plain rate flag; this brings it near the reader's 0.70 length scale
    }
  }
  if (-not (Test-Path -LiteralPath $sRaw)) { note ("no audio for: " + $sText) | Out-Null; return "" }
  Move-Item -LiteralPath $sRaw -Destination $sFile -Force
  if (-not (evenOut $sFile $dTempo)) { return "" }
  return $sFile
}

function silence([double] $dSeconds) {
  $sFile = pieceFile
  runTool $sFfmpeg @("-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t",
                     [string]::Format($sInv, "{0:0.00}", $dSeconds), $sFile) $null "ffmpeg-silence" | Out-Null
  return $sFile
}

function joinPieces([string[]] $lsFiles, [string] $sMp3) {
  $sList = $sMp3 + ".txt"
  $lsLines = @($lsFiles | Where-Object { $_ -ne "" } | ForEach-Object { "file '" + ($_ -replace "'", "'\''") + "'" })
  [System.IO.File]::WriteAllLines($sList, $lsLines)
  $iExit = runTool $sFfmpeg @("-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", $sList, "-c:a", "libmp3lame", "-q:a", "3", $sMp3) $null "ffmpeg-join"
  Remove-Item -LiteralPath $sList -Force -ErrorAction SilentlyContinue
  return ($iExit -eq 0 -and (Test-Path -LiteralPath $sMp3))
}

# Today's narrator: Kokoro af_sarah (speaker 3 of the English pack) at length scale 0.80, as buildTutorials speaks her.
$dNarrator = @{ engine = "kokoro"; dir = $sKokoroOld; sid = 3; scale = "0.80" }

$lsCandidates = @(
  @{ name = "piper john, as the tutorials have it now"; engine = "piper"; speaker = "john"; scale = "0.70"; noise = "0.333"; noisew = "0.333" },
  @{ name = "piper john, with its natural variation"; engine = "piper"; speaker = "john"; scale = "0.70"; noise = "0.667"; noisew = "0.8" },
  @{ name = "piper norman"; engine = "piper"; speaker = "norman"; scale = "0.70"; noise = "0.5"; noisew = "0.6" },
  @{ name = "Kokoro Michael"; engine = "kokoro"; dir = $sKokoroOld; sid = 6; scale = "0.70" },
  @{ name = "Kokoro Adam"; engine = "kokoro"; dir = $sKokoroOld; sid = 5; scale = "0.70" },
  @{ name = "Kokoro Puck"; engine = "kokoro"; dir = $sKokoroNew; sid = 18; scale = "0.70" },
  @{ name = "Kokoro Echo"; engine = "kokoro"; dir = $sKokoroNew; sid = 12; scale = "0.70" },
  @{ name = "Kokoro Liam"; engine = "kokoro"; dir = $sKokoroNew; sid = 15; scale = "0.70" },
  @{ name = "Kokoro Eric"; engine = "kokoro"; dir = $sKokoroNew; sid = 13; scale = "0.70" },
  @{ name = "Kokoro Fenrir"; engine = "kokoro"; dir = $sKokoroNew; sid = 14; scale = "0.70" },
  @{ name = "Phonon Easton"; engine = "phonon"; voice = "Easton" },
  @{ name = "Phonon Micah"; engine = "phonon"; voice = "Micah" },
  @{ name = "Phonon Trevor"; engine = "phonon"; voice = "Trevor" },
  @{ name = "Phonon Preston"; engine = "phonon"; voice = "Preston" },
  @{ name = "Phonon Miles"; engine = "phonon"; voice = "Miles" },
  @{ name = "Phonon Russell"; engine = "phonon"; voice = "Russell" }
)

# The exchange: narrator and reader in turn, with the short announcements a reader voice has most trouble with.
$lsExchange = @(
  @("n", "Press Control plus O to open a database."),
  @("r", "Open Database dialog. File name, edit."),
  @("n", "Choose the sample database, then press Enter."),
  @("r", "DbDo ready. Stations, list. Name, column 1. Row 1 of 52550."),
  @("r", "Checked. Not checked. Read only. No records found."),
  @("n", "Press Shift plus Z to hear the status."),
  @("r", "status: stations record 1 of 52550; order: name, stream url, source id"),
  @("n", "And Alt plus Shift plus Z starts a timer in FileDir."),
  @("r", "Timer Toggle, Alt+Shift+Z. Start a timer, pause it or resume it.")
)

if (Test-Path -LiteralPath $sOut) { Get-ChildItem -LiteralPath $sOut -Filter "*.mp3" | Remove-Item -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $sOut -Force | Out-Null
$lsAll = New-Object System.Collections.Generic.List[string]
$lsHeard = New-Object System.Collections.Generic.List[string]
$iNumber = 0
$dNarratorLines = @{}
foreach ($dCandidate in $lsCandidates) {
  $iNumber++
  $sTitle = "Reader " + $iNumber + ", " + $dCandidate.name
  if ($dCandidate.engine -eq "piper") {
    if ($sPiper -eq "") { say ($sTitle + ": skipped, piper is not in the voices folder.") | Out-Null; continue }
    $dCandidate.model = piperVoice $dCandidate.speaker
    if ($dCandidate.model -eq "") { say ($sTitle + ": skipped, its voice could not be fetched.") | Out-Null; continue }
  }
  if ($dCandidate.engine -eq "kokoro" -and -not (Test-Path -LiteralPath (Join-Path $dCandidate.dir "voices.bin"))) { say ($sTitle + ": skipped, its Kokoro voices are not here.") | Out-Null; continue }
  if ($dCandidate.engine -eq "phonon" -and $sPtts -eq "") { say ($sTitle + ": skipped, ptts could not be fetched.") | Out-Null; continue }
  say ($sTitle + " ...") | Out-Null
  $lsPieces = New-Object System.Collections.Generic.List[string]
  $lsPieces.Add((speak $dNarrator ($sTitle + ".")))
  $lsPieces.Add((silence 0.6))
  $bFailed = $false
  foreach ($aLine in $lsExchange) {
    # The narrator's lines are the same for every reader, so each is spoken once and reused.
    if ($aLine[0] -eq "n") {
      if (-not $dNarratorLines.ContainsKey($aLine[1])) { $dNarratorLines[$aLine[1]] = speak $dNarrator $aLine[1] }
      $sPiece = $dNarratorLines[$aLine[1]]
    }
    else { $sPiece = speak $dCandidate $aLine[1] }
    if ($sPiece -eq "" -and $aLine[0] -eq "r") { $bFailed = $true }
    $lsPieces.Add($sPiece)
    $lsPieces.Add((silence 0.3))
  }
  if ($bFailed) { say ("  " + $sTitle + " could not speak every line; the log says why, and it is left out.") | Out-Null; continue }
  $lsPieces.Add((silence 1.2))
  $sMp3 = Join-Path $sOut (("{0:00}" -f $iNumber) + " " + ($dCandidate.name -replace "[,]", "") + ".mp3")
  if (joinPieces $lsPieces.ToArray() $sMp3) {
    $lsHeard.Add($sTitle)
    foreach ($sPiece in $lsPieces) { if ($sPiece -ne "") { $lsAll.Add($sPiece) } }
    note ("made " + $sMp3 + ", " + (Get-Item -LiteralPath $sMp3).Length + " bytes") | Out-Null
  }
  else { say ("  " + $sTitle + ": the pieces could not be joined; the log says why.") | Out-Null }
}

if ($lsHeard.Count -eq 0) { say "No candidate could be rendered. The log says why." | Out-Null; exit 1 }
$sAllMp3 = Join-Path $sOut "00 All readers.mp3"
joinPieces $lsAll.ToArray() $sAllMp3 | Out-Null
Remove-Item -LiteralPath $sWork -Recurse -Force -ErrorAction SilentlyContinue
say ("" + $lsHeard.Count + " of " + $lsCandidates.Count + " readers rendered, in " + $sOut + ".") | Out-Null
say "00 All readers.mp3 plays them in order; each also has a file of its own. Tell Claude the number you like best." | Out-Null
say ("The log is " + $sLog) | Out-Null
exit 0
