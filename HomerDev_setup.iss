; HomerDev_setup.iss -- installer for the Homer Development Kit, built from FileDir's, which follows the HomerDev
; template with the most components of any Homer app.
;
; WHAT IS HOMERDEV'S OWN HERE, against FileDir's: the whole kit is the file list, so a person has every template,
; skill, script, sample and document in a standard place; every component any Homer app offers is on the finish page
; -- seventeen, alphabetical, the book tools and the developer's own tools included, plus the local AI model the HomerDev dialog's chat uses -- so one install sets a computer up
; for all of them; there are no JAWS scripts or NVDA add-on, since the kit has none of its own; and the HomerDev
; variable is set for the whole machine when it is not set already, so app builds find the kit in Program Files.
; Someone who works at the command line may install to C:\HomerDev instead, so the paths are shorter to type.
;
; Everything else -- machine wide, administrator, version from version.txt, the Install, Update and Reinstall wording,
; the Results box before the launch, the setup log kept with the program's logs -- is the shared pattern, unchanged.

#define AppName       "HomerDev"

#define VerFile FileOpen(AddBackslash(SourcePath) + "version.txt")
#define AppVersion Trim(FileRead(VerFile))
#expr FileClose(VerFile)
#undef VerFile

#define AppPublisher  "Jamal Mazrui"
#define AppUrl        "https://github.com/JamalMazrui/HomerDev"
#define AppExeName    "HomerDev.exe"
#define AppCopyright  "Copyright (c) 2026 Jamal Mazrui. MIT License."

; The desktop shortcut's hotkey. HotKey is the Inno Setup directive
; value, which requires Ctrl syntax; HotKeyDisplay is the same key in the
; notation a person reads -- Control rather than Ctrl, modifiers in alphabetical
; order. Alt+Control+key space belongs to desktop shortcuts, and a shortcut's own
; hotkey is the sanctioned use of it, so it is the right space to take here.
; Alt+Control+Shift+D: D for development. The H keys, with and without Shift, are HomerScribe's and HomerView's,
; and Alt+Control+D is DbDo's.
#define HotKey        "Alt+Ctrl+Shift+D"
#define HotKeyDisplay "Alt+Control+Shift+D"

[Setup]
; The AppId is the name, as FileDir's is, so every later setup recognizes the copy already installed.
AppId=HomerDev

AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
AppUpdatesURL={#AppUrl}/releases
AppCopyright={#AppCopyright}

; The version resource of the built setup. release reads the FileVersion
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

; THE INSTALLER IS WRITTEN TO THE TOP OF THE PROJECT, as in every Homer app:
; scripts\release looks for it there, and LocalFiles.txt names it, so tidy
; leaves it in place and git never takes it. Written into exec until
; 26 September 2026, when the release stopped with "FileDir_setup.exe not
; found".
OutputDir=.
OutputBaseFilename={#AppName}_setup
SolidCompression=yes
LicenseFile=
WizardStyle=modern
Compression=lzma2/max
MinVersion=10.0
AppComments=The Homer Development Kit: templates, skills, samples and shared code for building accessible programs with AI.
; THE MACHINE-WIDE HomerDev VARIABLE is written below in [Registry], so Windows is told when setup ends.
ChangesEnvironment=yes

SetupIconFile=HomerDev.ico

PrivilegesRequired=admin
; THE PER-USER AREAS ARE USED ON PURPOSE, so the warning about them is off. The
; setup log and the launch marker go to the profile of whoever answered the
; elevation prompt, which on a machine one person uses is that person -- and the
; template says so where it uses them.
UsedUserAreasWarning=no
PrivilegesRequiredOverridesAllowed=

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

Uninstallable=yes
UninstallDisplayIcon={app}\exec\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%n[name] -- the Homer Development Kit -- is licensed under the MIT License: free to use, copy, modify, and distribute; provided "as is" with no warranty. The full license is installed as License.htm in the program folder.%n%nIt is recommended that you close all other applications before continuing.

[Dirs]
; THE KIT'S OWN LAYOUT, as in C:\HomerDev; every folder is in the file list below.

[Files]
; THE WHOLE KIT, as the repository holds it, plus what its build makes: HomerDev.exe and Homer.dll in exec, the
; samples' programs, the tutorials' audio. Left out: what is never shipped -- logs, notes, git's own folder,
; Python's virtual environments and caches, PyInstaller's work folders, the fingerprint store -- and this setup
; program itself. Each folder keeps its place, so a skill finds its references and a build finds the kit's code.
Source: "*"; DestDir: "{app}"; Excludes: "\logs\*,\notes\*,.git,.venv,venv,__pycache__,*.pyc,\HomerDev_setup.exe,\HomerDev_setup.building.exe,\build_release.bat,\Templates\samples\build,\Templates\samples\dist,\Samples,warn-*.txt,xref-*.html,*.toc,*.pyz,*.pkg,\exec\fingerprints.json,\exec\fingerprints.json.tmp"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; HomerDev, FOR THE WHOLE MACHINE, ONLY WHEN IT IS NOT SET: every app's build looks for the kit by this variable
; first. A developer who keeps a working copy, such as C:\HomerDev, already has it pointing there, and setup must not
; send that developer's builds to the installed copy instead, so an existing value is left exactly as it is.
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "HomerDev"; ValueData: "{app}"; Flags: preservestringtype uninsdeletevalue; Check: isHomerDevUnset

[Icons]
; The documents stay at the root of the installed tree, where somebody looking
; for the ReadMe expects them. Everything that runs is one folder down.
Name: "{group}\{#AppName}"; Filename: "{app}\exec\{#AppExeName}"; WorkingDir: "{userdocs}"
Name: "{group}\{#AppName} documentation"; Filename: "{app}\ReadMe.htm"; Flags: createonlyiffileexists
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\exec\{#AppExeName}"; WorkingDir: "{userdocs}"; IconFilename: "{app}\HomerDev.ico"; HotKey: "{#HotKey}"; Comment: "Open the HomerDev dialog ({#HotKeyDisplay})"

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

; ---- 1. Install, ticked --------------------------------------------------------
; Alphabetical by name; each worded Install, Update or Reinstall by its state (help\FinishPage.md).
FileName: "{app}\scripts\installAce.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelAce}"; \
  Check: isInstallAce; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installEpubCheck.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelEpubCheck}"; \
  Check: isInstallEpubCheck; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installExifTool.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelExifTool}"; \
  Check: isInstallExifTool; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installFfmpeg.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelFfmpeg}"; \
  Check: isInstallFfmpeg; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installGit.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelGit}"; \
  Check: isInstallGit; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installGitHubCli.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelGitHubCli}"; \
  Check: isInstallGitHubCli; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installImageMagick.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelImageMagick}"; \
  Check: isInstallImageMagick; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installJava.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelJava}"; \
  Check: isInstallJava; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installMpv.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelMpv}"; \
  Check: isInstallMpv; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installNode.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelNode}"; \
  Check: isInstallNode; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installOllama.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelOllama}"; \
  Check: isInstallOllama; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installPandoc.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPandoc}"; \
  Check: isInstallPandoc; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installPdfTools.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPdfTools}"; \
  Check: isInstallPdfTools; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installPython.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPython}"; \
  Check: isInstallPython; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installTesseract.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelTesseract}"; \
  Check: isInstallTesseract; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installWhisper.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelWhisper}"; \
  Check: isInstallWhisper; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installYtDlp.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelYtDlp}"; \
  Check: isInstallYtDlp; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installModels.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelModel}"; \
  Check: isModelInstall; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

; ---- 2. Update, ticked ---------------------------------------------------------
FileName: "{app}\scripts\installAce.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelAce}"; \
  Check: isUpdateAce; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installEpubCheck.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelEpubCheck}"; \
  Check: isUpdateEpubCheck; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installExifTool.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelExifTool}"; \
  Check: isUpdateExifTool; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installFfmpeg.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelFfmpeg}"; \
  Check: isUpdateFfmpeg; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installGit.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelGit}"; \
  Check: isUpdateGit; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installGitHubCli.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelGitHubCli}"; \
  Check: isUpdateGitHubCli; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installImageMagick.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelImageMagick}"; \
  Check: isUpdateImageMagick; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installJava.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelJava}"; \
  Check: isUpdateJava; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installMpv.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelMpv}"; \
  Check: isUpdateMpv; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installNode.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelNode}"; \
  Check: isUpdateNode; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installOllama.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelOllama}"; \
  Check: isUpdateOllama; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installPandoc.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPandoc}"; \
  Check: isUpdatePandoc; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installPdfTools.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPdfTools}"; \
  Check: isUpdatePdfTools; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installPython.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPython}"; \
  Check: isUpdatePython; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installTesseract.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelTesseract}"; \
  Check: isUpdateTesseract; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installWhisper.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelWhisper}"; \
  Check: isUpdateWhisper; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

