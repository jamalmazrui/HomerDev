# newest.ps1 -- find every copy of a shared tool on this machine and print the
# newest, at or above a minimum version when one is given. Part of the HomerDev
# kit; the PowerShell twin of exec\Python\media.py's newestInstalled, for the cmd
# builds that do not require Python. Run it through newest.cmd.
#
#     newest pandoc                  the newest Pandoc
#     newest pandoc -Minimum 3.1     the newest Pandoc at 3.1 or later
#     newest pandoc -Log build.log   the same, with the search appended to a log
#
# WHY (1.56.0). Every build took the first Pandoc on the PATH. On the author's
# machine that was C:\bin\pandoc.exe, version 2.19.2, ahead of a current copy in
# Program Files. Media.cs had met that folder before, with mpv. So every place
# installers put a tool is searched -- official folders first, the PATH last --
# each copy is RUN for its version, and the newest is chosen.
#
# OUTPUT. Standard output gets exactly one line, the chosen path, so a cmd
# script can read it with for /f; nothing at all when no copy qualifies. The
# search -- every copy, its version, the choice -- goes to the -Log file when
# one is given, and to standard error otherwise. Exit code 0 when a copy was
# chosen, 1 when none qualifies.

param([Parameter(Mandatory = $true, Position = 0)] [string] $Name, [string] $Minimum = "", [string] $Log = "")

$dOfficial = @{ "exiftool" = @("ExifTool"); "ffmpeg" = @("ffmpeg"); "ffprobe" = @("ffmpeg"); "java" = @("Microsoft\jdk-*\bin", "Eclipse Adoptium\*\bin", "Java\*\bin"); "magick" = @("ImageMagick"); "mpv" = @("MPV Player", "mpv", "MPV Media Player", "mpv.net"); "node" = @("nodejs"); "npm" = @("nodejs"); "pandoc" = @("Pandoc"); "yt-dlp" = @("yt-dlp") }
$lExtensions = @(".exe", ".com", ".cmd", ".bat")
$lLines = New-Object System.Collections.ArrayList

function note([string] $sText) { [void] $lLines.Add($sText) }

function versionParts([string] $sText) {
    $oMatch = [regex]::Match($sText, '\d+(\.\d+)+')
    if (-not $oMatch.Success) { $oMatch = [regex]::Match($sText, '\d+') }
    if (-not $oMatch.Success) { return @() }
    return @($oMatch.Value.Split('.') | ForEach-Object { [int] $_ })
}

function compareVersions($aLeft, $aRight) {
    $iCount = [Math]::Max($aLeft.Count, $aRight.Count)
    for ($i = 0; $i -lt $iCount; $i++) {
        $iLeft = 0; if ($i -lt $aLeft.Count) { $iLeft = $aLeft[$i] }
        $iRight = 0; if ($i -lt $aRight.Count) { $iRight = $aRight[$i] }
        if ($iLeft -ne $iRight) { return [Math]::Sign($iLeft - $iRight) }
    }
    return 0
}

