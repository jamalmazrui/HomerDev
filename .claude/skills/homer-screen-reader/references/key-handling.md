# Handling a key in a Homer app's screen reader scripts

Every Homer app that ships screen reader scripts handles each key it cares about by making two choices, the same way in JAWS and NVDA. The app does the work and speaks through the kit's `Say`, which talks directly to JAWS, NVDA or Narrator; a script only decides who gets the key and whether the reader adds anything. Keyboard interruptibility is on in every screen reader, so the next key cuts off speech in progress, and nothing in a script or an app should try to interrupt speech itself.

## The two choices

**The way: what the script does with the key.** In alphabetical order:

- **Answer with the app's key.** A screen reader's own key asks a question the app answers better in one place, such as JAWS+F or NVDA+F asking the font in DbDo's grid of records. The script sends the app's key for that answer, Say Field Type, and the reader's own command runs everywhere else. Always only here.
- **Capture.** The script does the work, and the app never sees the key. HomerView's commands work this way, through its own bridge program or Python code.
- **Pass quietly.** The key goes to the app, and the reader says nothing; the app speaks. DbDo's chords work this way. It is the most common way.
- **Pass, then speak.** The key goes to the app, then the reader speaks, such as reading the new line.
- **Speak, then pass.** The reader speaks first, such as a short cue, then the key goes to the app. Rare.

**The scope: where the script does it.**

- **Everywhere** in the app, for keys only the app uses, such as Alt+Control with the arrows.
- **Only here**: in one control, window, mode or process, with a stated fallback elsewhere. The fallback is either the reader's own handling, as for DbDo's arrows outside its grid, or the key passed on as though nothing were bound, as for HomerView's commands outside its own browser.

Write both in a comment above each script: `Way: pass quietly. Where: only here, in the grid; elsewhere NVDA's own handling.`

## The shared code

- **NVDA:** the kit's `exec\Python\keys.py`. Each app's build copies it into its add-on's `homer` package, so every add-on runs the same code: `keys.passQuietly(gesture)`, `keys.passThenSpeak(gesture, text)`, `keys.speakThenPass(gesture, text)`, `keys.onlyHere(script, bHere)`, `keys.quietNextFocus()` with `keys.focusIsQuiet()`, and `keys.windowClassIs(obj, "SysListView32")`. It sends a key by its six-pack name even when the number pad was pressed with NumLock off, which plain `gesture.send()` did not deliver reliably.
- **JAWS:** a script file cannot import another app's, and a Homer `.jss` uses no `Include`, so it compiles with any installed JAWS. The shared part is the shapes below, copied from the kit's `Templates\screenReader\jaws` with the app's name: `pass<App>Key` for passing quietly, `in<App><Place>` for the scope test, and one script per key for the rest.

## JAWS

A key map line must name a Script, never a Function.

**JAWS reads a list's new row from its events, not only its scripts** (24 November 2026). This reference used to say replacing the arrow script was enough to keep JAWS quiet. It was not: DbDo said the cell on Alt+Down Arrow, then JAWS read the whole record, because moving the selection fires the list's ActiveItemChangedEvent however the move was made. That is also why DbDo's plain arrows read the row with no SayLine of their own. So a key the app answers itself in a list marks a short quiet time, and the app's ActiveItemChangedEvent skips the row announcement inside it, calling the default for everything else, as the JAWS manual's own example does. A plain arrow clears the mark.

    Globals int iAppQuietTick

    Void Function quietAppRow ()
    Let iAppQuietTick = GetTickCount ()
    EndFunction

    Int Function appRowIsQuiet ()
    Var
        int iAge
    If iAppQuietTick == 0 Then
    Return 0
    EndIf
    Let iAge = GetTickCount () - iAppQuietTick
    If iAge < 0 || iAge > 700 Then
    Let iAppQuietTick = 0
    Return 0
    EndIf
    Return 1
    EndFunction

    Void Function ActiveItemChangedEvent (handle hCurrent, int iCurrentObject, int iCurrentChild, handle hPrior, int iPriorObject, int iPriorChild)
    If appRowIsQuiet () && inAppList () Then
    Return
    EndIf
    ActiveItemChangedEvent (hCurrent, iCurrentObject, iCurrentChild, hPrior, iPriorObject, iPriorChild)
    EndFunction

