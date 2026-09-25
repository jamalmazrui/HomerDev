---
title: "HomerDev History"
author: "Jamal Mazrui"
---

# History

# 1.31.1 -- 25 September 2026

Two build failures from 1.31.0, both fixed. homerNoteTicked was declared a
function with no return type, which Pascal refuses ("colon expected"); it is
a procedure. The two C# sample builds and Templates\build_APP_.cmd compiled
Lbc.cs without the Elevate.cs it now depends on; each lists it.

help\Tutorials.md gains "How a screen reader trainer narrates": nine beats
taken from a professional JAWS training recording -- key, press, hear, then
translate; letters with their phonetic word; the reader quoted word for word
and then paraphrased; silence named; focus verified after every change; the
repeat key taught first; counts used as orientation; controls named as the
reader names them; a breath before each key. Templates\Tutorial_00_Overview.inix
carries the short form.

# 1.31.0 -- 25 September 2026

Two patterns every Homer app is to follow, asked for on this date.

THE ORDER OF THE FINISH-PAGE BOXES: Install (screen reader scripts first,
then components alphabetically), ticked; Update, ticked, alphabetical;
Reinstall, unticked, alphabetical; Launch, ticked; Open the user guide,
unticked. Done with three [Run] entries per component, one per verb, using
the new homerIs(i, state) and homerModelIs(model, present) checks; Inno's
script order and Check: do the grouping. FinishPage.md states the rule.
Templates\_APP__setup.iss is rewritten to it -- it includes
HomerComponents.iss, registers Ollama with homerAdd, keeps the screen reader
script entries, reports the Results box from homerOutcomeLine, starts the
program after that box through the launch marker, and its [UninstallDelete]
names only logs and settings, never the whole app-data folder. homerFinish.cmd
is no longer shipped by the template.

THE HELP BOX CHECKS THE WEB FOR A NEWER VERSION. New shared class
CSharp\Elevate.cs: an app calls Elevate.configure(owner, repo, version) once
at startup; the Lbc Help box then ends with "This is version X. Version Y is
on the web." and its buttons become Yes and No -- Yes the default when a newer
version exists, No when this is the newest, OK alone when the web could not be
checked (eight-second timeout, so an offline machine never hangs the box).
Yes fetches <repo>_setup.exe from the latest GitHub release and starts it.
Elevate.offer(owner) does the same conversation in a message box for an F11
handler. LBC NOW REQUIRES ELEVATE.CS: add CSharp\Elevate.cs to every build
that compiles Lbc.cs.

Util.spokenLength(seconds) says a LENGTH in words -- "19 minutes", "1 hour
and 6 minutes", "45 seconds" -- because a screen reader reads "19:00" as
nineteen hundred hours and "1:06:06" as a time of day. HomerScribe reported a
nineteen-minute run as "Took 19:00". A clock reading is only for a POSITION:
where in a film or recording something is.

Lbc.runWithButtons gains a third argument naming the default button, so a
Yes/No box can keep Yes-then-No order with No as the default. The first
label is the default when the argument is absent -- so list OK first: with
Help first, Enter in HomerScribe's source paths field opened Help.

# 1.30.0 -- 25 September 2026

The Results box after an install reports only the boxes that were ticked,
from a probe made after the scripts ran: homerNoteTicked records the ticked
captions when Finish is pressed (from NextButtonClick at wpFinished);
homerOutcomeLine and homerModelOutcomeLine each return a past-tense line for
a ticked box and nothing for one that was not. Until now the box recited
every component from the probe made when the wizard opened -- so a minute
after Whisper was installed and Ollama updated, it said neither had
happened, and it listed three components nobody had asked about.

FinishPage.md gains the Results-box rule and the "Downloading" rule for
install-script console messages.

# 1.29.0 -- 25 September 2026

Four files delivered the day before had landed in folders the kit never had:
Docs, Inno and Scripts. They now sit where RepoFiles.txt says kit files go --
FinishPage.md and Logging.md in help; HomerComponents.iss and homerInstall.cmd
in Templates, beside _APP__setup.iss and installOllama.cmd. The build's move
list removes the old copies once the new ones are in place, and the emptied
folders after them, so nobody deletes anything by hand.

The build's log moves to logs\HomerDev-build-yyyyMMdd-HHmmss.log, one file
per run, and each sample build's log to logs\<App>-build-yyyyMMdd-HHmmss.log
beside its script -- the convention every Homer build follows. The fixed
buildHomerDev.log and build<App>.log at the old places go the same way.

version.txt carries no byte order mark. cmd's set /p, which the app build
scripts use to read it, cannot strip one, and a build refused a kit of
exactly the version it asked for when one was present. normalizeHomer
already knew this; the file had been saved wrongly.

# 1.28.0 -- 24 September 2026

HomerComponents.iss gained a sixth homerAdd argument, the registry Uninstall
key name, checked under HKLM, HKCU and WOW6432Node. An installer runs
elevated, where winget is often unreachable and a per-user tool is not on
the PATH, so Ollama read as absent on a machine that runs it daily. It also
gained Ollama model detection (homerModelPresent, homerModelWanted,
homerModelLabel) from one ollama list call, and Install-Reinstall-Update
grouping with case-insensitive alpha sorting within each group.

homerInstall.cmd resolves the app name with ~f first, so a path ending in
".." cannot yield ".." as the name, and takes a noPause argument in place of
an environment variable. It and the build scripts stamp their logs with
PowerShell's Get-Date; WMIC is gone from Windows 11 and every log had been
named with zeros.

homerTidy.py writes logs\<App>-tidy-yyyyMMdd-HHmmss.log in the project the
script belongs to, worked out by climbing out of scripts, tools or exec,
rather than surveying whatever the current directory was.

Two documents: FinishPage.md, the rule for what a finish-page checkbox says
and whether it starts ticked; Logging.md, where logs go and what they open
with.

# 1.27.0 -- 23 September 2026

**Repeated speech is handled in the kit, not app by app.** `Say.say` drops a
line that repeats the last one within a second and a half, or that matches the
title of the window in front or the name of the control with focus -- the three
shapes of duplicate announcement that have been reported for years. `sayForced`
is never guarded, so a toggle can answer twice. Anything dropped is logged with
the reason.

The other mechanism, an accessible name repeating a caption, cannot be fixed at
run time and is now audited instead: every accessible name is compared against
every caption in the same source, and a match fails the check. A new section in
the guide, **Not twice: speech that repeats**, says which is which.

# 1.26.0 -- 22 September 2026

**The published repository was missing most of itself.** The whitelist in
.gitignore still named the documents at the top level, where they were before
they moved into `help`, and named neither `help`, `Tools`, `version.txt` nor the
check and release scripts. So a clone or a downloaded zip had no guide, no
history, no tools and no checker -- which is what an outside audit of the
published archive found. The whitelist is generated from RepoFiles.txt again,
and createHomerDevRepo is in RepoFiles.

**The lesson worth keeping:** the checker runs on the working folder, so it
passed while the thing people actually download was missing sixteen paths. Check
the archive, not the folder it came from.

# 1.25.0 -- 21 September 2026

Runtime logs record the conversation. **Say.onSpoken** sends every utterance to
the app's log, including those withheld because extra speech was off, so a
runtime log holds what the program said beside what the user pressed. A new
**Evidence for the AI** section in the guide sets out the four records of a
session -- build, release, runtime and the screen reader's speech history -- and
how to gather each.

