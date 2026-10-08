# What the JAWS trainers do, and what a Homer walk should take from it

*From 185 transcripts of Freedom Scientific training -- the JAWS Basic Training
modules, the FSCast and Training Resources podcasts, and the webinars -- read
on 5 October 2026. Ninety-eight of them demonstrate JAWS. The quoted lines are
what Whisper heard, and they include JAWS's own speech inside the trainer's,
which makes the set a record of real utterances in real sequences. For the
kit's Tutorials.md and the walks of every Homer app.*

## Eleven habits, each with its evidence

**Announce the key, with its letter spelled.** Every trainer says the key
before pressing it, and a lone letter gets its alphabet word: "I'm going to
press Windows key R, Romeo"; "I'll press Insert W, whiskey". A letter is the
hardest thing to hear in speech, and the word removes the doubt. A walk's Say
line does the same whenever the key is a single letter: "I press L, Lima".
(Getting Started with JAWS; JAWS Help.)

**Say what you expect to hear before it is heard.** "You should hear the word
WordPad spoken"; "You will hear a pop sound like the previous one, but lower in
pitch." The listener then knows the sound was the right one. A walk's Say line
before a key names what the reader will answer, when the answer matters.
(Read and Edit Text; So Many Cursors.)

**Then say what it meant.** After JAWS speaks, the trainer restates it: "So
JAWS gives you a prompt and it's asking, are you sure you want to quit." The
reader's line is evidence; the trainer's line is the lesson. The walk's four
beats already have this shape, and the second Say line is the one not to skip.
(Getting Started with JAWS.)

**Name the silence.** "And I'll wait a few seconds and JAWS will start up
again." Nothing in a recording is worse than a silence nobody explains. The
kit's rule to name silence stands; the trainers prove it.

**The reader's line on arriving at a control has an order, and the order is
the lesson.** "Participate checkbox not checked, alt plus P": name, role,
state, access key. "Folder View List View, not selected, JAWS 2020, not
checked, 5 of 12": container, then item, state, position. Hear lines follow
that order exactly, because the listener learns to parse it. (Menus, Dialog
Boxes and the Startup Wizard; JAWS Help.)

**Insert+Tab, not Insert+T, is the trainer's "where am I".** "I'll press Insert
Tab now to reread the current control" -- it repeats the control with its
state, position and tutor message; Insert+T reads the window title. The kit
tells walks to verify after a focus change with Insert+T; it should be
Insert+Tab inside a dialog, Insert+T for the window. (Menus, Dialog Boxes.)

**Tutor messages are shown once, then turned off.** "Tutor messages are things
like, when you get to a button JAWS says press space bar to activate ... I'm
turning them off for the rest of the basic training, and remember you can
always press Insert Tab." The trainers teach the hint, then remove it, because
it lengthens every line. A Homer walk should do exactly that: one step that
shows the hint, a Say line that says it is turned off from here, and Hear lines
without it thereafter -- which matches a reader at intermediate verbosity.
(Menus, Dialog Boxes.)

**One wrong turn, and the way back.** The podcast "When JAWS does the
unexpected" is an hour of recovery: a dialog nobody expected, Escape, "and that
keeps me right here, my focus is right here in this dialog". A walk with no
wrong turn teaches no recovery. Each walk should have one planned misstep --
the wrong letter, a dialog that was not wanted -- and the Escape that undoes
it, narrated as calmly as the rest.

**Sounds are named when they play.** "A pop sound like the previous one, but
lower in pitch" for Forms Mode. A reader's sounds are speech a listener must
learn too. If a Homer app plays a sound, the Hear line describes it in words.
(So Many Cursors.)

**The trainers slow down for teaching.** The voices webinar walks the rate
slider down a few steps before demonstrating; the basic-training narrator
speaks more slowly than a working user. The walk's reader voice is already
flattened and moderate; it should sit a little under a working speed, not at
it. (Customizing Voices.)

**Each module ends by going back over it.** Basic Training closes every
module with a review of the keys taught; the webinars end with a recap. A
walk's last step should be a Say line that names the two or three keys the
walk taught, and nothing else -- the thing the listener carries away.
(Getting Started with JAWS, and every module.)

## Two things learned about the recordings themselves

**Whisper hears JAWS.** The reader's speech comes through the transcripts as
text -- "Search box edit. Word app, press right." -- interleaved with the
trainer's. That means a transcript of a walk is checkable against the walk's
Hear lines, and a transcript of a real JAWS session is a source of Hear lines
that are right by construction. The 98 JAWS transcripts here are such a
source: a reader grammar can be read off them rather than guessed.

