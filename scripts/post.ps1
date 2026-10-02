# post.ps1 -- publish a project's document as a GitHub Page that meets WCAG 2.2
# AA and the Homer conventions. Part of the HomerDev kit; an app that uses it
# names "post.cmd post.ps1" in kitTools, and its build refreshes them into its
# scripts folder. Run it through post.cmd, which finds the project folder.
#
#     post                         publish the project's main document
#     post -Source help\FAQ.md     publish that document instead
#     post -DryRun                 stage everything and stop: nothing is pushed
#
# FOUR KINDS OF HOMER RESOURCE, AND WHERE EACH ONE'S PAGE GOES. kind.py, in
# this folder or the kit's scripts folder, says which this is.
#
#   An app, a collection or the kit. The repository already holds the code
#   or the documents, and push and release own its main branch and its tags.
#   So post never touches main and never makes a release: it builds the page
#   in a staging folder and force-pushes that to the gh-pages branch, which
#   nothing else writes, then points GitHub Pages at it. The owner and name
#   come from the origin remote. The page is help\<App>.md for an app or the
#   kit (help\HomerDev.md), and the ReadMe for a collection, whose .htm
#   documents go up beside it.
#
#   A page (such as a directory kept in a BlindVibeCoding folder). The repository
#   IS the page. post creates it when it does not exist yet, publishes to
#   main, keeps its description equal to the title and subtitle, and makes a
#   tagged release from the document's version field. The page is <Folder>.md
#   at the top, or the first other .md there.
#
#   Anything kind.py cannot place is left alone.
#
# WHAT GOES ON THE PAGE
#
#   index.md      the document, with its front matter, prepared for Jekyll
#   <name>.md     the same document under its own name
#   *.htm         every .htm beside the document, so its links to Hotkeys.htm
#                 and the rest still work on the web; self.htm never goes
#   site files    _includes, _layouts, assets and favicon.ico, from help\site
#                 in an app or from the top of a page project; when the
#                 project has no layout or stylesheet of its own, the kit's
#                 accessible ones from .claude\skills\homer-page\templates
#   _config.yml, README.md (page project only), .gitignore, .gitattributes
#
# PREPARING THE DOCUMENT FOR JEKYLL (each was a page that failed or misread)
#
#   - The byte order mark goes: Jekyll finds front matter only on byte one.
#   - Every heading gets an explicit {#id}, computed the way Pandoc computes
#     it. Pandoc and GitHub's kramdown name headings differently ("the-.inix-
#     format" against "the-inix-format"), so a contents list written for the
#     .htm would point nowhere on the web.
#   - The body's own "# Title" line goes when the front matter has a title,
#     because the layout prints the title as the page's one h1.
#   - Text that looks like Liquid ({{ or {%) is wrapped in raw tags, or one
#     GitHub workflow example in a document stops the whole site building.
#   - kramdown's hard_wrap is turned off in _config.yml: Homer documents wrap
#     at 80 columns, and GFM's default would turn every wrap into a line break.
#
# ENCODING. On disk the document keeps the Homer encoding, BOM and CRLF.
# Staged text has CRLF and no BOM; .gitattributes says "* -text", the kit's
# own rule, so git never rewrites line endings and never warns about them, and
# marks images and fonts binary.
#
# THE LOG is logs\<App>-post-yyyyMMdd-HHmmss.log in the project folder, in the
# Homer log format. The console says what happened in a few lines.

[CmdletBinding()]
param(
    [string]$Project = "",
    [string]$Source = "",
    [string]$Branch = "",
    [switch]$DryRun
)

$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$c_sJekyllTheme = "jekyll-theme-cayman"
$c_iWaitTries = 36
$c_iWaitSeconds = 5