**_APP_.cmd**, a template: with programs built into exec, typing the program's
name at the top of the project would find nothing. This wrapper runs the fresh
build from there.

# 1.24.0 -- 21 September 2026

**LbcMenuItem**, in Lbc.cs: a menu item that tells the screen reader both its
shortcut and its access letter. A stock item's name leaves out the shortcut;
replacing the name to put it in hides the letter, and the reader falls back to
announcing a first letter that may not work. LbcMenuItem answers both itself.
Use it for every item that runs a command; submenus keep the stock item.

**The tutorial narrator** gains a NarratorPitch setting, in semitones, applied
with ffmpeg after piper speaks so the length does not change. The default is -2
with NarratorScale 0.80: a beta tester with the high-frequency loss that comes
with age found the narrator hard to follow at 0.72 and full pitch.

# 1.23.0 -- 21 September 2026

homerTidy learns the Homer layout, and apps stop writing their own clean-up
scripts. It moves a file the installer takes from exec or help into that folder,
sends stray logs to logs, and never surveys exec or logs. A project's
**LocalFiles.txt** names what belongs on this disk but not in the repository --
the per-app customization that a separate cleanDir used to carry -- and every
line of it is written into .gitignore as never pushed.

Also fixed: two identical files the project names, such as the same script in
two sample folders, are no longer treated as duplicates to remove.

# 1.22.1 -- 21 September 2026

tagRelease joins the logs folder: each run writes
`logs\<App>-release-<date>-<time>.log` instead of overwriting `tagRelease.log` at
the top of the project. Install it with `Tools\installTools`, which copies the
kit's tools to C:\bin.

# 1.22.0 -- 21 September 2026

Development logs join the tree. Every build, clean, tidy, tutorial and audit run
writes its own file in the project's `logs` folder, named as the program names
its runtime logs: `<App>-<task>-yyyyMMdd-HHmmss.log`. One session per file, an
alphabetical sort is a chronological one, and one zip gathers them all. The build
template, homerTidy, buildTutorials, makeTutorials and makeHotkeys all follow it.

# 1.21.0 -- 21 September 2026

The development folder takes the installed shape. Sources and build files stay at
the top with ReadMe and License; programs are built into `exec`, documents live
in `help`, tooling in `scripts`. A clean-up script that predates the layout moved
DbDo's `scripts` folder as obsolete, since Windows treats Scripts and scripts as
one name -- the guide now says so.

Also recorded: why Homer menus are long and flat, when a submenu earns its place,
the function-key families, the two rules for letters with the X, Un- and Z
exceptions, and the Hotkeys.md format.

# 1.20.0 -- 20 September 2026

A demo script declares its own terms.

The tutorial .inix gains a `[global]` first section: the voices, their speeds,
the screen reader's flatness, the silence before the first word and between
passages, and where the engines are when they are somewhere unusual. Script 00
sets the series defaults and any later script can override them for itself.

That also gives the file kind a name. An .inix whose sections are speech
passages is a **demo script**, and it says so: `FileTask = demo`, the way report
and accept files declare themselves.

# 1.19.0 -- 20 September 2026

Spoken tutorials become a kit capability.

DbDo grew a set of simulated walkthroughs -- a narrator and a screen reader,
built from text files -- and the tooling was app-specific by accident rather
than by design. It is in the kit now: `buildTutorials` and `makeTutorials` in
Tools, a starter script in Templates, and a section in the guide covering the
format, the tools, the voices and what may be published.

Two things in that section are worth stating on their own.

**The voices are chosen by licence first.** Most of piper's best-known English
voices cannot be redistributed -- lessac is Blizzard 2013, research only; ryan
and the hfc pair are CC BY-NC-SA; libritts_r is fine-tuned from lessac. The kit
installs kristin and john, both trained on public domain recordings, so the
audio an app publishes is free of restrictions.

**Say the word the key comes from.** Now a universal guideline rather than a
tutorial habit: wherever a key is introduced, name the word its letter comes
from. A key whose mnemonic goes unsaid is one somebody has to memorise rather
than understand, and the association is why that key was chosen.

The same rule governs HEADINGS, which is where it is easiest to miss. A section
called "Sorting" teaches the wrong letter, because the command is Order and the
key is O. The test is simple: if the heading were the only thing somebody
remembered, which key would they press?

sayTutorial, which spoke a single script in two SAPI voices, is replaced by
buildTutorials, which does that and everything after it.


# 1.18.0 -- 19 September 2026

A script that shells out to an installer says where the window went.

`buildTutorials` in DbDo appeared to hang while fetching a voice. It was not
hung: a User Account Control prompt had opened behind everything, without taking
focus, and was waiting for an answer nobody knew it had asked for. A sighted
user gets a taskbar flash; a screen reader user gets silence.

So the kit's installer scripts now say, before they start, that Windows may ask
for permission in a window behind this one, and that Alt+Tab finds it. Where the
wait can be watched -- `consent.exe` is the prompt itself -- a script can say
"Windows is asking for permission now" the moment it appears, and give the wait
a time limit so an answer that never comes ends in a sentence rather than a
hang. The guide says all three.


# 1.17.0 -- 19 September 2026

Everything DbDo's installer taught this week, folded back in.

## The destination page

`DisableDirPage=auto` with `UsePreviousAppDir=yes`. A reinstall or an update now
asks nothing and goes where the last one went; a first install still chooses.
HomerScribe already did this and the template did not.

## Probe quoting, which cost three releases

`cmd /c` strips the first and last quote of what follows it, so a probe
beginning with a quoted path -- `"C:\...\ollama.exe" --version` -- lost its
opening quote and ran nothing. Empty output read as "not installed", and an
installer kept offering to install a tool that was already there. The whole
command is now wrapped in one more pair of quotes.

## Detect by looking, not by running

The file and the uninstall registry key are checked first: no process, no
quoting, no PATH, and an elevated installer still sees them. The tool is run
only to learn its version, never to learn whether it exists. Ollama installs per
user, into a profile an elevated installer's PATH cannot reach, which is what
made this the failure it was.

## Three entries per component, with versions in the label

One entry per state -- install, update, already current -- grouped so the ones
that do something come first, only one ever shown. The label carries the
versions and nothing else:

    Install Ollama 0.34.1
    Update Ollama from 0.33.0 to 0.34.1
    Reinstall Ollama 0.34.1 (current version)

A purpose clause belongs only in the fallback, where no version is known. The
launch and guide entries keep the words the other apps use, name and key
substituted and nothing more.

## The Results box is not a checkbox

It always runs and it must run last, so it is started from code in
`DeinitializeSetup` rather than listed on the finish page. A launch checkbox
leaves a marker instead of starting the program, and the summary starts it once
the box has been closed.

## Every probe is logged

Command, exit code, output. Three rounds went into finding a fault that one
logged probe would have shown at once.


# 1.16.0 -- 19 September 2026

Finish-page checkboxes that look before they offer.

DbDo's installer offered to install Ollama on a machine that already had it.
The guideline said what the finish page should contain and not that a checkbox
must first ask the machine, so the template did not either.

Both now do. `ollamaState` asks winget, then looks for the per-user copy at
`%LOCALAPPDATA%\Programs\Ollama\ollama.exe`, and caches the answer: 0 not
installed, 1 out of date, 2 current. `ollamaNeedsInstall` and `ollamaIsPresent`
gate the entries, and `descOllama` writes the label -- install, update, or
reinstall -- so the checkbox says what it would actually do. The pattern is
EdSharp's `devToolState`, at the scale a smaller app needs.

