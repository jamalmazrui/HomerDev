# Format handling

## Captions and subtitle files

Parse SRT and WebVTT cue blocks, distinguishing timestamps, cue IDs, markup, and speech. For YouTube JSON3, combine `events[].segs[].utf8` within each event and derive starts from `tStartMs`; preserve order and inspect append/rolling behavior before deduplicating. Do not extract configuration or window-style records as speech. For other JSON formats, inspect the schema instead of assuming all transcripts use these field names.

Retain a source-to-output range map during editing. When combining cues, use the first retained cue's timestamp. Do not treat a timestamp as a paragraph boundary by itself. Preserve the final utterance and any early audio glitch. Check for mid-sentence breaks where an editorial heading would otherwise split a sentence.

## OCR and hard-wrapped text

Distinguish line wrapping from paragraph breaks, poetry, addresses, lists, columns, and code. Rejoin a hyphenated word only when it is clearly a line-end split; preserve compound words, minus signs, and ranges. Remove recurring headers and footers only after verifying they are layout artifacts. Record meaningful notes and captions rather than dropping them. Do not guess multi-column reading order when the extraction is ambiguous.

## JSON, XML, CSV, and escaped text

Identify the intended records and text fields. Preserve relevant titles, author labels, order, and timestamps. Decode serialization syntax with the relevant parser. Keep identifiers and values exact. Handle CSV quoting with a CSV parser, not a split on commas. Treat XML/HTML markup as structure; avoid parsers that resolve untrusted external entities. Distinguish literal code examples from encoded prose.

## Logs

Preserve event times, severity, operation identifiers, and outcome. Distinguish past errors in an appended log from the latest run. Do not merge warnings with errors or remove repeated events merely because their wording matches. If the user requests readability rather than a summary, retain substantive diagnostic information in organized sections.

## Missing or contradictory sources

Keep incompatible accounts separate. Note missing segments and unknown speakers. Use the user's chosen source version when specified. Otherwise select based on evidence of completeness and recency, and disclose that selection. Do not fill missing content from memory or silently use another recording as the same source.
