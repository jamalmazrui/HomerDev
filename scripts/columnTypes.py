"""columnTypes: Homer"s vocabulary of declared column types (5 November 2026), the Python twin of Homer.ColumnTypes in
exec\\CSharp\\Schema.cs; change both together. The prefix states storage, as SQLite decides it from the name (TEXT for
UTF-8 text, BLOB for bytes); the rest names the format by its usual file extension, and each type records its MIME type.
No name may contain INT, and no BLOB name CHAR, CLOB or TEXT, or SQLite stores it otherwise. See help\\ColumnTypes.md."""

import os

# (type, file extension, MIME type, lines: multi | single | binary, action, meaning), alphabetical
lTypes = [
    ("BLOBDOCX", ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "binary", "show", "a Word document"),
    ("BLOBEPUB", ".epub", "application/epub+zip", "binary", "show", "an EPUB book"),
    ("BLOBGIF", ".gif", "image/gif", "binary", "show", "a GIF picture"),
    ("BLOBJPG", ".jpg", "image/jpeg", "binary", "show", "a JPEG photo"),
    ("BLOBM4A", ".m4a", "audio/mp4", "binary", "show", "AAC audio"),
    ("BLOBMP3", ".mp3", "audio/mpeg", "binary", "show", "MP3 audio"),
    ("BLOBMP4", ".mp4", "video/mp4", "binary", "show", "MP4 video"),
    ("BLOBOGG", ".ogg", "audio/ogg", "binary", "show", "Ogg audio"),
    ("BLOBPDF", ".pdf", "application/pdf", "binary", "show", "a PDF document"),
    ("BLOBPNG", ".png", "image/png", "binary", "show", "a PNG picture"),
    ("BLOBPPTX", ".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "binary", "show", "a PowerPoint deck"),
    ("BLOBWAV", ".wav", "audio/wav", "binary", "show", "WAV audio"),
    ("BLOBWEBM", ".webm", "video/webm", "binary", "show", "WebM video"),
    ("BLOBWEBP", ".webp", "image/webp", "binary", "show", "a WebP picture"),
    ("BLOBXLSX", ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "binary", "show", "an Excel workbook"),
    ("BLOBZIP", ".zip", "application/zip", "binary", "show", "a zip archive"),
    ("TEXTCSV", ".csv", "text/csv", "multi", "edit", "comma-separated values"),
    ("TEXTDBDO", ".dbdo", "text/x-dbdo", "multi", "edit", "a DbDo routine of dot-prompt commands"),
    ("TEXTEMAIL", "", "", "single", "mail", "an email address, written to with mailto"),
    ("TEXTHTML", ".htm", "text/html", "multi", "edit", "a web page"),
    ("TEXTICS", ".ics", "text/calendar", "multi", "edit", "iCalendar events"),
    ("TEXTINIX", ".inix", "text/x-inix", "multi", "edit", "Homer settings, in sections of key = value lines"),
    ("TEXTJSCRIPT", ".js", "text/javascript", "multi", "edit", "a JScript .NET program"),
    ("TEXTJSON", ".json", "application/json", "multi", "edit", "JSON data"),
    ("TEXTLINE", "", "text/plain", "single", "", "one line of plain text"),
    ("TEXTM3U", ".m3u", "audio/x-mpegurl", "multi", "edit", "a playlist"),
    ("TEXTMARKDOWN", ".md", "text/markdown", "multi", "edit", "Markdown"),
    ("TEXTMEMO", ".txt", "text/plain", "multi", "edit", "lines of plain text"),
    ("TEXTPATH", "", "", "single", "open", "the path of a file or folder, opened by Windows"),
    ("TEXTPHONE", "", "", "single", "call", "a phone number, called with tel"),
    ("TEXTSQL", ".sql", "application/sql", "multi", "edit", "SQL statements"),
    ("TEXTSRT", ".srt", "application/x-subrip", "multi", "edit", "SubRip captions"),
    ("TEXTSVG", ".svg", "image/svg+xml", "multi", "edit", "an SVG drawing, which is text"),
    ("TEXTTIME", "", "", "single", "", "a date and time, as YYYY-MM-DD HH:MM:SS"),
    ("TEXTTSV", ".tsv", "text/tab-separated-values", "multi", "edit", "tab-separated values"),
    ("TEXTURL", "", "", "single", "browse", "a web address, opened in the default browser"),
    ("TEXTVCAL", ".vcs", "text/x-vcalendar", "multi", "edit", "vCalendar events"),
    ("TEXTVCARD", ".vcf", "text/vcard", "multi", "edit", "vCard contacts"),
    ("TEXTVTT", ".vtt", "text/vtt", "multi", "edit", "WebVTT captions"),
    ("TEXTXML", ".xml", "application/xml", "multi", "edit", "XML"),
]
dExtAlias = {".html": "TEXTHTML", ".ini": "TEXTINIX", ".jpeg": "BLOBJPG", ".m3u8": "TEXTM3U", ".markdown": "TEXTMARKDOWN", ".text": "TEXTMEMO"}
dTypeAlias = {"BLOBJPEG": "BLOBJPG", "TEXTJS": "TEXTJSCRIPT", "TEXTJAVASCRIPT": "TEXTJSCRIPT", "TEXTMD": "TEXTMARKDOWN", "TEXTPLAIN": "TEXTMEMO", "TEXTTEL": "TEXTPHONE", "TEXTTXT": "TEXTMEMO"}


def names(): return [t[0] for t in lTypes]


def canonical(sType):
    s = (sType or "").strip().upper()
    return dTypeAlias.get(s, s)


def rowOf(sType):
    s = canonical(sType)
    for t in lTypes:
        if t[0] == s: return t
    return None


def typeForName(sFileName):
    """The type for a file, by its extension; TEXTMEMO when the extension names no format."""
    sExt = os.path.splitext(sFileName or "")[1].lower()
    if not sExt: return "TEXTMEMO"
    for t in lTypes:
        if t[1] and t[1] == sExt: return t[0]
    return dExtAlias.get(sExt, "TEXTMEMO")


def typeForMime(sMime):
    s = (sMime or "").split(";")[0].strip().lower()
    for t in lTypes:
        if t[2] and t[2] == s: return t[0]
    return ""


def affinityOf(sDeclared):
    """The affinity SQLite gives a declared type, by its rules in their order."""
    s = (sDeclared or "").upper()
    if "INT" in s: return "INTEGER"
    if "CHAR" in s or "CLOB" in s or "TEXT" in s: return "TEXT"
    if "BLOB" in s or not s.strip(): return "BLOB"
    if "REAL" in s or "FLOA" in s or "DOUB" in s: return "REAL"
    return "NUMERIC"


def isBinary(sType): return bool((sType or "").strip()) and affinityOf(canonical(sType)) == "BLOB"


def isMultiline(sType):
    t = rowOf(sType)
    if t: return t[3] == "multi"
    s = canonical(sType)
    return affinityOf(s) == "TEXT" and s.startswith("TEXT") and s != "TEXT"