The guide also now states what was previously only in the template: the last
checkbox runs `homerFinish.cmd` rather than the program, because Inno runs the
entries in order and a program started last puts its window over whatever the
other entries were still saying. And it says what the Results box should hold:
the program and where it is, one line per ticked checkbox, and the log's
location. Nothing about a step that did not run.


# 1.15.0 -- 19 September 2026

`jobs` became `scripts`, and `samples` folded into `templates`.

The folder layout is now, in the installed tree: `configs`, `data`, `exec`,
`help`, `scripts`, `templates`. In the per-user tree: `configs`, `data`, `logs`,
`results`, `scripts`, `temp`. Every initial is still distinct in each listing,
and `temp` and `templates` still never appear together.

**`jobs` became `scripts`** because the word arrived from mainframe batch
processing and everybody now says scripts. Same letter, better word. `Paths.jobs`
is `Paths.scripts`, `shippedJobs` is `shippedScripts`, and the MDI frame's
command is **Run a Script on Alt+Shift+S**, where it used to be Run a Job on
Alt+Shift+J.

**`samples` folded into `templates`.** A template that shows what is possible is
a sample with a purpose. The alternatives collided: `examples` wants e, which is
`exec`, and `demos` wants d, which is `data`. The installer template ships one
folder now, with a comment saying why.

