; _APP__setup.iss -- installer for _APP_.
;
; This is the HomerDev TEMPLATE. newHomerApp.cmd writes a copy of it with
; _APP_ replaced by a real app name. Two things must be changed by hand
; afterwards, and both are marked CHANGE ME below: the AppId GUID and the
; desktop hotkey.
;
; The pattern is the one every Homer Tools installer follows: per-machine
; install under Program Files, no "who is this for" question, the destination
; page shown on a first install and hidden on a reinstall, a desktop shortcut
; with a hotkey, and optional extras as checkboxes on the final page.
;
; ---- Version -----------------------------------------------------------------
; The version number is NOT stored in this script. It lives in version.txt, one
; line, which build_APP_.cmd increments on every build. Inno reads it here, and
; the build script also generates Version.cs from it, so the program, the
; installer, and the release tag always report the same number. Because no
; version literal appears in this file, a stale copy of it cannot rewind the
; version.

#define AppName       "_APP_"

#define VerFile FileOpen(AddBackslash(SourcePath) + "version.txt")
#define AppVersion Trim(FileRead(VerFile))
#expr FileClose(VerFile)
#undef VerFile

#define AppPublisher  "Jamal Mazrui"
#define AppUrl        "https://github.com/JamalMazrui/_APP_"
#define AppExeName    "_APP_.exe"
#define AppCopyright  "Copyright (c) 2026 Jamal Mazrui. MIT License."

; CHANGE ME. The desktop shortcut's hotkey. HotKey is the Inno Setup
; directive value, which requires Ctrl syntax; HotKeyDisplay is the same key
; in the notation a person reads -- Control rather than Ctrl, modifiers in
; alphabetical order. Check it against the other Homer Tools before choosing:
; Alt+Control+key space is reserved for desktop shortcuts, and a shortcut's
; own hotkey is the sanctioned use of it.
#define HotKey        "Alt+Ctrl+X"
#define HotKeyDisplay "Alt+Control+X"

[Setup]
; CHANGE ME. A fresh GUID, unique to this app, generated once and never
; changed afterwards: it is what lets an upgrade find the previous install.
; In PowerShell: [guid]::NewGuid()
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

; Install under Program Files. {autopf} resolves to "Program Files" on 64-bit
; Windows when the installer runs in 64-bit mode, per ArchitecturesInstallIn64BitMode.
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UsePreviousAppDir=yes

; Hide the destination page when a previous install of the same AppId is found:
; a reinstall then asks nothing at all and goes where the last one went. A first
; install still chooses the folder.
DisableDirPage=auto
UsePreviousGroup=yes

OutputDir=.
OutputBaseFilename={#AppName}_setup
SolidCompression=yes
; Empty on purpose: no license page. The license travels with the program and is
; on the Start menu, but it is not a gate on the way in.
LicenseFile=
WizardStyle=modern
Compression=lzma2/max
MinVersion=10.0
AppComments=A Homer Tools program for keyboard and screen-reader users.

#if FileExists(AddBackslash(SourcePath) + "_APP_.ico")
SetupIconFile={#AppName}.ico
#endif

; Admin, to write to Program Files. PrivilegesRequiredOverridesAllowed is left
; EMPTY on purpose: that is what removes the "install for me only or for all
; users" page that Inno shows first when the choice is offered. Anyone wanting
; a portable copy uses the zip instead.
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=

; 64-bit Windows only.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

Uninstallable=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Every line below the program itself carries skipifsourcedoesntexist. Only the
; executable is genuinely required; a missing document must not abort a build,
; and a wildcard matching nothing is a fatal error in Inno unless the line says
; otherwise.
;
; Both forms of the documentation travel: Markdown for reading in an editor or
; on a braille display, and HTML for opening in a browser, which is what the
; shortcuts point at.
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
; Settings and hotkey definitions, when the app ships defaults for them.
Source: "_APP_.inix"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP__hotkeys.inix"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
; Any DLL the program needs beside it. Nothing matches on a single-file build,
; which is why the flag is there.
Source: "*.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "_APP_.exe.config"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
; LOCAL AI. More than one Homer app now uses a model running on the user's own
; machine, so these two scripts are part of the kit and every app that can use
; AI ships them. An app that calls no model deletes these two lines and the two
; [Run] entries that go with them.
Source: "installOllama.cmd"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "installModels.cmd"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; WorkingDir is the user's Documents folder, so a run started from a shortcut
; writes its results somewhere writable by default.
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{userdocs}"
Name: "{group}\{#AppName} documentation"; Filename: "{app}\ReadMe.htm"; Flags: createonlyiffileexists
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
; Created without asking. The hotkey is mentioned on the launch checkbox at the
; end, which is where the user is looking when it matters.
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{userdocs}"; HotKey: "{#HotKey}"

[Run]
; Post-install checkboxes on the final wizard page, in the order they are
; offered: what the program needs first, then what to do next. runascurrentuser
; matters -- winget and Ollama install into the profile of whoever is signed in,
; and this installer is running elevated.
;
; LOCAL AI. The first two boxes are the kit default for any app that can use a
; model. Both are shown every time rather than hidden when the component is
; already there: the scripts themselves notice in a second and say so, and a
; checkbox that sometimes vanishes is worse than one that occasionally has
; nothing to do. The Ollama box is CHECKED when the program cannot do its main
; job without a model, and UNCHECKED when the model only adds something; change
; the flags on that one line to say which this app is.
;
; AI NOTE FOR CUSTOMIZING: edit the size and the description in these two
; Description strings to match the model named in installOllama.cmd, then add
; one more block per extra component (Pandoc, Tesseract, Whisper, ffmpeg) in the
; same shape.
FileName: "{cmd}"; \
  Parameters: "/c """"{app}\installOllama.cmd"""""; \
  WorkingDir: "{app}"; \
  Description: "Install Ollama and the local AI model, so the program can work on your text on this machine (about 2 GB; nothing is uploaded)"; \
  Flags: postinstall skipifsilent runascurrentuser skipifdoesntexist

FileName: "{cmd}"; \
  Parameters: "/c """"{app}\installModels.cmd"""""; \
  WorkingDir: "{app}"; \
  Description: "Install the model only (tick this if Ollama is already on this machine)"; \
  Flags: postinstall skipifsilent runascurrentuser unchecked skipifdoesntexist

FileName: "{app}\{#AppExeName}"; \
  WorkingDir: "{userdocs}"; \
  Description: "Launch {#AppName} now (desktop hotkey: {#HotKeyDisplay})"; \
  Flags: nowait postinstall skipifsilent

FileName: "{app}\ReadMe.htm"; \
  Description: "Read documentation for {#AppName}"; \
  Flags: postinstall shellexec skipifsilent skipifdoesntexist

[UninstallDelete]
; The settings and working files, so nothing of the program is left behind.
; What the user made with it is never touched: it lives where they put it.
Type: filesandordirs; Name: "{localappdata}\_APP_"
