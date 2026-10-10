---
title: "Announcing the Homer Development Kit"
author: "Jamal Mazrui"
lang: en-US
---

# Announcing the Homer Development Kit

Vibe coding means describing an app to an AI and refining it through conversation. It has made software development newly practical for blind and low-vision people. I have been building apps this way, and I would like to share the toolkit that grew out of that work.

The Homer Development Kit, or HomerDev, is a free, open-source collection of code, conventions, and AI skills for building Windows apps that work well with screen readers. It addresses what usually follows a promising first draft. That means a logical tab order and keyboard commands that do not conflict with JAWS or NVDA. It also means speech that is neither missing nor repeated, a dependable installer, and detailed logs that explain any failure.

The kit provides shared C# and Python code for dialogs, speech, settings, hotkeys, media playback, and in-place updates. It also includes templates, working sample apps, and scripts that build, check, publish, and release a project in one step. A release check catches common problems before they reach users. Seventeen skills teach an AI assistant how a HomerDev project is organized. Its conventions then need not be explained again in every conversation.

You need not adopt the whole kit. With today's AI assistants, you can usually share the HomerDev archive with your AI. Then ask it to bring what is useful into your own project. Your AI can examine the archive, decide what is relevant, and adapt it under the MIT License.

HomerDev is still evolving, but it is what I use every day to build and release my own apps. Its framework and components are behind DbDo, a database manager, and EdSharp, a text editor. They also power FileDir, a file manager, and HomerScribe, which describes videos and transcribes audio with AI on your own computer. I hope the kit spares others some of the trial and error it took to build. For a guided introduction to building apps this way, my book, Blind Vibe Coding: Building Apps Nonvisually with AI, is available on Amazon.

Download HomerDev: https://github.com/JamalMazrui/HomerDev/archive/main.zip

Feedback, questions, and contributions are welcome.
