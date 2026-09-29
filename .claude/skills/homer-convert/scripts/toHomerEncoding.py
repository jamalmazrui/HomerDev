"""
toHomerEncoding.py -- put text files into the Homer encoding.

Usage:
    python toHomerEncoding.py <file-folder-or-wildcard> [...]

The Homer encoding is UTF-8 with a byte order mark and CRLF line endings,
except .cmd and .bat files, version.txt and a skill's SKILL.md, which take
CRLF and no mark. Pandoc and most converters write UTF-8 with no mark and bare line
feeds, so run this on what they write. A file is read in the first encoding
that decodes it cleanly (UTF-8 with or without a mark, UTF-16 with a mark,
then Windows-1252); binary files are left alone. A folder is walked
recursively. Each file changed is reported, and a count at the end.

Exit code 0 when every file was read, 1 when one could not be, 2 for no
arguments.
"""

import glob, os, sys

c_lsNoMark = (".bat", ".cmd")
c_lsTextExt = (".bat", ".cmd", ".cs", ".css", ".csv", ".htm", ".html", ".inix", ".iss", ".js", ".json",
               ".md", ".ps1", ".py", ".tsv", ".txt", ".xml")


def decode(binData):
    """The text of a file, or None when it is not text."""
    if binData.startswith(b"\xff\xfe") or binData.startswith(b"\xfe\xff"):
        return binData.decode("utf-16")
    if b"\x00" in binData: return None
    for sEncoding in ("utf-8-sig", "cp1252"):
        try:
            return binData.decode(sEncoding)
        except UnicodeDecodeError:
            continue
    return None


def convert(sPath):
    """Rewrite one file in the Homer encoding. Returns "changed", "same" or a problem."""
    binData = open(sPath, "rb").read()
    sText = decode(binData)
    if sText is None: return "not text"
    sText = sText.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    sName = os.path.basename(sPath)
    # version.txt is read by build scripts and Inno, which want the number alone.
    bMark = not (sName.lower().endswith(c_lsNoMark) or sName in ("SKILL.md", "version.txt"))
    binNew = (b"\xef\xbb\xbf" if bMark else b"") + sText.encode("utf-8")
    if binNew == binData: return "same"
    open(sPath, "wb").write(binNew)
    return "changed"


def expand(sArgument):
    """The text files an argument names."""
    if os.path.isdir(sArgument):
        lsPaths = []
        for sDir, lsDirs, lsFiles in os.walk(sArgument):
            lsDirs[:] = [s for s in lsDirs if s not in (".git", "__pycache__")]
            lsPaths += [os.path.join(sDir, s) for s in lsFiles if s.lower().endswith(c_lsTextExt)]
        return sorted(lsPaths)
    return sorted(glob.glob(sArgument)) or [sArgument]


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    iChanged = 0
    bProblem = False
    for sArgument in sys.argv[1:]:
        for sPath in expand(sArgument):
            try:
                sOutcome = convert(sPath)
            except Exception as oError:
                sOutcome = "could not be read: %s" % oError
            if sOutcome == "changed":
                iChanged += 1
                print("changed: " + sPath)
            elif sOutcome not in ("same", "not text"):
                bProblem = True
                print("%s: %s" % (sPath, sOutcome))
    print("%d file%s changed." % (iChanged, "" if iChanged == 1 else "s"))
    return 1 if bProblem else 0


if __name__ == "__main__":
    sys.exit(main())