**A plus sign is spoken as a word.** The transcripts render the access key as
"alt plus P" and the help key as "insert plus tab": whether that is JAWS's
speech or Whisper's spelling, the words are what a listener hears, and the
checkTutorial rule that a Hear line writes the key in words is confirmed.

## What Quill does with tutorials, and what to take

*From the Quill Radio user guide, its generated tutorial document, the QUILL
Lite tutorials page, and the QUILL Cast transcripts, read on 5 October 2026.
Quill Radio ships 41 guided tutorials, 281 steps, about 244 minutes, in six
tracks.*

**Tutorials live inside the app, and the app watches.** Help > Tutorials opens
a window: find a lesson by typing words, or type "here" for lessons about the
window you came from; a tree by track says each lesson's steps, minutes, and
whether you finished it. The lesson page shows one step in a read-only box.
**Try it** has the app do the step; **Follow me** notices when you have done
it -- "it watches what changed in the app, never which key you pressed, it
never takes the keyboard, and nothing is graded" -- says what it saw, and
reads the next; **Say it again** repeats the step. Your place is kept. This
is the strongest idea in the set: a walk that is also a live lesson, run by
the program it teaches. A Homer app already has the parts -- the .inix walk,
Say, the runtime log that records what was spoken, and uiTest.inix, which
drives the program and reads back what happened. A Tutorials window in Lbc
that steps through a walk, speaks the Say line, waits, confirms from the log
that the Hear line was spoken, and moves on, would be Follow me.

**The keys are the person's keys.** "Rebind a key and the tutorial says your
key" inside the app; the generated document says so and shows the shipped
keys. A Homer walk spoken from KeyMap can do the same.

**Six tracks by the learner's timeline, each with a goal sentence.** Your
first hour; Finding something to listen to; Making it yours; Recording; More
than radio; Living with it. "By the end of this track you can find a station,
keep it, work the player from any window, and get yourself unstuck." Every
lesson opens with its goal, its step count and its minutes.

**Getting unstuck is lesson five of the first hour.** Escape and where it
lands you; hear the last announcement again; what is playing; the list of
what has failed; why a menu item is dimmed. "Read it once now so it is
familiar when you need it." That is the planned-misstep learning made into a
whole lesson, and a Homer app should have one by that name.

**Every step has the same five parts.** A bold imperative title; the
explanation; **Keys**; **You should hear** -- phrased so it survives a
different reader, "Favorite stations, tree -- or whatever your screen reader
calls an empty tree"; and **Worth knowing**, the aside. The Homer walk's
Say, Key, Hear and Note are the same four; the hedge for readers that differ
is worth borrowing in a Say line.

**The empty state is explained, not apologized for.** "An empty list here is
not a fault; it is a list you have not filled in yet, and the next few
minutes fill it." A walk that opens a template should say the same of a table
with three rows.

**Speech that is gone can be got back.** The Spoken Echo (QUILL) and Repeat
Last Announcement (Quill Radio) keep the last announcements in a read-only
list you can arrow through and copy. Homer's double-press shows one
announcement as text; a Say history command showing the last twenty, in Say.cs
so every app has it, is the same thing done once.

**The document is generated from the lessons**, so "it says exactly what the
app teaches" -- the rule makeTutorials already follows.

**The QUILL Cast is a second form, not a substitute**: two hosts, episodes in
arcs, each opening by recapping the last episode's takeaway. An audio course
beside the walks, for the car rather than the keyboard.

## Changes to make

- **Tutorials.md and checkTutorial**: verify-after-focus is Insert+Tab in a
  dialog, Insert+T for the window title; both allowed as the reader's own keys.
- **The walk format**: a closing `Say=` recap of the keys taught; one planned
  misstep with its Escape; a single step that shows a tutor message, then a
  line that says they are off from here.
- **Every walk**: alphabet words for lone letters in Say lines; sounds named in
  Hear lines where an app has them; Hear lines in name, role, state, position,
  access-key order.
- **Templates\Tutorial_0_Overview.inix**: teach Insert+Up Arrow (repeat) and
  Insert+Tab (where am I) in the first two steps, the way the trainers teach
  both in the first module.
- **The reader voice**: a step slower than a working rate.
- **From Quill**: walks grouped in tracks by the learner's timeline, each
  with a goal sentence and a running time; a "Getting unstuck" walk in the
  first track; the empty state explained; a Say history command in Say.cs;
  and, the large one, a Tutorials window in Lbc with Try it and Follow me,
  built on the walk files, Say's log and uiTest.

The DbDo walks are local files, not in the repository, so they are not in
this delivery; send `help\Tutorial_*.inix` and I will apply the five items to
them.
