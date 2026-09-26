---
title: "HomerDev Frequently Asked Questions"
author: "Jamal Mazrui"
---

# Frequently Asked Questions

## Why Windows only? Will there be a Mac or Linux version?

This kit is built on decades of doing productive work on Windows with a screen
reader, and its purpose is to make that experience as good as it can be. Every
convention in it -- what gets spoken and what does not, where the focus lands,
which keys are safe to use, how a dialog is laid out -- was learned from years of
using JAWS and NVDA on real work, and tested by shipping programs that people
use.

I do not have that depth of experience on macOS, iOS, Linux or Android. Writing
conventions for VoiceOver or Orca that I had not lived with would produce
confident guidance that turned out to be wrong, which is worse than none.

The code is MIT licensed, and developers who do know those platforms are welcome
to take any part of it. The ideas travel further than the code does: add order
as focus order, speech only for what the screen reader cannot work out, one
session log in a known place, evidence instead of eyeballing. None of those are
Windows ideas. If somebody ports the kit, tell me, and I will link to it.

## Do I need to know how to program?

No, but you do need to be comfortable typing exact commands and reading what
comes back. The kit is driven from a command prompt: you type
`buildHomerDev`, you read the lines it prints, and when something is wrong you
open a log file and look for the word ERROR.

If you have never written code, start with `help\Tutorials.md`, build the sample
programs, and change one line in one of them. The samples are written to be read
by somebody who is learning, with a comment on every decision that matters.

## Do I have to use C#, or Python?

Either. The kit provides the same toolbox in both, with the same names. Four of
the samples are pairs -- the same program in both languages, written block for
block -- so you can read across and decide.

Pick C# if you want a single .exe that needs nothing installed. Pick Python if
you already know it, or need a library that only Python has; the build packs
Python and every dependency into one file, so what you hand somebody else is
still a single program.

## Which screen readers does it work with?

JAWS, NVDA and Narrator. The controls are ordinary Windows controls, which is
why every reader already knows them; `Say` reaches JAWS through its own
interface, NVDA through its controller, and Narrator through a UI Automation
notification, and your program does not have to know which is running.

## Do I need Visual Studio?

No. The C# build uses the compiler that comes with the .NET Framework or with
the Build Tools, and the build script finds it. If nothing suitable is present,
the script says what to install and how.

## Will this work with my existing project?

The classes are plain C# and Python source files with no dependencies of their
own, so you can add one to an existing project and use it. `Lbc` gives the most
back for the least work: one dialog rewritten with it is usually enough to see
whether the rest is worth doing.

## Why not a package on NuGet or PyPI?

The kit travels by copying a file, which is deliberate. A fix is a file copy and
a rebuild, with no version resolution, no package manager, and nothing to go
wrong at install time on somebody else's machine. The cost is drift between
copies, and the kit exists precisely to stop that: one place holds the current
version, and `checkHomerDev` proves it still builds.

## Why MDI? Everything uses tabs now.

Because a window is a first-class object to a screen reader and a tab is not.
Alt+Tab reaches a window, the window list names it, its title is announced when
it is activated, and it keeps its own state. A tabbed interface has to
reimplement every one of those, and most do it badly. `help\HomerDev.md` has the
longer argument.

## Why is there so much logging?

Because the failure you need to explain is never the one you can reproduce.
Writing a line costs microseconds; not having it costs an evening. Every program
writes one log per run to `%LOCALAPPDATA%\<App>\logs`, holding the environment,
every setting, every external command with its exit code, and every error with
its stack. The console stays short, because the console is for a person.

## Is this an AI project?

No, but it is shaped by the fact that AI now writes the first draft of a lot of
code. A model will give you fluent, plausible work and will not tell you what it
failed to check. The kit's answer is evidence: acceptance criteria written before
the code, checks that run, and a report that says what was verified, what was
not checked, and what remains uncertain. That was good practice before; it is
necessary now.

## Can I use this commercially?

Yes. MIT licensed: use it, change it, sell what you build with it. Keep the
license text with the code.

## How do I report a problem or ask for something?

Open an issue on the repository. A log file helps more than a description:
`%LOCALAPPDATA%\<App>\logs` for a program, or `build<App>.log` beside the build
script for a build.

## Who made this, and why is it called Homer?

Jamal Mazrui, through Access Success LLC. Homer is the name the shared classes
have carried across twenty years of tools -- a blind poet who worked entirely by
ear, which is the point.
