# Camel Type: PowerShell Coding Guidelines

Camel Type is a coding style optimized for screen reader productivity and systematic readability. The following rules apply to PowerShell 5.1 and PowerShell 7.x scripts (`.ps1` files).

---

## 1. Set-StrictMode

Always place `Set-StrictMode -Version Latest` near the top of every script, after any `#Requires` directives and before any executable code. This causes PowerShell to throw terminating errors for common mistakes such as referencing undefined variables, calling undefined functions, and accessing non-existent properties.

```powershell
#Requires -Version 5.1
Set-StrictMode -Version Latest
```

---

## 2. Variable and Parameter Naming

All variables begin with `$` as required by PowerShell. After the `$`, apply Hungarian prefix notation to indicate type:

- `$a` — array (`@(...)`)
- `$b` — boolean (`$true` / `$false`)
- `$bin` — binary buffer (`[byte[]]`)
- `$dt` — date-time (`[datetime]`)
- `$f` — file or path string being used as a file reference
- `$i` — integer (`[int]` or `[long]`)
- `$n` — real number (`[double]` or `[float]`)
- `$s` — string (`[string]`)
- `$d` — dictionary / hashtable (`@{...}`)
- `$v` — variant (unknown or mixed type, `[object]`)

For **COM or .NET object instances**, use the lowercase class name or a well-known abbreviation as the prefix. If there is only one instance of that type in scope, the prefix is the entire variable name.

Examples:
- One `Outlook.Application` COM object: `$outlook`
- One `AppointmentItem`: `$appointment`
- One `[System.IO.StreamReader]`: `$streamReader`
- One `[datetime]` object: `$dt` (if no suffix is needed) or `$dtStart`, `$dtEnd` (when two exist)

The automatic variable `$_` (pipeline current object) and PowerShell's built-in variables (`$true`, `$false`, `$null`, `$PSScriptRoot`, etc.) are used as-is without prefixes.

---

## 3. Constant Naming

PowerShell has no true `const` keyword. Declare constants using `Set-Variable` with the `-Option Constant` flag, or use `New-Variable -Option ReadOnly` for values that should not change. Name them using the same lower camel case and Hungarian prefix convention as variables — no special prefix or capitalization to distinguish them from variables.

```powershell
Set-Variable -Name iDefaultTimeoutMs -Value 60000 -Option Constant
Set-Variable -Name sResultsDir -Value "results" -Option Constant
Set-Variable -Name sFallbackTitle -Value "untitled" -Option Constant
```

If the constant is only used locally and mutation is not a concern, a plain assignment is acceptable.

---

## 4. Capitalization

Use **lower camel case** for all custom names: variables, function names, and parameters. PowerShell is case-insensitive, but Camel Type enforces lower camel case for custom names as a readability discipline.

When calling PowerShell built-in cmdlets, use the standard `Verb-Noun` capitalization that PowerShell documentation specifies (e.g., `Write-Output`, `Get-ChildItem`, `New-Object`), as these are not custom names.

---

## 5. Variable Declarations and Initialization

PowerShell does not require explicit variable declarations, but variables should be **assigned and initialized at the top of their scope** (script level or function level) before any logic, grouped by type prefix in alphabetical order, with variables of the same type on the same line where practical.

Assign sensible zero-values: `0` for integers, `0.0` for floats, `""` for strings, `@()` for arrays, `@{}` for hashtables, `$null` for objects.

```powershell
$iCount = 0; $iMax = 100
$sDir = ""; $sTitle = ""; $sUrl = ""
$outlook = $null
```

For type safety and documentation clarity, you may optionally add a type accelerator before the variable name:

```powershell
[int] $iCount = 0
[string] $sTitle = ""
```

---

## 6. Script Structure and Entry Point

Prefer **top-level script code with no indentation** rather than wrapping everything in a `main` function. Write the main logic directly at the script's top level so a screen reader user can navigate to the bottom of the file to find the most recently written code.

When a `main` function is used (e.g., to improve testability or organize a larger script), place it **last** in the file, after all other functions, and call it just before its definition:

