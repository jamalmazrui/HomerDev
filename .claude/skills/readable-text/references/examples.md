# Examples and fidelity checks

Treat the following examples as synthetic illustrations, not mandatory templates.

## Joining caption lines

Input:

```text
[00:01:04] We tried the first
[00:01:06] approach, but it did not work.
[00:01:09] Um, the second approach
[00:01:12] worked on Windows only.
```

Edited output:

```text
[00:01:04] We tried the first approach, but it did not work. The second approach worked on Windows only.
```

Preserve both the failure and the platform limitation. Do not rewrite this as “The approach worked.”

## Preserving ambiguous technical speech

Input:

```text
[00:08:01] Import bee tee see, or bee tee speak,
[00:08:03] I cannot make out the module name.
```

Retain the uncertainty. Do not invent `import bt_speak` as runnable code. A readable rendition can say:

```text
[00:08:01] Import “bee tee see” or “bee tee speak”; I cannot make out the module name.
```

## Distinguishing escaped prose from a path

Input JSON:

```json
{"text":"First line.\nSecond line.","path":"C:\\new\\tools"}
```

Decode with a JSON parser. Present the text as prose, and preserve the path as `C:\new\tools`. Do not turn the path's `\n` into a newline by decoding the parsed value again.

## Avoiding global substitutions

If context establishes that “Blazy Technologies” refers to “Blazie Technologies,” correct that name. Do not replace every occurrence of “AP” with “APH”: “AP” could refer to Associated Press, an access point, or an identifier elsewhere.

## Preserving genuine repeated speech

Input:

```text
[00:04:00] Stop.
[00:04:03] Stop. That is unsafe.
```

Preserve both warnings. Deduplication requires evidence of overlapping caption display, not merely repeated text.

## Identifying the latest log outcome

Input:

```text
10:01 ERROR caption fetch failed
10:05 INFO caption fetch completed
10:05 ERROR output write failed
```

Preserve all three events. Do not report that the transcript was created; only the fetch completed.

## Chunk-boundary check

If one chunk ends with “The result was not” and the next begins with “significant,” join them as “The result was not significant.” Preserve the negation. Avoid an editorial heading between the fragments.
