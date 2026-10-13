# Camel Type: VBScript Coding Guidelines

Camel Type is a coding style optimized for screen reader productivity and systematic readability. The following rules apply to VBScript as used in Windows Script Host (WSH) `.vbs` files or Classic ASP.

---

## 1. Option Explicit

Always place `Option Explicit` as the very first line of every VBScript file. This requires all variables to be declared before use and catches typographical errors in variable names at runtime.

```vbscript
Option Explicit
```

---

## 2. Variable and Argument Naming

Use Hungarian prefix notation to indicate type. Prefix rules:

- `a` — array
- `b` — boolean
- `bin` — binary buffer
- `dt` — date-time
- `f` — file object
- `h` — window or OS handle
- `i` — integer
- `l` — list (typically an array used as a list)
- `n` — real number (float/double)
- `s` — string
- `d` — dictionary (`Scripting.Dictionary` object)
- `o` — generic object (use `o` for all non-specific COM or VBScript object instances)
- `v` — variant (unknown or mixed type; also the default VBScript type)

For **named COM or WSH object types**, use a prefix that reflects the object class or a well-known abbreviation. If there is only one instance of that object type in scope, the abbreviation is the entire variable name.

Common abbreviations:
- `fso` — `Scripting.FileSystemObject`
- `wsh` — `WScript.Shell`
- `rs` — `ADODB.Recordset`
- `conn` — `ADODB.Connection`
- `re` — `VBScript.RegExp`
- `xml` — `MSXML2.DOMDocument`

---

## 3. Constant Naming

Constants use the **same lower camel case naming convention as variables**, including the Hungarian type prefix. They are distinguished only by being declared with `Const` rather than `Dim`, not by any difference in capitalization or formatting.

Examples: `Const sDefaultEncoding = "utf-8"`, `Const iTimeoutMs = 60000`

VBScript built-in constants (e.g., `vbCrLf`, `vbTrue`, `True`, `False`, `ForReading`) should always be used by their built-in name, never by their underlying numeric value.

---

## 4. Capitalization

Use **lower camel case** for all custom names: variables, constants, and function names. VBScript is case-insensitive, but Camel Type enforces lower camel case as a discipline for readability.

When calling built-in VBScript functions or properties (e.g., `MsgBox`, `WScript.Echo`, `Len`, `UCase`), use the capitalization that VBScript documentation specifies, as these are not custom names.

---

## 5. Variable and Constant Declarations

- Always declare variables with `Dim` and constants with `Const`.
- Declare constants and variables at the **top of the script** (global scope) or at the **top of each function** (local scope), before any logic.
- Group `Const` statements by type first, then `Dim` statements by type.
- One `Const` or `Dim` statement per type group, names listed **alphabetically** and **comma-separated** on a single line.
- Type groups appear in **alphabetical order** by prefix letter.

Example:
```vbscript
Const iMaxRetries = 3
Const sEncoding = "utf-8"
Const sFallbackTitle = "untitled-page"

Dim iCount, iMax
Dim sDir, sTitle, sUrl
```

---

## 6. Script Structure and Entry Point

Prefer **top-level script code with no indentation** rather than wrapping everything in a `main` function. Write the main logic directly at the script's top level (after `Option Explicit`, constants, and global variable declarations) so a screen reader user can navigate to the bottom of the file to find the most recently written code.

When a `main` function is used, place it **last** in the file, after all other functions, and call it near the top of the script body:

```vbscript
Option Explicit

Const sResultsDir = "results"

Dim sUrl
sUrl = ""

main()

Function alphabeticallyFirstFunction()
  ' ...
End Function

Function main()
  ' ...
End Function
```

---

## 7. Function Order

All functions other than `main` are listed in **strict alphabetical order**. If a `main` function is used, it appears **last**. There are no organizational sections or divider comments grouping functions — strict alphabetical order is sufficient.

---

## 8. Functions

- Define all routines as **Functions**, not `Sub` procedures. Every `Function` should return a value, even if it is not always used.
- Use **single-line `If` syntax** for simple one-consequence conditionals:
  ```vbscript
  If sUrl = "" Then WScript.Quit 1
  If bReady Then getResult = True
  ```

---

## 9. Loops

Prefer **For Each** loops over index-based `For i = 0 To n` loops whenever iterating a collection or array.

```vbscript
For Each sItem In aItems
  processItem(sItem)
Next
```

Use index-based `For` loops only when the index itself is needed.

---

## 10. String Delimiters

VBScript uses only **double quotes** for string literals — there is no alternative. Use `&` for string concatenation.

```vbscript
sPath = sResultsDir & "\" & sTitle
```

---

## 11. Magic Numbers

Never use literal numeric or string values in logic. Assign them to named `Const` constants and reference the constant name. Always use VBScript's built-in named constants (e.g., `vbCrLf`, `vbOKCancel`, `ForReading`) rather than their numeric equivalents.

---

## 12. Object Creation

Use `CreateObject` with the full ProgID string. Assign the result to a variable named with the object's prefix convention. Release objects explicitly when done.

```vbscript
Const sFsoProgId = "Scripting.FileSystemObject"
Set fso = CreateObject(sFsoProgId)
' ... use fso ...
Set fso = Nothing
```

---

## 13. Error Handling

VBScript does not support structured `try`/`catch`. Use `On Error Resume Next` followed by an immediate `Err` check after any statement that may fail. Re-enable error trapping with `On Error GoTo 0` as soon as the guarded section ends.

```vbscript
On Error Resume Next
fso.DeleteFile sPath
If Err.Number <> 0 Then
  WScript.Echo "Error deleting file: " & Err.Description
  Err.Clear
End If
On Error GoTo 0
```
