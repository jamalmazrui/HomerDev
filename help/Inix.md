# The .inix format

*How Homer programs keep settings, answers and small tables in plain text, and why they prefer it to JSON. For the Homer Development Kit's help folder.*

## What .inix is

An .inix file is the familiar .ini settings format with a few additions. Section names sit in square brackets on a line of their own. Inside a section, each line is `name = value`. Lines that begin with a semicolon or a number sign are comments. Any plain .ini file is already a valid .inix file; the extension says that a Homer program wrote it and that the additions below may be in use. Homer programs create only .inix for their own configuration; .ini is used only when another program requires it.

The additions:

- **A value can span several lines.** Write the name and the equals sign with nothing after them, and put the value on the lines below. The value runs to the next `name =` line, the next section line, or the end of the file. Blank lines inside it are part of it; blank lines at its end are dropped. The reader keeps the text exactly as written, with no trimming of lines and no change of spacing; any trimming is the using program's later decision. If a line of the value would itself read as a `name =` line, write it with one leading space, which the reader removes.
- **A list** is a comma-separated value on one line, or, when the items themselves contain commas or are long, one item per line in a multi-line value.
- **A dictionary** is a section: each field is a `name = value` line.
- **A table** is one section per record, with each field on its own line and its own name, rather than a row of values that must be counted across. The kit's inixVert converts such a table to and from CSV, Excel and Markdown tables.

A short example, the shape of a book's KDP answers:

```
[details]
title = Blind Vibe Coding
keywords = screen reader programming, accessible app development
categories =
Kindle eBooks > Computers & Technology > Programming > Software Development
Kindle eBooks > Computers & Technology > Computer Science > Generative AI
description =
First paragraph of the description.

Second paragraph, after a blank line that is part of the value.

[aiContent]
used = Yes
tools = Claude
```

The program that reads the file turns these conventions into whatever structure suits it: the comma-separated line into a list, the multi-line value into a list of lines or one text, the section into a dictionary. That is a few lines of code in any language, and the Blind Vibe Coding project's `kdpSubmit.py` carries a reference reader and writer in Python (`readInix`, `writeInix`, `inixList`) with tests that show a file reading back exactly as written.

## Why prefer .inix to JSON

JSON is for programs talking to programs. Every string is quoted, every value must be followed by a comma except the last, brackets and braces must balance, and one missing comma makes the whole file unreadable. A screen reader reads all of that punctuation aloud. An .inix file says the same thing with less to hear and nothing to get wrong, and it can be opened and corrected in any text editor.

The rule: when a person will read or edit the file, use .inix. When another program insists on JSON, such as a web API, a package manifest or a tool whose settings are JSON by design, use JSON there and nowhere else. The same holds for YAML and TOML: fine where a tool demands them, not for a Homer program's own files.

## Writing rules for Homer programs

- Read and write without reordering sections or keys and without trimming values.
- Save a value as soon as the user answers, not at exit.
- A missing key means the default; do not write a key whose value is empty unless the empty value is itself the answer.
- Encoding is UTF-8 with BOM and CRLF, like every Homer text file.
- Name the file for the program or the job it serves, in Title_Snake_Case for a user-facing file (`Blind_Vibe_Coding_KDP.inix`) and the program's own name for its settings (`EdSharp.inix`). Settings live in `configs\`; a record of what a run did lives in `logs\`.
