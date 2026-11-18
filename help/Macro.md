---
title: "Homer Macros"
author: "Jamal Mazrui"
---

# Homer macros

Homer has two kinds of macro. Both are `.inix` files you can read and change in EdSharp or any text editor, and neither needs a macro editor.

- **A macro script** is written by a person, a line to a step, in the words of the app's menus and the screen reader's commands. It is played from outside the app by `scripts\runMacro`, which presses the keys, listens to the screen reader and reads what Windows shows. Its header says `FileTask = macroScript`.
- **A recorded macro** is made inside an app by its macro recorder, from the commands you run. The app plays it back itself. Its header says `FileTask = macro`.

## Macro scripts

A macro script reads like a list of things to do:

    FileTask = macroScript
    App = FileDir
    Name = Hear the filter and the position

    [steps]
    ; a line starting with a semicolon is a note
    Say Filter and Order
    Expect speech filter
    Say Position twice
    Press Escape
    Say Line

The header comes first: FileTask, App, and optionally Name, Note and Listen (the most seconds to listen after a key that gets no answer; 6 when left out). Then `[steps]` holds one step to a line. A step line may hold an equals sign, so `Type a=b` types a=b.

### What a line can say

Each line is matched in this order:

- **A command of the app,** by its name on the menus, such as `Say Filter and Order`. It is run by its key. A command with no key is run from the Alternate Menu. Add `twice` to press its key twice, for a command's second meaning.
- **A screen reader command,** by its script name, with or without spaces, such as `Say Line` or `SayWindowTitle`. Its key is read from JAWS's own key map, so a key you reassigned is followed. Under NVDA, the four everyone knows work: Say All, Say Line, Say Window Prompt and Text, and Say Window Title.
- **Expect focus** text: the control with focus after the step before holds this text.
- **Expect speech** text: the reader was heard saying most of these words after the step before. When either of two things may be right, split them with a bar, as in `Expect speech column | blank`; the better match counts.
- **Expect window** text: the title of the window in front after the step before holds this text.
- **JAWS** script: a JAWS script, when the app has a command of the same name.
- **Press** key: a key by its Homer name, such as `Control+Shift+F`, `Escape` or `Shift+Slash`. Add `twice` to press it twice.
- **Run** command: an app command, when a reader command has the same name.
- **Start** app: says which app the macro plays in. Every macro brings its app forward first, so this line is optional.
- **Type** text: types the text. Quotation marks around it are dropped.
- **Wait** seconds: waits before the next step.
- **Wait for window** text: the same as Expect window.

A line runMacro does not understand stops the whole macro before any key is pressed, and the console names the line.

### What you never have to write

No line says how long anything takes. Before each key, runMacro waits for the screen reader to fall quiet. After it, runMacro listens until the reader has finished, up to fifteen seconds. A window is given five more seconds to appear. The app is brought to the front first, and it is started if it is not running.

### Playing one

- **runMacro** file: plays it. Keep your hands off the keyboard. To stop, switch to another window.
- **runMacro --check** file: checks every line is understood, and presses nothing.
- **runMacro --no-hear** file: plays it without writing the speech down, so Expect speech is not checked.
- **runMacro --keep** file: leaves the app open at the end. An app that was open before the macro always stays open.

The report is `logs\<App>-recordWalk-<time>.md`. For each step, it gives the key, what was heard, what had focus, what the app said in its own log, and whether each Expect line held. runMacro's own log is `logs\<App>-runMacro-<time>.log`. The exit code is 0 when every Expect line held.

### How it works

runMacro turns the macro into a walk, the format tutorials use, and the kit's recordWalk plays it. So a macro, a tutorial and testSay are played by one engine, which records the computer's sound and writes it down with a local speech recognizer.

### Live tests in tidy

An app's `scripts\tests` folder holds a few macro scripts that are its important live tests. These are not every possible test. Tidy plays each one after a build, so a change that breaks what a person hears is found by the cycle. A test is played only when all of these are true:

- **Its fingerprint changed** since its last pass. The fingerprint covers the macro, the program, the key file, runMacro and recordWalk.
- **The app is closed,** so the build just made is the one tested, and nothing you have open is touched.
- **A screen reader is running.**

