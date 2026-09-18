# create_APP_Repo.ps1 -- establishes the _APP_ repo on github.com as
# JamalMazrui/_APP_ from the folder this script lives in, normally C:\_APP_,
# and pushes the first commit.
#
# ONE-TIME bootstrap. After this, publishing a release is tagRelease's job.
# Idempotent all the same: rerunning it wires up whatever is not yet wired.
#
# Requires git and an authenticated gh; run "gh auth login" once beforehand.
#
# ErrorActionPreference stays Continue: under Windows PowerShell 5.1 with the
# Stop preference, redirecting a native command's error stream (as the probes
# below do with *>) wraps any stderr line in a terminating NativeCommandError,
# so a mere "repo not found" probe would kill the script. Success is judged by
# $LASTEXITCODE after every call instead.

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

$sOwner = "JamalMazrui"
$sName = "_APP_"
$sFull = $sOwner + "/" + $sName
$sUrl = "https://github.com/" + $sFull
$sDescription = "A Homer Tools program for keyboard and screen-reader users on Windows."

Write-Output ("[INFO] Repo setup started " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Write-Output ("[INFO] Working directory: " + (Get-Location).Path)
if ($DryRun) { Write-Output "[INFO] Dry run: nothing will be changed on this machine or on github.com" }

foreach ($sTool in @("git", "gh")) {
    if (-not (Get-Command $sTool -ErrorAction SilentlyContinue)) {
        Write-Output ("[ERROR] " + $sTool + " was not found on the PATH.")
        exit 1
    }
}

& gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Output "[ERROR] gh is not authenticated; run: gh auth login"
    exit 1
}

$bRepoExists = $false
& gh repo view $sFull *> $null
if ($LASTEXITCODE -eq 0) { $bRepoExists = $true }
if ($bRepoExists) { Write-Output ("[INFO] " + $sFull + " already exists on github.com") }
else { Write-Output ("[INFO] " + $sFull + " does not exist on github.com yet") }

$bLocalRepo = Test-Path ".git"
if ($bLocalRepo) { Write-Output "[INFO] The local repository already exists" }
else { Write-Output "[INFO] There is no local repository here yet" }

# Guard against publishing what should not be published. Build products are
# release assets, not repository content.
if (-not (Test-Path ".gitignore")) {
    Write-Output "[ERROR] There is no .gitignore here. Refusing to run, because the build"
    Write-Output "        products and run logs would be committed. Restore .gitignore and try again."
    exit 1
}

if ($DryRun) {
    Write-Output "[INFO] Would run: git init -b main, git add -A, git commit"
    if ($bRepoExists) { Write-Output ("[INFO] Would point origin at " + $sUrl + " and push") }
    else { Write-Output ("[INFO] Would create " + $sUrl + " as public and push") }
    Write-Output "[INFO] Dry run finished. Nothing was changed."
    exit 0
}

if (-not $bLocalRepo) {
    Write-Output "[INFO] Initializing the local repository"
    & git init -b main
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# The remote must exist before anything is pushed: git will not create one.
if (-not $bRepoExists) {
    Write-Output ("[INFO] Creating " + $sUrl)
    & gh repo create $sFull --public --description $sDescription
    if ($LASTEXITCODE -ne 0) { exit 1 }
    $bRepoExists = $true
}

# Wire origin, whether or not it was there before.
& git remote get-url origin *> $null
if ($LASTEXITCODE -ne 0) {
    & git remote add origin ($sUrl + ".git")
    if ($LASTEXITCODE -ne 0) { exit 1 }
} else {
    & git remote set-url origin ($sUrl + ".git")
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Write-Output ("[INFO] origin is " + $sUrl + ".git")

# If the remote already has history -- because the repo existed before this
# folder did -- fetch it and move onto it WITHOUT touching the working tree, so
# the new files become one ordinary commit on top. Nothing is lost, nothing is
# forced.
& git fetch origin *> $null
$bRemoteHasMain = $false
$sHeads = & git ls-remote --heads origin main 2>$null
if ($LASTEXITCODE -eq 0 -and $sHeads) { $bRemoteHasMain = $true }

if ($bRemoteHasMain) {
    $bNeedRebase = $true
    & git rev-parse --verify HEAD *> $null
    if ($LASTEXITCODE -eq 0) {
        & git merge-base --is-ancestor origin/main HEAD *> $null
        if ($LASTEXITCODE -eq 0) { $bNeedRebase = $false }
    }
    if ($bNeedRebase) {
        Write-Output "[INFO] The repository already has history. Placing this work on top of it."
        Write-Output "[INFO] The working files are left exactly as they are."
        & git reset --mixed origin/main
        if ($LASTEXITCODE -ne 0) {
            Write-Output "[ERROR] Could not move onto the existing history."
            exit 1
        }
    }
}

& git add -A
if ($LASTEXITCODE -ne 0) { exit 1 }

& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Output "[INFO] Nothing new to commit"
} else {
    & git commit -m "_APP_, first commit"
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

& git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Output "[ERROR] The push failed. Nothing local has been lost."
    Write-Output "[ERROR] See the messages above; run this script again once the cause is clear."
    exit 1
}

Write-Output ("[INFO] Done. The repo is at " + $sUrl)
Write-Output "[INFO] Next: run build_APP_.cmd, commit, then tagRelease to publish a release."
