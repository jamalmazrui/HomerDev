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
; CHECKBOX ORDER AND DEFAULTS, in the order the user meets them (HomerDev
; rule, 25 September 2026; the [Run] section says how it is done):
;   1. Install entries, TICKED: screen reader scripts first -- a blind user
;      installing a Homer tool wants its JAWS scripts and its NVDA add-on --
;      then components in alphabetical order.
;   2. Update entries, TICKED, alphabetical.
;   3. Reinstall entries, UNTICKED, alphabetical.
;   4. Launch, TICKED, after the Results box has been read.
;   5. Open the user guide, UNTICKED: there when wanted, out of the way when not.
;
; THE RESULTS BOX COMES BEFORE THE LAUNCH. The Launch entry only leaves a
; marker; CurStepChanged(ssDone) shows one Results box -- a past-tense line per
; box that was ticked, probed after its script ran, and nothing about the rest
; -- and starts the program only after that box is dismissed.

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
; Hide the destination page when a previous install of the same AppId is found:
; a reinstall then asks nothing at all and goes where the last one went. A first
; install still chooses the folder.
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
;   configs data exec help scripts templates
; temp and logs are not here: they belong to the per-user tree, which the
; program makes for itself. A temp folder under Program Files could not be
; written to anyway.
Name: "{app}\configs"
Name: "{app}\data"
Name: "{app}\help"
Name: "{app}\exec"
Name: "{app}\scripts"
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
Source: "homerInstall.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion
; EVERY COMPONENT APPEARS THREE TIMES: one entry per state -- install, update,
; already current -- grouped so the ones that do something come first, and only
; one is ever shown because the others are skipped by their Check function. The
; label carries the versions in play and nothing else:
;     Install Ollama 0.34.1
;     Update Ollama from 0.33.0 to 0.34.1
;     Reinstall Ollama 0.34.1 (current version)
; A purpose clause belongs only in the fallback label, where no version is known.
;
; LOCAL AI. More than one Homer app now uses a model on the user's own machine,
; so these two are part of the kit. An app that calls no model deletes these two
; lines and the AI entries in [Run].
Source: "installOllama.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
Source: "installModels.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
; SCREEN READER support: the JAWS scripts and the NVDA add-on, when the app has
; them, plus the script that puts them where each reader looks.
Source: "installScreenReaderSupport.cmd"; DestDir: "{app}\exec"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP__JAWS.zip"; DestDir: "{app}\scripts"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP_.nvda-addon"; DestDir: "{app}\scripts"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; The documents stay at the root of the installed tree, where somebody looking
; for the ReadMe expects them. Everything that runs is one folder down.
Name: "{group}\{#AppName}"; Filename: "{app}\exec\{#AppExeName}"; WorkingDir: "{userdocs}"
Name: "{group}\{#AppName} documentation"; Filename: "{app}\ReadMe.htm"; Flags: createonlyiffileexists
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\exec\{#AppExeName}"; WorkingDir: "{userdocs}"; HotKey: "{#HotKey}"

[Run]
; FINISH-PAGE ORDER, a HomerDev rule (25 September 2026):
;   1. Install entries, ticked -- screen reader scripts first, then components
;      in alphabetical order.
;   2. Update entries, ticked, alphabetical.
;   3. Reinstall entries, UNTICKED, alphabetical.
;   4. Launch, ticked.
;   5. Open the user guide, unticked.
; Inno shows [Run] entries in script order and Check: hides the ones that do not
; apply, so three entries per component -- one per verb, each with its own
; Check: from Templates\HomerComponents.iss -- group the page by themselves.
; The label function words each one: "Install X 1.2 (what it is for)",
; "Update X from 1.1 to 1.2 (...)", "Reinstall X 1.2 (...)".
;
; AI NOTE FOR CUSTOMIZING: register each component once in InitializeSetup
; (see homerAdd below), then copy its three entries here into the three groups,
; keeping each group in alphabetical order. A model has Install and Reinstall
; only: ollama pull always fetches the current one.
;
; Scripts run DIRECTLY, with "noPause" as their argument -- never through a cmd
; wrapper with a "set X=1 &&" prefix, which cmd /s cannot quote correctly.

; ---- 1. Install ---------------------------------------------------------------
FileName: "{app}\exec\installScreenReaderSupport.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\exec"; \
  Description: "Install the JAWS scripts and the NVDA add-on for {#AppName}"; \
  Check: isFreshInstall; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\exec\installOllama.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\exec"; \
  Description: "{code:labelOllama}"; \
  Check: isInstallOllama; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\exec\installModels.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\exec"; \
  Description: "{code:labelModel}"; \
  Check: isModelInstall; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

; ---- 2. Update ----------------------------------------------------------------
FileName: "{app}\exec\installScreenReaderSupport.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\exec"; \
  Description: "Update the JAWS scripts and the NVDA add-on for {#AppName}"; \
  Check: isUpgradeOrSame; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\exec\installOllama.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\exec"; \
  Description: "{code:labelOllama}"; \
  Check: isUpdateOllama; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

; ---- 3. Reinstall, unticked ---------------------------------------------------
FileName: "{app}\exec\installOllama.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\exec"; \
  Description: "{code:labelOllama}"; \
  Check: isReinstallOllama; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated unchecked skipifdoesntexist

FileName: "{app}\exec\installModels.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\exec"; \
  Description: "{code:labelModel}"; \
  Check: isModelReinstall; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated unchecked skipifdoesntexist

; ---- 4. Launch, ticked --------------------------------------------------------
; The entry only leaves a marker. The program starts from CurStepChanged(ssDone),
; AFTER the Results box has been read and closed -- so the box is not hidden
; behind the program's own window. Inno runs postinstall entries before ssDone.
; TWO pairs of quotes: this Parameters value starts with a quote, which is the
; one case where cmd /s strips the outer pair correctly.
FileName: "{cmd}"; \
  Parameters: "/c echo launch > ""{localappdata}\{#AppName}\logs\{#AppName}_launch.flag"""; \
  Description: "Launch {#AppName} now (desktop hotkey: {#HotKeyDisplay})"; \
  Flags: postinstall skipifsilent runhidden runasoriginaluser

; ---- 5. Open the user guide, unticked -----------------------------------------
FileName: "{app}\ReadMe.htm"; \
  Description: "Open the user guide (F1 opens it inside {#AppName})"; \
  Flags: postinstall shellexec nowait skipifsilent skipifdoesntexist runasoriginaluser unchecked

[UninstallDelete]
; ONLY WHAT THIS PROGRAM WROTE. Never the whole {localappdata}\{#AppName}
; folder: every upgrade runs the uninstaller first, and a folder that may hold
; something a user installed or made is never removed wholesale. On
; 24 September 2026 a wholesale line here deleted Whisper on every HomerScribe
; upgrade.
Type: filesandordirs; Name: "{localappdata}\_APP_\logs"
Type: files; Name: "{localappdata}\_APP_\*.inix"

[Code]
//  WHAT THE CODE SECTION DOES, in one screen:
//    - registers the components this app needs, in the shared table from
//      Templates\HomerComponents.iss, which probes each once (winget, then a
//      file, then the exe, then the registry) and words every checkbox;
//    - reads the version of any previous install, so the screen reader
//      script entries say Install or Update truthfully;
//    - records which boxes were ticked when Finish is pressed, and after
//      the scripts have run, reports what happened to each of THOSE -- one
//      past-tense line per ticked box, nothing about the rest;
//    - keeps the setup log with the program's own logs;
//    - starts the program only after the Results box has been closed.
//
//  The include goes INSIDE [Code], and HomerComponents.iss carries no [Code]
//  header of its own. Comments inside [Code] use // or (* *), never ;.
#include "C:\HomerDev\Templates\HomerComponents.iss"

var
  iOllama: Integer;
  sActions: String;
  sPriorVersion: String;

//  AI NOTE FOR CUSTOMIZING: one homerAdd per component. Arguments: name,
//  winget ids (semicolon separated, or ''), an exe that answers --version,
//  a file that proves it (Inno constants allowed), three or four words of
//  use, and the uninstall registry key name (or ''). Add a var above for each.
function InitializeSetup(): Boolean;
begin
  iOllama := homerAdd('Ollama', 'Ollama.Ollama', 'ollama',
    '{localappdata}\Programs\Ollama\ollama.exe', 'runs the local AI model', 'Ollama');
  sPriorVersion := '';
  Result := True;
end;

//  ---- the previous install, for the screen reader script entries ----------
function priorVersion(): String;
var
  sKey, sFound: String;
begin
  Result := '';
  sKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';
  if RegQueryStringValue(HKLM, sKey, 'DisplayVersion', sFound) then Result := sFound
  else if RegQueryStringValue(HKCU, sKey, 'DisplayVersion', sFound) then Result := sFound;
end;

function isFreshInstall(): Boolean;
begin
  if sPriorVersion = '' then sPriorVersion := priorVersion();
  Result := (sPriorVersion = '');
end;

function isUpgradeOrSame(): Boolean;
begin
  Result := not isFreshInstall();
end;

function isOlderInstalled(): Boolean;
begin
  Result := False;
  if isFreshInstall() then exit;
  Result := ComparePackedVersion(PackVersionString(sPriorVersion),
                                 PackVersionString('{#AppVersion}')) < 0;
end;

//  ---- checkbox wording and visibility, one line each ----------------------
//  AI NOTE FOR CUSTOMIZING: three functions per component, one per verb, and
//  a label function; two per model. Name the model as installModels.cmd does.
function labelOllama(sParam: String): String;  begin Result := homerLabel(iOllama); end;
function isInstallOllama(): Boolean;           begin Result := homerIs(iOllama, 0); end;
function isUpdateOllama(): Boolean;            begin Result := homerIs(iOllama, 1); end;
function isReinstallOllama(): Boolean;         begin Result := homerIs(iOllama, 2); end;
function labelModel(sParam: String): String;   begin Result := homerModelLabel('qwen2.5:7b', 'works on your text', 'about 4.7 GB'); end;
function isModelInstall(): Boolean;            begin Result := homerModelIs('qwen2.5:7b', False); end;
function isModelReinstall(): Boolean;          begin Result := homerModelIs('qwen2.5:7b', True); end;

//  ---- the Results box: one line per ticked box, probed after the scripts ran
procedure addAction(sText: String);
begin
  if sText = '' then exit;
  if sActions <> '' then sActions := sActions + #13#10;
  sActions := sActions + '  ' + sText;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
//  Finish pressed: the boxes are settled, the scripts have not yet run.
begin
  Result := True;
  if CurPageID = wpFinished then homerNoteTicked();
end;

procedure startIfAsked();
//  Starts the program if the Launch box left its marker, and removes the marker.
//  Started from cmd so it runs as the person, not as the elevated installer.
var
  sFlag: String;
  iResult: Integer;
begin
  sFlag := ExpandConstant('{localappdata}\{#AppName}\logs\{#AppName}_launch.flag');
  if not FileExists(sFlag) then exit;
  DeleteFile(sFlag);
  Exec(ExpandConstant('{cmd}'),
       '/s /c ""' + ExpandConstant('{app}\exec\{#AppExeName}') + '""',
       ExpandConstant('{userdocs}'), SW_SHOW, ewNoWait, iResult);
end;

procedure reportWhatHappened();
var
  sBody: String;
begin
  //  AI NOTE FOR CUSTOMIZING: one addAction per component and per model, in
  //  the same alphabetical order as the [Run] section.
  addAction(homerOutcomeLine(iOllama));
  addAction(homerModelOutcomeLine('qwen2.5:7b', 'works on your text', 'about 4.7 GB'));
  sBody := '{#AppName} {#AppVersion} is installed.';
  if sActions <> '' then sBody := sBody + #13#10 + #13#10 + sActions;
  sBody := sBody + #13#10 + #13#10
         + 'Logs are kept in ' + ExpandConstant('{localappdata}\{#AppName}\logs') + '.';
  MsgBox(sBody, mbInformation, MB_OK);
  startIfAsked();
end;

//  ---- keep the setup log with the program's own logs ------------------------
//  Inno writes its log to the temporary folder, where nobody finds it. One
//  caveat: the installer runs elevated, so {localappdata} is the profile of
//  whoever answered the elevation prompt.
procedure keepSetupLog();
var
  sFolder, sTarget: String;
begin
  sFolder := ExpandConstant('{localappdata}\{#AppName}\logs');
  if not DirExists(sFolder) then
    if not ForceDirectories(sFolder) then exit;
  sTarget := sFolder + '\{#AppName}-setup-' + GetDateTimeString('yyyymmdd-hhnnss', #0, #0) + '.log';
  FileCopy(ExpandConstant('{log}'), sTarget, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssDone then
  begin
    keepSetupLog();
    reportWhatHappened();
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
//  Say on the welcome page what is about to happen, because a user reading by
//  ear should not have to work it out from a version number in a caption.
begin
  if CurPageID = wpWelcome then
  begin
    if isFreshInstall() then
      WizardForm.WelcomeLabel1.Caption := 'Install {#AppName} {#AppVersion}'
    else if isOlderInstalled() then
      WizardForm.WelcomeLabel1.Caption := 'Update {#AppName} from ' + sPriorVersion + ' to {#AppVersion}'
    else
      WizardForm.WelcomeLabel1.Caption := 'Reinstall {#AppName} {#AppVersion}';
  end;
end;
