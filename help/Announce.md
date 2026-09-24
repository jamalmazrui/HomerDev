---
title: "Announcing the Homer Development Kit"
subtitle: "Foundations for Windows programs that work by keyboard and speech"
author: "Jamal Mazrui"
---

# Announcing the Homer Development Kit

### Foundations for Windows programs that work by keyboard and speech

September 2026
Copyright 2026 by Jamal Mazrui
MIT License

Building a small Windows tool of your own should not require first discovering,
by trial and error, what makes a program work well with a screen reader. The
Homer Development Kit is free and open source, and it exists so that you can
skip that part.

It consolidates decades of screen reader oriented development I have done under
Windows -- tools and techniques that I hope will help others get started and
succeed, based on lessons I have learned and tried to write down. The knowledge
is not new; gathering it into one place is, and AI is what made that practical.

Start a new program and it already does the things that usually take years to
learn. The tab order is right. The keys do not fight Windows, JAWS or NVDA.
Nothing is announced twice, and nothing important goes unannounced. When
something goes wrong there is a log that says what happened, in a place you can
find. When it works, one command builds an installer and publishes a release.

What makes that possible is that the decisions are in classes you call rather
than rules you remember. The project holds equivalent versions in C#, for .NET
Framework 4.8, which builds on any modern Windows, and in Python, for any recent
version. They support layout by code, standard dialogs, and several components
that help a screen reader user work either with AI assistance or by hand. The
order you add a control is the order you tab through it. An ampersand in a label
is the whole of an access key. Speech is used only for what a screen reader
cannot work out for itself. Settings and logs land in the same folders in every
program.

You can also find out what your program does without looking at it. One command
checks the things that can be checked -- an accessible name that repeats a
caption, two controls claiming one access key, the build, a smoke run, and the
criteria you wrote before you began -- then starts the program, presses the keys,
and reads back the same accessibility tree a screen reader reads. The report says
what was verified, what was not checked, and what remains uncertain. Knowing
which is which is the difference between a program you hope works and one you can
vouch for.

The sample programs include fruit basket dialogs in C# and in Python, built with
the shared classes, as a single dialog and as a multiple-document application.
The pairs read side by side, so you can see one design in two languages and pick
the one you want to work in. Template files help with the rest: a build script
for an app that uses Homer components, and an installer built with Inno Setup.

MIT licensed, for Windows 10 or later, with JAWS, NVDA or Narrator.

- HomerDev project page on GitHub: https://github.com/JamalMazrui/HomerDev

If you use a screen reader and have wanted to build something of your own, start
with the ReadMe and tell me where it loses you. If you already build Windows
software, I would value your eyes on what is there.
