---
title: "Homer Tools, Now Built on One Common Foundation"
author: "Jamal Mazrui"
lang: en-US
---

# Homer Tools, Now Built on One Common Foundation

## Eleven Windows apps for screen reader users, sharing one tested set of parts and practices

For more than 30 years, I have written software for productive work without sight. In 2026, with AI assistance, I built the Homer Tools. They are free, open source Windows apps for people who use screen readers. Three are for daily work: DbDo manages databases, EdSharp edits text, and FileDir manages files. HomerScribe describes videos and transcribes audio. HomerView helps you browse the web. bookFido catalogs your book libraries. And five help with accessibility and documents: 2htm turns documents into web pages, BatCon converts many files at once, extCheck checks Office documents, urlCheck checks web pages, and urlFido downloads files from them.

These apps now share one common foundation, the Homer Development Kit. Each app draws on the same parts rather than its own copy of them:

- The same dialogs, speech, keys, settings and logs, so what you learn in one app works in the others.
- The same dialog for the six apps that take files or web addresses and make results from them: the same controls in the same order, the same keys, a progress window that tells you the percentage done and the time left, but only while you are in it, and one Results box at the end.
- The same way of saving a file, which keeps a whole copy of your old file until the new one is safely in place.
- The same installer, which asks the same questions the same way, and can take every default for you.
- The same help: a guide, a list of keys and a history for each app, written in plain language, with a list of contents, and spoken tutorials in two voices.
- The same support for JAWS and NVDA, with commands that match across the two wherever possible.

Each release also passes the same checks before it goes out. One step builds the app, tidies its folder, publishes its source and releases its installer, and stops if a check fails. The checks cover the help, for reading level and broken links; the installer, against the common pattern; the tutorials; and tests of each app's own, such as transcribing a recording four ways in HomerScribe, or checking every sample database in DbDo.

The shared parts were reviewed again and again by a second AI, finding by finding, and each finding was answered in writing: what changed, and how it was tested. Most were fixed. The rest are listed openly, with what each still needs.

The kit and its review are at this address:

[https://github.com/JamalMazrui/HomerDev](https://github.com/JamalMazrui/HomerDev)
