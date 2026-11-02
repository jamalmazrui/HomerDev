;_APP_.jss -- JAWS scripts for _APP_.exe, from the HomerDev template.
;
; Each key has a way and a scope, the same as in _APP_'s NVDA add-on (see the
; homer-screen-reader skill's references\key-handling.md). The app speaks for
; itself through the kit's Say; these scripts only decide who gets the key.
; No Include or Use: scompile builds it against any installed JAWS version.

; Way: pass quietly. Where: everywhere in _APP_.
Script pass_APP_Key ()
TypeCurrentScriptKey ()
EndScript

; Way: pass quietly. Where: only here, in _APP_'s list; elsewhere JAWS's own script.
Int Function in_APP_List ()
Return StringContains (GetWindowClass (GetFocus ()), "SysListView32") > 0
EndFunction

Script next_APP_Row ()
If in_APP_List () Then
TypeCurrentScriptKey ()
Else
PerformScript SayNextLine ()
EndIf
EndScript

Script prior_APP_Row ()
If in_APP_List () Then
TypeCurrentScriptKey ()
Else
PerformScript SayPriorLine ()
EndIf
EndScript

; WHO THESE SCRIPTS ARE, AND THEIR GUIDE (2 November 2026). Two standard entry
; points every Homer app's scripts share. JAWS+Q starts with the scripts' name
; and the program's own version, read from the running program so it is never
; stale. JAWS+F1 pressed twice opens the program's guide; pressed once, JAWS's
; own help, as always.

Script ScriptFileName ()
ScriptAndAppNames ("_APP_ scripts, for _APP_ " + GetVersionInfoString (GetAppFilePath (), "FileVersion"))
EndScript

Script ScreenSensitiveHelp ()
Var
    string sHelp, sPath
If IsSameScript () Then
Let sPath = GetAppFilePath ()
Let sHelp = StringLeft (sPath, StringLength (sPath) - StringLength (GetAppFileName ())) + "help\\_APP_.htm"
If FileExists (sHelp) Then
Run (sHelp)
Return
EndIf
EndIf
PerformScript ScreenSensitiveHelp ()
EndScript
