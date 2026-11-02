# Handling a key in a Homer app's screen reader scripts

Every Homer app that ships screen reader scripts handles each key it cares about by making two choices, the same way in JAWS and NVDA. The app does the work and speaks through the kit's `Say`, which talks directly to JAWS, NVDA or Narrator; a script only decides who gets the key and whether the reader adds anything. Keyboard interruptibility is on in every screen reader, so the next key cuts off speech in progress, and nothing in a script or an app should try to interrupt speech itself.

## The two choices

**The way: what the script does with the key.** In alphabetical order:

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

A key map line must name a Script, never a Function. JAWS speaks a list's or edit's new line from its own scripts (`SayNextLine`, `SayPriorLine`, `JAWSPageDown`, `JAWSPageUp`), not from an event unless the app's .jcf sets `MSAAMode=2`, so replacing the script is enough to keep it quiet.

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

    # Way: capture. Where: only here; elsewhere the key passes on (a global plugin's getScript).
    def getScript(self, gesture):
        functionScript = super().getScript(gesture)
        return keys.onlyHere(functionScript, self.focusIsMine()) if functionScript else None

A list's new row is announced by NVDA's focus event, not by a script, so the pass-only-here script quiets that one announcement; the app speaks the row instead.

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