Define a function before the first one that calls it, and use 0 and 1 rather than TRUE and FALSE, which come from a header a Homer script does not include.

    ; Way: pass quietly. Where: everywhere.
    Script passAppKey ()
    TypeCurrentScriptKey ()
    EndScript

    ; Way: pass quietly. Where: only here, in the list; elsewhere JAWS's own script.
    Int Function inAppList ()
    Return StringContains (GetWindowClass (GetFocus ()), "SysListView32") > 0
    EndFunction
    Script nextAppRow ()
    If inAppList () Then
    TypeCurrentScriptKey ()
    Else
    PerformScript SayNextLine ()
    EndIf
    EndScript

    ; Way: capture. Where: only here; elsewhere the key passes on.
    Script doAppCommand ()
    If Not appOwnsWindow () Then
    TypeCurrentScriptKey ()
    Return
    EndIf
    ; ... the command's work ...
    EndScript

    ; Way: pass, then speak.
    Script appKeyThenLine ()
    TypeCurrentScriptKey ()
    Pause ()
    SayLine ()
    EndScript

    ; Way: speak, then pass.
    Script appCueThenKey ()
    SayString ("cue")
    TypeCurrentScriptKey ()
    EndScript

    ; Way: answer with the app's key. Where: only here; elsewhere JAWS's own script. JAWS's script is replaced by
    ; name, so no key map line is needed and the key works in every layout.
    Script SayFont ()
    If inAppList () && IsPCCursor () Then
    TypeKey ("Alt+Shift+F")
    Else
    PerformScript SayFont ()
    EndIf
    EndScript

Keys JAWS takes everywhere are handed on by the kit itself: `tidy` writes them into a marked block of `scripts\jaws\<App>.jkm` from the reviewed allowlist in `data\KeyOwnership.inix`.

## NVDA

    from .homer import keys

    # Way: pass quietly. Where: everywhere in the app.
    @scriptHandler.script(canPropagate=True, gestures=["kb:alt+control+rightArrow"])
    def script_passKey(self, gesture):
        keys.passQuietly(gesture)

    # Way: pass quietly. Where: only here, in the list; elsewhere NVDA's own handling.
    class AppList(NVDAObject):
        @scriptHandler.script(gestures=["kb:upArrow", "kb:downArrow"])
        def script_passRowKey(self, gesture):
            keys.quietNextFocus()
            keys.passQuietly(gesture)
        def event_gainFocus(self):
            if keys.focusIsQuiet():
                return
            super().event_gainFocus()
    # ... and in the AppModule:
    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        if keys.windowClassIs(obj, "SysListView32"):
            clsList.insert(0, AppList)

    # Way: answer with the app's key. Where: only here, on the list's overlay class; elsewhere NVDA's own command.
    @scriptHandler.script(description="In the app's list, say the current field's type.", gesture="kb:nvda+f")
    def script_sayAppFieldType(self, gesture):
        keys.answerWithKey("alt+shift+f")

    # Way: capture. Where: only here; elsewhere the key passes on (a global plugin's getScript).
    def getScript(self, gesture):
        functionScript = super().getScript(gesture)
        return keys.onlyHere(functionScript, self.focusIsMine()) if functionScript else None

A list's new row is announced by NVDA's focus event, not by a script, so the pass-only-here script quiets that one announcement; the app speaks the row instead.

## The readers' own keys the suite answers

A reader's key keeps its meaning wherever the app has nothing better to say. Where the reader's answer means nothing in an app's main view -- a font in a grid of records, a pixel position in a list -- the app answers instead, in that view only. The same key gets the same kind of answer in every app (24 November 2026):

- **Address, JAWS+A.** DbDo: the cell's column name, record and column numbers. EdSharp: Say Address, with the page. FileDir: the folder's name and path, as JAWS reads File Explorer's address bar. The key map names `Insert+A`, not `JAWSKey+A`, so a laptop's CapsLock+A stays Say All. NVDA has no address key, and NVDA+A is Say All on a laptop, so it is left alone.
- **Font, JAWS+F and NVDA+F.** DbDo: the field's declared type. FileDir: the item's type. EdSharp keeps the reader's answer, since a document has a font.
- **Position, JAWS+Number Pad Delete and NVDA+Number Pad Delete.** Each app's Say Position, as Alt+Delete.
- **Tables.** DbDo's grid takes JAWS's Say Current Cell and NVDA's table reading keys (NVDA+Alt+Control with an arrow) and answers them by its own table model.
- **Everything else** stays the reader's: Tab, title, current line, status line, Say All. HomerView answers none of these, since its browser's keys already mean what they say there, and JAWS+A must keep reading Edge's address bar.

## Typing echo is the user's

A script never binds a letter, a digit or Shift with a letter to quiet the reader's typing echo, even where the app answers the key itself, such as a Say command on Shift with a letter (Jamal, 23 November 2026). Typing echo is the user's own setting, and scripting those keys would change it in every text box of the app as well. The echoed letter before the app's answer is the accepted cost.

