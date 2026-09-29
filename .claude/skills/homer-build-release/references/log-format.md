# The Homer log format

## Where logs are

- A project's steps: `C:\<App>\logs\<App>-<task>-yyyyMMdd-HHmmss.log`, one per
  run (tasks: build, tidy, push, check, release, release-launch, encoding,
  tutorials and others). The check also writes `<App>-evidence-<stamp>.md`.
- An installed or built program's own runs:
  `%LOCALAPPDATA%\<App>\logs\<App>-yyyyMMdd-HHmmss.log`.
- An installer: `<App>-setup-<stamp>.log`, and the component summary in
  `%LOCALAPPDATA%\<App>\logs\<App>_setup.log` for apps that write one.

## The line

```
2026-09-27T16:16:40.123-07:00 INFO  session start app=2htm version=1.19.4 pid=4312
2026-09-27T16:16:40.125-07:00 INFO  env windows="Windows 11 25H2 (10.0.26200.9550)"
2026-09-27T16:16:41.002-07:00 ERROR run exit=1 ms=812 cmd="pandoc ReadMe.md"
2026-09-27T16:16:41.003-07:00 ERROR | at Homer.Web.get(...)
```

- ISO 8601 time with milliseconds and UTC offset; level INFO, WARN or ERROR
  in five characters; then the message.
- Facts are `key=value`, keys in lower camel case; a value is quoted when it
  holds a space, a quote or an equals sign.
- Named events: `session start`, `session end`, `env`, `settings`, `run`,
  `exception`, `prune`, and in scripts `<script> start` and `<script> end`.
- A line continuing the one above starts `| `.
- In kit scripts a line is ERROR when it says ERROR, FAIL or FAILED, and WARN
  when it says WARN. `CONSOLE:` lines repeat what the user saw.

Build logs from `.cmd` scripts stamp only their `build start` and `build end`
lines; the lines between are the compiler's and Inno Setup's own output.
Logs written before HomerDev 1.43.21 use older forms ("Build succeeded
Sun 09/27/2026 ..." and "Key = value").
