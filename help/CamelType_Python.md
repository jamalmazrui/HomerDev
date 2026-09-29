# Camel Type: Python Coding Guidelines

Camel Type is a coding style optimized for screen reader productivity and systematic readability. The following rules apply to Python 3. Equivalent documents in this folder cover C# (`CamelType_CSharp.md`) and JAWS scripting (`CamelType_JAWSScript.md`).

This is the kit's copy. An app does not carry one of its own; urlCheck's copy moved here in HomerDev 1.43.0.

---

## Contents

- 1\. Variable and Argument Naming
- 2\. Constant Naming
- 3\. Capitalization
- 4\. Variable Initialization
- 5\. Constants
- 6\. Script Structure and Entry Point
- 7\. Function Order
- 8\. Functions
- 9\. Loops
- 10\. Imports
- 11\. String Delimiters
- 12\. Magic Numbers
- 13\. Object and Array Literals
- 14\. Error Handling
- 15\. Cross-Program Naming Conventions
- 16\. The Homer Kit

## 1. Variable and Argument Naming

Use Hungarian prefix notation to indicate type. Prefix rules:

- `a` — array (or tuple used as a fixed sequence)
- `b` — boolean
- `bin` — binary buffer (`bytes` or `bytearray`)
- `dt` — date-time (`datetime` object)
- `f` — file object
- `h` — window or OS handle (an `int` from `ctypes`, or `frm.Handle.ToInt64()` under pythonnet)
- `i` — integer
- `l` — list
- `n` — real number (float)
- `s` — string
- `d` — dictionary
- `v` — variant (unknown or mixed type)

For **Python object instances** (class instances, library objects), use the **lowercase class name** as the prefix, OR a common abbreviation if one is universally understood (e.g., `pd` for pandas, `np` for numpy, `bs` for BeautifulSoup, `ex` for Exception, `df` for DataFrame).

If there is only one instance of that class in scope, the class name prefix is the entire variable name — no additional suffix is added.

Examples:
- One `Path` instance: `path`
- One `requests.Session` instance: `session`
- One `BeautifulSoup` instance: `bs`
- One `pandas.DataFrame`: `df`
- A caught exception: `ex` (universal abbreviation; if multiple `Exception` variables coexist, use `exParse`, `exNetwork`, etc.)

The `o` prefix is **reserved for COM objects only** (e.g., `oWord`, `oExcel`, `oWorkbook`, `oRange`). Do not use `o` as a generic "other object" prefix; use the class-name prefix instead.

This convention extends naturally: a `pathlib.Path` is `path` or `pathInput`; a `urllib.request.Request` is `request`; a `playwright.sync_api.Page` is `page`; an `io.StringIO` for output capture is `capture` (the role) — but if multiple StringIO objects coexist, distinguish them with the class-name prefix: `stringIoOut`, `stringIoErr`.

---

## 2. Constant Naming

A constant is named like a variable, Hungarian type prefix included, with **`c_` in front**: `c` for constant, then an underscore. The prefix is what tells a listener, at the point of use, that the value never changes.

Examples: `c_sDefaultEncoding = "utf-8"`, `c_iTimeoutSec = 60`

Programs written before this rule (urlCheck among them) name their constants without `c_`. New constants in those programs take the prefix; the old ones are renamed only when a file is being reworked anyway.

---

## 3. Capitalization

Use **lower camel case** for all custom names: variables, constants, function names, and parameters. Python conventionally uses snake case, but Camel Type overrides this with lower camel case everywhere except where a framework or external API requires otherwise.

Class names, if defined, use upper camel case as Python convention requires.

---

## 4. Variable Initialization

Python does not require explicit variable declarations. Assign zero-value initializations at the **top of each function scope**, grouped by type in alphabetical order of prefix letter, variables of the same type assigned alphabetically.

Where a meaningful initial value is not yet known, assign a sensible zero-value: `0` for integers, `0.0` for floats, `""` for strings, `[]` for lists, `{}` for dicts, `None` for objects.

Example:
```python
iCount = 0
iMax = 100
sDir = ""
sTitle = ""
sUrl = ""
```

---

## 5. Constants

Define constants at the **top of the module**, before any function definitions, grouped by type, each group in alphabetical order, constants within each group in alphabetical order.

Example:
```python
c_iTimeoutSec = 60
c_sEncoding = "utf-8"
c_sFallbackTitle = "untitled-page"
c_sResultsDir = "results"
```

---

## 6. Script Structure and Entry Point

Prefer **top-level script code with no indentation** rather than wrapping everything in a `main` function. Write the main logic directly at the module's top level so a screen reader user can navigate to the bottom of the file to find the most recently written code.

When a `main` function is used (e.g., to enable the `if __name__` guard for reusable modules), place it **last** in the file, after all other functions. The `if __name__ == "__main__":` block appears at the very bottom, calling `main()` on a single line.

```python
if __name__ == "__main__": main()
```

---

## 7. Function Order

All functions other than `main` are listed in **strict alphabetical order**. If a `main` function is used, it appears **last**. There are no organizational sections or divider comments grouping functions — strict alphabetical order is sufficient.

---

## 8. Functions