DbDo needs no change for this: it already keeps its scripts in `Scripts\`.


# 1.14.1 -- 19 September 2026

The build template fetches what it needs.

Reviewing DbDo's build against the kit's own showed that the kit was not
following its own rule in two places. A build script asks the web for what it
needs rather than asking the person, and the template said "Inno Setup was not
found. To produce the installer, open the .iss and click Compile" -- which is a
manual step -- and left pandoc to the same fate.

Both are now installed with winget when they are missing. A missing Inno Setup
after that attempt fails the build rather than quietly skipping the installer,
because the installer is part of a release. And an ISCC that returns 0 without
writing the .exe now fails too.


# 1.14.0 -- 19 September 2026

A module can need an assembly, and now it says so.

DbDo's first build against the kit failed with four copies of

    error CS0246: The type or namespace name 'ZipArchive' could not be found

in `Inix.cs`. Nothing was wrong with `Inix.cs`: reading and writing .xlsx means
reading and writing a zip archive, csc does not resolve `System.IO.Compression`
from csc.rsp, and DbDo's build script did not pass it. The kit's own template
always had, which is why the samples never showed it.

That is the same class of fault as `Mdi.cs` needing `KeyMap.cs`, one level
lower, and nastier: a missing module reports a missing NAME and points at the
build script, while a missing assembly reports a missing TYPE and points at the
module.

So a module now declares both:

    // REQUIRES: KeyMap.cs, Lbc.cs, Log.cs, Paths.cs, Say.cs, Util.cs.
    // ASSEMBLIES: System.IO.Compression.dll, System.IO.Compression.FileSystem.dll.

`Inix.cs`, `Say.cs` and `Web.cs` carry ASSEMBLIES lines, and `checkHomerDev`
reads every build script -- the samples', the templates', and any other it is
pointed at -- for one that compiles a module without the references it names.


# 1.13.5 -- 19 September 2026

`Announce.md` carries the facts a reader asks for first.

Jamal's own explanation of the project, written after the first posting, added
what the draft had left out: that the project consolidates decades of screen
reader oriented development under Windows; that the classes come in equivalent
C# and Python versions, the C# for .NET Framework 4.8 which builds on any modern
Windows and the Python for any recent version; that the functionality covers
layout by code, standard dialogs, and components that help a screen reader user
work with AI assistance or by hand; and that template files help with a build
script and an Inno Setup installer.

All of that is now in the announcement, in the places where a reader would look
for it, and the piece is still one posting at about 2,800 characters.


# 1.13.4 -- 19 September 2026

`Announce.md` leads with what somebody gets.

The previous version listed what the kit contains and left the reader to work out
why that mattered. It now opens with the benefit -- building a small Windows tool
of your own should not require first discovering, by trial and error, what makes
a program work well with a screen reader -- and the features appear underneath as
what makes that possible.

It also follows the form of the other Homer announcements: a title and subtitle,
the date, the licence, the link, and plain paragraphs. One piece of content, 2,581
characters, which fits a LinkedIn post, a Facebook post, or an email as it
stands.


# 1.13.3 -- 19 September 2026

`Announce.md` is one announcement.

It held three versions and a page of notes about character limits and editorial
intent. None of that belongs in a document whose job is to be posted. The file is
now a single piece of content, 2,241 characters of body, which fits LinkedIn's
3,000-character cap, fits Facebook, and reads as an email.

It opens with what the kit is, then says what it is built on, then the features,
then the checks, then the samples, the licence and the link. No headings about
where to paste it and no commentary about itself.


# 1.13.2 -- 19 September 2026

The announcements say what this actually is.

## All four programs built at 1.13.1

FruitBasketCs, FruitBasketMdiCs, FruitBasketMdiPy and FruitBasketPy each
produced their executable, and the kit audit found 0 problems.

## Announce.md, rewritten around the honest claim

The three posts now say the true thing rather than the impressive one: this is
about twenty years of learning consolidated into one place, with AI making the
consolidation practical, so that somebody else can start from foundations that
work rather than from a blank file.

Both halves of that are stated plainly. The knowledge is not new and the posts
do not pretend it is. The consolidation is what is new -- gathering decisions
scattered across a dozen programs, writing down why each is what it is, and
checking that they still hold is work that was always worth doing and never
quite got done -- and it is honest to say that AI is what made it affordable.

The posts also say that the kit covers both shapes these tools take: a graphical
window, or a command line with the same settings and the same log.

The file now opens with what the announcements deliberately avoid: no claim to be
first, no promise about what somebody will build, no number that cannot be
checked.

Lengths are measured rather than estimated: the short post is about 1,600
characters, the standard post about 2,500, and the email version longer because
email has no limit.


# 1.13.1 -- 19 September 2026

One command for the whole release.

## All four samples built at 1.13.0

`buildHomerDev` converted the documents, built FruitBasketCs, FruitBasketMdiCs,
FruitBasketMdiPy and FruitBasketPy, and found 0 problems.

## releaseHomerDev

    releaseHomerDev "What changed."

Four steps, stopping at the first failure: `installTools` puts the kit's current
tools on the PATH so an old `tagRelease` cannot refuse the release;
`checkHomerDev` records the environment, builds everything from clean, checks the
dependency rule and the tools on the PATH, and drives every program through its
keys with uiCheck; `gitPush` commits and pushes what the whitelist allows; and
`gitRelease` tags and publishes.

Nothing in it is a test somebody has to remember. What it cannot do is read the
third list of its own evidence report -- what remains uncertain -- and that is
the one thing to do before announcing.

`gitRelease` now prefers `checkHomerDev` when the folder has one, so releasing
the kit runs the kit's own check rather than the per-app one.


# 1.13.0 -- 19 September 2026

The keys are now pressed by a script.

## uiCheck

    uiCheck                    every uiTest.inix beside the script
    uiCheck --path C:\JobDo    an app's own tests

It starts a real program, sends keystrokes, and reads back the Windows UI
Automation tree -- the same interface a screen reader uses to find out what is
on the screen. A control with no accessible name is invisible to both, so a
check that finds nothing has found something real.

Tests live beside the program in `uiTest.inix`: `Run` names the program, then
each `[step]` has `Keys` to send, `Wants` for a string that must appear in the
tree, `Title` for a window that must exist, and `Escape` to close what the step
opened. pywinauto does the driving and installs itself on first run.

`Samples\uiTest.inix` drives all four samples, including every key an MDI app
gets free: Control+N for a second window, F4 for the window list, Alt+Shift+J
for the job list, Alt+Shift+C for the settings list, Alt+F1 for about.

This replaces the last instruction in this project that said "open it and press
the keys". A check a person has to remember is a check that stops happening in
the week it matters.

## checkHomerDev checks the machine too

Two additions, both from faults that actually happened:

- **The environment is recorded** -- which Python and which pandoc the run
  actually used -- so a report says what it was produced with.
- **Every tool on your PATH is compared with the kit's copy.** A release failed
  on a `tagRelease` from before source-only releases were supported, and nothing
  could see it, because the kit only inspected itself. When the check reports a
  stale tool, `Tools\installTools` fixes it.

`checkHomerDev` now runs uiCheck as its last step, so one command builds
everything from clean and then drives it.

## What is still not automated

Speech. UI Automation reports that a control exists and what it is called, not
what JAWS said. NVDA can log what it speaks at debug level, so a future check
could run a scripted session and read that log back. It is written down as the
next step rather than claimed as done, and every report says so.


# 1.12.1 -- 19 September 2026

Everything builds; the release itself needed one more script.

## All four samples built, and the kit audited clean

`buildHomerDev` converted the documents, built FruitBasketCs, FruitBasketMdiCs,
FruitBasketMdiPy and FruitBasketPy, and found 0 problems. That is the first run
where the whole kit -- three shapes, two languages, one command -- came through
in one pass.

## tagRelease failed, and it was not tagRelease

    Could not find HomerDev_setup.iss in C:\HomerDev

That is a `tagRelease` from before source-only releases were supported. The kit
has carried the fixed one since 1.1, in `Tools`, but the copy that runs is the
one on the PATH, and nothing had ever updated it.

`Tools\installTools.cmd` does that now. It copies checkHomerApp, gitPush,
gitRelease, homerTidy, sayTutorial and tagRelease to a folder on the PATH --
`C:\bin` unless another is named -- and says plainly if that folder is not on
the PATH. Run it after updating the kit.

The lesson generalizes: a tool that acts on the current directory is meant to
have one copy, and one copy means one copy that can go stale. `Developer.md` now
opens with the release sequence, `installTools` included.

## Smaller things

- The migration list covers the MDI sample's rename, so the old
  `FruitBasketMdi.exe` and its log go on the next build.
- The tutorial playlist no longer implies the two planned episodes are written.
  They are not.


# 1.12.0 -- 19 September 2026

The MDI shape in both languages, two lists that matter, and an FAQ.

## FruitBasketMdiCs and FruitBasketMdiPy

The MDI sample is now a pair, like the single-dialog one. `homer\mdi.py` is the
Python side of `Mdi.cs`: same command names, same keys, same title rule, same
menus. So the claim the kit makes -- one behaviour, either language -- now holds
for all three shapes rather than two.

One honest note, which is in the file as well: `lbc.Dialog` builds a dialog, and
a wx dialog cannot be an MDI child, so the band layout in `mdi.py` is written
again rather than reused. Everything that makes a control accessible IS reused.
Lifting lbc's building methods into a mixin that a dialog and a panel can share
is the next refactor, and it has not been done.

## One command builds everything

`buildHomerDev` now converts the documents, **builds all four samples**, and
audits the kit. Somebody who changes a shared class should not have to remember
four build scripts; a problem anywhere surfaces from the one thing they already
run. Each sample still writes its own log beside itself, and a failure is named
on screen with the log that holds the compiler output.

`checkHomerDev` is unchanged in purpose and now covers all four: it cleans
first, checks the module dependency rule, and writes the evidence report.

## Run a Job, and Change a Setting

Every MDI app now gets two more commands free:

    Alt+Shift+J    run a job: a list of the scripts in the jobs folder
    Alt+Shift+C    change a setting: a list of what this program lets you change

Both are lists, and `HomerDev.md` says at length why. Briefly: without sight, a
folder is a sequence to be heard and a typed path is a spelling test, while a
list is reached by one key and narrowed by first letter. The job list is read
fresh every time, so dropping a script into the folder makes it available with
nothing to register. The user's own jobs live in the per-user tree, where an
update cannot overwrite them, and appear above the shipped ones.

Settings are declared by the app with `addSetting`, changed through one field,
saved the moment they are answered, and handed back to the app through
`onSettingChanged` so they take effect at once. No file to edit by hand, no
twenty-control preferences dialog, no restart.

## FAQ.md

A new standard document, in `help` with the others. It answers the question that
comes first from outside the Windows world -- why not Mac -- plainly: this kit
is built on decades of Windows screen reader experience and exists to make that
experience as good as it can be; that depth is missing for other platforms, and
writing conventions I had not lived with would produce confident guidance that
turned out to be wrong. The code is MIT licensed and developers on those
platforms are welcome to it.

The full document set is now `ReadMe.md` and `License.md` at the top, and in
`help`: `<App>.md`, `Announce.md`, `Developer.md`, `FAQ.md`, `History.md`,
`Hotkeys.md` and `Tutorials.md`.


# 1.11.0 -- 19 September 2026

Ready for a first public release.

## The documents now say what the kit does

A full pass over every document against the actual contents of the folder. What
had drifted:

- The kit has **twelve** C# modules, not nine. Inix, KeyMap, KeyName, Lbc, Log,
  Mdi, Paths, PdfRead, Say, Util, Web and inixVert.
- The Python side has **seven** modules -- inix, lbc, log, paths, say, util and
  web -- plus the package file and the version file the build writes.
- There are **three** samples, not two.
- `Style\` no longer exists; its files are in `help`. Three documents still
  pointed at the old path.
- `Developer.md` carried the folder tree from three layouts ago.
- `Hotkeys.md` had no section for the MDI frame's keys, which every
  multiple-document app gets for free.

## Announce.md is now three announcements, each already the right length

The Word document made from `Announce.md` was always far too long to paste into
a post, which is the wrong way round: the document should hold posts that are
ready to use.

It now holds three, with their character counts measured rather than estimated:

- **the short post, about 1,700 characters** -- fits anywhere, including a
  mailing list digest or a forum with a tight limit
- **the standard post, about 2,200 characters** -- for LinkedIn and Facebook
- **the email version** -- longer, plain text, with a subject line

LinkedIn caps a post at 3,000 characters including spaces, which its own help
page states, and that is the only limit that rejects a post outright. Facebook's
is far larger. The limit that decides whether anybody reads it is smaller than
either: roughly the first 140 to 210 characters are shown before a "see more"
link, so both posts are written to carry their point in the first two sentences.

The file also says what the announcements deliberately avoid: no claim to be the
first anything, no promise about what somebody will be able to build, and no
number that cannot be checked.


# 1.10.1 -- 19 September 2026

The build now clears up after a move.

## All three samples built at 1.10.0

FruitBasketCs, FruitBasketMdi and FruitBasketPy each produced their program
again, so moving the documents disturbed nothing that compiles.

## Twenty documents, when there are twelve

The 1.10.0 run converted 20 documents instead of 12. Unarchiving over an
existing folder adds and replaces; it never deletes. So every document that
moved into `help` was still sitting at the old path as well, and `Style` was
still there beside it. Two files with the same name and different contents is
worse than either alone.

The previous release answered that with a sentence telling the user to delete
the old copies. That was the wrong kind of answer, and it broke a standing rule
of this kit: ship a script that makes the change, not a step for somebody to
carry out.

`buildHomerDev` now does it. It carries a list of pairs -- where a file used to
be, and where it is now -- and removes the old copy when, and only when, the new
one is already in place. The same list clears the folders an earlier layout
left empty: `Style`, `Python\homer`, and the three per-sample folders from
before the samples were flattened. It is logged file by file and summarized in
one line on screen.

Every move the kit has made is in that list, back to `Keys.cs` becoming
`KeyName.cs`, so a machine carrying any earlier version tidies itself on the
next build.


# 1.10.0 -- 19 September 2026

A place for the documents, and two scripts for releasing.

## help, the tenth folder

`help` joins the layout, at the same level as configs, data, exec, jobs, logs,
results, samples, temp and templates. Its letter, h, was free, and it holds every
document -- the guide, `Tutorials.md`, `History.md`, `Hotkeys.md`, `Announce.md`,
`Developer.md`, the style guides and the tutorial scripts -- in both `.md` and
`.htm`.

`ReadMe` and `License` stay at the top of the project. That is not sentiment: it
is what GitHub recognizes, and it is where a person opening the folder for the
first time looks.

**Why not `docs`, which is the GitHub convention?** Because `d` is `data` here,
and the letters are the point of the layout. What that costs is one feature:
GitHub Pages published from a `/docs` folder. Homer apps are listed from the
separate HomerTools site instead, so nothing is actually given up. README
recognition is unaffected, since the ReadMe stays at the root. Community health
files, if a project ever wants them, go in `.github`, which GitHub also
recognizes and which leaves the letters alone.

## Tutorials.md and Announce.md join the standard set

The full documentation set is now: `ReadMe.md` and `License.md` at the top, and
in `help`: `<App>.md`, `Announce.md`, `Developer.md`, `History.md`,
`Hotkeys.md` and `Tutorials.md`. Every one has a matching `.htm`, and
`checkHomerApp` checks for all of them in their right place.

`Tutorials.md` holds nine worked scenarios -- starting an app, adding a field,
finding out what a key does, turning one window into many, reading a log,
writing acceptance criteria, changing a shared class, releasing, and asking an
AI for a Homer app -- plus the audio tutorial playlist and how to record more.

## gitPush and gitRelease

Both from the versions in daily use, with three changes. `gitPush` takes the
commit message as an argument instead of always saying "Fix.", refuses to run
outside a git repository rather than creating one by accident, and writes a log.
`gitRelease` runs `checkHomerApp --build` first and stops if anything failed,
because a release is the one moment where a fault costs somebody else time
rather than you. `--skip-check` is there for when you already know.

Both stage only what the whitelist allows, so `git add -A` means "everything the
project has named" rather than "everything in the folder".

## Every file, listed

`HomerDev.md` gained a manifest: every file in the kit with one line saying why
it is there, grouped by folder. A file you have not seen before can now be
looked up rather than guessed at.


# 1.9.0 -- 19 September 2026

The kit can now check itself with a compiler.

## All three samples built at 1.8.1

FruitBasketCs, FruitBasketMdi and FruitBasketPy each produced their program.
The MDI one is the news: it is the first real exercise of the adopting
constructor added to `LbcDialog`, so an MDI child laid out by the same builder
as a dialog now has a compiler's word for it.

## checkHomerDev

    checkHomerDev
    checkHomerDev --deep
    checkHomerDev --no-clean

It runs the kit audit, checks the module dependency rule, deletes what previous
builds wrote, builds all three samples with their own scripts, and writes
`evidence-kit-<yyyymmdd-hhmmss>.md` beside itself. Exit code 1 when anything
failed, so a release script can act on it.

The cleaning is the part that makes the answer mean something. A build that is
not run still leaves yesterday's executable in the folder, and an existence
check would call that a pass.

**The dependency check is new and general.** Every module may declare what it
needs in a `// REQUIRES:` line, and the check reads every build script -- the
samples' and the templates' -- for a script that includes a module without one
of its requirements, ignoring commented lines, since a commented module is one
deliberately left out. Today `Mdi.cs` is the only module with a REQUIRES line.
The check exists because that was not true a release ago.

