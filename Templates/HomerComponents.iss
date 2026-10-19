// HomerComponents.iss -- shared component detection for Homer installers.
//
//   #include "C:\HomerDev\Inno\HomerComponents.iss"
//
// A FAITHFUL PORT OF WHAT ALREADY WORKS. EdSharp and FileDir have got this
// right for months; HomerScribe kept getting it wrong because I wrote my own
// instead of reading theirs. Three things I was missing, and each one caused a
// component he already had to be offered as "Install":
//
//   1. SEVERAL WINGET IDS PER COMPONENT. A tool can register under more than
//      one id -- Node from the plain download is OpenJS.NodeJS, from winget it
//      is OpenJS.NodeJS.LTS -- so every id is tried before giving up.
//   2. ASK THE EXECUTABLE ITSELF. A tool installed by its own installer, or by
//      an MSI, is invisible to `winget list`. `<exe> --version` still answers,
//      and an install winget does not know about is still an install.
//   3. THE REMOTE VERSION EVEN WHEN NOTHING IS INSTALLED. `winget show` gives
//      the latest version, so "Install X 1.8.4" carries a number in parallel
//      with "Update X from 1.8.2 to 1.8.4".
//
// THE TABLE. An app registers each component once, in InitializeWizard, and
// quotes the returned index in its Check: and {code:} expressions. Nothing
// about a component is written twice.
//
// THE THREE STATES, and what each means for the finish page:
//   0 absent    "Install X <latest>"                TICKED
//   1 outdated  "Update X from <old> to <new>"      TICKED
//   2 current   "Reinstall X <version>"             unticked
//
// Pressing Enter therefore installs everything missing and updates everything
// stale, and reinstalls nothing already current.

// NO [Code] LINE HERE. This file is #included FROM INSIDE the app's own [Code]
// section, so declaring one of its own started a second section: everything
// after the include reverted to [Setup], and the app's real [Code] section
// later in the file replaced these functions rather than adding to them. The
// compiler then reported "Unknown identifier 'homerAdd'" while the definitions
// sat right there in the log, included and read.

type
  THomerComponent = record
    sName:    String;   (* shown to a person: "Whisper" *)
    sIdList:  String;   (* winget ids, semicolon separated; may be empty *)
    sExe:     String;   (* an executable that answers --version *)
    sFile:    String;   (* a path that proves it, Inno constants allowed *)
    sUse:     String;   (* three or four words: "transcribes speech" *)
    sRegKey:  String;   (* uninstall key name, e.g. "Ollama"; "" if none *)
    iState:   Integer;
    sLocal:   String;
    sRemote:  String;
    bKnown:   Boolean;
    (* the same three, probed again after the finish-page scripts have run *)
    iStateAfter: Integer;
    sLocalAfter: String;
    bKnownAfter: Boolean;
  end;

var
  gHomer: array of THomerComponent;
  (* captions of the finish-page boxes that were ticked when Finish was
     pressed, one per line -- see homerNoteTicked *)
  gHomerTicked: String;

function homerProbeLines(sCommand: String; var lsLines: TArrayOfString): Boolean;
var
  sTemp: String;
  iCode: Integer;
begin
  Result := False;
  sTemp := ExpandConstant('{tmp}\homerProbe.txt');
  if not Exec(ExpandConstant('{cmd}'), '/c ' + sCommand + ' > "' + sTemp + '" 2>&1',
              '', SW_HIDE, ewWaitUntilTerminated, iCode) then exit;
  Result := LoadStringsFromFile(sTemp, lsLines);
  DeleteFile(sTemp);
end;

function homerWingetInfo(sId: String; var sInstalled, sAvailable: String): Boolean;
(* True when winget lists the package. Columns are located from the header row,
   because package names contain spaces. *)
var
  lsLines: TArrayOfString;
  i, iVer, iAvail, iSrc: Integer;
  sLine: String;
begin
  Result := False; sInstalled := ''; sAvailable := '';
  iVer := 0; iAvail := 0; iSrc := 0;
  if sId = '' then exit;
  if not homerProbeLines('winget list --id ' + sId + ' --exact --disable-interactivity',
                         lsLines) then exit;
  for i := 0 to GetArrayLength(lsLines) - 1 do
  begin
    sLine := lsLines[i];
    if (iVer = 0) and (Pos('Name', sLine) > 0) and (Pos('Version', sLine) > 0) then
    begin
      iVer := Pos('Version', sLine);
      iAvail := Pos('Available', sLine);
      iSrc := Pos('Source', sLine);
      continue;
    end;
    if (iVer > 0) and (Pos(sId, sLine) > 0) then
    begin
      Result := True;
      if iAvail > 0 then
      begin
        sInstalled := Trim(Copy(sLine, iVer, iAvail - iVer));
        if iSrc > iAvail then sAvailable := Trim(Copy(sLine, iAvail, iSrc - iAvail))
        else sAvailable := Trim(Copy(sLine, iAvail, 200));
      end
      else if iSrc > iVer then sInstalled := Trim(Copy(sLine, iVer, iSrc - iVer))
      else sInstalled := Trim(Copy(sLine, iVer, 200));
      exit;
    end;
  end;