- Define all routines as **functions**. Every function should return a value, even if `None`.
- Use simple **single-line conditionals** for one-consequence cases:
  ```python
  if not sUrl: raise ValueError(sUsage)
  if bReady: return True
  ```

---

## 9. Loops

Prefer **for-each** style loops over index-based loops whenever iterating a collection.

```python
for sItem in lItems: process(sItem)
```

Use `enumerate()` only when the index itself is needed. Avoid `range(len(...))`.

---

## 10. Imports

Use exactly **two import statements**: one for built-in standard library modules, one for third-party modules. Each statement lists module names in **alphabetical order** on a single line, separated by commas. Place the built-in import first, then the third-party import, separated by a blank line.

```python
import json, os, pathlib, re, sys

import bs4, playwright, requests
```

If `from X import Y` syntax is needed for specific names, place those lines after the two main import statements, alphabetized.

The Homer kit's modules come last, in one line, alphabetized. They are not copied into the app: the build puts `C:\HomerDev` on PyInstaller's search path and names each module with `--hidden-import`.

```python
from homer import elevate, inix, log, paths
```

---

## 11. String Delimiters

Use **double quotes** for all strings. Use f-strings when embedding expressions.

```python
sPath = f"{sResultsDir}/{sTitle}"
```

---

## 12. Magic Numbers

Never use literal numeric or string values in logic. Assign them to named constants and reference the constant name.

---

## 13. Object and Array Literals

Keep short dict and list literals on a **single line** where practical, to maximize information density per line for screen reader review.

```python
dConfig = {"encoding": sEncoding, "timeout": iTimeoutSec}
lEngines = ["axe", "ibm", "alfa"]
```

---

## 14. Error Handling

Use `try`/`except` with a named exception variable. Catch specific exception types where possible rather than a bare `except`. Use `ex` as the conventional abbreviation for caught exceptions (it is universally understood and avoids shadowing Python's builtin `Exception` class name).

```python
try:
    result = riskyOperation()
except ValueError as ex:
    print(f"Validation error: {ex}")
    sys.exit(1)
```

If the same `try` block has multiple `except` handlers and you want to keep them distinguishable in nested or multi-catch contexts, use a role suffix: `exParse`, `exNetwork`. But for the common single-handler case, plain `ex` is correct.

---

## 15. Cross-Program Naming Conventions

When the same concept appears across multiple programs in a related project (e.g., a family of companion tools that share a common command-line and GUI layout), use the **same identifier name** in each program for that concept. Consistency of naming across programs makes it easy for a reader who knows one program to understand another.

The following shared names are conventional in the author's project family:

| Concept | Identifier |
|---|---|
| Program's display name | `sProgramName` |
| Program's version string | `sProgramVersion` |
| Config directory name | `sConfigDirName` |
| Config file name | `sConfigFileName` |
| Log file name | `sLogFileName` |
| Source-input variable (the user's source files / URLs / etc.) | `sSource` |
| Output directory variable | `sOutputDir` |
| GUI layout: left margin | `iLayoutLeft` |
| GUI layout: right margin | `iLayoutRight` |
| GUI layout: top margin | `iLayoutTop` |
| GUI layout: gap between adjacent controls | `iLayoutGap` |
| GUI layout: gap between rows | `iLayoutRowGap` |
| GUI layout: width of leading labels | `iLayoutLabelWidth` |
| GUI layout: width of buttons | `iLayoutButtonWidth` |
| GUI layout: height of buttons | `iLayoutButtonHeight` |
| GUI layout: height of text fields and rows | `iLayoutTextHeight` |
| GUI layout: form (dialog) width | `iLayoutFormWidth` |

The following shared classes are conventional in the project family (using lowerCamelCase for class names per Camel Type):

| Class | Purpose |
|---|---|
| `program` | The top-level program class (entry point, argument parsing, dispatch) |
| `logger` | Diagnostic logger with `open`, `close`, `info`, `warn`, `error`, `debug` methods, writing through `homer.log` |
| `configManager` | Loads and saves `%LOCALAPPDATA%\<program>\configs\<program>.inix` through `homer.paths` and `homer.inix` |
| `guiDialog` | The parameter dialog with `show` / `run` methods |
| `comHelper` | COM lifecycle helper (creating apps, releasing references, retrying ops). Used only when the program drives Office or other COM servers. |

For the `logger` class, all six methods (`open`, `close`, `info`, `warn`, `error`, `debug`) should be present even if the program currently calls only some of them. This keeps the surface uniform across the family so future code (or a developer moving between programs) can use any level method without having to check whether it exists.

## 16. The Homer Kit

Prefer a kit module to new code. The more the shared modules are used, the better they get, and a fix in one reaches every program on its next build.

- `homer.elevate` -- F11: is there a newer release, and would you like it?
- `homer.inix` -- settings files that keep their comments and order
- `homer.log` -- one log per session in `%LOCALAPPDATA%\<App>\logs`
- `homer.paths` -- where the program's files are, installed and per user
- `homer.say` -- speech through JAWS or NVDA, one utterance per part
- `homer.util`, `homer.web` -- strings and plurals; browser-like HTTP

`homer.lbc` and `homer.mdi` build windows with wx. A program whose windows are WinForms through pythonnet, as urlCheck's are, uses the other modules and keeps its own dialog code.