```powershell
Set-StrictMode -Version Latest

Set-Variable -Name sResultsDir -Value "results" -Option Constant

$sUrl = ""

addEvent   # call appears before the definition

function addEvent { ... }   # main function last
```

---

## 7. Function Order

All functions other than `main` (or the primary entry-point function) are listed in **strict alphabetical order**. If a primary function is used, it appears **last**. There are no organizational section comments grouping functions — strict alphabetical order is sufficient.

---

## 8. Functions

- Define all routines as **functions**, not scripts or filter blocks. Every function should return a value, even if `$null`.
- Do not use `return` at the end of a function merely to return `$null` — PowerShell functions implicitly return the last value in the pipeline.
- Use explicit `return` when exiting early or returning a specific value.
- Use **single-line `if` syntax** for simple one-consequence conditionals:

```powershell
if (-not $sUrl) { throw "URL is required" }
if ($bReady) { return $true }
```

- Prefer `throw` for error conditions over `Write-Error` when the error should be terminating.

---

## 9. Parameters

Declare function parameters in a `param()` block at the top of each function. Apply the same Hungarian prefix convention as variables. Use `[type]` annotations for clarity.

```powershell
function buildBody {
  param(
    [string] $sDescription,
    [string] $sNotes
  )
  ...
}
```

---

## 10. Loops

Prefer **`foreach` loops** (or `ForEach-Object` in pipelines) over index-based `for` loops whenever iterating a collection.

```powershell
foreach ($sItem in $aItems) { processItem $sItem }
$aItems | ForEach-Object { processItem $_ }
```

Use index-based `for` loops only when the index itself is needed.

---

## 11. COM Object Creation

Use `New-Object -ComObject` to create COM objects, assigning the result to a variable named with the object's class abbreviation as prefix. Try to attach to a running instance first via `[Runtime.InteropServices.Marshal]::GetActiveObject()` before creating a new instance.

```powershell
$outlook = $null
try { $outlook = [Runtime.InteropServices.Marshal]::GetActiveObject("Outlook.Application") }
catch { $outlook = New-Object -ComObject Outlook.Application }
```

Release COM objects explicitly when done using `[Runtime.InteropServices.Marshal]::ReleaseComObject()` followed by setting the variable to `$null`:

```powershell
[void][Runtime.InteropServices.Marshal]::ReleaseComObject($appointment)
$appointment = $null
```

---

## 12. String Delimiters

Use **double-quoted strings** (`"..."`) for all strings. Double-quoted strings support variable interpolation, which is the more commonly needed behavior. Use single-quoted strings (`'...'`) only when a string must be taken completely literally and contains characters that would be incorrectly interpolated.

```powershell
$sMessage = "Processing $sTitle..."
$sLiteral = 'Use $dollar signs literally here'
```

---

## 13. Magic Numbers

Never use literal numeric or string values in logic. Assign them to named variables or constants and reference those names. Always use PowerShell's built-in named values (`$true`, `$false`, `$null`) rather than their numeric equivalents.

---

## 14. Error Handling

Use `try`/`catch`/`finally` with a named exception variable. Catch specific exception types where possible.

```powershell
try {
  $dt = [datetime]::Parse($sStartDateTime)
} catch [System.FormatException] {
  Write-Output "Error: Could not parse date: $sStartDateTime"
  return $false
}
```

For code that must always clean up (such as releasing COM objects), use a `finally` block.

---

## 15. Object and Array Literals

Keep short hashtable and array literals on a **single line** where practical, to maximize information density per line for screen reader review.

```powershell
$dConfig = @{ Server = "localhost"; Port = 8080; Debug = $true }
$aEngines = @("axe", "ibm", "alfa")
```

Use multi-line syntax only when the literal is too long to read comfortably on one line.

---

## 16. Output

Use `Write-Output` to send data through the pipeline. Use `Write-Host` only for console display that should not enter the pipeline. Avoid `Write-Host` in functions that are meant to return values, as it bypasses the pipeline entirely.