FileName: "{app}\scripts\installYtDlp.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelYtDlp}"; \
  Check: isUpdateYtDlp; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist

; ---- 3. Reinstall, unticked -----------------------------------------------------
FileName: "{app}\scripts\installAce.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelAce}"; \
  Check: isReinstallAce; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installEpubCheck.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelEpubCheck}"; \
  Check: isReinstallEpubCheck; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installExifTool.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelExifTool}"; \
  Check: isReinstallExifTool; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installFfmpeg.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelFfmpeg}"; \
  Check: isReinstallFfmpeg; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installGit.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelGit}"; \
  Check: isReinstallGit; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installGitHubCli.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelGitHubCli}"; \
  Check: isReinstallGitHubCli; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installImageMagick.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelImageMagick}"; \
  Check: isReinstallImageMagick; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installJava.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelJava}"; \
  Check: isReinstallJava; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installMpv.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelMpv}"; \
  Check: isReinstallMpv; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installNode.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelNode}"; \
  Check: isReinstallNode; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installOllama.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelOllama}"; \
  Check: isReinstallOllama; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installPandoc.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPandoc}"; \
  Check: isReinstallPandoc; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installPdfTools.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPdfTools}"; \
  Check: isReinstallPdfTools; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installPython.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelPython}"; \
  Check: isReinstallPython; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installTesseract.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelTesseract}"; \
  Check: isReinstallTesseract; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installWhisper.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelWhisper}"; \
  Check: isReinstallWhisper; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installYtDlp.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelYtDlp}"; \
  Check: isReinstallYtDlp; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

FileName: "{app}\scripts\installModels.cmd"; \
  Parameters: "noPause"; \
  WorkingDir: "{app}\scripts"; \
  Description: "{code:labelModel}"; \
  Check: isModelReinstall; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated skipifdoesntexist unchecked

; ---- 4. Launch, ticked --------------------------------------------------------
; The entry only leaves a marker. The program starts from CurStepChanged(ssDone),
; AFTER the Results box has been read and closed -- so the box is not hidden
; behind the program's own window. Inno runs postinstall entries before ssDone.
; TWO pairs of quotes: this Parameters value starts with a quote, which is the
; one case where cmd /s strips the outer pair correctly.
FileName: "{cmd}"; \
  Parameters: "/c md ""{localappdata}\{#AppName}\logs"" 2>nul & echo launch > ""{localappdata}\{#AppName}\logs\{#AppName}_launch.flag"""; \
  Description: "Launch {#AppName} (desktop hotkey {#HotKeyDisplay})"; \
  Flags: postinstall skipifsilent runhidden runasoriginaluser

; ---- 5. Open the user guide, unticked -----------------------------------------
FileName: "{app}\help\HomerDev.htm"; \
  Description: "Open the user guide (F1 in {#AppName})"; \
  Flags: postinstall shellexec nowait skipifsilent skipifdoesntexist runasoriginaluser unchecked

