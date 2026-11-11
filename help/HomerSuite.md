---
title: "Homer Suite"
subtitle: "Four desktop apps, one way of working"
---

# Homer Suite

Homer Suite is four free Windows apps built for screen reader users, which work the same way. Each one handles a different kind of work: data, documents, files and the web. Learn one, and you know most of how to use the other three.

## The apps

- **DbDo** manages data. It opens SQLite, Access, Excel, dBASE and delimited text files, and shows each table as a list you move through cell by cell. Its template databases cover radio stations, job leads, books, music and more.
- **EdSharp** edits text, documents and code. It reads and writes Word, PowerPoint, PDF, Markdown and many more formats, and runs scripts and compilers from inside the editor.
- **FileDir** manages files and folders. It marks, copies, moves, renames, converts and compares files, and searches them by name or content, from a folder list.
- **HomerView** reads web pages and documents. It drives Microsoft Edge so NVDA or JAWS can read a page as a structured document, and opens Word files, PDFs and ebooks the same way.

## One way of working

The same command has the same name, the same key and the same one-sentence description in every app. A release check enforces it, so the apps cannot drift apart.

- **Help:**
  - F1 opens the app's guide.
  - Shift+F1 says what the control with focus does.
  - Control+Slash says where you are.
  - Control+F1 turns the key describer on or off.
  - Alt+F10 lists every command in one place.
- **Documents:** the Help menus of DbDo, EdSharp and FileDir list the same documents: the guide, the quick start, the history of changes, the list of keys, answers to frequent questions, the tutorials, the announcement, the developer guide and the license.
- **Keys you learn once:**
  - F4 lists the open windows, and Control+Tab moves among them.
  - Control+C copies, and Alt+C adds to what you copied.
  - Control+J jumps, Control+K searches by keywords, and F3 repeats the last search.
  - Alt+V runs a script.
  - F11 installs the newest version.
- **HomerView's exceptions:** HomerView follows these too, except where Microsoft Edge already owns a key. Its guide is a Help menu item with no key, Where Am I is Alt+Shift+Slash, and installing the newest version is Control+F11.
- **Say keys:** each app answers a question in words, such as how many items there are or where you are. A second press spells a short answer or shows a long one in a window.
- **Settings:** each app keeps its settings in a plain text file you can read and edit.
- **Installers:** each app has one installer that also offers to install its screen reader scripts.

## The foundation

**HomerDev**, the Homer Development Kit, holds the parts the four apps share: their dialogs, menus, keys, speech, settings, file conversions, installers and release checks. It is how the apps stay one suite, and it is also a kit for developers who build accessible apps with AI help.

## What else is Homer, and why it is not in the suite

The suite is kept small on purpose: four apps that each cover a broad kind of desktop work, and share one way of working. A project joins only if it adds a kind of work the four do not cover and can work the same way. The rest are Homer Tools: still built on HomerDev, still accessible, but for a narrower job.

- **2htm** converts files to HTML. EdSharp and FileDir now make the same conversions, through HomerDev.
- **BatCon** converts many files at once between formats. FileDir is the natural home for this, as one command on marked files, so it need not be a separate app in the suite. I recommend keeping BatCon as a tool for scripted batch work, and making sure FileDir offers the same conversions from its menus.
- **bookFido** builds catalogs of your books from four libraries. It is a specialist tool; its results suit DbDo's book database.
- **extCheck** and **urlCheck** check files and web pages for accessibility. They serve accessibility professionals and produce reports, not day-to-day desktop work.
- **HomerScribe** describes and transcribes video and audio, using AI on your own computer. None of the four apps covers media, so it is the strongest candidate to join. I recommend it stay a companion, not a member, for now: it works as a single job you start and let run, not as windows you work in, and it needs several gigabytes of AI models. If it gains a window for reviewing and editing descriptions, it would fit the suite.
- **KeyLine** is a command-line toolkit of file and text utilities. It serves people working at the command prompt.
- **urlFido** downloads files linked from a web page. EdSharp and FileDir offer this as Web Download, Alt+Shift+W.

## My recommendation

- **The suite:** keep it to DbDo, EdSharp, FileDir and HomerView. Four apps covering data, documents, files and the web is a story people can remember and a set they can learn. Five or more would add apps that share less of the way of working, which weakens the main promise: learn one, and you know the others.
- **The companion:** name HomerScribe as the suite's companion for media.
- **The tools:** list everything else as Homer Tools, each with its own one-line purpose.
- **The kit:** present HomerDev separately, to developers.
- **The announcement:** lead with the promise and back it with the check, which proves every shared command is the same in every app.

## Summary

- **Homer Suite** is DbDo, EdSharp, FileDir and HomerView: data, documents, files and the web, with one way of working.
- **What makes it a suite:** shared commands have the same names, keys and descriptions everywhere, and a release check enforces it.
- **The foundation:** HomerDev.
- **The companion:** HomerScribe, for media.
- **Homer Tools:** everything else, kept outside the suite so it stays easy to learn.
