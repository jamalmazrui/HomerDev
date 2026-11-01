# The Homer search syntax

Kit 1.95.0 gives every Homer app one way to say what to look for, in every search that is not a regular expression. The matcher is `Homer.Search`, in Lbc.cs, which every app already compiles.

Every Homer search that is not a regular expression reads what you type the same way. A plain word is enough most of the time; the symbols are there when you need more.

- **A word** is found anywhere, whatever its case: `river` finds "Riverside".
- **`*`** stands for any run of characters, and **`?`** for any one character: `chap*`, `c?t`.
- **`&`** means all of them: `red & blue`.
- **`|`** means any of them: `red | blue`. `&` is read first, so `red & blue | green` means red and blue, or else green.
- **`!`** before a word means not: `!draft`.
- **Quotes** find exactly what is inside, symbols and all: `"C#"`, `"a & b"`.

Where a wildcard counts depends on what is searched. When the search reads a **name** -- a file name, a line of a list, one field -- a word with `*` or `?` must match the whole name, so `*.md` means a name ending in .md, and `chap*` one starting with chap. When it reads **text** -- a file's contents, a whole record -- every word may match anywhere. A word with no wildcard is found anywhere in both.

F3 repeats the last search, in the same way and over the same things, going forward; Shift+F3 repeats it going back.

## For developers

- `Search.isMatch(sTarget, sPattern, bName)` tests one target. Pass `bName` true when the target is a name and false when it is text; `isMatch(sTarget, llParsed, bName, bCaseSensitive)` takes a pattern parsed once with `Search.parse`, for a search over many targets.
- `Search.likePattern(term, bName)` gives one term as a SQL LIKE pattern with `\` as its escape, for an app that searches a database; DbDo's `searchSql` shows the rest.
- `Search.Syntax` is the one-line reminder for a prompt.
- `LbcDialog.keywordsMatch` still works and now calls `Search` in text mode.

## Where each app uses it

- **The kit's list dialogs:** Filter and Jump read each line as a name; Keywords, and Filter in a list that knows more about each item than its line shows, read text.
- **FileDir:** the folder filter, Jump and File Find's Filter read names; Keywords and File Find's Text read file contents as text.
- **EdSharp:** Search for Topic reads each topic heading as a name; File Find reads names and contents; pick lists filter and jump by name. Find stays literal, because in an editor `&&` or `*` must be found as typed.
- **DbDo:** Keywords and Any Field read whole records as text; a Fields box with no operator, and Jump Record, read one field as a name.

Regular-expression commands, EdSharp's Find and Replace, and FileDir's Rename with Wildcards (which follows the Windows `ren` command) keep their own rules.