Setting `HomerLive=0` leaves the live tests out. A failed live test is reported but never makes tidy fail. Only a pass is recorded, so a failed test runs again at the next tidy.

### testSay

`scripts\testSay`, in every app that copies it from the kit, writes a macro script of every Say command in the app's key file and plays it. It runs each command once, then twice, then presses Escape. Then it turns on the Key Describer and presses each key again, so you hear each one described. It gathers the reports, the recordings and the app's own logs in one folder under logs, ready to upload. `testSay --check` writes the macro and checks it without pressing anything.

## Recorded macros

The macro recorder lets a person record a sequence of an app's own commands, save it as an `.inix` file, and play it back later. It lives in `exec\CSharp\Macro.cs`, which an app compiles beside `Inix.cs`. DbDo is the first app to use it, with its record-navigation commands; other apps can add it the same way.

### What a macro is

A macro is a list of the app's commands, as the person ran them. It is not a list of keystrokes or mouse clicks. A command replays the same way whatever the window layout, the screen reader or the keyboard, so a macro does not break when a dialog moves or a key is reassigned.

A recorded macro is an `.inix` file whose header says `FileTask = macro`. Each command is one `[step]` section:

    FileTask = macro
    MacroVersion = 1
    App = DbDo
    Name = Third customer from the top

    [step]
    CommandId = firstRecord
    Command = First Record

    [step]
    CommandId = goToRecord
    Command = Go To
    Argument = 3

The header fields are FileTask, MacroVersion, App, Name, Requires, Incomplete and Note. The step fields are CommandId, Command, Argument and Note. Any other field is refused, so a macro never plays with part of it unread.

- **CommandId** is the stable name the app plays by, the same as KeyMap.toId of the command's menu name.
- **Command** is the name the person sees, kept so the file reads plainly.
- **Requires** holds the view the macro was recorded in, when the person chose This View. The macro then plays only in that view.
- **Incomplete = yes** marks a recording in which the person did something the recorder cannot repeat. Such a macro does not play.

### How an app takes part

An app gives the engine an object that implements `IMacroHost`:

- **sApp** -- the app's name, written into the macro and checked on playback.
- **sScope** -- the current view, in words that change when the view changes. An empty value means there is nothing to record in.
- **validate(step)** -- whether this command, with this argument, can run now.
- **execute(step)** -- runs the command and returns true only when it did what it should.
- **expect(step)** -- what the command should leave behind, said from the state before it runs, such as "row 9 of 12". It returns "" when that cannot be said in advance.
- **observe()** -- the state now, in the same words as expect.
- **log(message)** -- writes a line to the app's log.

The app calls `MacroSession.record` itself, after it has seen a command succeed. A command handler that returns has not proved it did anything: Go To can be cancelled, and Next Record can sit on the last row. Anything else the person does while recording is reported with `gap`, which marks the macro incomplete.

### Expected against actual

During playback, every step is checked. Before the step runs, the engine asks the app what it should leave behind; after it runs, the engine asks what it did leave. Both go to the log, side by side, with the state before:

    Audit step 4 of 6: Go To (goToRecord) with 9; before row 3 of 12; expected row 9 of 12; actual row 9 of 12; same

A step whose outcome differs stops playback at that step, and the log says where and why. `auditLines()` returns the last playback's steps as `commandId|argument|expected|actual`, for a test to compare with what it meant to happen.

### Threads and timing

A session belongs to the thread of its window. Between steps, playback waits 25 milliseconds, only so that Escape and repainting get their turn; it does not treat that wait, or Application.Idle, as proof that a command finished. A command is finished when execute returns.

### Limits

A macro file is at most 2 MiB and 10,000 steps. A value is at most 32,768 characters.

### How the kit proves it

The kit's build runs `scripts\testMacro`, which compiles `Macro.cs` with the .NET Framework's own C# 5 compiler and runs a test against a pretend 12-row view. The test records six steps, saves and loads them, plays them from another row, and compares the audit trail with the expected one. Then it proves that a host which claims success without moving is stopped at its first step, and that a wrong view, a failing step, a cancel, a gap, an unknown command, a later version, an unknown field, a duplicate field, another app's macro and an oversized file are all refused. Every check is written to `logs\HomerDev-testMacro-<time>.log` with what was expected and what happened.
