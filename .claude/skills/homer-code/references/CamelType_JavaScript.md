# Camel Type: JavaScript Coding Guidelines

Camel Type is a coding style optimized for screen reader productivity and systematic readability. The following rules apply to JavaScript (ES module, Node.js context).

---

## 1. Strict Mode

ES modules enforce strict mode automatically, so no `"use strict"` declaration is needed when using `import`/`export` syntax. If writing a CommonJS script (not recommended), add `"use strict";` as the very first line.

---

## 2. Variable and Argument Naming

Use Hungarian prefix notation to indicate type. Prefix rules:

- `a` — array
- `b` — boolean
- `bin` — binary buffer
- `dt` — date-time
- `f` — file
- `h` — window or OS handle (not used for JavaScript objects)
- `i` — integer
- `l` — list
- `n` — real number (float)
- `s` — string
- `d` — dictionary (plain key-value object)
- `v` — variant (unknown or mixed type)

For **JavaScript object instances** (class instances, library objects), use the **lowercase class name** as the prefix. If there is only one instance of that class in scope, the class name prefix is the entire variable name — no additional suffix is added.

Examples:
- One Playwright `Browser` instance: `browser`
- One Playwright `Page` instance: `page`
- One `AxeBuilder` instance: `axeBuilder`
- One `URL` instance: `urlParsed` (two `URL` instances would need distinguishing suffixes)
- A caught error: `error`

---

## 3. Constant Naming

Constants use the **same lower camel case naming convention as variables**, including the Hungarian type prefix. They are distinguished only by being declared with `const` rather than `let`, not by any difference in capitalization or formatting.

Examples: `const sDefaultEncoding = "utf-8";`, `const iTimeoutMs = 60000;`

---

## 4. Capitalization

Use **lower camel case** for all custom names: variables, constants, functions, parameters. Avoid upper camel case and snake case except where a language API or external library requires it.

---

## 5. Variable and Constant Declarations

- Declare constants with `const` and variables with `let` at the **top of their scope**, before any logic.
- Group declarations by type, one statement per type group, names listed **alphabetically** within the group.
- Type groups appear in **alphabetical order** by prefix letter.
- Constants are declared before variables.
- Explicitly initialize `let` variables on the lines immediately following the declarations.

Example:
```js
const iMaxRetries = 3;
const sEncoding = "utf-8";
const sFallbackTitle = "untitled-page";

let iCount;
let sDir, sTitle, sUrl;

iCount = 0;
sDir = "";
sTitle = "";
sUrl = "";
```

---

## 6. Script Structure and Entry Point

Prefer **top-level script code with no indentation** rather than wrapping everything in a `main` function. Write the main logic directly at the module's top level so a screen reader user can navigate to the bottom of the file to find the most recently written code.

The exception is when top-level `await` is required (Node.js ES modules support this natively), in which case `await` expressions may appear at the top level without a wrapper function.

When a `main` function is truly necessary (e.g., to create an explicit async scope in an environment that does not support top-level `await`), place it **last** in the file, after all other functions, and invoke it with `main()` or `await main()` on the line immediately before the `main` function definition.

---

## 7. Function Order

All functions other than `main` are listed in **strict alphabetical order**. If a `main` function is used, it appears **last**. There are no organizational sections or divider comments grouping functions — strict alphabetical order is sufficient.

---

## 8. Functions

- Define all routines as **functions**, never as subprocedures. Every function returns a value, even if the return value is not always used.
- Use `async`/`await` throughout; avoid `.then()` chains.
- Use **single-line syntax** for simple one-consequence conditionals:
  ```js
  if (!sUrl) throw new Error(sUsage);
  if (bReady) return true;
  ```

---

## 9. Loops

Prefer **for-of** (for-each) loops over index-based loops whenever iterating a collection.

```js
for (const item of aItems) process(item);
```

Use index-based loops only when the index itself is needed.

---

## 10. Imports

Use one `import` statement per module, listed in **alphabetical order**. Place Node.js built-in imports (with `node:` prefix) first, then third-party package imports, separated by a blank line.

```js
import { createRequire } from "node:module";
import { dirname, resolve as resolvePath } from "node:path";
import { mkdir, writeFile } from "node:fs/promises";

import { AxeBuilder } from "@axe-core/playwright";
import { chromium } from "playwright";
```

---

## 11. String Delimiters

Use **double quotes** for all strings. Use template literals (backticks) when embedding expressions.

---

## 12. Magic Numbers

Never use literal numeric or string values in logic. Assign them to named constants and reference the constant name.

---

## 13. Object and Array Literals

Keep short object and array literals on a **single line** where practical. This maximizes information density per line, which benefits screen reader review.

```js
browser = await chromium.launch({ channel: "msedge", headless: true });
return { sAlfaPath: resolvePath(sDir, sAlfaFileName), sAxePath: resolvePath(sDir, sAxeFileName) };
```

---

## 14. File and Module Conventions

- Use ES module syntax (`import`/`export`), not CommonJS (`require`).
- Set `"type": "module"` in `package.json`.
- Use the `node:` prefix for all Node.js built-in module imports.
