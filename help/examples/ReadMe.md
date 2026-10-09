---
title: "Examples for Blind Vibe Coders"
lang: en-US
---

# Examples for Blind Vibe Coders

This folder holds small, tested projects for people who build software with AI help and a screen reader. Each one goes with a tutorial in the book *Blind Vibe Coding: Building Apps Nonvisually with AI*, and each was written to the same request the book asks you to give an AI, so you can compare your own result with it.

## The examples

- **timer, the talking timer (chapter 2).** One web page, `timer\timer.htm`, that counts down a number of minutes and speaks through your screen reader. Open it in any web browser. It accepts whole minutes from 1 to 120, says so plainly when the entry is blank or out of range, runs one countdown at a time, says "Started" and "Stopped", says how many minutes remain once a minute, and says "Time is up" at the end. It counts from the clock, not by counting ticks, so a page the browser slows down still keeps time. It is a convenience, not an alarm for medication or safety.

## The request it answers

The book's chapter 2 asks an AI for a page like this:

> Write a complete web page, in one HTML file with no outside files, that works as a countdown timer for a screen reader user. It has a labeled number field for minutes, a Start button, and a Stop button. While the timer runs, announce the time remaining once a minute through an ARIA live region, and announce "Time is up" at the end. Use standard HTML controls with visible labels, make everything work from the keyboard, and keep keyboard focus where it was when the timer starts. Accept whole minutes from 1 to 120, and say so if the field is blank or out of range. Run only one countdown at a time, so Start while it runs starts it over, and announce "Started" and "Stopped". Count from the clock rather than from the number of ticks, so a busy or background page stays accurate. Explain briefly how to save and open the file.

Your page will differ in its details, and that is fine. Compare what each one says, and where each one leaves focus.

## More resources

The [Blind Vibe Coding directory](https://jamalmazrui.github.io/BlindVibeCoding/) lists tools, guides, communities and research for building software nonvisually with AI.
