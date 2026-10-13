# Camel Type

Camel Type is the coding style of every Homer program and script: a style for
reading code by ear and in braille as quickly as by eye. It carries each name's
type in the name itself, keeps related things together on one line, and puts
things in an order a reader can predict, so a screen reader user hears `sPath`,
`bFound` or `iCount` and knows what it holds without seeking back to where it
was declared.

This page gives the rules every language shares. A guide for each language
gives its details:

- [C#](CamelType_CSharp.htm), with a fuller [C# reference](CamelType_CSharp_Reference.htm)
- [JavaScript](CamelType_JavaScript.htm)
- [JAWS scripting](CamelType_JAWSScript.htm)
- [PowerShell](CamelType_PowerShell.htm)
- [Python](CamelType_Python.htm)
- [VBScript](CamelType_VBScript.htm)

## Names

- **A type prefix on every variable, argument and constant:** `a` array, `b`
  boolean, `bin` binary buffer, `d` dictionary, `dt` date-time, `f` file, `h`
  window handle, `i` integer, `l` list, `n` real number, `s` string, `v` variant
  of unknown type. Any other object takes its class name in lower camel case
  (`form`, `writer`) or the usual short name for it (`pd` for pandas, `df` for a
  data frame, `browser` for a web browser). Only VBScript uses `o` for objects;
  in C#, `o` is kept for COM objects.
- **Lower camel case** for every name the program makes -- variables, functions,
  methods, properties and events -- wherever the language allows. Upper camel
  case and snake case only where a language or an API demands them.
- **A constant is named exactly like a variable**, type prefix and all:
  `sFormat`, `iMaxRetries`. It is set apart by being declared as a constant,
  before the variables. The earlier `c_` prefix is obsolete, and the kit's tidy
  renames any it finds. When a constant and a variable made from it would share
  a name, the constant says what it holds: `lAllSamples`, beside `lSamples`.

## Structure

- **Functions, never subprocedures:** a routine is a function even when what it
  returns does not matter.
- **One line for a simple statement and its consequence:** an `if`, `while` or
  `for` with a single statement under it stays on one line. Lines are long by
  design: a listener presses Down Arrow to skip the rest of one.
- **For-each loops** over a collection, rather than counting through an index,
  wherever the language allows.
- **Declarations at the top** of the program or function: one line per type,
  the names on it in alphabetical order, the lines themselves in alphabetical
  order by type, constants before variables.
- **Functions in alphabetical order**, with the main code last and unindented,
  starting with a `main` comment.
- **No magic numbers:** use the language's own named constant, or define one.

## Details that apply where the language allows

- **Double quotes** for strings, where either quote works.
- **async and await** rather than promises and callbacks, wherever a simple
  synchronous form is available.
- **Imports:** in Python, one line of standard modules in alphabetical order,
  then `from` lines in alphabetical order, then one line for each third-party
  module; in JavaScript, one import or require per line, in alphabetical order.
