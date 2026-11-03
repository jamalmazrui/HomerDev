# packScreenReaderSupport.ps1 -- pack a Homer app's JAWS scripts and NVDA add-on, the same way for both.
#
# THE BUILD HALF OF THE KIT'S ONE DESIGN FOR BOTH READERS (kit 1.98.0). installScreenReaderSupport.cmd
# installs and fingerprints the two packages alike; this makes them alike, so every Homer app's build
# packs both with one call instead of a block of its own.
#
#   JAWS  sources in scripts\jaws (.jss, .jkm, .jsd, .jsh, .jcf; never a compiled .jsb, which is removed)
#         -> <OutDir>\<App>_JAWS.zip
#   NVDA  the add-on's sources in scripts\nvda, or in addon for an app that is itself an add-on
#         -> <OutDir>\<App>.nvda-addon, after the kit's exec\Python\keys.py is copied into the
#         add-on's homer package: appModules\homer for an app module, globalPlugins\<name>\homer for
#         a global plugin, with an __init__.py when there is none.
#
# Either may be absent; what is there is packed. Every step and its outcome goes to the log, and the
# console gets one line per package. Exit 0 when everything there was packed, 1 when anything failed.
param(
    [Parameter(Mandatory = $true)][string] $Root,
    [Parameter(Mandatory = $true)][string] $App,
    [string] $OutDir = "",
    [string] $Kit = ""
)
$ErrorActionPreference = "Stop"
if (-not $OutDir) { $OutDir = $Root }
if (-not $Kit) { $Kit = Split-Path -Parent $PSScriptRoot }
$sLogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $sLogDir | Out-Null
$sLog = Join-Path $sLogDir ("$App-packScreenReaderSupport-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
function logLine([string] $sText) { Add-Content -LiteralPath $sLog -Value ((Get-Date -Format "HH:mm:ss") + " " + $sText) -Encoding UTF8 }
logLine "packScreenReaderSupport started; script=$PSCommandPath; PowerShell $($PSVersionTable.PSVersion); cwd=$((Get-Location).Path)"
logLine "Root=$Root App=$App OutDir=$OutDir Kit=$Kit"
$bFailed = $false

# ---- SOURCES THE INSTALLER NEEDS, MADE AGAIN WHEN MISSING (3 November 2026) ----
# DbDo's installer installed JAWS scripts and an NVDA add-on, but its scripts\jaws and scripts\nvda were not named in
# RepoFiles.txt, so tidy moved them to notes and every build after packed nothing; Setup then compiled an old package
# left in Program Files, which failed in every JAWS version. BatCon was in the same state. So: when the app's
# installer runs installScreenReaderSupport and a reader's sources are missing, they are made from the kit's own
# templates (Templates\screenReader), _APP_ and _app_ replaced by the app's name, and named in RepoFiles.txt so tidy
# keeps them. Sources that are there are never touched.
$sIss = Join-Path $Root "${App}_setup.iss"
$bWanted = (Test-Path -LiteralPath $sIss) -and ((Get-Content -LiteralPath $sIss -Raw) -match 'installScreenReaderSupport')
$sTemplates = Join-Path $Kit "Templates\screenReader"
if ($bWanted -and (Test-Path -LiteralPath $sTemplates)) {
    $lsMade = @()
    foreach ($sReader in @("jaws", "nvda")) {
        $sTarget = Join-Path $Root ("scripts\" + $sReader)
        $bHave = if ($sReader -eq "jaws") { Test-Path -LiteralPath (Join-Path $sTarget "$App.jss") } else { (Test-Path -LiteralPath (Join-Path $sTarget "manifest.ini")) -or (Test-Path -LiteralPath (Join-Path $Root "addon\manifest.ini")) }
        if ($bHave) { logLine "scripts\$sReader is here; left as it is"; continue }
        $sFrom = Join-Path $sTemplates $sReader
        foreach ($oFile in @(Get-ChildItem -LiteralPath $sFrom -File -Recurse | Where-Object { $_.Extension -ne ".pyc" -and $_.FullName -notmatch '__pycache__' })) {
            $sRelative = $oFile.FullName.Substring($sFrom.Length).TrimStart('\').Replace("_APP_", $App).Replace("_app_", $App.ToLowerInvariant())
            $sDest = Join-Path $sTarget $sRelative
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $sDest) | Out-Null
            # Each file keeps the byte order mark its template has, or has not.
            $aBytes = [IO.File]::ReadAllBytes($oFile.FullName)
            $bMark = ($aBytes.Length -ge 3 -and $aBytes[0] -eq 0xEF -and $aBytes[1] -eq 0xBB -and $aBytes[2] -eq 0xBF)
            $sText = [IO.File]::ReadAllText($oFile.FullName).Replace("_APP_", $App).Replace("_app_", $App.ToLowerInvariant())
            [IO.File]::WriteAllText($sDest, $sText, (New-Object System.Text.UTF8Encoding $bMark))
            $lsMade += ("scripts/" + $sReader + "/" + $sRelative.Replace('\', '/'))
        }
        logLine "Made scripts\$sReader from the kit's template, since ${App}_setup.iss installs it and it was missing"
        Write-Host "Made $App's $(if ($sReader -eq 'jaws') { 'JAWS scripts' } else { 'NVDA add-on' }) from the kit's template; they were missing"
    }
    $sRepoFiles = Join-Path $Root "RepoFiles.txt"
    if ($lsMade.Count -gt 0 -and (Test-Path -LiteralPath $sRepoFiles)) {
        $lsHave = @(Get-Content -LiteralPath $sRepoFiles)
        $lsAdd = @($lsMade | Where-Object { $lsHave -notcontains $_ })
        if ($lsAdd.Count -gt 0) {
            Add-Content -LiteralPath $sRepoFiles -Value (@("# Screen reader sources, made from the kit's template (packScreenReaderSupport, " + (Get-Date -Format "d MMMM yyyy") + ").") + $lsAdd) -Encoding UTF8
            logLine "Named in RepoFiles.txt, so tidy keeps them: $($lsAdd -join ', ')"
        }
    }
} elseif (-not $bWanted) { logLine "${App}_setup.iss does not install screen reader support, so nothing is made" }

# ---- JAWS ----
$sJaws = Join-Path $Root "scripts\jaws"
if (Test-Path -LiteralPath (Join-Path $sJaws "$App.jss")) {
    try {
        foreach ($oOld in @(Get-ChildItem -LiteralPath $sJaws -Filter *.jsb -File)) { Remove-Item -LiteralPath $oOld.FullName -Force; logLine "Removed compiled $($oOld.Name): the installer compiles with each JAWS version" }
        $lsSources = @(Get-ChildItem -LiteralPath $sJaws -File | Where-Object { $_.Extension -ne ".jsb" } | ForEach-Object { $_.FullName })
        $sZip = Join-Path $OutDir "${App}_JAWS.zip"
        if (Test-Path -LiteralPath $sZip) { Remove-Item -LiteralPath $sZip -Force }
        Compress-Archive -Path $lsSources -DestinationPath $sZip -Force
        logLine "Packed ${App}_JAWS.zip from scripts\jaws: $($lsSources.Count) file(s): $((($lsSources | ForEach-Object { Split-Path -Leaf $_ }) -join ', '))"
        Write-Host "Packed ${App}_JAWS.zip"
    } catch { $bFailed = $true; logLine "ERROR packing ${App}_JAWS.zip: $($_.Exception.Message)"; Write-Host "ERROR: ${App}_JAWS.zip could not be packed; see $sLog" }
} else { logLine "No scripts\jaws\$App.jss, so no JAWS package" }

# ---- NVDA ----
$sNvda = ""
foreach ($sCandidate in @((Join-Path $Root "scripts\nvda"), (Join-Path $Root "addon"))) {
    if (Test-Path -LiteralPath (Join-Path $sCandidate "manifest.ini")) { $sNvda = $sCandidate; break }
}
if ($sNvda) {
    try {
        $sKeys = Join-Path $Kit "exec\Python\keys.py"
        if (-not (Test-Path -LiteralPath $sKeys)) { throw "the kit at $Kit has no exec\Python\keys.py" }
        $lsHomes = @()
        if (Test-Path -LiteralPath (Join-Path $sNvda "appModules")) { $lsHomes += (Join-Path $sNvda "appModules\homer") }
        if (Test-Path -LiteralPath (Join-Path $sNvda "globalPlugins")) {
            $lsHomes += @(Get-ChildItem -LiteralPath (Join-Path $sNvda "globalPlugins") -Directory | ForEach-Object { Join-Path $_.FullName "homer" })
        }
        foreach ($sHome in $lsHomes) {
            New-Item -ItemType Directory -Force -Path $sHome | Out-Null
            $sInit = Join-Path $sHome "__init__.py"
            if (-not (Test-Path -LiteralPath $sInit)) {
                [IO.File]::WriteAllText($sInit, "# The kit modules this add-on carries, copied in by the build from the kit's exec\Python.`r`n", (New-Object Text.UTF8Encoding($true)))
            }
            Copy-Item -LiteralPath $sKeys -Destination (Join-Path $sHome "keys.py") -Force
            logLine "Kit module exec\Python\keys.py copied into $sHome"
        }
        $sAddon = Join-Path $OutDir "$App.nvda-addon"
        $sTemp = "$sAddon.zip"
        if (Test-Path -LiteralPath $sTemp) { Remove-Item -LiteralPath $sTemp -Force }
        Compress-Archive -Path (Join-Path $sNvda "*") -DestinationPath $sTemp -Force
        Move-Item -LiteralPath $sTemp -Destination $sAddon -Force
        logLine "Packed $App.nvda-addon from $sNvda"
        Write-Host "Packed $App.nvda-addon"
    } catch { $bFailed = $true; logLine "ERROR packing $App.nvda-addon: $($_.Exception.Message)"; Write-Host "ERROR: $App.nvda-addon could not be packed; see $sLog" }
} else { logLine "No scripts\nvda\manifest.ini or addon\manifest.ini, so no NVDA package" }

logLine "packScreenReaderSupport finished; exit $([int]$bFailed)"
exit ([int]$bFailed)
