# Homer logging convention

Every Homer script and program writes a log. This says where it goes and what
it is called, so that one answer serves every tool and nobody has to guess.

## Where

- **A tool run from a project folder** — a build, a clean, a tidy, an audit —
  writes into that project's `logs\` folder.
- **An installed program** writes into `%LOCALAPPDATA%\<App>\logs`.
- **A standalone script**, run from nowhere in particular, writes beside
  itself.

A tool in `scripts\`, `tools\` or `exec\` belongs to the project one level up,
so it writes to that project's `logs\`, not into its own folder.

## What it is called

    <App>-<task>-yyyyMMdd-HHmmss.log

For example `HomerScribe-tidy-20260924-124602.log`.

**One file per run.** An alphabetical sort is then a chronological one, and the
whole folder can be zipped and sent when something needs diagnosing.

## Why not one fixed name

A single fixed name overwrites the run before it. That is exactly the file you
want when something has gone wrong twice, and it is gone.

`homerTidy.py` wrote `homerTidy.log` beside itself for months. When a tidy went
wrong, the only way to see what the previous run had done was to not run it
again — which nobody remembers in time.

## Console versus log

The **console** says, briefly and in plain words, what was found and what was
done. The **log** holds the detail: every command, its exit code, every path,
every setting, and any error or traceback.

A failure must never produce only a console message with nothing in the log.

## What a log opens with

Enough to tell where it came from without asking:

- the script's full path
- the language runtime and platform
- the working directory
- the command line, with its arguments
- every effective setting

## The helper

`homerLogPath(sScriptDir)` in `homerTidy.py` works the project folder out and
returns the timestamped path. Copy it rather than rewriting the rule.