**Why it exists, in three failures.** 1.5.0 shipped a class-name collision that
stopped `Lbc.cs` compiling. 1.6.0 shipped a build script that treated a missing
`version.txt` as fatal after the samples' were removed. 1.8.0 shipped `Mdi.cs`
without `KeyMap.cs` beside it. Every check in the kit read files; none compiled
anything; a user found all three. A compiler is the only instrument that answers
"does this still work."

**What it does not do**, and says so in every report: it does not run the
programs. All three samples are windowed, and a check that needs a person to
close a window is not a check. What a screen reader says is still for a person
to hear, and the report's uncertain list names that first.


# 1.8.1 -- 19 September 2026

Three faults from the first run of 1.8.0, and one of them is a new kind.

## The MDI sample would not compile

    Mdi.cs(137,13): error CS0103: The name 'KeyMap' does not exist in the current context

Nine times over. `Mdi.cs` registers every command with `KeyMap` as it is added,
and `KeyMap.cs` was commented out in the build script, as it has been in every
Homer build script since the switches were written.

This is a kind of fault the kit had not had before: **a shared module that needs
another shared module**. The module list was written as though every file were
independent, and until MDI arrived every file was. Three changes:

- `Mdi.cs` now states what it requires at the top, where a reader looks.
- The build template pairs KeyMap and Mdi under one comment, since turning on one
  without the other cannot work.
- The MDI sample's build script switches both on.

`Mdi.cs` and `KeyMap.cs` are the only pair in the kit. Everything else is
independent, and the comment in the template says so, so nobody hunts for
dependencies that are not there.

## The C# and Python samples both built and ran

FruitBasketCs and FruitBasketPy each produced their program on the first try at
1.8.0, which means the adopting-constructor change to `LbcDialog` did not disturb
ordinary dialogs. The MDI sample is still the real test of that seam.

## The kit check audited files the build had written

`Version.cs` and `version.py` are generated on every build and are already in the
never-pushed list, so their encoding says nothing about the kit. Both the kit
check and `checkHomerApp` now skip them.


# 1.8.0 -- 19 September 2026

MDI, and the three shapes named.

## Mdi.cs

`MdiFrame` and `MdiChild` carry the frame of a multiple-document app, so
EdSharp, FileDir and DbDo can share one implementation instead of three that
drift. Free with the frame: the window picker on F4, the spoken window list on
Shift+F4, next and previous, close and close-others, the alternate menu on
Alt+F10, the key describer on Control+F1, about on Alt+F1 and the guide on F1.
Commands are named sentences rather than control ids, registered with KeyMap as
they are added, so the menu, the alternate menu, the key describer and the
hotkey document cannot disagree.

The design is the Homer.NET MDI fruit basket of 2010 -- LbcMdiApp, LbcMdiFrame,
LbcMdiChild, a menu declared by name and key, focus tips, a window picker, an
alternate menu, a key describer. That program was right about the shape; this is
the same shape with today's classes under it.

The title rule is enforced rather than documented: the frame carries the app
name, a child carries its subject, and `setTitle` is the only way to set one.