## Conventions every script set shares

These hold for every Homer app's scripts, in both readers, alongside the way and scope of each key.

- **Act when there is something to do, otherwise pass.** A script that handles a key only sometimes ends by passing it on when it did nothing -- `TypeCurrentScriptKey ()` in JAWS, `gesture.send()` in NVDA -- so the key is never swallowed.
- **Every layout.** JAWS key assignments go in the key map's `[Common Keys]` section, so they work in the desktop and laptop layouts alike.
- **Keys a user can move.** NVDA lists an add-on's scripts in its Input Gestures dialog under the class's `scriptCategory`, the app's name, where any key can be rebound.
- **Many commands, few keys.** When a script set needs more commands than there are free keys, use a command key: one prefix key, then a second key for the command, with Tab and Shift+Tab speaking each command at that level, Enter running the one last spoken, and Escape leaving. It costs one key, and nothing else in the program is taken. Choose a key rarely typed, such as the left bracket or the grave accent; say a word or play a sound when the layer starts, so the person knows the next key is a command; and let a double press type the key's own character, so it is never lost.
- **Names that cannot collide.** Every JAWS function and script, and every NVDA script, starts with the app's name (`nextDbDoRow`, `passDbDoKey`, `script_passRowKey` on DbDo's class), in lower camel case as Camel Type asks, so nothing clashes with the reader's default scripts or with another author's set for the same program.
- **Time without GetTickCount arithmetic.** JAWS's GetTickCount drops its top bit, so subtracting two readings goes wrong about every 24.85 days of uptime and can make a cache permanent. Treat a negative difference as stale, or time with something else.
- **Where the guide is.** In JAWS, JAWS+F1 pressed twice opens the program's guide, `help\<App>.htm` beside the program; once, JAWS's own help. JAWS's own double press opens its help topic for the program, and it has none for a Homer app, so the guide takes that place. In NVDA, the manifest's `docFileName` puts the guide behind the add-on's Help button.
- **Who the scripts are.** In JAWS, JAWS+Q starts with the scripts' name and the program's version, read from the running program so it is never stale. In NVDA, NVDA+Shift+V says the program's version and the add-on's, through `keys.sayVersions`. Asking for support starts with these.

## Building, fingerprinting, installing and operating, the same way for both

The kit handles the two packages in parallel at every stage, so a fix to one is a fix to both.

- **Building.** Sources live in the repository: `scripts\jaws\<App>.jss` and `<App>.jkm`, and the NVDA add-on in `scripts\nvda` (manifest.ini, `appModules\<app>.py`, readme.html), or in `addon` for an app that is itself an add-on, as HomerView is. The app's build calls the kit's `packScreenReaderSupport.cmd -Root <folder> -App <App>`, which packs `<App>_JAWS.zip` from the JAWS sources, never a compiled .jsb, and `<App>.nvda-addon` after copying the kit's `keys.py` into the add-on's `homer` package.
- **Fingerprinting.** The installer's box comes from comparing the shipped sources with each installed copy, every file's name and bytes, leaving out what the reader makes for itself: a compiled .jsb, or Python caches. Install when none is there, Update when any differs, Reinstall when every copy is current. Nothing is recorded on the side.
- **Installing.** `installScreenReaderSupport.cmd` never needs the reader running. It installs into every place the reader looks. For JAWS, that's every installed version and every language folder of its user settings, Settings\enu, Settings\deu and so on, compiled by that version's own scompile.exe and fully undone if a source fails to compile. For NVDA, it's %APPDATA%\nvda, made if NVDA has never run, and the userConfig folder of any running portable NVDA.
- **Operating.** JAWS uses new scripts the next time the app comes to the front; NVDA loads the add-on the next time it starts. The installer's results say so, one line per place, worded alike.

DbDo follows all four. HomerView's NVDA side does too; its JAWS scripts extend Edge's, so it keeps its own JAWS installer for the chaining, which is to adopt the kit's discovery and fingerprint next.

## Where the files live

- `scripts\jaws\<App>.jss` and `<App>.jkm`, sources only: the installer compiles the .jss with each installed JAWS version, and a .jsb is never shipped.
- The NVDA add-on's sources: `scripts\nvda` for an app module (manifest.ini, `appModules\<app>.py`, readme.html), as DbDo has; an app that is itself an add-on, as HomerView is, keeps its `addon` folder.
- The build copies `keys.py` into the add-on's `homer` package and packs `<App>_JAWS.zip` and `<App>.nvda-addon`, which the installer offers. DbDo and HomerView are complete working examples.
