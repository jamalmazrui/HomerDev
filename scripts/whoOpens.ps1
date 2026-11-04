# whoOpens.ps1 -- name the program behind Windows's "Select an app to open this file" prompt.
#
# WHY (3 November 2026). Jamal heard "Select an app to open this .log file -- Just once" again and again, with no
# build running, and JAWS never read which file. The prompt is OpenWith.exe, and Windows starts it with the file's
# full path on its command line; its parent process is whoever asked. So this watches for OpenWith.exe and, for each
# one, says the file and the program that asked, and logs the parent chain four levels up -- each with its own
# command line, so a script shows as, say, python.exe running kdpSubmit.py. It changes nothing on the machine.
#
#   whoOpens                 watch for ten minutes
#   whoOpens -minutes 30     watch longer
param([int] $Minutes = 10)
$ErrorActionPreference = "Stop"
$sKit = Split-Path -Parent $PSScriptRoot
$sLogDir = Join-Path $env:LOCALAPPDATA "HomerDev\logs"
New-Item -ItemType Directory -Force -Path $sLogDir | Out-Null
$sLog = Join-Path $sLogDir ("HomerDev-whoOpens-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
function logLine([string] $sText) { Add-Content -LiteralPath $sLog -Value ((Get-Date -Format "HH:mm:ss.fff") + "  " + $sText) -Encoding UTF8 }
logLine "whoOpens started; script=$PSCommandPath; PowerShell $($PSVersionTable.PSVersion); cwd=$((Get-Location).Path); minutes=$Minutes"
Write-Host "whoOpens: watching for the Open with prompt for $Minutes minutes. Leave this window open; Control+C stops it."
Write-Host "Log: $sLog"

function describeProcess([int] $iPid) {
    $oProc = Get-CimInstance Win32_Process -Filter "ProcessId = $iPid" -ErrorAction SilentlyContinue
    if ($null -eq $oProc) { return $null }
    return $oProc
}

$dSeen = @{}
$dtUntil = (Get-Date).AddMinutes($Minutes)
$iFound = 0
while ((Get-Date) -lt $dtUntil) {
    foreach ($oOpen in @(Get-CimInstance Win32_Process -Filter "Name = 'OpenWith.exe'" -ErrorAction SilentlyContinue)) {
        if ($dSeen.ContainsKey($oOpen.ProcessId)) { continue }
        $dSeen[$oOpen.ProcessId] = $true
        $iFound++
        $sCommand = [string] $oOpen.CommandLine
        $oMatch = [regex]::Match($sCommand, '"([^"]+\.[A-Za-z0-9]+)"\s*$')
        $sFile = if ($oMatch.Success) { $oMatch.Groups[1].Value } else { $sCommand }
        logLine "OpenWith.exe pid $($oOpen.ProcessId) started $($oOpen.CreationDate); command line: $sCommand"
        $lsChain = @()
        $iParent = [int] $oOpen.ParentProcessId
        for ($iLevel = 1; $iLevel -le 4 -and $iParent -gt 0; $iLevel++) {
            $oParent = describeProcess $iParent
            if ($null -eq $oParent) { logLine "  parent $iLevel : pid $iParent has already ended"; break }
            logLine "  parent $iLevel : $($oParent.Name) pid $($oParent.ProcessId); command line: $($oParent.CommandLine)"
            $lsChain += $oParent.Name
            $iParent = [int] $oParent.ParentProcessId
        }
        $sAsker = if ($lsChain.Count -gt 0) { $lsChain -join ", started by " } else { "a program that had already ended" }
        Write-Host ("Prompt " + $iFound + ": " + $sFile)
        Write-Host ("  asked by " + $sAsker + ". The log has each one's command line.")
    }
    Start-Sleep -Milliseconds 500
}
logLine "whoOpens end; prompts seen: $iFound"
Write-Host ("whoOpens is done: " + $iFound + $(if ($iFound -eq 1) { " prompt" } else { " prompts" }) + " seen. Log: $sLog")
exit 0