end;

function homerWingetLatest(sId: String): String;
(* The newest version winget offers, installed or not, so an Install label can
   carry a number as an Update label does. *)
var
  lsLines: TArrayOfString;
  i: Integer;
  sLine: String;
begin
  Result := '';
  if sId = '' then exit;
  if not homerProbeLines('winget show --id ' + sId + ' --exact --disable-interactivity',
                         lsLines) then exit;
  for i := 0 to GetArrayLength(lsLines) - 1 do
  begin
    sLine := Trim(lsLines[i]);
    if Pos('Version:', sLine) = 1 then
    begin
      Result := Trim(Copy(sLine, 9, 100));
      exit;
    end;
  end;
end;

function homerExeVersion(sExe: String): String;
(* What the tool says about itself. This is what catches an install winget has
   never heard of -- and it is the check HomerScribe was missing when it kept
   offering to install things he already had. *)
var
  lsLines: TArrayOfString;
  i: Integer;
begin
  Result := '';
  if sExe = '' then exit;
  if not homerProbeLines(sExe + ' --version', lsLines) then exit;
  for i := 0 to GetArrayLength(lsLines) - 1 do
    if Trim(lsLines[i]) <> '' then
    begin
      Result := Trim(lsLines[i]);
      exit;
    end;
end;

// ---- versions read from a program found by its file (15 October 2026) ------
// winget lists only what it installed. DbDo 1.0.287 found mpv by its file under
// Program Files, which winget had not installed, and stopped there: its log said
// "its version could not be read", and the box could only ever say Reinstall.
// These three ask the program itself and compare the answer with the newest
// release winget offers, so a stale copy is offered as Update.

function homerVersionIn(sText: String): String;
(* The first version number in a line: digits joined by dots, with at least one
   dot. "mpv v0.40.0-dirty Copyright 2000-2025" gives 0.40.0. Empty if none. *)
var
  bDot: Boolean;
  i, iLength, iStart: Integer;
begin
  Result := '';
  iLength := Length(sText);
  i := 1;
  while i <= iLength do
  begin
    if (sText[i] >= '0') and (sText[i] <= '9') then
    begin
      iStart := i;
      bDot := False;
      while i <= iLength do
      begin
        if (sText[i] >= '0') and (sText[i] <= '9') then
          i := i + 1
        else if (sText[i] = '.') and (i < iLength) then
        begin
          if (sText[i + 1] >= '0') and (sText[i + 1] <= '9') then
          begin
            bDot := True;
            i := i + 1;
          end
          else break;
        end
        else break;
      end;
      if bDot then
      begin
        Result := Copy(sText, iStart, i - iStart);
        exit;
      end;
    end
    else i := i + 1;
  end;
end;

function homerVersionPart(var sRest: String): Integer;
(* The next dot-separated number, taken off the front of sRest; -1 when none is left. *)
var
  iDot: Integer;
begin
  Result := -1;
  if sRest = '' then exit;
  iDot := Pos('.', sRest);
  if iDot = 0 then
  begin
    Result := StrToIntDef(sRest, 0);
    sRest := '';
  end
  else
  begin
    Result := StrToIntDef(Copy(sRest, 1, iDot - 1), 0);
    sRest := Copy(sRest, iDot + 1, 100);
  end;
end;

function homerVersionOrder(sOne, sTwo: String): Integer;
(* -1 when sOne is older than sTwo, 0 the same, 1 newer; 2 when they cannot be
   compared -- either is empty, or one is a dated build (a first number of 1000
   or more) and the other a numbered release -- so no box gets its verb on a guess. *)
var
  iOne, iTwo: Integer;
begin
  Result := 2;
  if (sOne = '') or (sTwo = '') then exit;
  iOne := homerVersionPart(sOne);
  iTwo := homerVersionPart(sTwo);
  if (iOne >= 1000) <> (iTwo >= 1000) then exit;
  while True do
  begin
    if iOne < iTwo then begin Result := -1; exit; end;
    if iOne > iTwo then begin Result := 1; exit; end;
    if (sOne = '') and (sTwo = '') then begin Result := 0; exit; end;
    iOne := homerVersionPart(sOne);
    iTwo := homerVersionPart(sTwo);
    if iOne < 0 then iOne := 0;
    if iTwo < 0 then iTwo := 0;
  end;
end;

function homerFileVersion(sPath: String): String;
(* The version a program at a full path gives for --version, as a number. TWO
   PAIRS OF QUOTES: cmd /c strips the outermost pair, which leaves the quoted
   Program Files path whole. *)
var
  lsLines: TArrayOfString;
  i, iCode: Integer;
  sTemp: String;
