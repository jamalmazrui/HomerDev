; _APP__setup.iss -- installer for _APP_.
;
; This is the HomerDev TEMPLATE. newHomerApp.cmd writes a copy of it with _APP_
; replaced by a real app name. Two things must be changed by hand afterwards,
; and both are marked CHANGE ME below: the AppId GUID and the desktop hotkey.
;
; ---- What this template settles, so no app decides again ---------------------
;
; MACHINE WIDE, ADMINISTRATOR. Program Files, no per-user fallback, no "who is
; this for" page. Somebody who wants a portable copy takes the zip.
;
; THE VERSION COMES FROM version.txt, read at compile time. No version literal
; appears here, so a stale copy of this file cannot rewind the number.
;
; IT KNOWS WHAT IS ALREADY INSTALLED. The [Code] section reads the version of
; any previous install from this app's own uninstall key and compares it with
; the version being installed. The checkboxes are worded from that comparison --
; "Install" when nothing is there, "Update" when something older is -- by
; pairing two [Run] lines with Check: functions so only one of each pair
; appears. Nothing says "Install" over the top of a copy that is already there.
;
; CHECKBOX ORDER AND DEFAULTS, in the order the user meets them:
;   1. Components the program needs: local AI, converters, and the like.
;      CHECKED, because a component that is missing or stale is what the user
;      came here to get.
;   2. SCREEN READER scripts and add-ons. ALWAYS CHECKED BY DEFAULT. A blind
;      user installing a Homer tool wants its JAWS scripts and its NVDA add-on,
;      and having to notice a cleared box is exactly the friction this suite
;      exists to remove.
;   3. Documentation, second from last. UNCHECKED: there when wanted, out of the
;      way when not.
;   4. Launch, last. CHECKED.
;
; THE RESULTS BOX COMES BEFORE THE LAUNCH. The launch entry does not start the
; program directly. It runs homerFinish.cmd, which reads the setup log, shows a
; single Results box saying what this install actually did, and starts the
; program only after that box is dismissed. Being last in [Run], it runs after
; every other checkbox, so the box can report all of them.

#define AppName       "_APP_"

#define VerFile FileOpen(AddBackslash(SourcePath) + "version.txt")
#define AppVersion Trim(FileRead(VerFile))
#expr FileClose(VerFile)
#undef VerFile

#define AppPublisher  "Jamal Mazrui"
#define AppUrl        "https://github.com/JamalMazrui/_APP_"
#define AppExeName    "_APP_.exe"
#define AppCopyright  "Copyright (c) 2026 Jamal Mazrui. MIT License."

; CHANGE ME. The desktop shortcut's hotkey. HotKey is the Inno Setup directive
; value, which requires Ctrl syntax; HotKeyDisplay is the same key in the
; notation a person reads -- Control rather than Ctrl, modifiers in alphabetical
; order. Alt+Control+key space belongs to desktop shortcuts, and a shortcut's own
; hotkey is the sanctioned use of it, so it is the right space to take here.
; Check it against the other Homer Tools before choosing.
#define HotKey        "Alt+Ctrl+X"
#define HotKeyDisplay "Alt+Control+X"