## LbcDialog can adopt a form

A dialog and an MDI child differ in how they are shown, not in how they are laid
out. `LbcDialog` now takes an optional existing form and builds into it, so a
child gets add-order focus, the status line, the list search, the line chords
and the access keys from the same code a dialog uses. An adopted form is
finished with `layoutIntoForm`, which sizes it and sets the opening focus
without showing anything, because the frame shows the child.

## FruitBasketMdi.cs

The third sample. It does not repeat the nine decisions -- FruitBasketCs still
carries those -- and marks only what changes when a program holds several things
at once: the title rule, commands as sentences, what the frame gives free, state
per window, and closing the last window closing the program.

## The guide names the three shapes

A single tool with a command line and a dialog; a desktop-only program whose
dependencies decided that; and a multiple-document program. The consistent flags
for the first are written down -- `--help`, `--gui`, `--version`, `--log`, and an
unknown switch refused rather than ignored -- and so is the list of everything
all three share, which is nearly all of it.


# 1.7.0 -- 19 September 2026

The kit learnt to produce evidence.

## checkHomerApp

    checkHomerApp
    checkHomerApp --build
    checkHomerApp --path C:\JobDo

Eleven checks, each recorded with the command that ran it and the exit code it
returned: the document set and its HTML, encodings, zero-byte files, the
version's single source of truth, the publishing whitelist, whether the program
opens a log, accessible names that repeat a caption, reserved key combinations
and access keys claimed twice, the build, a smoke run of `--help`, and the app's
own acceptance criteria. It writes `evidence-<yyyymmdd-hhmmss>.md` and exits 1
when something failed, so a script can act on it.

The report says three things, and the third is the point: what was verified,
what was not checked, and what remains uncertain. A skip is never counted as a
pass. The uncertain list is printed every time, because a report claiming
everything is fine is worth nothing.

Two rules are built in, both learned on its first run. It ignores the kit's own
modules, since a shared class sets accessible names and names key combinations
on purpose, and it ignores comment lines, since a comment explaining that
Alt+Control is reserved is the rule rather than a breach of it. A checker that
cries wolf teaches people to ignore it.

On that first run it found a real fault: both fruit basket samples had given the
access key S to two controls at once. Fixed -- the speaking check is now
"Spea&k each change".

## accept.inix

What "done" means, written before the code is:

    [check]
    Name   = the help text names every switch
    Run    = JobDo.exe --help
    Expect = 0
    Wants  = --source

Four fields and no more, because the point is that criteria get written.
`Templates\accept.inix` starts a new app off; `Samples\accept.inix` checks that
both fruit baskets build and produce their programs.

## The guide gained two parts

"Evidence, and checking without sight" explains the instrument and the three
lists. The AI-assisted coding part gained "the method, in four moves" --
specify, build in small recoverable steps, verify, package and defend -- with
what in the kit carries each.


# 1.6.1 -- 19 September 2026

Two faults from the first run of 1.6.0, both mine.

## A missing version.txt stopped the build

Flattening the samples in 1.5.0 removed their `version.txt` files, on the
grounds that a sample is never released and so has no number to step. The build
script still treated a missing one as fatal, and both samples failed at the
first line that mattered:

    ERROR: version.txt not found.

A build needs a number whatever else is true -- the program reports it, the
installer carries it, the release tag is it. So a missing `version.txt` is now
created holding 1.0.0 and the build carries on, in both templates and both
samples. Stopping there left a manual step, which no Homer build does.

## The kit check walked into a virtual environment

`buildHomerDev` audits every text file in the kit. The Python sample's build had
left a `.venv` beside it holding the whole of PyInstaller, so the check dutifully
audited several thousand files that belong to somebody else and wrote 611 KB of
complaints about their line endings.

Two changes. The check and `homerTidy` now skip the folders a build makes --
`.git`, `.venv`, `__pycache__`, `build`, `dist`, `notes`, `venv` -- and those
folders join the never-pushed list. And the console now shows the first twenty
problems and says how many more there are, with every one of them in the log. A
console that scrolls for a minute tells a screen reader user nothing at all.

## Also

The Homer module list in the C# build template is now in lowercase alphabetical
order, which it had drifted out of when KeyName was renamed.


# 1.6.0 -- 19 September 2026

A folder layout whose initials are all different.

## The nine folders

`configs`, `data`, `exec`, `jobs`, `logs`, `results`, `samples`, `temp`,
`templates`. Nine folders, nine different first letters, because a screen reader
user reaches a folder by typing its initial and duplicated initials turn one
keystroke into several.

`temp` and `templates` both begin with t and never appear together: `temp`
exists only in the per-user tree, `templates` only in the installed tree. That
is where each belongs anyway -- a temp folder under Program Files cannot be
written to, and templates are shipped and read-only -- so no folder needed an
unobvious name, and the rule that makes it hold is simply that temp always lives
in the per-user tree, portable copies included.

## Paths.cs and homer/paths.py

New, and parallel: the two trees, the nine folders, and three things every app
was writing for itself.

- `configFile` hands back the user's copy of a settings file, making it from the
  shipped one the first time it is asked, so an update never overwrites a
  change somebody made.
- `clearTemp` empties the temp folder at startup. Whatever it finds is what a
  previous run could not clean up after itself.
- `tempFile` names a scratch file nothing else is using.

`Log` now asks `Paths` for its folder, so one class decides the layout.

## The installer lays the tree down

`[Dirs]` creates the six shipped folders, and the files go where they belong:
the executable and the DLLs in `exec`, the shipped `.inix` in `configs`, seed
data in `data`, scripts and the screen reader packages in `jobs`, and `samples`
and `templates` as shipped. The documents stay at the root of the installed
tree, where somebody looking for the ReadMe expects them.

One consequence to plan for: `{app}\<App>.exe` became `{app}\exec\<App>.exe`.
Shortcuts, the uninstall icon and the finish helper were all updated, but an app
adopting this layout should be reinstalled rather than updated in place the
first time.


# 1.5.0 -- 18 September 2026

A failed build, a flatter tree, and a tutorial.

## The C# build failed, and the cause was a name

The first real build of FruitBasketCs against the kit stopped with

    Lbc.cs(368,60): error CS0721: 'Keys': static types cannot be used as parameters
    Lbc.cs(368,29): error CS0115: 'LbcForm.ProcessCmdKey(ref Message, Keys)':
                    no suitable method found to override

Homer's key-name class was called `Keys`, and so is the WinForms enum that
`ProcessCmdKey` takes. In one namespace the static class wins the lookup, the
override no longer matches, and an app writing `Keys.Delete` gets an ambiguity
error as well. The class is now **KeyName**, in `CSharp\KeyName.cs`, and the
file says at the top what the old name cost. Nothing else calls it yet, so
nothing else breaks.

The Python build succeeded on the first try and produced FruitBasketPy.exe.

## A flatter tree

Two folder levels went, because navigating them by screen reader is slower than
reading a longer list:

