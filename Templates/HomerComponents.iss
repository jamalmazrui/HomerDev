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
  sInstalled, sAvailable, sId, sRest, sVersion: String;
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
      if sAvailable <> '' then Result := 1 else Result := 2;
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

  (* Nothing installed: fetch the version that WOULD be installed, so the
     Install label carries a number too. *)
  if Result = 0 then
  begin
    sRest := gHomer[iAt].sIdList;
    if sRest <> '' then gHomer[iAt].sRemote := homerWingetLatest(homerNextId(sRest));
  end;

  gHomer[iAt].iState := Result;
  gHomer[iAt].bKnown := True;
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
(* 1 Install, 2 Reinstall, 3 Update -- the order the finish page shows them. A
   number rather than a sort of the verbs, so rewording a label later cannot
   quietly change the order. *)
begin
  case homerState(iAt) of
    0: Result := 1;
    1: Result := 3;
  else Result := 2;
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
