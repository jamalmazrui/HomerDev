---
title: "Homer Macro Recorder"
author: "Jamal Mazrui"
---

# Homer macro recorder

The macro recorder lets a person record a sequence of an app's own commands, save it as an `.inix` file, and play it back later. It lives in `exec\CSharp\Macro.cs`, which an app compiles beside `Inix.cs`. DbDo is the first app to use it, with its record-navigation commands; other apps can add it the same way.

## What a macro is

A macro is a list of the app's commands, as the person ran them. It is not a list of keystrokes or mouse clicks. A command replays the same way whatever the window layout, the screen reader or the keyboard, so a macro does not break when a dialog moves or a key is reassigned.

A macro file is an `.inix` file whose header says `FileTask = macro`. Each command is one `[step]` section:

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

## How an app takes part

An app gives the engine an object that implements `IMacroHost`:

- **sApp** -- the app's name, written into the macro and checked on playback.
- **sScope** -- the current view, in words that change when the view changes. An empty value means there is nothing to record in.
- **validate(step)** -- whether this command, with this argument, can run now.
- **execute(step)** -- runs the command and returns true only when it did what it should.
- **expect(step)** -- what the command should leave behind, said from the state before it runs, such as "row 9 of 12". It returns "" when that cannot be said in advance.
- **observe()** -- the state now, in the same words as expect.
- **log(message)** -- writes a line to the app's log.

The app calls `MacroSession.record` itself, after it has seen a command succeed. A command handler that returns has not proved it did anything: Go To can be cancelled, and Next Record can sit on the last row. Anything else the person does while recording is reported with `gap`, which marks the macro incomplete.

## Expected against actual

During playback, every step is checked. Before the step runs, the engine asks the app what it should leave behind; after it runs, the engine asks what it did leave. Both go to the log, side by side, with the state before:

    Audit step 4 of 6: Go To (goToRecord) with 9; before row 3 of 12; expected row 9 of 12; actual row 9 of 12; same

A step whose outcome differs stops playback at that step, and the log says where and why. `auditLines()` returns the last playback's steps as `commandId|argument|expected|actual`, for a test to compare with what it meant to happen.

## Threads and timing

A session belongs to the thread of its window. Between steps, playback waits 25 milliseconds, only so that Escape and repainting get their turn; it does not treat that wait, or Application.Idle, as proof that a command finished. A command is finished when execute returns.

## Limits

A macro file is at most 2 MiB and 10,000 steps. A value is at most 32,768 characters.

## How the kit proves it

The kit's build runs `scripts\testMacro`, which compiles `Macro.cs` with the .NET Framework's own C# 5 compiler and runs a test against a pretend 12-row view. The test records six steps, saves and loads them, plays them from another row, and compares the audit trail with the expected one. Then it proves that a host which claims success without moving is stopped at its first step, and that a wrong view, a failing step, a cancel, a gap, an unknown command, a later version, an unknown field, a duplicate field, another app's macro and an oversized file are all refused. Every check is written to `logs\HomerDev-testMacro-<time>.log` with what was expected and what happened.