- `Python\homer\` became `homer\`. A Python app now puts the kit itself on the
  path rather than a subfolder of it.
- `Samples\FruitBasketCs\` and `Samples\FruitBasketPy\` became a flat
  `Samples\` holding four files. The samples' `version.txt` files went with
  them: a sample is never released, so it never had a version to step.

Nothing is deeper than two levels now. Every build script, document and check
was repointed.

## The tutorial

`Tutorial_HomerDev.inix` is a spoken walkthrough in the step format the existing
makeTutorial.py already reads: `Say` for the narration, `Key` for the keystroke,
`Hear` for what the screen reader answers, `Note` for the written version. It
covers what the kit is, unarchiving it into `C:\HomerDev`, running
`buildHomerDev`, building and running both fruit baskets, and the point the
whole thing exists to make -- that the two behave the same because the behaviour
lives in the components rather than in either program.

`Tools\sayTutorial.cmd` and `.py` render it to audio in **two voices**: the
narration in one, the screen reader's answers in another, because a listener who
cannot see the screen has no other way to tell the teacher from the machine.
Windows' own voices do the speaking through System.Speech, so nothing is
installed and nothing is uploaded. One .wav per line, kept, and one .mp3 when
ffmpeg is present.


# 1.4.0 -- 18 September 2026

Logging, publishing, and a notebook.

## Every program and every installer keeps a log

`CSharp\Log.cs` and `homer\log.py` are the same class in two languages:
same file name, same folder, same header block, same method names -- start,
close, line, info, warn, error, section, keyValue, command, exception, prune,
show. Both were taken from the two implementations that already worked and had
converged separately, HomerScribe's C# session log and HomerView's Python
logger.

    %LOCALAPPDATA%\<App>\logs\<App>-<yyyymmdd-hhmmss>.log        one per run
    %LOCALAPPDATA%\<App>\logs\<App>-setup-<yyyymmdd-hhmmss>.log  one per install

One file per session, named for when the session began, with the most recent
thirty kept. The header block records the version, the program, the working
directory, the command line, the Windows build, the user, the machine and, in
C#, which screen reader Say can reach.

The installer template now sets `SetupLogging=yes` and copies Inno's own log
into the same folder at ssDone, after the final-page checkboxes have run. The
one caveat -- an elevated installer writes to the elevating account's profile --
is documented where it happens rather than left to be discovered.

Logging is deliberately not optional. When it becomes so, the switch goes inside
the class rather than into every caller.

## .gitignore became a whitelist

`RepoFiles.txt` names what the repository carries, and `homerTidy --gitignore`
turns it into a `.gitignore` that ignores everything and puts back exactly what
was named. A file dropped into the folder is invisible to git until somebody
names it.

This replaces a habit rather than codifying one, so it is worth saying why: a
list of exclusions is only ever as complete as the last time somebody remembered
to add a line, and the tidy scripts existed because things got pushed that should
not have. A blacklist cannot fix that class of problem.

A never-pushed list overrides the whitelist for private and generated files:
self.md, self.htm, tagRelease, create<App>Repo, every .log, notes\, Version.cs,
version.py, __pycache__\ and the build products.

## self.md

A new Homer convention: a dated, headed notebook in every project, never
published. It holds decisions with their rejected alternatives, findings, and
honest open items -- the things History.md cannot hold because History.md is
public and is about releases.

The kit's own `self.md` opens with a report on what a full reading of DbDo,
EdSharp, FileDir, HomerScribe, HomerView, 2htm, extCheck and urlCheck found:
what the apps had already converged on, what they disagreed about, what they got
wrong, and a review of every one of the kit's inclusion decisions against that
evidence. `newHomerApp` writes a starter into each new app.

## Smaller things

- Both samples now open a log first and record what they do, and their headers
  list the keys that arrive free with an Lbc text box and list box: Control+C
  with nothing selected, Control+J to search a list, F3 to repeat, Alt+F8 to
  read all, F8 and Shift+F8 to mark, Control+Enter to accept from anywhere.
- Hotkeys.md gained a list box section; the list-search keys had been missing.
- ReadMe.md's quick start now walks the whole path: install the kit, build and
  run both fruit baskets, try the free keys, read the two side by side, look at
  the log, start an app, publish it.


# 1.3.0 -- 18 September 2026

The two samples were rewritten to be read side by side.

## Twelve blocks, the same in both

Each sample now carries twelve markers of the form `---- BLOCK n: <title> ----`,
with the same numbers and the same titles in each file, and the same function
names throughout: addFruit, basketState, handleButton, saveBasket, settingsPath,
showReport, showState, sortBasket. Somebody with both files open can move
between them by block rather than by searching.

They deliberately do not track line for line. C# needs a class where Python
needs none, and pretending otherwise would teach padding rather than design. The
rule kept instead: nothing appears in one file without a counterpart in the
other, and the counterpart carries the same name.

Three places where the two genuinely differ are commented where they happen: how
each library keeps a dialog open while a button does work, the different shapes
of stringPlural, and the status line that C# has and wx does not.

## More of Lbc, on purpose

The samples now use a combo pick box for the sort order, a check box to turn the
speaking off, a read-only report window, a status line in C# and the window
title in Python, tips on every control, and the list search and line-editing
chords that come free with a list box and a field. More than a fruit basket
needs, which is the point of a sample; the guide now says so plainly, so nobody
reads the sample as a minimum.

## A wart found by making them parallel

`Util.stringPlural` in C# returns the count and the noun together, "3 fruits";
`util.stringPlural` in Python returns only the noun, "fruits". Two functions,
one name, two shapes. Neither was changed here, because the Python one has
callers in HomerView, but both samples now say so where they use it, and the
Python one should take the C# shape the next time that add-on is touched.


# 1.2.0 -- 18 September 2026

The kit became a teaching kit.

## The fruit basket came back

`Samples\FruitBasketCs.cs` and `Samples\FruitBasketPy.py` hold the same program twice:
once on the C# classes, once on the Python package, with `buildFruitBasketCs.cmd`
and `buildFruitBasketPy.cmd` producing `FruitBasketCs.exe` and
`FruitBasketPy.exe`. The Python one is a single file with Python and every
dependency inside it, built with PyInstaller in a virtual environment beside the
script, so it installs on the same terms as a C# program.

The specification is the one from 2005, and the legacy collection of thirty-six
implementations is what it comes from. That collection answered "what does this
language look like". These two answer "what does a program look like when it is
built out of components that already know the conventions", which is the
question a builder working with an AI actually has.

Nine numbered comments in each sample mark the nine decisions a working program
has to get right and an AI will not make unless it is asked: which library, add
order as focus order, bands, access keys, what the screen reader already says,
where the focus goes, counts that match their nouns, saving as the answer is
given, and the escape hatch. The two files number them identically so they can
be read side by side.

## AI-assisted coding, written down

A new part of HomerDev.md explains why the kit prefers that name to vibe coding,
gives the three sentences that carry most of the kit into an AI session, and
sets out a five-step teaching sequence around the samples: ask for the program
cold, read the sample, ask again with the conventions, read the other language,
then change one thing and watch which decisions it touches.

## The build scripts look in three places

Both build templates now find the kit in this order, first hit wins: the
`HomerDev` environment variable, then `C:\HomerDev`, then the current directory.
The third is what lets a sample, a demonstration, or a machine with no kit
installed still build, by carrying its own copy of the folder.

## The templates became opinionated

Every component any Homer app has ever needed is now listed in both build
templates as a switch. The ones used by more than one app are switched on --
configuration file, documentation through pandoc, icon, installer, manifest,
NuGet fetching, screen reader scripts, version stepping -- because that is the
evidence the next app will want them too. The ones used by a single app are
commented out with the app named, so turning one on is one character: exiftool,
ffmpeg, Markdig, NPOI, PdfPig, SQLite, Tesseract, Ude and Whisper on the C# side;
beautifulsoup4, pillow, playwright, pythonnet and requests on the Python side.

A single `:getNuGet` subroutine now does every package fetch, so Markdig, NPOI,
PdfPig, SQLite and Ude are one line each rather than five variations on the same
PowerShell.

## Smaller things

- `newHomerApp <App> --python` writes a Python app: the Python build script in
  place of the C# one, with the rest of the set unchanged.
- Alphabetical order is now a stated convention for every list in Homer code and
  documentation, unless another order is clearly more logical. The module lists,
  the component switches and the option catalogues in this release all follow it.


# 1.1.0 -- 18 September 2026

Everything in this release came from running 1.0.0 for a day and from the logs
of apps the kit had not yet been tried on.

## tagRelease could not release a source-only project

The log said it plainly: "Could not find HomerDev_setup.iss in C:\HomerDev".
The kit ships source and has no installer, and the script treated a missing
setup script as a fatal error rather than as an answer. It now recognizes two
kinds of project. One with an installer is released exactly as before, from the
version stamped into <App>_setup.exe with that installer attached. One without
is released from version.txt, with no asset and no URL check. Nothing on the
installer path changed, so EdSharp, FileDir, DbDo, HomerView and HomerScribe
behave as they always have.

Two smaller changes came with it. A -Path argument aims the script at a repo
without a cd first, and the header now says outright that the script acts on the
current directory, so one copy at C:\bin serves everything. The edition line in
the banner names the kit, so a log says which copy ran.

The version of tagRelease that the kit shipped in 1.0.0 was the older copy from
the EdSharp folder. The base is now the newer one, the copy actually in daily
use.

## cleanDir and tidyRepo became homerTidy

They asked the same question -- does this file belong to the project? -- of two
places, the folder and the repository, which meant two surveys, two plans, and
two chances to disagree. homerTidy asks it once and fixes both in one pass:
empty files deleted, duplicates and unnamed files moved into notes\ under
subfolders named for what they are, tracked files that do not belong untracked
and added to .gitignore under a dated comment, and anything large in the history
reported with the command that would remove it. History is never rewritten
automatically.

What belongs is still decided by the project's own <App>_setup.iss and
RepoFiles.txt, so the script needs no editing. homerPolicy.py is gone: it is
inside homerTidy now.

## The installer template learnt what is already installed

The [Code] section reads the version of any previous install from the app's own
uninstall key. The welcome page says "Install", "Update from X to Y" or
"Reinstall" accordingly, and each component checkbox is now a pair of [Run]
lines gated by a Check: function, so the wording matches the situation instead
of always saying "Install".

Three conventions were settled at the same time:

- A checkbox that installs SCREEN READER scripts or add-ons is CHECKED by
  default. A blind user installing a Homer tool wants them, and a cleared box
  they have to notice is the friction the whole suite exists to remove.
- The last two checkboxes are always documentation, unchecked, then launch,
  checked.
- The launch does not start the program. It runs homerFinish.cmd, which reads
  the setup log, shows one Results box describing what this install actually
  did, and starts the program only once that box is dismissed. Being last, it
  runs after every other checkbox, so the box can report all of them.

installScreenReaderSupport.cmd is new and generic: it unpacks <App>_JAWS.zip
into every JAWS settings folder it finds and hands <App>.nvda-addon to NVDA,
skipping without complaint whichever is absent.

## Smaller things

- version.txt is written without a byte order mark. A batch file's "set /p" and
  Inno's FileRead both take a mark as part of the number, which would have made
  every version wrong by one invisible character.
- The kit carries its own RepoFiles.txt, so homerTidy can tidy the kit.
- homerTidy leaves a project's own script logs where the scripts that write them
  expect to find them, rather than filing them into notes\logs.


# 1.0.0 -- 18 September 2026

First release. The kit was assembled by comparing every duplicated shared file
across DbDo, EdSharp, FileDir, HomerScribe and HomerView, and taking the better
version of each. What that comparison found is recorded here, because the
differences explain why the kit exists.

## Which version won, and why

- **Say.cs** -- byte for byte identical in DbDo, EdSharp and HomerScribe once
  line endings are normalized. The CRLF copy was taken.
- **Web.cs** -- identical in all four apps that carry it. The CRLF copy was
  taken.
- **Inix.cs** -- three generations were in circulation. DbDo and HomerScribe
  carried the original 29 KB codec. EdSharp carried the version that added
  `InixTable`, the converter between .inix, .csv, .tsv, Markdown and .xlsx.
  HomerView carried that plus `InixCodec.readValue`, the single-setting reader
  whose absence had every caller reading the whole file and walking the
  sections itself. HomerView's is a strict superset and was taken, which also
  means DbDo and HomerScribe had been two generations behind.
- **Lbc.cs** -- neither of the two newest copies was a superset of the other, so
  they were merged. EdSharp's is the base: it holds `LbcBandLayout`,
  `LbcBandDialog` and `LbcInixForm`, better access-key handling in the button
  row, the rule that Enter presses the button meaning accept wherever it sits,
  and `sortedIgnoringCase`. HomerScribe's contributed the horizontal band API --
  `addBand`, `endBand`, `bandTarget` and `addButton` -- with all thirteen `add`
  methods rerouted through `bandTarget()` and `addSeparator` closing an open
  band. Without that merge, HomerScribe would not compile against the kit and
  EdSharp would lose its form work.
- **KeyMap.cs, Keys.cs, Util.cs, inixVert.cs, PdfRead.cs** -- one copy each, no
  contest. Keys.cs came from HomerView, the rest from EdSharp and HomerScribe.
- **The Python homer package** -- only HomerView carries it, and it was already
  written to know nothing about HomerView.
- **tagRelease, cleanDir, tidyRepo, homerPolicy** -- these four say in their own
  headers that they are app-independent, and they are: tagRelease takes the app
  name from the directory, and cleanDir and tidyRepo decide what belongs by
  reading the project's own `<App>_setup.iss` and `RepoFiles.txt`. tidyRepo
  still named one app in five strings, and those were replaced with a name taken
  from the folder.
- **The install scripts for Pandoc, the GitHub CLI, Python, Node and Ollama** --
  these read as generic but each writes to its own app's folder and its own
  app's log, so they are not portable files. The pattern is documented in
  HomerDev.md instead, and the kit ships fresh generic `installOllama.cmd` and
  `installModels.cmd` for the local AI case.
- **The build script and the installer script** -- HomerScribe's are the newest
  and most refined of each, and became the templates.

## One behavior deliberately changed in the merge

HomerScribe's Lbc selects the text of the field that opens with the focus, and
extends that to the first focusable control rather than only an explicitly set
one. That was taken, with one change: a **multi-line** box now gets the caret at
position 0 instead of a full selection, because its value is a document rather
than a field and the Homer rule is that the caret opens on the first line. This
is the only place in the kit where the merged file is not simply the union of
what already existed.

## What is new rather than merged

- `buildHomerDev.cmd` and `.py` -- convert the documents and audit the kit:
  components present, encodings right, templates still holding their
  placeholder, no empty files.
- `newHomerApp.cmd` and `.py` -- write a new app folder from the templates.
- `Templates\_APP_.cs` -- a working launchpad app with the standard controls,
  the two message boxes, the matching command line, and settings saved as they
  are answered.
- `Templates\installOllama.cmd` and `installModels.cmd` -- local AI as an
  installer checkbox, now that more than one Homer app uses a model.
- The documentation set.
