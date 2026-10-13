"""fingerprint.py -- the Homer cache: skip work whose inputs have not changed, and ask the web for a newer tool only
every so many days. One module for every step (build, tidy, push, release) and every project, so no script invents
its own (1.65.34).

WHY. One kit cycle built the four samples three times -- in the build, in push's check and in release's check --
and ran the 42-second conversion test on every build, with nothing changed. buildBooks asked npm about Ace on every
run. Work is now done when its inputs changed, or its outputs are gone or altered, and not otherwise.

HOW IT DECIDES. A job has a key (such as "sample FruitBasketCs"), inputs (files and folders) and outputs (files). Its
fingerprint is one SHA-256 over every input file's path, relative to the project, and its content, plus any extra
text the caller adds (a tool's version, a setting). The job is current when the fingerprint matches the one recorded
after its last success, and every output still exists with the SHA-256 recorded then. Anything else -- a changed
input, a missing or altered output, no record -- means the work runs. Only success is recorded, so a failure is
always retried.

SPEED. Hashing a large tree on every run would cost what it saves, so each file's hash is remembered with its size
and modification time, and read again only when either changes.

WHERE. exec\\fingerprints.json in the project: beside the outputs it describes, never in git (exec is local), and
deleting exec forces every job to run again. The caller passes the project folder; exec is made there if missing.

FROM PYTHON
    import fingerprint
    oCache = fingerprint.Cache(sProject)
    sPrint = oCache.fingerprint(["FruitBasketCs.cs", "buildFruitBasketCs.cmd"], ["csc " + sCscVersion])
    if oCache.isCurrent("sample FruitBasketCs", sPrint, ["FruitBasketCs.exe"]): skip
    else: build, then oCache.record("sample FruitBasketCs", sPrint, ["FruitBasketCs.exe"])
    if oCache.checkDue("ace", 7): ask npm, then oCache.noteChecked("ace", "1.4.6")

FROM A BATCH FILE (exit 0 means current, 1 means the work must run, 2 a problem)
    python scripts\\fingerprint.py check  <project> <key> --in <path>... --out <path>... [--extra <text>...]
    python scripts\\fingerprint.py record <project> <key> --in <path>... --out <path>... [--extra <text>...]

Every decision is logged by the caller through the log function passed in, or printed when there is none.
"""

import datetime, hashlib, json, os, sys, time

c_sStoreName = "fingerprints.json"
c_setSkipFolders = {".git", ".venv", "__pycache__", "logs", "notes", "node_modules"}
# Build products inside an input folder are outputs, never inputs: a build that wrote one would change its own print.
c_setProductFolders = {"build", "dist"}
c_setProductExts = {".dll", ".exe", ".pdb", ".pyc", ".pyo", ".tmp"}