[UninstallDelete]
; ONLY WHAT THIS PROGRAM WROTE. Never the whole {localappdata}\{#AppName}
; folder: every upgrade runs the uninstaller first, and a folder that may hold
; something a user installed or made is never removed wholesale. On
; 24 September 2026 a wholesale line here deleted Whisper on every HomerScribe
; upgrade.
Type: filesandordirs; Name: "{localappdata}\{#AppName}\logs"

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
// The kit comes from the build as /DHomerDev=; compiled by hand, C:\HomerDev.
// (Inside [Code] the language is Pascal: a comment starts with //, never ;.)
// The kit compiles its own installer, so the components file is beside this one, wherever the kit is.
#ifndef HomerDev
  #define HomerDev RemoveBackslash(SourcePath)
#endif
#include HomerDev + "\Templates\HomerComponents.iss"

var
  iAce, iEpubCheck, iExifTool, iFfmpeg, iGit, iGitHubCli, iImageMagick, iJava, iMpv, iNode, iOllama, iPandoc, iPdfTools, iPython, iTesseract, iWhisper, iYtDlp: Integer;
  sActions: String;
  sPriorVersion: String;

//  AI NOTE FOR CUSTOMIZING: one homerAdd per component. Arguments: name,
//  winget ids (semicolon separated, or ''), an exe that answers --version,
//  a file that proves it (Inno constants allowed), three or four words of
//  use, and the uninstall registry key name (or ''). Add a var above for each.
function InitializeSetup(): Boolean;
begin
  //  Each line: name, winget id, an exe that answers --version, a file that
  //  proves it, what it is for in a few words, and the uninstall key name.
  //  Machine-wide tools go to their own default folders; an app upgrade must
  //  never remove them, so none is under {app}.
  iAce := homerAdd('Ace by DAISY', '', 'ace',
    '{userappdata}\npm\ace.cmd', 'checks the accessibility of EPUB books', '');
  iEpubCheck := homerAdd('EPUBCheck', '', '',
    '{pf}\EPUBCheck\epubcheck.jar', 'validates EPUB books', '');
  iExifTool := homerAdd('ExifTool', 'OliverBetz.ExifTool;PhilHarvey.ExifTool', 'exiftool',
    '', 'reads what a recording or photo knows about itself', 'ExifTool');
  iFfmpeg := homerAdd('ffmpeg', 'Gyan.FFmpeg', 'ffmpeg',
    '', 'converts audio and video, with ffprobe', '');
  iGit := homerAdd('Git', 'Git.Git', 'git',
    '{pf}\Git\cmd\git.exe', 'keeps each project''s history', 'Git_is1');
  iGitHubCli := homerAdd('GitHub CLI', 'GitHub.cli', 'gh',
    '{pf}\GitHub CLI\gh.exe', 'publishes projects and releases to GitHub', '');
  iImageMagick := homerAdd('ImageMagick', 'ImageMagick.ImageMagick', 'magick',
    '', 'converts and resizes images', 'ImageMagick');
  iJava := homerAdd('Java', 'Microsoft.OpenJDK.21', '',
    '', 'runs EPUBCheck', '');
  iMpv := homerAdd('mpv', 'shinchiro.mpv', 'mpv',
    '{pf}\MPV Player\mpv.exe', 'plays audio and video, including the tutorials', 'mpv');
  iNode := homerAdd('Node.js', 'OpenJS.NodeJS.LTS;OpenJS.NodeJS', 'node',
    '{pf}\nodejs\node.exe', 'runs Ace by DAISY and other JavaScript tools', '');
  iOllama := homerAdd('Ollama', 'Ollama.Ollama', 'ollama',
    '{localappdata}\Programs\Ollama\ollama.exe', 'runs the local AI model', 'Ollama');
  iPandoc := homerAdd('Pandoc', 'JohnMacFarlane.Pandoc', 'pandoc',
    '{pf}\Pandoc\pandoc.exe', 'converts documents between formats', 'Pandoc');
  iPdfTools := homerAdd('PDF tools', 'Python.Python.3.13', 'python',
    '', 'reads PDF files as text, through Python', 'Python 3.13');
  iPython := homerAdd('Python', 'Python.Python.3.14;Python.Python.3.13', 'python',
    '', 'runs the kit''s scripts', '');
  iTesseract := homerAdd('Tesseract', 'UB-Mannheim.TesseractOCR', 'tesseract',
    '{pf}\Tesseract-OCR\tesseract.exe', 'reads scanned pages', 'Tesseract-OCR');
  iWhisper := homerAdd('Whisper', '', '"{pf}\Whisper\whisper-cli.exe"',
    '{pf}\Whisper\whisper-cli.exe', 'transcribes speech', '');
  iYtDlp := homerAdd('yt-dlp', 'yt-dlp.yt-dlp', 'yt-dlp',
    '', 'fetches audio and video from web pages', '');
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

//  versionPart: the Nth dotted number of a version, or 0 where there is none.
//  Written out rather than using PackVersionString, which this Inno Setup does
//  not have: the version check must not depend on the compiler's own version.
function versionPart(sVersion: String; iWanted: Integer): Integer;
var
  iAt, iPart: Integer;
  sNumber: String;
begin
  Result := 0;
  iPart := 1;
  sNumber := '';
  for iAt := 1 to Length(sVersion) do
  begin
    if sVersion[iAt] = '.' then
    begin
      if iPart = iWanted then begin Result := StrToIntDef(sNumber, 0); exit; end;
      iPart := iPart + 1;
      sNumber := '';
    end
    else if (sVersion[iAt] >= '0') and (sVersion[iAt] <= '9') then
      sNumber := sNumber + sVersion[iAt];
  end;
  if iPart = iWanted then Result := StrToIntDef(sNumber, 0);
end;

function versionIsOlder(sHave, sWant: String): Boolean;
var
  iPart, iHave, iWant: Integer;
begin
  Result := False;
  for iPart := 1 to 4 do
  begin
    iHave := versionPart(sHave, iPart);
    iWant := versionPart(sWant, iPart);
    if iHave < iWant then begin Result := True; exit; end;
    if iHave > iWant then exit;
  end;
end;

function isOlderInstalled(): Boolean;
begin
  Result := False;
  if isFreshInstall() then exit;
  Result := versionIsOlder(sPriorVersion, '{#AppVersion}');
end;

//  ---- checkbox wording and visibility, one line each ----------------------
//  AI NOTE FOR CUSTOMIZING: three functions per component, one per verb, and
//  a label function; two per model. Name the model as installModels.cmd does.
function labelAce(sParam: String): String;  begin Result := homerLabel(iAce); end;
function isInstallAce(): Boolean;           begin Result := homerIs(iAce, 0); end;
function isUpdateAce(): Boolean;            begin Result := homerIs(iAce, 1); end;
function isReinstallAce(): Boolean;         begin Result := homerIs(iAce, 2); end;
function labelEpubCheck(sParam: String): String;  begin Result := homerLabel(iEpubCheck); end;
function isInstallEpubCheck(): Boolean;           begin Result := homerIs(iEpubCheck, 0); end;
function isUpdateEpubCheck(): Boolean;            begin Result := homerIs(iEpubCheck, 1); end;
function isReinstallEpubCheck(): Boolean;         begin Result := homerIs(iEpubCheck, 2); end;
function labelExifTool(sParam: String): String;  begin Result := homerLabel(iExifTool); end;
function isInstallExifTool(): Boolean;           begin Result := homerIs(iExifTool, 0); end;
function isUpdateExifTool(): Boolean;            begin Result := homerIs(iExifTool, 1); end;
function isReinstallExifTool(): Boolean;         begin Result := homerIs(iExifTool, 2); end;
function labelFfmpeg(sParam: String): String;  begin Result := homerLabel(iFfmpeg); end;
function isInstallFfmpeg(): Boolean;           begin Result := homerIs(iFfmpeg, 0); end;
function isUpdateFfmpeg(): Boolean;            begin Result := homerIs(iFfmpeg, 1); end;
function isReinstallFfmpeg(): Boolean;         begin Result := homerIs(iFfmpeg, 2); end;
function labelGit(sParam: String): String;  begin Result := homerLabel(iGit); end;
function isInstallGit(): Boolean;           begin Result := homerIs(iGit, 0); end;
function isUpdateGit(): Boolean;            begin Result := homerIs(iGit, 1); end;
function isReinstallGit(): Boolean;         begin Result := homerIs(iGit, 2); end;
function labelGitHubCli(sParam: String): String;  begin Result := homerLabel(iGitHubCli); end;
function isInstallGitHubCli(): Boolean;           begin Result := homerIs(iGitHubCli, 0); end;
function isUpdateGitHubCli(): Boolean;            begin Result := homerIs(iGitHubCli, 1); end;
function isReinstallGitHubCli(): Boolean;         begin Result := homerIs(iGitHubCli, 2); end;
function labelImageMagick(sParam: String): String;  begin Result := homerLabel(iImageMagick); end;
function isInstallImageMagick(): Boolean;           begin Result := homerIs(iImageMagick, 0); end;
function isUpdateImageMagick(): Boolean;            begin Result := homerIs(iImageMagick, 1); end;
function isReinstallImageMagick(): Boolean;         begin Result := homerIs(iImageMagick, 2); end;
function labelJava(sParam: String): String;  begin Result := homerLabel(iJava); end;
function isInstallJava(): Boolean;           begin Result := homerIs(iJava, 0); end;
function isUpdateJava(): Boolean;            begin Result := homerIs(iJava, 1); end;
function isReinstallJava(): Boolean;         begin Result := homerIs(iJava, 2); end;
function labelMpv(sParam: String): String;  begin Result := homerLabel(iMpv); end;
function isInstallMpv(): Boolean;           begin Result := homerIs(iMpv, 0); end;
function isUpdateMpv(): Boolean;            begin Result := homerIs(iMpv, 1); end;
function isReinstallMpv(): Boolean;         begin Result := homerIs(iMpv, 2); end;
function labelNode(sParam: String): String;  begin Result := homerLabel(iNode); end;
function isInstallNode(): Boolean;           begin Result := homerIs(iNode, 0); end;
function isUpdateNode(): Boolean;            begin Result := homerIs(iNode, 1); end;
function isReinstallNode(): Boolean;         begin Result := homerIs(iNode, 2); end;
function labelOllama(sParam: String): String;  begin Result := homerLabel(iOllama); end;
function isInstallOllama(): Boolean;           begin Result := homerIs(iOllama, 0); end;
function isUpdateOllama(): Boolean;            begin Result := homerIs(iOllama, 1); end;
function isReinstallOllama(): Boolean;         begin Result := homerIs(iOllama, 2); end;
function labelPandoc(sParam: String): String;  begin Result := homerLabel(iPandoc); end;
function isInstallPandoc(): Boolean;           begin Result := homerIs(iPandoc, 0); end;
function isUpdatePandoc(): Boolean;            begin Result := homerIs(iPandoc, 1); end;
function isReinstallPandoc(): Boolean;         begin Result := homerIs(iPandoc, 2); end;
function labelPdfTools(sParam: String): String;  begin Result := homerLabel(iPdfTools); end;
function isInstallPdfTools(): Boolean;           begin Result := homerIs(iPdfTools, 0); end;
function isUpdatePdfTools(): Boolean;            begin Result := homerIs(iPdfTools, 1); end;
function isReinstallPdfTools(): Boolean;         begin Result := homerIs(iPdfTools, 2); end;
function labelPython(sParam: String): String;  begin Result := homerLabel(iPython); end;
function isInstallPython(): Boolean;           begin Result := homerIs(iPython, 0); end;
function isUpdatePython(): Boolean;            begin Result := homerIs(iPython, 1); end;
function isReinstallPython(): Boolean;         begin Result := homerIs(iPython, 2); end;
function labelTesseract(sParam: String): String;  begin Result := homerLabel(iTesseract); end;
function isInstallTesseract(): Boolean;           begin Result := homerIs(iTesseract, 0); end;
function isUpdateTesseract(): Boolean;            begin Result := homerIs(iTesseract, 1); end;
function isReinstallTesseract(): Boolean;         begin Result := homerIs(iTesseract, 2); end;
function labelWhisper(sParam: String): String;  begin Result := homerLabel(iWhisper); end;
function isInstallWhisper(): Boolean;           begin Result := homerIs(iWhisper, 0); end;
function isUpdateWhisper(): Boolean;            begin Result := homerIs(iWhisper, 1); end;
function isReinstallWhisper(): Boolean;         begin Result := homerIs(iWhisper, 2); end;
function labelYtDlp(sParam: String): String;  begin Result := homerLabel(iYtDlp); end;
function isInstallYtDlp(): Boolean;           begin Result := homerIs(iYtDlp, 0); end;
function isUpdateYtDlp(): Boolean;            begin Result := homerIs(iYtDlp, 1); end;
function isReinstallYtDlp(): Boolean;         begin Result := homerIs(iYtDlp, 2); end;
function labelModel(sParam: String): String;   begin Result := homerModelLabel('qwen2.5:7b', 'answers questions about HomerDev', 'about 4.7 GB'); end;
function isModelInstall(): Boolean;            begin Result := homerModelIs('qwen2.5:7b', False); end;
function isModelReinstall(): Boolean;          begin Result := homerModelIs('qwen2.5:7b', True); end;

//  isHomerDevUnset: True when no machine-wide HomerDev variable exists, so setup may write one. An existing value --
//  a developer's own working copy -- is never replaced.
function isHomerDevUnset(): Boolean;
var
  sValue: String;
begin
  Result := not RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'HomerDev', sValue) or (Trim(sValue) = '');
end;

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
  addAction(homerScreenReaderOutcome());
  addAction(homerOutcomeLine(iExifTool));
  addAction(homerOutcomeLine(iffmpeg));
  addAction(homerOutcomeLine(iImageMagick));
  addAction(homerOutcomeLine(impv));
  addAction(homerOutcomeLine(iOllama));
  addAction(homerOutcomeLine(iPandoc));
  addAction(homerOutcomeLine(iPdfTools));
  addAction(homerOutcomeLine(iYtDlp));
  addAction(homerModelOutcomeLine('qwen2.5:7b', 'translates text', 'about 4.7 GB'));
  sBody := '{#AppName} {#AppVersion} is installed.';
  if sActions <> '' then sBody := sBody + #13#10 + #13#10 + sActions;
  sBody := sBody + #13#10 + #13#10
         + 'Logs are kept in ' + ExpandConstant('{localappdata}\{#AppName}\logs') + '.';
  homerResultsBox(sBody);
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
  CopyFile(ExpandConstant('{log}'), sTarget, False);
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