[Setup]
; CHANGE ME. A fresh GUID, unique to this app, generated once and never changed:
; it is what lets an upgrade find the previous install, and what the version
; comparison below reads. In PowerShell: [guid]::NewGuid()
AppId={{00000000-0000-0000-0000-000000000000}

AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
AppUpdatesURL={#AppUrl}/releases
AppCopyright={#AppCopyright}

; The version resource of the built setup. tagRelease reads the FileVersion
; STRING from it and tags v<that>, so the text form is set explicitly: the tag
; wanted is v1.0.0, not v1.0.0.0.
VersionInfoVersion={#AppVersion}
VersionInfoTextVersion={#AppVersion}
VersionInfoProductVersion={#AppVersion}
VersionInfoProductTextVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoCopyright={#AppCopyright}
VersionInfoDescription={#AppName} Setup

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
DisableDirPage=auto
UsePreviousGroup=yes

; THE INSTALLER KEEPS A LOG, always, and puts it where the program's own logs
; go. SetupLogging makes Inno write a detailed log of every file, registry key
; and run entry into the temporary folder; the [Code] section at the foot of
; this file copies it to
;     %LOCALAPPDATA%\{#AppName}\logs\{#AppName}-setup-<yyyymmdd-hhmmss>.log
; when setup finishes, so an install can be explained a week later. Writing it
; costs nothing; not having it costs an evening.
SetupLogging=yes

OutputDir=.
OutputBaseFilename={#AppName}_setup
SolidCompression=yes
LicenseFile=
WizardStyle=modern
Compression=lzma2/max
MinVersion=10.0
AppComments=A Homer Tools program for keyboard and screen-reader users.

#if FileExists(AddBackslash(SourcePath) + "_APP_.ico")
SetupIconFile={#AppName}.ico
#endif

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

Uninstallable=yes
UninstallDisplayIcon={app}\exec\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%n[name] is licensed under the MIT License: free to use, copy, modify, and distribute; provided "as is" with no warranty. The full license is installed as License.htm in the program folder.%n%nIt is recommended that you close all other applications before continuing.

[Dirs]
; THE HOMER FOLDER LAYOUT. Every folder starts with a different letter, so a
; screen reader user reaches any of them with one keystroke:
;   configs data exec jobs samples templates
; temp and logs are not here: they belong to the per-user tree, which the
; program makes for itself. A temp folder under Program Files could not be
; written to anyway.
Name: "{app}\configs"
Name: "{app}\data"
Name: "{app}\help"
Name: "{app}\exec"
Name: "{app}\jobs"
Name: "{app}\samples"
Name: "{app}\templates"

[Files]
; THE PROGRAM AND WHAT RUNS WITH IT go in exec: .exe, .dll, .py, .vbs.
Source: "{#AppExeName}"; DestDir: "{app}\exec"; Flags: ignoreversion
; Every line below the program itself carries skipifsourcedoesntexist. Only the
; executable is genuinely required; a missing document must not abort a build,
; and a wildcard matching nothing is a fatal error in Inno unless the line says
; otherwise.
;
; Both forms of the documentation travel: Markdown for an editor or a braille
; display, HTML for a browser, which is what the shortcuts open.
Source: "ReadMe.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP_.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Hotkeys.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "History.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "License.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Developer.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ReadMe.htm"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP_.htm"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Hotkeys.htm"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "History.htm"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "License.htm"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Developer.htm"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP_.inix"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP__hotkeys.inix"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "*.dll"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP_.exe.config"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
; The finish helper: the Results box and then the launch. Always shipped, and
; it lives beside the program because that is what it starts.
Source: "homerFinish.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion
; LOCAL AI. More than one Homer app now uses a model on the user's own machine,
; so these two are part of the kit. An app that calls no model deletes these two
; lines and the AI entries in [Run].
Source: "installOllama.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
Source: "installModels.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
; SCREEN READER support: the JAWS scripts and the NVDA add-on, when the app has
; them, plus the script that puts them where each reader looks.
Source: "installScreenReaderSupport.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP__JAWS.zip"; DestDir: "{app}\jobs"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP_.nvda-addon"; DestDir: "{app}\jobs"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; The documents stay at the root of the installed tree, where somebody looking
; for the ReadMe expects them. Everything that runs is one folder down.
Name: "{group}\{#AppName}"; Filename: "{app}\exec\{#AppExeName}"; WorkingDir: "{userdocs}"
Name: "{group}\{#AppName} documentation"; Filename: "{app}\ReadMe.htm"; Flags: createonlyiffileexists
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\exec\{#AppExeName}"; WorkingDir: "{userdocs}"; HotKey: "{#HotKey}"

[Run]
; ---- 1. Components the program needs --------------------------------------
; Two lines per component, one worded for a first install and one for a
; reinstall or update, each gated by a Check: function so only one appears.
;
; AI NOTE FOR CUSTOMIZING: change the size and the wording to match the model
; named in installOllama.cmd, then copy the pair for each further component
; (Pandoc, Tesseract, Whisper, ffmpeg).
FileName: "{cmd}"; \
  Parameters: "/c """"{app}\exec\installOllama.cmd"""""; \
  WorkingDir: "{app}\exec"; \
  Description: "Install Ollama and the local AI model, so the program can work on your text on this machine (about 2 GB; nothing is uploaded)"; \
  Check: isFreshInstall; \
  Flags: postinstall skipifsilent runascurrentuser skipifdoesntexist

FileName: "{cmd}"; \
  Parameters: "/c """"{app}\exec\installOllama.cmd"""""; \
  WorkingDir: "{app}\exec"; \
  Description: "Check Ollama and the local AI model, and fetch anything missing (nothing is downloaded if it is already here)"; \
  Check: isUpgradeOrSame; \
  Flags: postinstall skipifsilent runascurrentuser skipifdoesntexist

FileName: "{cmd}"; \
  Parameters: "/c """"{app}\exec\installModels.cmd"""""; \
  WorkingDir: "{app}\exec"; \
  Description: "Install the model only (tick this if Ollama is already on this machine)"; \
  Flags: postinstall skipifsilent runascurrentuser unchecked skipifdoesntexist

; ---- 2. Screen reader support, CHECKED BY DEFAULT --------------------------
; Never "unchecked". A blind user installing a Homer tool wants its scripts.
FileName: "{cmd}"; \
  Parameters: "/c """"{app}\exec\installScreenReaderSupport.cmd"""""; \
  WorkingDir: "{app}\exec"; \
  Description: "Install the JAWS scripts and the NVDA add-on for {#AppName}"; \
  Check: isFreshInstall; \
  Flags: postinstall skipifsilent runascurrentuser skipifdoesntexist

FileName: "{cmd}"; \
  Parameters: "/c """"{app}\exec\installScreenReaderSupport.cmd"""""; \
  WorkingDir: "{app}\exec"; \
  Description: "Update the JAWS scripts and the NVDA add-on for {#AppName}"; \
  Check: isUpgradeOrSame; \
  Flags: postinstall skipifsilent runascurrentuser skipifdoesntexist

; ---- 3. Documentation, second from last, UNCHECKED -------------------------
FileName: "{app}\ReadMe.htm"; \
  Description: "Read the documentation for {#AppName}"; \
  Flags: postinstall shellexec skipifsilent unchecked skipifdoesntexist

; ---- 4. Launch, last, CHECKED ----------------------------------------------
; Through homerFinish.cmd, which shows the Results box first and starts the
; program only when that box is dismissed.
FileName: "{cmd}"; \
  Parameters: "/c """"{app}\exec\homerFinish.cmd"" ""{#AppExeName}"""""; \
  WorkingDir: "{app}\exec"; \
  Description: "Show what this install did, then launch {#AppName} (desktop hotkey: {#HotKeyDisplay})"; \
  Flags: postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\_APP_"

[Code]
//  WHAT IS ALREADY ON THIS MACHINE.
//
//  Inno records every install under its own uninstall key, named for the AppId
//  with "_is1" on the end, and puts the version in DisplayVersion. Reading it
//  here is what lets the checkboxes say "Install" or "Update" truthfully rather
//  than always saying the same thing.
//
//  Three answers, and every checkbox is worded from one of them:
//    fresh    -- nothing of this app is installed
//    older    -- an OLDER version is installed
//    same     -- this same version, or a newer one, is installed

var
  sPriorVersion: String;

function priorVersion(): String;
var
  sKey: String;
  sFound: String;
begin
  Result := '';
  sKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';
  if RegQueryStringValue(HKLM, sKey, 'DisplayVersion', sFound) then Result := sFound
  else if RegQueryStringValue(HKCU, sKey, 'DisplayVersion', sFound) then Result := sFound;
end;

function isFreshInstall(): Boolean;
begin
  Result := (sPriorVersion = '');
end;

function isUpgradeOrSame(): Boolean;
begin
  Result := (sPriorVersion <> '');
end;

//  True when what is installed is OLDER than what is being installed. Kept
//  separate so an app can word three cases when it wants to; the template uses
//  two, which is enough for most.
function isOlderInstalled(): Boolean;
begin
  Result := False;
  if sPriorVersion = '' then exit;
  Result := ComparePackedVersion(PackVersionString(sPriorVersion),
                                 PackVersionString('{#AppVersion}')) < 0;
end;

function InitializeSetup(): Boolean;
begin
  sPriorVersion := priorVersion();
  Result := True;
end;

//  KEEP THE SETUP LOG WITH THE PROGRAM'S OWN LOGS.
//
//  Inno writes a detailed log to the temporary folder when SetupLogging is on,
//  and deletes nothing -- but nobody finds it there. Copying it to
//  %LOCALAPPDATA%\<App>\logs, with the same name shape the program's own
//  session logs use, means one folder holds the whole story: the install, and
//  every run since.
//
//  ssDone is after the files are in place and after the final-page checkboxes
//  have run, so the copy includes what they did.
//
//  ONE CAVEAT, stated because it will be noticed: this installer runs elevated,
//  so {localappdata} is the profile of whoever answered the elevation prompt.
//  When that is a different account from the one that will use the program, the
//  setup log lands in the administrator's folder. The program's own logs always
//  land in the user's.
procedure keepSetupLog();
var
  sFolder: String;
  sTarget: String;
begin
  sFolder := ExpandConstant('{localappdata}\{#AppName}\logs');
  if not DirExists(sFolder) then
    if not ForceDirectories(sFolder) then exit;
  sTarget := sFolder + '\{#AppName}-setup-' + GetDateTimeString('yyyymmdd-hhnnss', #0, #0) + '.log';
  FileCopy(ExpandConstant('{log}'), sTarget, False);
end;

procedure CurStepChanged(iStep: TSetupStep);
begin
  if iStep = ssDone then keepSetupLog();
end;

procedure CurPageChanged(iPageId: Integer);
begin
  //  Say on the welcome page what is about to happen, because a user reading by
  //  ear should not have to work it out from a version number in a caption.
  if iPageId = wpWelcome then
  begin
    if sPriorVersion = '' then
      WizardForm.WelcomeLabel1.Caption := 'Install {#AppName} {#AppVersion}'
    else if isOlderInstalled() then
      WizardForm.WelcomeLabel1.Caption := 'Update {#AppName} from ' + sPriorVersion + ' to {#AppVersion}'
    else
      WizardForm.WelcomeLabel1.Caption := 'Reinstall {#AppName} {#AppVersion}';
  end;
end;