begin
  Result := '';
  if (sPath = '') or (not FileExists(sPath)) then exit;
  // A VERSION.TXT BESIDE THE FILE ANSWERS FIRST (kit 1.78.2). EPUBCheck is a .jar with no --version an
  // installer can run, so its version was never known ("its version could not be read" at every install).
  // Its install script writes version.txt beside the jar; any component whose script does the same is read
  // the same way. Only a program, .exe or .cmd, is asked for --version.
  sTemp := ExtractFilePath(sPath) + 'version.txt';
  if FileExists(sTemp) and LoadStringsFromFile(sTemp, lsLines) then
    for i := 0 to GetArrayLength(lsLines) - 1 do
      if homerVersionIn(lsLines[i]) <> '' then
      begin
        Result := homerVersionIn(lsLines[i]);
        exit;
      end;
  if (CompareText(ExtractFileExt(sPath), '.exe') <> 0) and (CompareText(ExtractFileExt(sPath), '.cmd') <> 0) then exit;
  sTemp := ExpandConstant('{tmp}\homerVersion.txt');
  if not Exec(ExpandConstant('{cmd}'), '/c ""' + sPath + '" --version > "' + sTemp + '" 2>&1"',
              '', SW_HIDE, ewWaitUntilTerminated, iCode) then exit;
  if LoadStringsFromFile(sTemp, lsLines) then
    for i := 0 to GetArrayLength(lsLines) - 1 do
      if homerVersionIn(lsLines[i]) <> '' then
      begin
        Result := homerVersionIn(lsLines[i]);
        break;
      end;
  DeleteFile(sTemp);
end;

function homerAdd(sName, sIdList, sExe, sFile, sUse, sRegKey: String): Integer;
(* Register one component and get its index back. Call these from
   InitializeWizard, in any order -- homerOrder sorts them for display. *)
var
  iAt: Integer;
begin
  iAt := GetArrayLength(gHomer);
  SetArrayLength(gHomer, iAt + 1);
  gHomer[iAt].sName := sName;
  gHomer[iAt].sIdList := sIdList;
  gHomer[iAt].sExe := sExe;
  gHomer[iAt].sFile := sFile;
  gHomer[iAt].sUse := sUse;
  gHomer[iAt].sRegKey := sRegKey;
  gHomer[iAt].bKnown := False;
  Result := iAt;
end;

function homerNextId(var sRest: String): String;
(* Pull the next semicolon-separated id off the list. *)
var
  iSplit: Integer;
begin
  iSplit := Pos(';', sRest);
  if iSplit > 0 then
  begin
    Result := Copy(sRest, 1, iSplit - 1);
    sRest := Copy(sRest, iSplit + 1, 500);
  end
  else
  begin
    Result := sRest;
    sRest := '';
  end;
end;

function homerState(iAt: Integer): Integer;
(* 0 absent, 1 outdated, 2 current. Worked out once and remembered, because
   winget is slow enough that asking repeatedly shows as a pause.

   The order matters: every winget id first, then the FILE, then the EXE. A
   file that exists cannot lie; winget can be absent, slow or refused. *)
var
  iOrder: Integer;
  sAvailable, sId, sInstalled, sRest, sVersion: String;