class Cache:
    """The fingerprints of one project, read from and written to exec\\fingerprints.json."""

    def __init__(self, sProject, fnLog=None):
        self.sProject = os.path.abspath(sProject)
        self.sStore = os.path.join(self.sProject, "exec", c_sStoreName)
        self.fnLog = fnLog or (lambda s: None)
        try:
            self.d = json.loads(open(self.sStore, encoding="utf-8").read()) if os.path.isfile(self.sStore) else {}
        except Exception as oError:
            self.fnLog("fingerprint store unreadable, so every job runs: %s" % oError)
            self.d = {}
        self.d.setdefault("jobs", {}); self.d.setdefault("files", {}); self.d.setdefault("checks", {})
        # What this object changed, so a save writes only that and keeps what other processes wrote meanwhile.
        self.setChanged = set()

    # ---- hashing ----
    def fileHash(self, sPath):
        """A file's SHA-256, read again only when its size or modification time changed since it was last hashed."""
        oStat = os.stat(sPath)
        sKey = os.path.normcase(os.path.abspath(sPath))
        dKnown = self.d["files"].get(sKey)
        if dKnown and dKnown.get("size") == oStat.st_size and dKnown.get("mtime") == oStat.st_mtime_ns:
            return dKnown["sha"]
        oSha = hashlib.sha256()
        with open(sPath, "rb") as f:
            for binChunk in iter(lambda: f.read(1 << 20), b""): oSha.update(binChunk)
        sSha = oSha.hexdigest()
        self.d["files"][sKey] = {"size": oStat.st_size, "mtime": oStat.st_mtime_ns, "sha": sSha}
        self.setChanged.add(("files", sKey))
        return sSha

    def expand(self, lsInputs, bSkipProducts=False):
        """Every file under the inputs, folders walked, sorted, skipping git, virtual environments, caches, logs, notes;
        with bSkipProducts, also programs, libraries and PyInstaller's build and dist folders found inside them."""
        lsFiles = []
        for sInput in lsInputs:
            sPath = sInput if os.path.isabs(sInput) else os.path.join(self.sProject, sInput)
            if os.path.isfile(sPath): lsFiles.append(sPath)
            elif os.path.isdir(sPath):
                for sDir, lsDirs, lsNames in os.walk(sPath):
                    lsDirs[:] = sorted(s for s in lsDirs if s not in c_setSkipFolders and not (bSkipProducts and s in c_setProductFolders))
                    lsFiles += [os.path.join(sDir, s) for s in sorted(lsNames)
                                if not s.endswith((".pyc", ".pyo")) and not s.startswith(c_sStoreName)
                                and not (bSkipProducts and os.path.splitext(s)[1].lower() in c_setProductExts)]
            else:
                lsFiles.append(sPath)  # a missing input is part of the fingerprint, as missing
        return lsFiles

    def fingerprint(self, lsInputs, lsExtra=None, bSkipProducts=False):
        """One SHA-256 over every input file's relative path and content, and the extra text given."""
        oSha = hashlib.sha256()
        for sFile in self.expand(lsInputs, bSkipProducts):
            # AN INPUT ON ANOTHER DRIVE (12 October 2026): an app's build names the kit's classes, and the kit may sit on
            # another drive, where a relative path cannot be made; its whole path stands in.
            try: sRelative = os.path.relpath(sFile, self.sProject).replace("\\", "/").lower()
            except ValueError: sRelative = os.path.normcase(os.path.abspath(sFile)).replace("\\", "/")
            oSha.update(sRelative.encode("utf-8") + b"\0")
            oSha.update((self.fileHash(sFile) if os.path.isfile(sFile) else "missing").encode("ascii") + b"\n")
        for sExtra in (lsExtra or []): oSha.update(b"extra\0" + str(sExtra).encode("utf-8") + b"\n")
        return oSha.hexdigest()

    # ---- jobs ----
    def isCurrent(self, sKey, sPrint, lsOutputs):
        """True when the job last succeeded with this fingerprint and every output is still as it left them."""
        dJob = self.d["jobs"].get(sKey)
        if not dJob:
            self.fnLog("%s: runs, no record of a successful run" % sKey); return False
        if dJob.get("print") != sPrint:
            self.fnLog("%s: runs, its inputs changed since %s" % (sKey, dJob.get("when", "?"))); return False
        for sOutput, sSha in dJob.get("outputs", {}).items():
            sPath = os.path.join(self.sProject, sOutput)
            if not os.path.isfile(sPath):
                self.fnLog("%s: runs, %s is missing" % (sKey, sOutput)); return False
            if self.fileHash(sPath) != sSha:
                self.fnLog("%s: runs, %s changed since it was made" % (sKey, sOutput)); return False
        lsNamed = [os.path.relpath(s if os.path.isabs(s) else os.path.join(self.sProject, s), self.sProject) for s in lsOutputs]
        if set(lsNamed) - set(dJob.get("outputs", {})):
            self.fnLog("%s: runs, it now has outputs not recorded before" % sKey); return False
        self.fnLog("%s: skipped, unchanged since %s" % (sKey, dJob.get("when", "?")))
        return True

    def record(self, sKey, sPrint, lsOutputs):
        """Notes a successful run: its fingerprint and the hash of each output. Saved at once."""
        dOutputs = {}
        for sOutput in lsOutputs:
            sPath = sOutput if os.path.isabs(sOutput) else os.path.join(self.sProject, sOutput)
            if os.path.isfile(sPath): dOutputs[os.path.relpath(sPath, self.sProject)] = self.fileHash(sPath)
        self.d["jobs"][sKey] = {"print": sPrint, "outputs": dOutputs, "when": datetime.datetime.now().isoformat(timespec="seconds")}
        self.setChanged.add(("jobs", sKey))
        self.save()

    def forget(self, sKey):
        """Drops a job's record, so it runs next time."""
        if self.d["jobs"].pop(sKey, None) is not None:
            self.setChanged.add(("jobs", sKey))
            self.save()

    # ---- version checks on the web ----
    def checkDue(self, sTool, fDays):
        """True when the web has not been asked about sTool within fDays days."""
        dCheck = self.d["checks"].get(sTool)
        if not dCheck: return True
        fAge = (time.time() - float(dCheck.get("checked", 0))) / 86400
        if fAge > fDays:
            self.fnLog("%s: newest version asked again, last asked %.1f days ago" % (sTool, fAge)); return True
        self.fnLog("%s %s: newest version asked %.1f days ago; not asked again until %s days" % (sTool, dCheck.get("version", ""), fAge, fDays))
        return False

    def noteChecked(self, sTool, sVersion):
        self.d["checks"][sTool] = {"version": sVersion or "", "checked": time.time()}
        self.setChanged.add(("checks", sTool))
        self.save()

    def checkedVersion(self, sTool):
        return self.d["checks"].get(sTool, {}).get("version", "")

    def save(self):
        """Written to a temporary file and moved into place, so a crash never leaves half a store.

        ONLY WHAT THIS OBJECT CHANGED IS WRITTEN (12 October 2026). A save once wrote back the whole store as it stood
        when this object read it, so a process opened earlier and saved later erased everything recorded in between:
        checkHomerDev opened the store, built the four samples and recorded each through other objects, then saved its
        pass over them, and the next build rebuilt all four, finding programs it had no record of. The store is now
        read again here, and only the entries this object added, changed or removed are put into it."""
        try:
            os.makedirs(os.path.dirname(self.sStore), exist_ok=True)
            dDisk = {}
            if os.path.isfile(self.sStore):
                try: dDisk = json.loads(open(self.sStore, encoding="utf-8").read())
                except Exception as oError: self.fnLog("fingerprint store unreadable while saving; rewritten from this run: %s" % oError)
            for sSection in ("jobs", "files", "checks"): dDisk.setdefault(sSection, {})
            for sSection, sKey in self.setChanged:
                if sKey in self.d[sSection]: dDisk[sSection][sKey] = self.d[sSection][sKey]
                else: dDisk[sSection].pop(sKey, None)
            sTemp = self.sStore + ".tmp"
            with open(sTemp, "w", encoding="utf-8") as f: f.write(json.dumps(dDisk, indent=1, sort_keys=True))
            os.replace(sTemp, self.sStore)
            self.d, self.setChanged = dDisk, set()
        except Exception as oError:
            self.fnLog("fingerprint store not written, so this work runs again next time: %s" % oError)


def main(lsArgs):
    """The batch-file form: check or record a job. Exit 0 current (or recorded), 1 must run, 2 a problem."""
    if len(lsArgs) < 3 or lsArgs[0] not in ("check", "record"):
        print("Usage: fingerprint.py check|record <project> <key> --in <path>... --out <path>... [--extra <text>...]")
        return 2
    sVerb, sProject, sKey = lsArgs[0], lsArgs[1], lsArgs[2]
    dLists, sList = {"--in": [], "--out": [], "--extra": []}, ""
    for sArg in lsArgs[3:]:
        if sArg in dLists: sList = sArg; continue
        if not sList: print("Expected --in, --out or --extra before %s" % sArg); return 2
        dLists[sList].append(sArg)
    oCache = Cache(sProject, print)
    sPrint = oCache.fingerprint(dLists["--in"], dLists["--extra"])
    if sVerb == "check": return 0 if oCache.isCurrent(sKey, sPrint, dLists["--out"]) else 1
    oCache.record(sKey, sPrint, dLists["--out"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