function candidatePaths([string] $sName) {
    $lPatterns = New-Object System.Collections.ArrayList
    $lRoots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:ProgramW6432) | Where-Object { $_ } | Select-Object -Unique
    $lFolders = @()
    if ($dOfficial.ContainsKey($sName.ToLower())) { $lFolders += $dOfficial[$sName.ToLower()] }
    $lFolders += $sName
    foreach ($sRoot in $lRoots) {
        foreach ($sFolder in $lFolders) {
            foreach ($sExt in $lExtensions) {
                [void] $lPatterns.Add((Join-Path $sRoot (Join-Path $sFolder ($sName + $sExt))))
                [void] $lPatterns.Add((Join-Path $sRoot (Join-Path $sFolder (Join-Path "bin" ($sName + $sExt)))))
            }
        }
    }
    if ($env:LOCALAPPDATA) {
        foreach ($sExt in $lExtensions) {
            [void] $lPatterns.Add((Join-Path $env:LOCALAPPDATA ("Pandoc\" + $sName + $sExt)))
            [void] $lPatterns.Add((Join-Path $env:LOCALAPPDATA ("Programs\" + $sName + "\" + $sName + $sExt)))
            [void] $lPatterns.Add((Join-Path $env:LOCALAPPDATA ("Microsoft\WinGet\Links\" + $sName + $sExt)))
        }
    }
    $lFound = New-Object System.Collections.ArrayList
    foreach ($sPattern in $lPatterns) {
        foreach ($oItem in @(Get-Item -Path $sPattern -ErrorAction SilentlyContinue)) { [void] $lFound.Add($oItem.FullName) }
    }
    if ($env:LOCALAPPDATA) {
        $sPackages = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
        if (Test-Path -LiteralPath $sPackages) {
            foreach ($oDir in @(Get-ChildItem -LiteralPath $sPackages -Directory -Filter ("*" + $sName + "*") -ErrorAction SilentlyContinue)) {
                foreach ($oExe in @(Get-ChildItem -LiteralPath $oDir.FullName -Recurse -File -Filter ($sName + ".exe") -ErrorAction SilentlyContinue)) { [void] $lFound.Add($oExe.FullName) }
            }
        }
    }
    foreach ($oCommand in @(Get-Command $sName -CommandType Application -All -ErrorAction SilentlyContinue)) { [void] $lFound.Add($oCommand.Source) }
    $lUnique = New-Object System.Collections.ArrayList
    foreach ($sPath in $lFound) {
        $bSeen = $false
        foreach ($sHad in $lUnique) { if ([string]::Equals($sHad, $sPath, [StringComparison]::OrdinalIgnoreCase)) { $bSeen = $true } }
        if (-not $bSeen) { [void] $lUnique.Add($sPath) }
    }
    return $lUnique
}

# A RECORD OF EACH COPY'S VERSION (14 October 2026). Every copy was RUN for its version on every call -- for Pandoc,
# several copies, every build of every app, about four seconds each time -- though a copy's version changes only when
# its file does. Each copy's version is now kept with its size and time in %LOCALAPPDATA%\HomerDev\newest-<name>.txt;
# a copy whose file is unchanged takes its version from there without being run, and a new or changed copy is run and
# recorded. Every copy is still found and weighed, so a newly installed one is noticed at once. If the record cannot be
# read or written, every copy is simply run, as before.
$sRecordDir = ""
if ($env:LOCALAPPDATA) { $sRecordDir = Join-Path $env:LOCALAPPDATA "HomerDev" }
$sRecord = ""
if ($sRecordDir) { $sRecord = Join-Path $sRecordDir ("newest-" + $Name.ToLower() + ".txt") }
$dKnown = @{}
if ($sRecord -and (Test-Path -LiteralPath $sRecord)) {
    try {
        foreach ($sLine in [System.IO.File]::ReadAllLines($sRecord)) {
            $aParts = $sLine.Split([char]9)
            if ($aParts.Count -eq 4) { $dKnown[$aParts[0].ToLower()] = $aParts }
        }
    } catch { $dKnown = @{} }
}
$lRecord = New-Object System.Collections.ArrayList
$iFromRecord = 0

$aMinimum = @()
if ($Minimum) { $aMinimum = versionParts $Minimum }
if ($Minimum) { note ("Looking for every copy of " + $Name + " at " + $Minimum + " or later:") } else { note ("Looking for every copy of " + $Name + ":") }
$sBest = ""
$aBest = @()
$sBestText = ""
$iSeen = 0
foreach ($sOne in (candidatePaths $Name)) {
    $iSeen++
    $sArgs = "--version"
    if ($Name.ToLower() -eq "java") { $sArgs = "-version" }
    $sOut = ""
    $sSize = ""
    $sTicks = ""
    try {
        $oFile = Get-Item -LiteralPath $sOne -ErrorAction Stop
        $sSize = [string] $oFile.Length
        $sTicks = [string] $oFile.LastWriteTimeUtc.Ticks
    } catch { }
    $aKnown = $dKnown[$sOne.ToLower()]
    if ($aKnown -and $sSize -ne "" -and $aKnown[1] -eq $sSize -and $aKnown[2] -eq $sTicks -and $aKnown[3] -ne "") {
        # Unchanged since its version was read: that version stands, and the copy is not run.
        $sOut = $aKnown[3]
        $iFromRecord++
    } else {
        # Run the copy itself. 2>&1 turns each stderr line (java -version writes
        # there) into an error record; "$_" makes each one its plain text again.
        try { $sOut = (@(& $sOne $sArgs 2>&1) | ForEach-Object { "$_" }) -join "`n" } catch { $sOut = "" }
    }
    $aVersion = versionParts $sOut
    if ($aVersion.Count -gt 0 -and $sSize -ne "") {
        [void] $lRecord.Add($sOne + [char]9 + $sSize + [char]9 + $sTicks + [char]9 + (($aVersion | ForEach-Object { [string] $_ }) -join "."))
    }
    if ($aVersion.Count -eq 0) { note ("  " + $sOne + " -- will not run"); continue }
    $sText = ($aVersion | ForEach-Object { [string] $_ }) -join "."
    note ("  " + $sOne + " -- version " + $sText)
    if ($aMinimum.Count -gt 0 -and (compareVersions $aVersion $aMinimum) -lt 0) { continue }
    if ($sBest -eq "" -or (compareVersions $aVersion $aBest) -gt 0) { $sBest = $sOne; $aBest = $aVersion; $sBestText = $sText }
}
if ($iFromRecord -gt 0) { note ("  " + $iFromRecord + " of these versions came from the record, " + $sRecord + ", since those copies are unchanged; the rest were run.") }
if ($sRecord) {
    try {
        if (-not (Test-Path -LiteralPath $sRecordDir)) { [void] (New-Item -ItemType Directory -Path $sRecordDir -Force) }
        [System.IO.File]::WriteAllLines($sRecord, [string[]] $lRecord.ToArray())
    } catch { note ("  The record could not be written, so next time every copy is run again: " + $_.Exception.Message) }
}
if ($sBest) { note ("Chosen: " + $sBest + ", version " + $sBestText + ", of " + $iSeen + " found.") }
elseif ($iSeen -gt 0) { note "None qualifies." }
else { note "No copy found in Program Files, the user's Programs, winget's folders or the PATH." }
$sReport = ($lLines -join "`r`n")
if ($Log) { [System.IO.File]::AppendAllText($Log, $sReport + "`r`n", (New-Object System.Text.UTF8Encoding($false))) }
else { [Console]::Error.WriteLine($sReport) }
if ($sBest) { [Console]::Out.WriteLine($sBest); exit 0 }
exit 1
