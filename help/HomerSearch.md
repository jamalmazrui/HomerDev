# The Homer pattern

Kit 1.95.0 gave every Homer app one way to say what to look for, in every search that is not a regular expression. Kit 1.294.0 named it the **Homer pattern**, the parallel of a regex pattern, and added near, and, where there are fields, letters anywhere and the three field parts. The matcher is `Homer.Search`, in Lbc.cs, which every app already compiles.

Every Homer search that is not a regex pattern reads what you type as a **Homer pattern**. A plain word is enough most of the time; the symbols are there when you need more.

- **A word** is found anywhere, whatever its case: `river` finds "Riverside".
- **`*`** stands for any run of characters, and **`?`** for any one character: `chap*`, `c?t`.
- **`&`** means all of them: `red & blue`.
- **`|`** means any of them: `red | blue`. `&` is read first, so `red & blue | green` means red and blue, or else green.
- **`!`** before a word means not: `!draft`.
- **Quotes** find exactly what is inside, symbols and all: `"C#"`, `"a & b"`.
- **Quotes and a tilde** find words near each other: `"guide dog"~5` finds guide and dog with at most five words between them, in either order.

Where there are fields, as in a DbDo table, a Homer pattern has four more parts. Each reuses a symbol of DbDo's filter form, where `%` means contains and `=` means is:

- **`%`** before a word finds those letters anywhere, even inside words: `%brail` finds braille and Braillenote. In Keywords every word works this way already; in Full-text match, which matches whole words, `%` asks for letters instead.
- **A field name and `:`** find a whole word in that field: `title:convention` finds Convention but not Conventional.
- **A field name and `%`** find letters anywhere in that field: `title%conv` finds Convention and Conversation.
- **A field name and `=`** find a field that is exactly the text, case aside: `title=Here and There`, or `title="Here and There"`.

A field part works only with a real field name, so `50%` or `x=y` is still plain text. `!` goes before any of them: `!kind:article` leaves out articles.

Where a wildcard counts depends on what is searched. When the search reads a **name** -- a file name, a line of a list, one field -- a word with `*` or `?` must match the whole name, so `*.md` means a name ending in .md, and `chap*` one starting with chap. When it reads **text** -- a file's contents, a whole record -- every word may match anywhere. A word with no wildcard is found anywhere in both.

F3 repeats the last search, in the same way and over the same things, going forward; Shift+F3 repeats it going back.

## For developers

- `Search.isMatch(sTarget, sPattern, bName)` tests one target. Pass `bName` true when the target is a name and false when it is text; `isMatch(sTarget, llParsed, bName, bCaseSensitive)` takes a pattern parsed once with `Search.parse`, for a search over many targets.
- `Search.likePattern(term, bName)` gives one term as a SQL LIKE pattern with `\` as its escape, for an app that searches a database; DbDo's `searchSql` shows the rest.
- `Search.Syntax` is the one-line reminder for a prompt, and `Search.FieldSyntax` the field parts' reminder.
- `Search.parse(sPattern, lsFields)` reads the field parts and a leading `%` only where a caller names its fields; `Search.isMatchRecord(dValues, llParsed, bCaseSensitive)` tests a record's fields, a field term on its field alone; `Search.termMatchAs` tests one term by its kind (near, whole word, exactly, letters).
- `Search.ftsTerm(term, lsIndexColumns)` gives one term in SQLite FTS5's language, or "" when a full-text index cannot say it, and `Search.likeBody(term)` one term as the inside of a LIKE pattern; DbDo's `patternWhere` puts them together, the index for what it can say and the fields for the rest.
- `LbcDialog.keywordsMatch` still works and now calls `Search` in text mode.

## Where each app uses it

- **The kit's list dialogs:** Filter and Jump read each line as a name; Keywords, and Filter in a list that knows more about each item than its line shows, read text.
- **FileDir:** the folder filter, Jump and File Find's Filter read names; Keywords and File Find's Text read file contents as text.
- **EdSharp:** Search for Topic reads each topic heading as a name; File Find reads names and contents; pick lists filter and jump by name. Find stays literal, because in an editor `&&` or `*` must be found as typed.
- **DbDo:** Keywords and Any Field read whole records as text, with the field parts; Full-text match reads them through the table's full-text index where it can; a Fields box with no operator, and Jump Record, read one field as a name.

Regular-expression commands, EdSharp's Find and Replace, and FileDir's Rename with Wildcards (which follows the Windows `ren` command) keep their own rules.