begin
  Result := 0;
  if (iAt < 0) or (iAt >= GetArrayLength(gHomer)) then exit;
  if gHomer[iAt].bKnown then
  begin
    Result := gHomer[iAt].iState;
    exit;
  end;

  sRest := gHomer[iAt].sIdList;
  while (Result = 0) and (sRest <> '') do
  begin
    sId := homerNextId(sRest);
    if homerWingetInfo(sId, sInstalled, sAvailable) then
    begin
      gHomer[iAt].sLocal := sInstalled;
      gHomer[iAt].sRemote := sAvailable;
      if sAvailable <> '' then Result := 1
      else
      begin
        Result := 2;
        // WINGET'S SILENCE IS AN ANSWER (kit 1.77.7, from Jamal's setup logs of 19 October
        // 2026). winget list fills its Available column only when an upgrade exists, so a
        // package it lists with nothing there is the newest winget knows. That is a real
        // comparison; 17 of 19 components were logged "no newer version could be looked up"
        // when each was in fact current, as ImageMagick showed: Update on 18 October, then this.
        gHomer[iAt].sRemote := sInstalled;
      end;
    end;
  end;

  (* Installed outside winget's knowledge still counts as installed: offer a
     reinstall, not a second copy. *)
  if (Result = 0) and (gHomer[iAt].sFile <> '')
     and FileExists(ExpandConstant(gHomer[iAt].sFile)) then Result := 2;

  // THE REGISTRY, which DbDo checked and I had dropped. The installer runs
  // ELEVATED, and in that context winget is often not reachable at all and a
  // per-user tool like Ollama is not on the PATH -- so the two probes above
  // can both come back empty for something plainly installed. The uninstall
  // key is written by the component's own installer and is readable from
  // anywhere. This is what stopped Ollama being offered as "Install" on a
  // machine that runs it every day.
  if (Result = 0) and (gHomer[iAt].sRegKey <> '') then
  begin
    if RegKeyExists(HKEY_LOCAL_MACHINE,
         'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + gHomer[iAt].sRegKey)
    or RegKeyExists(HKEY_CURRENT_USER,
         'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + gHomer[iAt].sRegKey)
    or RegKeyExists(HKEY_LOCAL_MACHINE,
         'Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\' + gHomer[iAt].sRegKey)
    then Result := 2;
  end;
  if Result = 0 then
  begin
    sVersion := homerExeVersion(gHomer[iAt].sExe);
    if sVersion <> '' then
    begin
      gHomer[iAt].sLocal := sVersion;
      Result := 2;
    end;
  end;

  // FOUND OUTSIDE WINGET, ITS VERSION IS STILL READ (15 October 2026): the program
  // found is asked, by its file when there is one, and compared with the newest
  // release winget offers; older is Update, ticked. Two numbers that cannot be
  // compared stay Reinstall, and the log says so. installCommon's wingetUpgrade
  // installs the newest release when winget knows no installed copy.
  if (Result = 2) and (gHomer[iAt].sLocal = '') then
  begin
    if (gHomer[iAt].sFile <> '') and FileExists(ExpandConstant(gHomer[iAt].sFile)) then
      gHomer[iAt].sLocal := homerFileVersion(ExpandConstant(gHomer[iAt].sFile))
    else
      gHomer[iAt].sLocal := homerVersionIn(homerExeVersion(gHomer[iAt].sExe));
    if gHomer[iAt].sLocal <> '' then
    begin
      sRest := gHomer[iAt].sIdList;
      if sRest <> '' then gHomer[iAt].sRemote := homerVersionIn(homerWingetLatest(homerNextId(sRest)));
      iOrder := homerVersionOrder(gHomer[iAt].sLocal, gHomer[iAt].sRemote);
      if iOrder = -1 then Result := 1;
      if (iOrder = 2) and (gHomer[iAt].sRemote <> '') then
      begin
        Log('Component ' + gHomer[iAt].sName + ': ' + gHomer[iAt].sLocal + ' found and '
            + gHomer[iAt].sRemote + ' offered, but the two cannot be compared');
        gHomer[iAt].sRemote := '';
      end;
    end;
  end;

  (* Nothing installed: fetch the version that WOULD be installed, so the
     Install label carries a number too. *)
  if Result = 0 then
  begin
    sRest := gHomer[iAt].sIdList;
    if sRest <> '' then gHomer[iAt].sRemote := homerWingetLatest(homerNextId(sRest));
  end;

  gHomer[iAt].iState := Result;
  gHomer[iAt].bKnown := True;
  // EVERY VERDICT IS LOGGED (1.43.20). Reinstalling all ten apps on 27
  // September left no record of why a box was ticked: only EdSharp and DbDo,
  // with their own probes, said what they found. Now the setup log -- the one
  // written with /LOG, copied to the app's logs folder -- names each
  // component, what was found, and the verb its box was given.
  case Result of
    0: Log('Component ' + gHomer[iAt].sName + ': not found; offered as Install ' + gHomer[iAt].sRemote);
    1: Log('Component ' + gHomer[iAt].sName + ': ' + gHomer[iAt].sLocal + ' found, '
           + gHomer[iAt].sRemote + ' available; offered as Update');
  else
    // "CURRENT" ONLY WHEN COMPARED (13 October 2026, from an audit): mpv and Whisper were
    // logged "found, current" with no version read at all. Reinstall is still the right
    // offer, unticked, but the log says what is actually known.
    if gHomer[iAt].sLocal = '' then
      Log('Component ' + gHomer[iAt].sName + ': found; its version could not be read, so whether a newer one exists is unknown; offered as Reinstall')
    else if gHomer[iAt].sRemote = '' then
      Log('Component ' + gHomer[iAt].sName + ': ' + gHomer[iAt].sLocal + ' found; no newer version could be looked up; offered as Reinstall')
    else
      Log('Component ' + gHomer[iAt].sName + ': ' + gHomer[iAt].sLocal + ' found, current (' + gHomer[iAt].sRemote + ' is the newest); offered as Reinstall');
  end;
end;

function homerIs(iAt, iState: Integer): Boolean;
(* The Check: for one of the three entries a component has on the finish
   page: 0 its Install entry, 1 its Update entry, 2 its Reinstall entry.

   THE FINISH-PAGE ORDER IS THE ORDER OF THE [Run] SECTION. Inno shows entries
   in script order and Check: hides those that do not apply, so an app writes
   every Install entry first (screen reader scripts before the rest, then
   components in alphabetical order), then every Update entry, then every
   Reinstall entry (with the unchecked flag), then Launch, then Open the user
   guide. Three entries per component, one per verb, and the page groups
   itself with no sorting code at all. *)
begin
  Result := homerState(iAt) = iState;
end;

function homerWanted(iAt: Integer): Boolean;
(* What a Check: expression uses. True when missing or stale -- the two cases
   where pressing Enter should act. *)
begin
  Result := homerState(iAt) <> 2;
end;

function homerMessageBox(hWnd: Integer; sText, sCaption: String; iType: Cardinal): Integer;
  external 'MessageBoxW@user32.dll stdcall';

(* THE DEFAULTS SWITCH. setup.exe /verysilent /defaults installs with no screens
   and takes every default the finish page would: it runs each finish-page entry
   whose box is ticked by default -- Install and Update yes, Reinstall no, Launch
   yes, the user guide no -- and writes the Results box to the setup log. /silent
   /defaults does the same with a progress window. The switches are read without
   regard to case.
   ONLY WITH A SILENT SWITCH (13 October 2026). /defaults alone used to start
   setup again with /verysilent added, since Inno decides whether to show screens
   from the command line before any code runs and no code can change that for the
   run under way. The second start failed on DbDo with no reason given, and two
   installers never tried it, so all three showed every screen. That restart is
   gone: given alone, /defaults changes nothing, and the log says to add
   /verysilent. Plain /silent and /verysilent still install the program alone and
   run no entry. Each [Run] finish-page entry says Check: homerFinishRuns (and its
   own test) in place of skipifsilent; Inno itself then runs a ticked entry in a
   silent install, leaves an unticked one, and evaluates each entry's own Check as
   the finish page would. *)
function homerDefaults(): Boolean;
begin
  Result := Pos('/DEFAULTS', Uppercase(GetCmdTail)) > 0;
end;

function homerFinishRuns(): Boolean;
(* A finish-page entry may run: the page is shown, or /defaults stands in for it. *)
begin
  Result := (not WizardSilent) or homerDefaults();
end;

function homerStartForDefaults(): Boolean;
(* Called first in InitializeSetup; it starts nothing. Always False, so setup goes on. *)
begin
  Result := False;
  if homerDefaults() and not WizardSilent then
    Log('/defaults: every page that can be skipped is skipped, each keeping its default; the finish page shows with its default boxes ticked, and Enter finishes. For no screens at all, run setup with /verysilent /defaults.');
end;

function ShouldSkipPage(PageID: Integer): Boolean;
(* /DEFAULTS ALONE TAKES THE DEFAULTS (14 October 2026, from an audit by another
   AI, after Jamal ran "setup /defaults" and got the whole wizard). Inno decides
   before any code runs whether a run is silent, so this cannot make the run
   silent; what it can do, from the command line and in Pascal, is skip every
   page Inno allows to be skipped -- each keeps its default, as if Next had been
   pressed on it. The finish page is kept: it is where the default boxes, ticked,
   run when Enter finishes, and skipping it is not something this kit has seen
   work. So /defaults alone is one Enter, not a wizard; /silent and /verysilent
   with /defaults still show nothing. No installer here defines this event
   itself; one that needs to must fold this rule into its own. *)
begin
  Result := homerDefaults() and (not WizardSilent) and (PageID <> wpFinished);
end;

procedure homerResultsBox(sBody: String);
(* THE RESULTS BOX HAS A TITLE (1.43.20): "<App> Setup Results". Inno's MsgBox
   takes none -- its caption is the wizard's own, so the box a screen reader
   announced was called "Setup", not "Results". Windows' own MessageBox takes a
   caption, and is otherwise the same OK box: information icon, one button.
   NOT IN A SILENT INSTALL (kit 1.72.12): /SUPPRESSMSGBOXES reaches only Inno's
   own boxes, so a /VERYSILENT install stopped here, waiting for an OK nobody
   could see. Silent, the results go to the setup log instead -- for /defaults,
   the box taken as read. *)
begin
  if WizardSilent then
  begin
    Log('Results (not shown: a silent install): ' + sBody);
    exit;
  end;
  homerMessageBox(WizardForm.Handle, sBody,
    '{#SetupSetting("AppName")} Setup Results', MB_OK or $40);  (* $40: the information icon *)
end;

function homerLabel(iAt: Integer): String;
(* The checkbox wording: the action first, a version, then three or four words
   saying what the component is for. A finish page is arrowed down, not
   studied, so nothing else belongs here. *)
var
  sUse: String;
begin
  sUse := '';
  if gHomer[iAt].sUse <> '' then sUse := ' (' + gHomer[iAt].sUse + ')';
  case homerState(iAt) of
    0:
      if gHomer[iAt].sRemote <> '' then
        Result := 'Install ' + gHomer[iAt].sName + ' ' + gHomer[iAt].sRemote + sUse
      else
        Result := 'Install ' + gHomer[iAt].sName + sUse;
    1:
      Result := 'Update ' + gHomer[iAt].sName + ' from ' + gHomer[iAt].sLocal
                + ' to ' + gHomer[iAt].sRemote + sUse;
  else
    if gHomer[iAt].sLocal <> '' then
      Result := 'Reinstall ' + gHomer[iAt].sName + ' ' + gHomer[iAt].sLocal + sUse
    else
      Result := 'Reinstall ' + gHomer[iAt].sName + sUse;
  end;
end;

function homerSummaryLine(iAt: Integer; sCost: String): String;
(* One line for the Results box, from the same probe as the checkbox, so the
   two cannot tell different stories. *)
begin
  case homerState(iAt) of
    0:
      Result := gHomer[iAt].sName + ' is not installed. ' + sCost;
    1:
      Result := gHomer[iAt].sName + ' ' + gHomer[iAt].sLocal + ' is installed; '
                + gHomer[iAt].sRemote + ' is available.';
  else
    if gHomer[iAt].sLocal <> '' then
      Result := gHomer[iAt].sName + ' ' + gHomer[iAt].sLocal + ' is installed and current.'
    else
      Result := gHomer[iAt].sName + ' is installed.';
  end;
end;

function homerGroup(iAt: Integer): Integer;
(* 1 Install, 2 Update, 3 Reinstall -- the order the finish page shows them:
   the ticked boxes first, then the unticked ones (FinishPage.md; 1.43.25, when
   this said Install, Reinstall, Update against that document). A number rather
   than a sort of the verbs, so rewording a label later cannot quietly change
   the order. *)
begin
  case homerState(iAt) of
    0: Result := 1;
    1: Result := 2;
  else Result := 3;
  end;
end;

function homerSortsBefore(iOne, iTwo: Integer): Boolean;
(* Group first, then the name, always case-insensitively. *)
begin
  if homerGroup(iOne) <> homerGroup(iTwo) then
  begin
    Result := homerGroup(iOne) < homerGroup(iTwo);
    exit;
  end;
  Result := CompareText(gHomer[iOne].sName, gHomer[iTwo].sName) < 0;
end;

function homerOrder(): String;
(* The indices in display order, comma separated. *)
var
  lOrder: array of Integer;
  i, j, iSwap, iCount: Integer;
begin
  iCount := GetArrayLength(gHomer);
  SetArrayLength(lOrder, iCount);
  for i := 0 to iCount - 1 do lOrder[i] := i;
  for i := 0 to iCount - 2 do
    for j := 0 to iCount - 2 - i do
      if homerSortsBefore(lOrder[j + 1], lOrder[j]) then
      begin
        iSwap := lOrder[j];
        lOrder[j] := lOrder[j + 1];
        lOrder[j + 1] := iSwap;
      end;
  Result := '';
  for i := 0 to iCount - 1 do
  begin
    if Result <> '' then Result := Result + ',';
    Result := Result + IntToStr(lOrder[i]);
  end;
end;


// ---- Ollama models ---------------------------------------------------------
// A model is not a program: winget knows nothing of it and there is no file to
// test for. `ollama list` says what is pulled. Asked once and remembered.

var
  gOllamaList: String;
  gOllamaListKnown: Boolean;
  gOllamaListAfter: String;
  gOllamaListAfterKnown: Boolean;

(* ---- JAWS scripts and NVDA add-on as components (1.43.43) ----------------
   Each is worded and ticked like any other component: Install when nothing of
   this app's is there, Update when what is there differs from what ships,
   Reinstall (unticked) when it is the same. installScreenReaderSupport.cmd
   decides, since only it can read a JAWS settings folder or an NVDA add-on;
   the answer is asked once per reader and kept. -1 means the reader is not on
   this computer, or the app ships nothing for it, and every box is hidden. *)
var
  gHomerJawsState, gHomerNvdaState: Integer;
  gHomerJawsRead, gHomerNvdaRead: Boolean;

//  THE APP'S OWN SCREEN READER SCRIPT, ASKED THE KIT'S WAY (10 October 2026). Most apps ship the kit's
//  installScreenReaderSupport.cmd. An app whose screen reader support needs more than unpacking and compiling --
//  HomerView chains its scripts into JAWS's defaults -- names its own script with #define HomerReaderScript before
//  this include; that script answers the same question in the same form ("state jaws <file>", writing install,
//  update or reinstall), so every installer's verbs and ticks come from this one function.
#ifndef HomerReaderScript
  #define HomerReaderScript "installScreenReaderSupport.cmd"
#endif
function homerReaderState(sReader: String): Integer;
var
  sFile, sScript: String;
  sAnswer: AnsiString;
  iCode: Integer;
begin
  if (sReader = 'jaws') and gHomerJawsRead then begin Result := gHomerJawsState; exit; end;
  if (sReader = 'nvda') and gHomerNvdaRead then begin Result := gHomerNvdaState; exit; end;
  Result := -1;
  sScript := ExpandConstant('{app}\scripts\{#HomerReaderScript}');
  sFile := ExpandConstant('{tmp}\homerReader_') + sReader + '.txt';
  if FileExists(sScript) then
    if Exec(ExpandConstant('{cmd}'), '/c ""' + sScript + '" state ' + sReader + ' "' + sFile + '""',
            ExpandConstant('{app}\scripts'), SW_HIDE, ewWaitUntilTerminated, iCode) then
      if LoadStringFromFile(sFile, sAnswer) then
      begin
        sAnswer := Trim(sAnswer);
        if sAnswer = 'install' then Result := 0
        else if sAnswer = 'update' then Result := 1
        else if sAnswer = 'reinstall' then Result := 2;
      end;
  Log('Component ' + sReader + ' scripts: state ' + IntToStr(Result) + ' (-1 not offered, 0 Install, 1 Update, 2 Reinstall)');
  if sReader = 'jaws' then begin gHomerJawsState := Result; gHomerJawsRead := True; end
  else begin gHomerNvdaState := Result; gHomerNvdaRead := True; end;
end;

function homerReaderIs(sReader: String; iWanted: Integer): Boolean;
begin
  Result := homerReaderState(sReader) = iWanted;
end;

function homerReaderLabel(sReader: String): String;
var
  sVerb, sWhat: String;
begin
  case homerReaderState(sReader) of
    1: sVerb := 'Update';
    2: sVerb := 'Reinstall';
  else sVerb := 'Install';
  end;
  if sReader = 'jaws' then sWhat := 'JAWS scripts' else sWhat := 'NVDA add-on';
  Result := sVerb + ' ' + sWhat;
end;

function homerScreenReaderFile(): String;
(* Where installScreenReaderSupport.cmd reports: beside the setup log. The
   script runs as the same account as the installer (runascurrentuser), so
   {localappdata} is the same folder for both. *)
begin
  Result := ExpandConstant('{localappdata}\{#SetupSetting("AppName")}\logs\{#SetupSetting("AppName")}_screenReaders.txt');
end;

procedure homerNoteTicked();
(* Call from NextButtonClick when CurPageID = wpFinished: that is the moment
   the finish page's boxes are settled and the scripts have not yet run. The
   Results box later reports on exactly these, and on nothing else -- a box
   nobody ticked is not an action taken this session. *)
var
  i: Integer;
begin
  gHomerTicked := '';
  for i := 0 to WizardForm.RunList.Items.Count - 1 do
    if WizardForm.RunList.Checked[i] then
      gHomerTicked := gHomerTicked + WizardForm.RunList.ItemCaption[i] + #10;
  //  A report left by an earlier install must not be read as this one's.
  DeleteFile(homerScreenReaderFile());
end;

function homerScreenReaderOutcome(): String;
(* The lines installScreenReaderSupport.cmd wrote this session -- one per JAWS
   version, and one for NVDA -- for the Results box: installed and compiled,
   or NOT installed with the reason (1.43.39). Empty when neither box was
   ticked. The file is removed once read. *)
var
  aLines: TArrayOfString;
  i: Integer;
begin
  Result := '';
  if not LoadStringsFromFile(homerScreenReaderFile(), aLines) then exit;
  for i := 0 to GetArrayLength(aLines) - 1 do
    if Trim(aLines[i]) <> '' then
    begin
      if Result <> '' then Result := Result + #13#10 + '  ';
      Result := Result + Trim(aLines[i]);
    end;
  DeleteFile(homerScreenReaderFile());
end;

function homerTicked(sCaption: String): Boolean;
begin
  Result := Pos(#10 + sCaption + #10, #10 + gHomerTicked) > 0;
end;

function homerStateAfter(iAt: Integer): Integer;
(* The state probed again NOW, after the scripts have run. The first probe is
   kept untouched, because the checkbox wording and the outcome wording both
   need to know what was true before. *)
var
  iState: Integer;
  sLocal, sRemote: String;
  bKnown: Boolean;
begin
  if not gHomer[iAt].bKnownAfter then
  begin
    iState := gHomer[iAt].iState; sLocal := gHomer[iAt].sLocal;
    sRemote := gHomer[iAt].sRemote; bKnown := gHomer[iAt].bKnown;
    gHomer[iAt].bKnown := False;
    gHomer[iAt].iStateAfter := homerState(iAt);
    gHomer[iAt].sLocalAfter := gHomer[iAt].sLocal;
    gHomer[iAt].bKnownAfter := True;
    gHomer[iAt].iState := iState; gHomer[iAt].sLocal := sLocal;
    gHomer[iAt].sRemote := sRemote; gHomer[iAt].bKnown := bKnown;
  end;
  Result := gHomer[iAt].iStateAfter;
end;

function homerOutcomeLine(iAt: Integer): String;
(* One Results-box line for a component whose box was ticked; '' when it was
   not. Says what happened, in the past tense, from a probe made after the
   script ran -- not what was hoped for when the box was drawn. *)
var
  sName, sBefore, sAfter: String;
  iBefore, iAfter: Integer;
begin
  Result := '';
  if not homerTicked(homerLabel(iAt)) then exit;
  sName := gHomer[iAt].sName;
  iBefore := homerState(iAt);
  sBefore := gHomer[iAt].sLocal;
  iAfter := homerStateAfter(iAt);
  sAfter := gHomer[iAt].sLocalAfter;
  case iBefore of
    0:
      if iAfter > 0 then
        Result := sName + ' ' + sAfter + ' was installed.'
      else
        Result := sName + ' was not installed. Its log says why.';
    1:
      if (sAfter <> '') and (sAfter <> sBefore) then
        Result := sName + ' was updated from ' + sBefore + ' to ' + sAfter + '.'
      else if iAfter = 2 then
        Result := sName + ' ' + sAfter + ' is current.'
      else
        Result := sName + ' is still ' + sBefore + '. Its log says why.';
  else
    if iAfter > 0 then
      Result := sName + ' ' + sAfter + ' was reinstalled.'
    else
      Result := sName + ' was not reinstalled. Its log says why.';
  end;
end;

function homerOllamaList(): String;
var
  lsLines: TArrayOfString;
  i: Integer;
begin
  if not gOllamaListKnown then
  begin
    gOllamaList := '';
    if homerProbeLines('ollama list', lsLines) then
      for i := 0 to GetArrayLength(lsLines) - 1 do
        gOllamaList := gOllamaList + Lowercase(lsLines[i]) + #10;
    gOllamaListKnown := True;
  end;
  Result := gOllamaList;
end;

function homerModelPresent(sModel: String): Boolean;
// True when `ollama list` names the model. "qwen2.5vl:7b" matches a line that
// starts with it; ":latest" is how ollama shows an untagged pull.
begin
  Result := Pos(Lowercase(sModel), homerOllamaList()) > 0;
end;

function homerModelIs(sModel: String; bPresent: Boolean): Boolean;
// The Check: for a model's Install entry (bPresent False) or Reinstall entry
// (bPresent True). A model has no Update entry: ollama pull always fetches the
// current one.
begin
  Result := homerModelPresent(sModel) = bPresent;
end;

function homerModelWanted(sModel: String): Boolean;
// The Check: for a model box -- ticked when the model is missing.
begin
  Result := not homerModelPresent(sModel);
end;

function homerModelPresentAfter(sModel: String): Boolean;
(* Asks ollama again, once, after the scripts have run. The first list is kept
   for the "before" side of the outcome. *)
var
  lsAfterLines: TArrayOfString;
  iAfter: Integer;
begin
  if not gOllamaListAfterKnown then
  begin
    gOllamaListAfterKnown := True;
    gOllamaListAfter := '';
    if homerProbeLines('ollama list', lsAfterLines) then
      for iAfter := 0 to GetArrayLength(lsAfterLines) - 1 do
        gOllamaListAfter := gOllamaListAfter + Lowercase(lsAfterLines[iAfter]) + #10;
  end;
  Result := Pos(Lowercase(sModel), gOllamaListAfter) > 0;
end;


function homerModelLabel(sModel, sUse, sSize: String): String;
// "Install <model> (<use>, <size>)" or "Reinstall <model> (<use>)".
begin
  if homerModelPresent(sModel) then
    Result := 'Reinstall ' + sModel + ' (' + sUse + ')'
  else
    Result := 'Install ' + sModel + ' (' + sUse + ', ' + sSize + ')';
end;

function homerModelOutcomeLine(sModel, sUse, sSize: String): String;
(* The Results-box line for a model whose box was ticked; '' when it was not. *)
var
  bBefore, bAfter: Boolean;
begin
  Result := '';
  if not homerTicked(homerModelLabel(sModel, sUse, sSize)) then exit;
  bBefore := homerModelPresent(sModel);
  bAfter := homerModelPresentAfter(sModel);
  if bBefore then
  begin
    if bAfter then Result := 'The ' + sUse + ' model ' + sModel + ' was reinstalled.'
    else Result := 'The ' + sUse + ' model ' + sModel + ' was not reinstalled. Its log says why.';
  end else begin
    if bAfter then Result := 'The ' + sUse + ' model ' + sModel + ' was installed.'
    else Result := 'The ' + sUse + ' model ' + sModel + ' was not installed. Its log says why.';
  end;
end;

//  ---- the screen reader wrappers the [Components] lines call ------------
//  An app's [Components] checks name isInstallJaws, isUpdateJaws and so on,
//  and Inno wants each as a function of its own. They are the same three
//  lines for every app, so the kit supplies them; an app that writes its
//  own -- DbDo did, before the kit had these -- says so with
//  #define HomerReaderWrappersInApp before the include, and these stay out,
//  since Inno refuses a function defined twice. FileDir's build failed on
//  6 October 2026 because a kit without these was laid over one that had
//  them; the kit carries them from now on.
#ifndef HomerReaderWrappersInApp
function labelJaws(sParam: String): String;  begin Result := homerReaderLabel('jaws'); end;
function isInstallJaws(): Boolean;           begin Result := homerReaderIs('jaws', 0); end;
function isUpdateJaws(): Boolean;            begin Result := homerReaderIs('jaws', 1); end;
function isReinstallJaws(): Boolean;         begin Result := homerReaderIs('jaws', 2); end;
function labelNvda(sParam: String): String;  begin Result := homerReaderLabel('nvda'); end;
function isInstallNvda(): Boolean;           begin Result := homerReaderIs('nvda', 0); end;
function isUpdateNvda(): Boolean;            begin Result := homerReaderIs('nvda', 1); end;
function isReinstallNvda(): Boolean;         begin Result := homerReaderIs('nvda', 2); end;
#endif