$oUtf8NoBom = [System.Text.UTF8Encoding]::new($false)
if ($Project -eq "") { $Project = (Get-Location).Path }
$sProject = (Resolve-Path -LiteralPath $Project).Path.TrimEnd("\")
$sApp = Split-Path -Leaf $sProject
$sLogDir = Join-Path $sProject "logs"
if (-not (Test-Path -LiteralPath $sLogDir)) { New-Item -ItemType Directory -Path $sLogDir | Out-Null }
$sLog = Join-Path $sLogDir ($sApp + "-post-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
$oLog = [System.IO.StreamWriter]::new($sLog, $false, [System.Text.UTF8Encoding]::new($true))
$oLog.NewLine = "`r`n"
$oLog.AutoFlush = $true
$iResult = 0

function logLine([string]$sText, [string]$sLevel = "") {
    if ($sLevel -eq "") {
        $sLevel = "INFO"
        if ($sText -match "\b(ERROR|FAIL|FAILED)\b") { $sLevel = "ERROR" }
        elseif ($sText -match "\bWARN") { $sLevel = "WARN" }
    }
    $oLog.WriteLine((Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffzzz") + " " + $sLevel.PadRight(5) + " " + $sText)
    return $true
}

function quoteValue([string]$sValue) {
    if ($sValue -match '[\s"=]') { return '"' + ($sValue -replace '"', '\"') + '"' }
    return $sValue
}

function yamlQuote([string]$sValue) {
    return '"' + (($sValue -replace '\\', '\\') -replace '"', '\"') + '"'
}

function say([string]$sText) {
    Write-Host $sText
    logLine $sText | Out-Null
    return $true
}

function runLogged([string]$sDescription, [string]$sExe, [string[]]$aArgs) {
    # Runs a native command, logs its exit code, time and every output line
    # (continued lines start "| "), and returns the exit code with the output.
    $dtStart = Get-Date
    $aOut = @(& $sExe @aArgs 2>&1 | ForEach-Object { "$_" })
    $iCode = $LASTEXITCODE
    if ($null -eq $iCode) { $iCode = 0 }
    $iMs = [int]((Get-Date) - $dtStart).TotalMilliseconds
    $sLevel = if ($iCode -eq 0) { "INFO" } else { "WARN" }
    logLine ("run " + $sDescription + " exit=" + $iCode + " ms=" + $iMs + " cmd=" + (quoteValue ($sExe + " " + ($aArgs -join " ")))) $sLevel | Out-Null
    foreach ($sLine in $aOut) { logLine ("| " + $sLine) $sLevel | Out-Null }
    return @{ Code = $iCode; Out = $aOut }
}

function writeCrlfNoBom([string]$sPath, [string]$sContent) {
    $sContent = ($sContent -replace "`r`n", "`n") -replace "`n", "`r`n"
    [System.IO.File]::WriteAllText($sPath, $sContent, $script:oUtf8NoBom)
    return $true
}

function readText([string]$sPath) {
    $sText = [System.IO.File]::ReadAllText($sPath)
    if ($sText.Length -gt 0 -and $sText[0] -eq [char]0xFEFF) { $sText = $sText.Substring(1) }
    return $sText
}

function findKit() {
    # The kit wherever it is (1.46.0): only Windows and the folder name
    # HomerDev are assumed, never a drive or a depth. The HomerDev variable;
    # then the project folder and every folder above it, and this script's
    # folder and every folder above it, each either the kit or holding a
    # HomerDev folder; then a HomerDev folder at the top of any ready fixed drive.
    $fnIsKit = { param($sDir) $sDir -and ((Test-Path -LiteralPath (Join-Path $sDir "exec\CSharp\Lbc.cs")) -or (Test-Path -LiteralPath (Join-Path $sDir "exec\Python\lbc.py"))) }
    if (& $fnIsKit $env:HomerDev) { return $env:HomerDev }
    foreach ($sStart in @($sProject, $PSScriptRoot)) {
        $sDir = $sStart
        while ($sDir) {
            if (& $fnIsKit $sDir) { return $sDir }
            if (& $fnIsKit (Join-Path $sDir "HomerDev")) { return (Join-Path $sDir "HomerDev") }
            $sUp = Split-Path -Parent $sDir
            if (-not $sUp -or $sUp -eq $sDir) { break }
            $sDir = $sUp
        }
    }
    foreach ($oDrive in [System.IO.DriveInfo]::GetDrives()) {
        if ($oDrive.DriveType -ne "Fixed" -or -not $oDrive.IsReady) { continue }
        $sTry = Join-Path $oDrive.RootDirectory.FullName "HomerDev"
        if (& $fnIsKit $sTry) { return $sTry }
    }
    return ""
}

function getField([string]$sYaml, [string]$sName) {
    $sPattern = '(?m)^' + [regex]::Escape($sName) + ':\s*"?([^"\r\n]*?)"?\s*$'
    if ($sYaml -match $sPattern) { return $Matches[1].Trim() }
    return ""
}

function pandocId([string]$sText) {
    # Pandoc's auto_identifiers, checked against Pandoc on every heading of
    # HomerDev.md: links and markup become their text; a backslash and what
    # follows it go; "--" and "---" are dashes, which go; lower case; only
    # letters, digits, "_", "-" and "." stay; words join with one hyphen; and
    # everything before the first letter goes.
    $sText = $sText -replace '!?\[([^\]]*)\]\([^)]*\)', '$1'
    $sText = $sText -replace '[`*_]{1,3}([^`*_]+)[`*_]{1,3}', '$1'
    $sText = $sText -replace '\\+\S*', ''
    $sText = $sText -replace '---|--', ' '
    $sText = $sText.ToLowerInvariant()
    $sText = ($sText -replace '[^\p{L}\p{N}_\-\.\s]', '')
    $sText = (($sText.Trim() -split '\s+') -join '-')
    $sText = $sText -replace '^[^\p{L}]+', ''
    if ($sText -eq "") { $sText = "section" }
    return $sText
}

function prepareDocument([string]$sText, [string]$sTitle) {
    # Returns the document ready for Jekyll: front matter kept, body h1 that
    # repeats the title removed, every heading given Pandoc's id, Liquid-looking
    # text wrapped in raw.
    $sFront = ""
    $sBody = $sText -replace "`r`n", "`n"
    $oMatch = [regex]::Match($sBody, '\A---\n.*?\n---\n', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if ($oMatch.Success) { $sFront = $oMatch.Value; $sBody = $sBody.Substring($oMatch.Length) }
    $aLines = $sBody -split "`n"
    $dSeen = @{}
    $bFence = $false
    $bFirstHeading = $true
    $iIds = 0
    $sPrevious = ""
    $oOut = [System.Collections.Generic.List[string]]::new()
    foreach ($sLine in $aLines) {
        $sBefore = $sPrevious
        $sPrevious = $sLine
        if ($sLine -match '^\s*(```|~~~)') { $bFence = -not $bFence; $oOut.Add($sLine); continue }
        # Pandoc counts a line as a heading only after a blank line.
        if (-not $bFence -and $sBefore.Trim() -eq "" -and $sLine -match '^(#{1,6})\s+(.*?)\s*$') {
            $sHashes = $Matches[1]; $sHeading = $Matches[2]
            $bWasFirst = $bFirstHeading
            $bFirstHeading = $false
            if ($bWasFirst -and $sHashes -eq "#" -and $sTitle -ne "") {
                logLine ("removed the body h1, since the layout prints the title as the page's one h1: " + $sHeading) | Out-Null
                $dSeen[(pandocId $sHeading)] = 1
                continue
            }
            if ($sHeading -match '\{#([^}]+)\}\s*$') {
                $dSeen[$Matches[1]] = 1
                $oOut.Add($sLine); continue
            }
            $sBase = pandocId $sHeading
            $sId = $sBase; $iN = 0
            while ($dSeen.ContainsKey($sId)) { $iN++; $sId = $sBase + "-" + $iN }
            $dSeen[$sId] = 1
            $oOut.Add($sHashes + " " + $sHeading + " {#" + $sId + "}")
            $iIds++
            continue
        }
        $oOut.Add($sLine)
    }
    logLine ("heading ids added=" + $iIds) | Out-Null
    $sBody = ($oOut -join "`n")
    if ($sBody -match '\{\{|\{%') {
        if ($sBody -match '\{%-?\s*endraw\s*-?%\}') {
            logLine "WARN: the document holds Liquid-looking text and its own endraw tag; left as it is, and the Pages build may fail." | Out-Null
        } else {
            $sBody = "{% raw %}`n" + $sBody + "`n{% endraw %}`n"
            logLine "wrapped the body in raw: it holds text that looks like Liquid template tags" | Out-Null
        }
    }
    return $sFront + $sBody
}

function copySiteFiles([string]$sFromDir, [string]$sToDir) {
    # Copies _includes, _layouts, assets and favicon.ico. Text loses any BOM,
    # since Jekyll reads front matter from byte one; images go byte for byte.
    $aText = @(".css", ".htm", ".html", ".js", ".json", ".md", ".scss", ".svg", ".txt", ".xml", ".yml")
    $iCount = 0
    foreach ($sName in @("_includes", "_layouts", "assets")) {
        $sDir = Join-Path $sFromDir $sName
        if (-not (Test-Path -LiteralPath $sDir -PathType Container)) { continue }
        foreach ($oFile in (Get-ChildItem -LiteralPath $sDir -Recurse -File)) {
            $sRelative = $oFile.FullName.Substring($sFromDir.Length).TrimStart("\")
            $sTarget = Join-Path $sToDir $sRelative
            $sParent = Split-Path -Parent $sTarget
            if (-not (Test-Path -LiteralPath $sParent)) { New-Item -ItemType Directory -Path $sParent | Out-Null }
            if ($aText -contains $oFile.Extension.ToLowerInvariant()) {
                writeCrlfNoBom $sTarget (readText $oFile.FullName) | Out-Null
                logLine ("site file text=" + (quoteValue $sRelative)) | Out-Null
            } else {
                Copy-Item -LiteralPath $oFile.FullName -Destination $sTarget -Force
                logLine ("site file binary=" + (quoteValue $sRelative)) | Out-Null
            }
            $iCount++
        }
    }
    $sIcon = Join-Path $sFromDir "favicon.ico"
    if (Test-Path -LiteralPath $sIcon) {
        Copy-Item -LiteralPath $sIcon -Destination (Join-Path $sToDir "favicon.ico") -Force
        logLine "site file binary=favicon.ico" | Out-Null
        $iCount++
    }
    return $iCount
}

try {
    logLine ("post start app=" + $sApp + " pid=" + $PID) | Out-Null
    logLine ("env script=" + (quoteValue $PSCommandPath) + " powershell=" + $PSVersionTable.PSVersion + " windows=" + (quoteValue ([Environment]::OSVersion.VersionString))) | Out-Null
    logLine ("env workingDirectory=" + (quoteValue (Get-Location).Path) + " project=" + (quoteValue $sProject)) | Out-Null
    logLine ("arguments source=" + (quoteValue $Source) + " branch=" + (quoteValue $Branch) + " dryRun=" + [bool]$DryRun) | Out-Null

    # ---- the kind of resource --------------------------------------------
    $sKind = ""
    $sKindPy = Join-Path $PSScriptRoot "kind.py"
    if (-not (Test-Path -LiteralPath $sKindPy)) { $sKit0 = findKit; if ($sKit0 -ne "") { $sKindPy = Join-Path $sKit0 "scripts\kind.py" } }
    if ((Test-Path -LiteralPath $sKindPy) -and (Get-Command python -ErrorAction SilentlyContinue)) {
        $oKind = runLogged "kind" "python" @($sKindPy, $sProject, "--word")
        if ($oKind.Out.Count -gt 0) { $sKind = ([string]$oKind.Out[0]).Trim() }
    }
    if ($sKind -eq "") {
        $sKind = if (Test-Path -LiteralPath (Join-Path $sProject ".git")) { "app" } else { "page" }
        logLine ("WARN: kind.py could not be run, so the kind was taken from whether the folder is a repository: " + $sKind) | Out-Null
    }
    logLine ("setting kind=" + $sKind) | Out-Null
    if ($sKind -eq "unknown") {
        say "This folder is not an app, a collection, the kit or a page, so there is nothing to publish. Run kind to see why." | Out-Null
        $iResult = 5; return
    }
    $bAppRepo = ($sKind -ne "page")

    # ---- the document ----------------------------------------------------
    $sSourcePath = ""
    if ($Source -ne "") {
        $sSourcePath = if ([System.IO.Path]::IsPathRooted($Source)) { $Source } else { Join-Path $sProject $Source }
    } elseif ($sKind -eq "collection") {
        foreach ($sTry in @((Join-Path $sProject "ReadMe.md"), (Join-Path $sProject "README.md"))) {
            if (Test-Path -LiteralPath $sTry) { $sSourcePath = $sTry; break }
        }
    } elseif ($bAppRepo) {
        foreach ($sTry in @((Join-Path $sProject ("help\" + $sApp + ".md")), (Join-Path $sProject ($sApp + ".md")), (Join-Path $sProject "ReadMe.md"))) {
            if (Test-Path -LiteralPath $sTry) { $sSourcePath = $sTry; break }
        }
    } else {
        $sTry = Join-Path $sProject ($sApp + ".md")
        if (Test-Path -LiteralPath $sTry) { $sSourcePath = $sTry }
        else {
            $oFirst = Get-ChildItem -LiteralPath $sProject -Filter "*.md" -File | Where-Object { @("readme.md", "index.md", "self.md") -notcontains $_.Name.ToLowerInvariant() } | Sort-Object Name | Select-Object -First 1
            if ($oFirst) { $sSourcePath = $oFirst.FullName }
        }
    }
    if ($sSourcePath -eq "" -or -not (Test-Path -LiteralPath $sSourcePath)) {
        say "No document to publish was found. Name one with -Source." | Out-Null
        $iResult = 5; return
    }
    if ((Split-Path -Leaf $sSourcePath) -ieq "self.md") {
        say "self.md is the private notebook and is never published." | Out-Null
        $iResult = 5; return
    }
    $sSourceName = Split-Path -Leaf $sSourcePath
    $sSourceDir = Split-Path -Parent $sSourcePath
    logLine ("setting source=" + (quoteValue $sSourcePath)) | Out-Null

    # ---- the front matter ------------------------------------------------
    $sText = readText $sSourcePath
    $sYaml = ""
    if ($sText -match '(?s)\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n') { $sYaml = $Matches[1] }
    else { logLine "WARN: the document has no front matter, so the page title falls back to the folder name. Add title, subtitle, description and version." | Out-Null }
    $sTitle = getField $sYaml "title"
    $sSubtitle = getField $sYaml "subtitle"
    $sDescription = getField $sYaml "description"
    $sVersion = getField $sYaml "version"
    $sAuthor = getField $sYaml "author"
    $sLanguage = getField $sYaml "lang"
    if ($sTitle -eq "") { $sTitle = $sApp }
    if ($sLanguage -eq "") { $sLanguage = "en-US" }
    if ($sDescription -eq "") { $sDescription = if ($sSubtitle -ne "") { $sSubtitle } else { $sTitle } }
    $sRepoDescription = if ($sSubtitle -ne "") { $sTitle + ": " + $sSubtitle } else { $sTitle }
    $dSettings = [ordered]@{ author = $sAuthor; description = $sDescription; lang = $sLanguage; subtitle = $sSubtitle; title = $sTitle; version = $sVersion }
    foreach ($sKey in $dSettings.Keys) { logLine ("setting " + $sKey + "=" + (quoteValue $dSettings[$sKey])) | Out-Null }

    # ---- tools -----------------------------------------------------------
    foreach ($sTool in @("git", "gh")) {
        if (-not (Get-Command $sTool -ErrorAction SilentlyContinue)) {
            say ("$sTool is not installed. Install it (winget install " + $(if ($sTool -eq "gh") { "GitHub.cli" } else { "Git.Git" }) + ") and run post again.") | Out-Null
            $iResult = 2; return
        }
        logLine ("env " + $sTool + "=" + (quoteValue (Get-Command $sTool).Source)) | Out-Null
    }

    # ---- owner, repository and branch ------------------------------------
    if ($bAppRepo) {
        $oRemote = runLogged "origin" "git" @("-C", $sProject, "remote", "get-url", "origin")
        $sOrigin = ([string]($oRemote.Out | Select-Object -First 1)).Trim()
        if ($oRemote.Code -ne 0 -or $sOrigin -notmatch 'github\.com[:/]([^/]+)/([^/]+?)(\.git)?$') {
            say ("This " + $sKind + "'s repository has no GitHub origin, so there is nowhere to publish.") | Out-Null
            $iResult = 3; return
        }
        $sOwner = $Matches[1]; $sRepo = $Matches[2]
        if ($Branch -eq "") { $Branch = "gh-pages" }
        if ($Branch -ieq "main" -or $Branch -ieq "master") {
            say ("A " + $sKind + "'s page is never published to " + $Branch + ", which push and release own. Leave -Branch off to use gh-pages.") | Out-Null
            $iResult = 3; return
        }
    } else {
        $oUser = runLogged "user" "gh" @("api", "user", "--jq", ".login")
        if ($oUser.Code -ne 0) { say "The GitHub CLI is not signed in. Run gh auth login, then post again." | Out-Null; $iResult = 4; return }
        $sOwner = ($oUser.Out | Select-Object -First 1).Trim()
        $sRepo = $sApp
        if ($Branch -eq "") { $Branch = "main" }
    }
    logLine ("setting owner=" + $sOwner + " repo=" + $sRepo + " branch=" + $Branch) | Out-Null
    $sPagesUrl = "https://" + $sOwner.ToLowerInvariant() + ".github.io/" + $sRepo + "/"

    # ---- staging ---------------------------------------------------------
    $sStage = Join-Path $env:TEMP ($sApp + "_page")
    if (Test-Path -LiteralPath $sStage) { Remove-Item -LiteralPath $sStage -Recurse -Force }
    New-Item -ItemType Directory -Path $sStage | Out-Null
    logLine ("setting stage=" + (quoteValue $sStage)) | Out-Null

    $sPrepared = prepareDocument $sText $(if ($sYaml -ne "") { $sTitle } else { "" })
    # THE LICENSE IS NAMED ON EVERY PAGE (1.48.0). The layout's footer prints
    # the front matter's license and license_url. A document without them gets
    # its kind's license in the staged copy -- MIT for an app or the kit,
    # CC BY-SA 4.0, as Wikipedia uses, for a page or a collection -- and the
    # log asks for the two lines to be added to the source.
    if ($sYaml -ne "" -and $sYaml -notmatch '(?m)^license:') {
        if ($sKind -eq "app" -or $sKind -eq "kit") {
            $sLicenseLines = 'license: "MIT"' + "`n" + 'license_url: "https://github.com/' + $sOwner + '/' + $sRepo + '/blob/main/License.md"'
        } else {
            $sLicenseLines = 'license: "CC BY-SA 4.0"' + "`n" + 'license_url: "https://creativecommons.org/licenses/by-sa/4.0/"'
        }
        $sPrepared = [regex]::Replace($sPrepared, '\A(---\n.*?)(\n---\n)', { param($oMatch) $oMatch.Groups[1].Value + "`n" + $sLicenseLines + $oMatch.Groups[2].Value }, [System.Text.RegularExpressions.RegexOptions]::Singleline)
        logLine ("WARN: the front matter names no license, so the staged page carries the " + $sKind + "'s: " + ($sLicenseLines -replace "`n", "; ") + ". Add these lines to " + $sSourceName + ".") | Out-Null
    }
    writeCrlfNoBom (Join-Path $sStage "index.md") $sPrepared | Out-Null
    if ($sSourceName -ine "index.md") { writeCrlfNoBom (Join-Path $sStage $sSourceName) $sPrepared | Out-Null }

    $iHtm = 0
    foreach ($oHtm in (Get-ChildItem -LiteralPath $sSourceDir -Filter "*.htm" -File)) {
        if ($oHtm.Name -ieq "self.htm") { continue }
        writeCrlfNoBom (Join-Path $sStage $oHtm.Name) (readText $oHtm.FullName) | Out-Null
        $iHtm++
    }
    logLine ("documents htm=" + $iHtm) | Out-Null

    $sSiteRoot = ""
    foreach ($sTry in @((Join-Path $sProject "help\site"), $sProject)) {
        if ((Test-Path -LiteralPath (Join-Path $sTry "_layouts")) -or (Test-Path -LiteralPath (Join-Path $sTry "assets"))) { $sSiteRoot = $sTry; break }
    }
    $iSite = 0
    if ($sSiteRoot -ne "") { $iSite = copySiteFiles $sSiteRoot $sStage }
    logLine ("site root=" + (quoteValue $sSiteRoot) + " files=" + $iSite) | Out-Null

    $sKit = findKit
    $sTemplates = if ($sKit -ne "") { Join-Path $sKit ".claude\skills\homer-page\templates" } else { "" }
    foreach ($sPiece in @("_layouts\default.html", "assets\css\style.scss")) {
        $sTarget = Join-Path $sStage $sPiece
        if (Test-Path -LiteralPath $sTarget) { continue }
        $sFrom = if ($sTemplates -ne "") { Join-Path $sTemplates $sPiece } else { "" }
        if ($sFrom -ne "" -and (Test-Path -LiteralPath $sFrom)) {
            $sParent = Split-Path -Parent $sTarget
            if (-not (Test-Path -LiteralPath $sParent)) { New-Item -ItemType Directory -Path $sParent | Out-Null }
            writeCrlfNoBom $sTarget (readText $sFrom) | Out-Null
            logLine ("kit template used=" + (quoteValue $sPiece)) | Out-Null
        } else {
            logLine ("WARN: no " + $sPiece + " in the project or the kit; the theme's own is used, and its colors fail WCAG contrast.") | Out-Null
        }
    }

    $sConfig = "title: " + (yamlQuote $sTitle) + "`ndescription: " + (yamlQuote $sDescription) + "`n"
    if ($sAuthor -ne "") { $sConfig += "author: " + (yamlQuote $sAuthor) + "`n" }
    $sConfig += "theme: " + $c_sJekyllTheme + "`nlang: " + $sLanguage + "`nmarkdown: kramdown`nkramdown:`n  input: GFM`n  hard_wrap: false`n  auto_ids: true`n"
    writeCrlfNoBom (Join-Path $sStage "_config.yml") $sConfig | Out-Null

    if (-not $bAppRepo) {
        $sReadme = ""
        if (Test-Path -LiteralPath (Join-Path $sStage ("assets\images\" + $sRepo + "-logo.svg"))) {
            $sReadme += "![" + $sTitle + " logo](assets/images/" + $sRepo + "-logo.svg)`n`n"
        }
        $sReadme += "# " + $sTitle + "`n`n" + $sDescription + "`n`n[Read " + $sTitle + " as a web page](" + $sPagesUrl + ").`n`nThe Markdown source is [" + $sSourceName + "](" + $sSourceName + ").`n"
        writeCrlfNoBom (Join-Path $sStage "README.md") $sReadme | Out-Null
    }
    writeCrlfNoBom (Join-Path $sStage ".gitignore") "_site/`n.jekyll-cache/`n.jekyll-metadata`n.sass-cache/`n*.log`nThumbs.db`n" | Out-Null
    writeCrlfNoBom (Join-Path $sStage ".gitattributes") "* -text`n*.gif binary`n*.ico binary`n*.jpeg binary`n*.jpg binary`n*.mp3 binary`n*.png binary`n*.webp binary`n*.woff binary`n*.woff2 binary`n" | Out-Null

    $iStaged = @(Get-ChildItem -LiteralPath $sStage -Recurse -File).Count
    say ("Staged " + $iStaged + $(if ($iStaged -eq 1) { " file" } else { " files" }) + " for " + $sPagesUrl) | Out-Null
    if ($DryRun) {
        say ("Dry run: nothing was pushed. The staged page is in " + $sStage) | Out-Null
        return
    }

    # ---- commit and push -------------------------------------------------
    $sMessage = "Publish " + $sTitle + $(if ($sVersion -ne "") { " " + $sVersion } else { "" })
    $null = runLogged "init" "git" @("-C", $sStage, "init", "-b", $Branch)
    $null = runLogged "add" "git" @("-C", $sStage, "add", "-A")
    $oCommit = runLogged "commit" "git" @("-C", $sStage, "commit", "-m", $sMessage)
    if ($oCommit.Code -ne 0) { say "The staged page could not be committed. The log has why." | Out-Null; $iResult = 6; return }

    $sRemote = "https://github.com/" + $sOwner + "/" + $sRepo + ".git"
    if (-not $bAppRepo) {
        $oView = runLogged "repo view" "gh" @("repo", "view", ($sOwner + "/" + $sRepo))
        if ($oView.Code -ne 0) {
            $oCreate = runLogged "repo create" "gh" @("repo", "create", ($sOwner + "/" + $sRepo), "--public", "--description", $sRepoDescription)
            if ($oCreate.Code -ne 0) { say "The repository could not be created. The log has why." | Out-Null; $iResult = 6; return }
            say ("Created the repository " + $sOwner + "/" + $sRepo + ".") | Out-Null
        } else {
            $null = runLogged "repo edit" "gh" @("repo", "edit", ($sOwner + "/" + $sRepo), "--description", $sRepoDescription)
        }
    }
    $oPush = runLogged "push" "git" @("-C", $sStage, "push", "--force", $sRemote, ($Branch + ":" + $Branch))
    if ($oPush.Code -ne 0) { say "The push failed. The log has why." | Out-Null; $iResult = 7; return }

    # ---- GitHub Pages ----------------------------------------------------
    $sJson = Join-Path $sStage "pages.json"
    [System.IO.File]::WriteAllText($sJson, ('{"source":{"branch":"' + $Branch + '","path":"/"}}'), $oUtf8NoBom)
    $oPages = runLogged "pages get" "gh" @("api", ("repos/" + $sOwner + "/" + $sRepo + "/pages"))
    if ($oPages.Code -ne 0) {
        $oSet = runLogged "pages enable" "gh" @("api", "-X", "POST", ("repos/" + $sOwner + "/" + $sRepo + "/pages"), "--input", $sJson)
    } else {
        $oSet = runLogged "pages source" "gh" @("api", "-X", "PUT", ("repos/" + $sOwner + "/" + $sRepo + "/pages"), "--input", $sJson)
    }
    if ($oSet.Code -ne 0) {
        say ("GitHub Pages could not be pointed at " + $Branch + ". In the repository's Settings, Pages, choose Deploy from a branch, " + $Branch + ", root.") | Out-Null
        $iResult = 8; return
    }

    # ---- release, page projects only -------------------------------------
    if (-not $bAppRepo -and $sVersion -ne "") {
        $oRelease = runLogged "release view" "gh" @("release", "view", $sVersion, "--repo", ($sOwner + "/" + $sRepo))
        if ($oRelease.Code -ne 0) {
            $sNotes = "Release " + $sVersion + " of " + $sTitle + ". The Markdown source is attached. Read it as a web page at " + $sPagesUrl
            $oMake = runLogged "release create" "gh" @("release", "create", $sVersion, "--repo", ($sOwner + "/" + $sRepo), "--title", ($sTitle + " " + $sVersion), "--notes", $sNotes, $sSourcePath)
            if ($oMake.Code -ne 0) { say "The release could not be made. The log has why." | Out-Null; $iResult = 9; return }
            say ("Released " + $sVersion + ".") | Out-Null
        } else {
            say ("Release " + $sVersion + " already exists; raise version in the front matter for a new one.") | Out-Null
        }
    }

    # ---- wait for GitHub's build -----------------------------------------
    $sStatus = ""; $sBuildError = ""
    for ($iTry = 0; $iTry -lt $c_iWaitTries; $iTry++) {
        Start-Sleep -Seconds $c_iWaitSeconds
        $sOut = (& gh api ("repos/" + $sOwner + "/" + $sRepo + "/pages/builds/latest") 2>&1 | Out-String)
        try {
            $oBuild = $sOut | ConvertFrom-Json
            $sStatus = [string]$oBuild.status
            if ($oBuild.error -and $oBuild.error.message) { $sBuildError = [string]$oBuild.error.message }
        } catch { $sStatus = "unreadable" }
        if ($sStatus -eq "built" -or $sStatus -eq "errored") { break }
    }
    logLine ("pages build status=" + $sStatus + " message=" + (quoteValue $sBuildError)) | Out-Null
    if ($sStatus -ne "built") {
        say ("GitHub could not build the page (" + $sStatus + "). " + $(if ($sBuildError -ne "") { $sBuildError } else { "The log has the details." })) | Out-Null
        $iResult = 10; return
    }
    say ("Published: " + $sPagesUrl) | Out-Null
} catch {
    logLine ("ERROR exception " + $_.Exception.Message) "ERROR" | Out-Null
    logLine ("| " + $_.ScriptStackTrace) "ERROR" | Out-Null
    Write-Host "Something unexpected stopped post. The log has it."
    if ($iResult -eq 0) { $iResult = 99 }
} finally {
    logLine ("post end exit=" + $iResult) | Out-Null
    $oLog.Close()
    Write-Host ("Log: " + $sLog)
    exit $iResult
}
