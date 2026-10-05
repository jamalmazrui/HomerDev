// Media.cs -- finding and running ExifTool, ffmpeg and ffprobe, for Homer Tools.
//
// Copyright 2006-2026 by Jamal Mazrui
// MIT License. See License.md, which carries the terms in full.
//
// WHAT THIS IS FOR
//
// ExifTool reads and writes the metadata inside a file: the camera that took a
// photograph, the artist and album of a song, the duration and codecs of a
// video, the author and producer of a PDF. It knows thousands of tags across
// hundreds of formats, which is why FileDir asks it rather than parsing any of
// those formats itself.
//
// ffmpeg and ffprobe are here for the same reason and are located the same way.
//
// This code is adapted from HomerScribe, which uses ExifTool to write picture
// descriptions. The finding is the hard part and HomerScribe already solved it;
// what each program does with the tool afterwards differs.
//
// WHY EVERY CANDIDATE IS RUN RATHER THAN GUESSED AT
//
// HomerScribe's note is worth keeping whole: a copy installed with winget sat
// alongside an older one in the build folder, and the question "which will be
// used" could not be answered by looking. So every likely place is tried, each
// candidate is RUN to learn its version, and all of them are recorded with the
// choice and the reason. The log then answers that question without anybody
// going to look.
//
// ONE DIFFERENCE FROM HOMERSCRIBE
//
// HomerScribe insists on a single-file ExifTool, because a packaged one --
// a small launcher plus an "exiftool_files" folder holding Perl -- complicates
// what it has to ship. FileDir only READS, so a packaged copy works perfectly
// well and is accepted. A single file beside FileDir.exe is still preferred,
// and the log says which was chosen.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace Homer {

public static class Media {

private static string sExifToolCache = null;
private static string sExifToolLog = "";

// What Windows counts as runnable, in the order it prefers them. A .cmd or a
// .bat is a real way to run a program -- "where mpv" answered with
// c:\bin\mpv.cmd on the machine where this went wrong -- but a batch file
// cannot be started directly by the process object, so callers must send one
// through the command interpreter. needsShell says which is which.
public static readonly string[] c_aRunnable = {".exe", ".com", ".cmd", ".bat"};

public static bool needsShell(string sProgram) {
string sExt = Path.GetExtension(sProgram).ToLower();
return sExt == ".cmd" || sExt == ".bat";
} // needsShell method

public static string findTool(string sName) {
return findToolOfKind(sName, c_aRunnable);
} // findTool method

public static string findToolOfKind(string sName, string[] aExtensions) {
// Beside the program first, then the PATH. A tool the developer dropped into
// the program folder is the one meant to be used, whatever else is installed.
//
// Looking only for .exe is half of why FileDir said mpv was not installed on a
// machine that had it: the PATH held a .cmd wrapper, which runs mpv perfectly
// well, and it was walked straight past.
foreach (string sExt in aExtensions) {
string sBeside = Path.Combine(exeFolder(), sName + sExt);
if (File.Exists(sBeside)) return sBeside;
}
string sPath = Environment.GetEnvironmentVariable("PATH");
if (sPath == null) return "";
foreach (string sFolder in sPath.Split(Path.PathSeparator)) {
if (sFolder.Trim().Length == 0) continue;
foreach (string sExt in aExtensions) {
string sTry = "";
try {
sTry = Path.Combine(sFolder.Trim(), sName + sExt);
}
catch (Exception) {
break;
}
if (File.Exists(sTry)) return sTry;
}
}
return "";
} // findToolOfKind method

public static string exeFolder() {
try {
return Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
}
catch (Exception) {
return Directory.GetCurrentDirectory();
}
} // exeFolder method

public static double versionRank(string sVersion) {
// A version turned into something that sorts correctly.
//
// "13.11" is LATER than "13.8" -- ExifTool numbers its releases that way --
// but as decimals 13.8 is the larger and the older copy would be chosen. Each
// part is a whole number, so the second is scaled rather than treated as a
// fraction.
Match parts = Regex.Match(sVersion.Trim(), @"^(\d+)(?:\.(\d+))?");
if (!parts.Success) return -1.0;
double nMajor = 0.0;
double nMinor = 0.0;
double.TryParse(parts.Groups[1].Value, System.Globalization.NumberStyles.Integer,
                System.Globalization.CultureInfo.InvariantCulture, out nMajor);
if (parts.Groups[2].Success)
double.TryParse(parts.Groups[2].Value, System.Globalization.NumberStyles.Integer,
                System.Globalization.CultureInfo.InvariantCulture, out nMinor);
return nMajor * 1000.0 + nMinor;
} // versionRank method

public static string exifToolLog() {
// What the search found and why, for the Type Extended dialog to show when
// nothing was found. A person who is told "not found" and nothing else has no
// idea what to do next.
return sExifToolLog;
} // exifToolLog method

public static string exifToolProgram() {
// Every ExifTool on this machine, run, and the newest chosen.
//
// The places cover winget's two habits -- a real install under Program Files
// or the user's Programs folder, and a shim under WinGet\Links -- as well as
// the package folder it unpacks into, FileDir's own folder, and the PATH.
if (sExifToolCache != null) return sExifToolCache;
sExifToolCache = "";
StringBuilder sbLog = new StringBuilder();

List<string> lsWhere = new List<string>();
lsWhere.Add(Path.Combine(exeFolder(), "exiftool.exe"));
lsWhere.Add(@"C:\FileDir\exiftool.exe");
foreach (string sRoot in new string[] {
Environment.GetEnvironmentVariable("ProgramFiles"),
Environment.GetEnvironmentVariable("ProgramFiles(x86)"),
Environment.GetEnvironmentVariable("ProgramW6432")}) {
if (sRoot != null && sRoot.Length > 0) lsWhere.Add(Path.Combine(sRoot, "ExifTool", "exiftool.exe"));
}
string sLocal = Environment.GetEnvironmentVariable("LOCALAPPDATA");
if (sLocal != null && sLocal.Length > 0) {
lsWhere.Add(Path.Combine(sLocal, "Programs", "ExifTool", "exiftool.exe"));
// winget's shim folder, which is on the PATH of a shell opened after the
// install but not of one opened before it.
lsWhere.Add(Path.Combine(sLocal, "Microsoft", "WinGet", "Links", "exiftool.exe"));
string sPackages = Path.Combine(sLocal, "Microsoft", "WinGet", "Packages");
try {
if (Directory.Exists(sPackages)) {
foreach (string sOne in Directory.GetDirectories(sPackages, "*ExifTool*")) {
foreach (string sExe in Directory.GetFiles(sOne, "exiftool.exe", SearchOption.AllDirectories))
lsWhere.Add(sExe);
}
}
}
catch (Exception) {
}
}
string sOnPath = findTool("exiftool");
if (sOnPath.Length > 0) lsWhere.Add(sOnPath);

string sBest = "";
string sBestVersion = "";
double nBest = -1.0;
List<string> lsSeen = new List<string>();
foreach (string sOne in lsWhere) {
if (sOne == null || sOne.Length == 0 || !File.Exists(sOne)) continue;
bool bAlready = false;
foreach (string sHad in lsSeen) if (String.Compare(sHad, sOne, true) == 0) bAlready = true;
if (bAlready) continue;
lsSeen.Add(sOne);
string sOut, sErr;
int iCode = run(sOne, "-ver", out sOut, out sErr);
string sVersion = (sOut + sErr).Trim();
if (iCode != 0 || sVersion.Length == 0 || !Regex.IsMatch(sVersion, @"^\d+(\.\d+)?")) {
sbLog.AppendLine("  " + sOne + " -- will not run");
continue;
}
double nVersion = versionRank(sVersion);
sbLog.AppendLine("  " + sOne + " -- version " + sVersion);
if (nVersion > nBest) {
nBest = nVersion;
sBest = sOne;
sBestVersion = sVersion;
}
}
if (sBest.Length == 0) {
sbLog.AppendLine("No ExifTool was found. Put exiftool.exe in the FileDir folder,");
sbLog.AppendLine("or install it with: winget install OliverBetz.ExifTool");
}
else {
sbLog.AppendLine("Chosen: " + sBest + ", version " + sBestVersion
+ (lsSeen.Count > 1 ? ", the newest of " + lsSeen.Count + " found." : "."));
}
sExifToolLog = sbLog.ToString();
sExifToolCache = sBest;
return sExifToolCache;
} // exifToolProgram method

public static string ffmpegProgram() {
return findInstalled("ffmpeg");
} // ffmpegProgram method

// Where each installer actually puts its program, when the folder is not
// simply the command's own name. Read before the PATH, because these are
// certain and the PATH is not.
private static readonly string[,] c_aOfficialFolders = {
// "MPV Player" is what shinchiro's installer actually creates. It was guessed
// as "MPV Media Player", which is close, wrong, and finds nothing. Guessing a
// folder name is how this went round three times; the others below are read
// from real installations too, not invented.
{"mpv", "MPV Player"}, {"mpv", "mpv"}, {"mpv", "MPV Media Player"}, {"mpv", "mpv.net"},
{"pandoc", "Pandoc"},
{"exiftool", "ExifTool"},
{"ffmpeg", "ffmpeg"}, {"ffprobe", "ffmpeg"},
{"magick", "ImageMagick"},
{"yt-dlp", "yt-dlp"}
};

public static string mpvProgram() {
return findInstalled("mpv");
} // mpvProgram method

private static string sSearchLog = "";

public static string searchLog() {
// Where the last findInstalled looked, and what it found. Shown to the person
// when a tool is missing, so "it says not installed" stops being a mystery and
// becomes a list they can check against their own machine.
return sSearchLog;
} // searchLog method

public static string findInstalled(string sName) {
// A REAL EXECUTABLE IS PREFERRED OVER A WRAPPER, wherever each is found.
//
// findTool walks the PATH and takes the first runnable thing it meets, which on
// one machine was c:\bin\mpv.cmd -- a batch wrapper sitting in a folder early
// on the PATH, while the actual player was in Program Files. The wrapper was
// launched, and nothing played: a wrapper that does not forward its arguments
// swallows the play list silently, and there is no way to tell from outside
// which kind it is.
//
// So the whole search runs twice. The first pass accepts only .exe and .com,
// which are programs. Only if that finds nothing does the second pass accept
// .cmd and .bat, because a wrapper is better than no player at all.
string sReal = findInstalledOfKind(sName, c_aPrograms);
if (sReal.Length > 0) return sReal;
return findInstalledOfKind(sName, c_aRunnable);
} // findInstalled method

// Things that are programs, as against things that describe how to run one.
public static readonly string[] c_aPrograms = {".exe", ".com"};

private static string findInstalledOfKind(string sName, string[] aExtensions) {
// A tool anywhere it might plausibly be, not merely on this process's PATH.
//
// THE FAULT THIS EXISTS FOR. The installer ran "where mpv", found it, and
// offered Reinstall. FileDir then said it was not installed. Both were telling
// the truth: the installer's shell was started after winget added mpv to the
// machine path, and FileDir was started from a desktop shortcut by an Explorer
// that had been running since before the install. A process inherits the
// environment it was born with, so FileDir's PATH did not have mpv in it and
// would not until the next sign-in.
//
// Asking the PATH is therefore never enough for a tool that may have been
// installed minutes ago. Every place winget and ordinary installers put things
// is looked at as well, including the package folder winget unpacks into,
// which no PATH ever mentions. This is the same search exifToolProgram already
// does; it is written once here so every tool gets it.
StringBuilder sbLog = new StringBuilder();
sbLog.Append("Looking for " + sName + " with " + String.Join(" ", aExtensions) + ":\r\n");
// THE EXTENSIONS OF THIS PASS, not every runnable one. Calling findTool here
// undid the whole point of the two passes: findTool accepts .cmd, so the first
// pass -- the one meant to find only real programs -- returned the wrapper on
// the PATH before it ever looked in Program Files. The two-pass search was
// written, shipped, and did nothing, because this one line still asked the
// wrong question.
// THE OFFICIAL LOCATION IS ASKED FIRST, AND THE PATH LAST.
//
// The PATH used to come first, and that is the wrong order for anything the
// installer put there itself. FileDir launched from the installer's own finish
// page is the worst case: it starts before winget has finished, inherits a
// PATH from before the install, and then cannot find what the installer just
// wrote to disk. That is what Scott hit.
//
// Broadcasting WM_SETTINGCHANGE, the usual answer, tells OTHER programs to
// re-read their environment. It cannot help a process that has already
// started. So the environment is not relied on where a real location will do.
//
// Beside FileDir first, because a copy the developer put there is the one
// meant to be used.
foreach (string sExt in aExtensions) {
string sBeside = Path.Combine(exeFolder(), sName + sExt);
sbLog.Append("  " + sBeside + ": " + (File.Exists(sBeside) ? "found" : "no") + "\r\n");
if (File.Exists(sBeside)) {
sSearchLog = sbLog.ToString();
return sBeside;
}
}

List<string> lsWhere = new List<string>();

// THE NAMED FOLDER EACH INSTALLER ACTUALLY USES. Certain, machine wide, and
// true the moment the installer finishes, whatever the PATH says. mpv installs
// as "MPV Media Player", which no rule about the command name would guess.
foreach (string sRoot in new string[] {
Environment.GetEnvironmentVariable("ProgramFiles"),
Environment.GetEnvironmentVariable("ProgramFiles(x86)"),
Environment.GetEnvironmentVariable("ProgramW6432")}) {
if (sRoot == null || sRoot.Length == 0) continue;
for (int i = 0; i < c_aOfficialFolders.GetLength(0); i++) {
if (!String.Equals(c_aOfficialFolders[i, 0], sName, StringComparison.OrdinalIgnoreCase)) continue;
foreach (string sExt in aExtensions) {
lsWhere.Add(Path.Combine(sRoot, Path.Combine(c_aOfficialFolders[i, 1], sName + sExt)));
lsWhere.Add(Path.Combine(sRoot, Path.Combine(c_aOfficialFolders[i, 1], Path.Combine("bin", sName + sExt))));
}
}
}

foreach (string sRoot in new string[] {
Environment.GetEnvironmentVariable("ProgramFiles"),
Environment.GetEnvironmentVariable("ProgramFiles(x86)"),
Environment.GetEnvironmentVariable("ProgramW6432")}) {
if (sRoot == null || sRoot.Length == 0) continue;
foreach (string sExt in aExtensions) {
lsWhere.Add(Path.Combine(sRoot, Path.Combine(sName, sName + sExt)));
lsWhere.Add(Path.Combine(sRoot, Path.Combine(sName, Path.Combine("bin", sName + sExt))));
}
}
string sLocal = Environment.GetEnvironmentVariable("LOCALAPPDATA");
if (sLocal != null && sLocal.Length > 0) {
foreach (string sExt in aExtensions)
lsWhere.Add(Path.Combine(sLocal, Path.Combine("Programs", Path.Combine(sName, sName + sExt))));
// winget's shim folder: on the machine path, but not on the path of a
// process that started before the install.
foreach (string sExt in aExtensions)
lsWhere.Add(Path.Combine(sLocal, Path.Combine("Microsoft", Path.Combine("WinGet", Path.Combine("Links", sName + sExt)))));
}
foreach (string sTry in lsWhere) {
bool bThere = File.Exists(sTry);
sbLog.Append("  " + sTry + ": " + (bThere ? "found" : "no") + "\r\n");
if (bThere) {
sSearchLog = sbLog.ToString();
return sTry;
}
}

// A program's folder is rarely named exactly after its command. mpv installs
// into "MPV Player", and looking only for a folder called "mpv" is the other
// half of why FileDir declared it missing on a machine where it plainly was.
// So the likely roots are read and any folder whose NAME CONTAINS the tool
// name is examined.
foreach (string sRoot in new string[] {
Environment.GetEnvironmentVariable("ProgramFiles"),
Environment.GetEnvironmentVariable("ProgramFiles(x86)"),
Environment.GetEnvironmentVariable("ProgramW6432"),
(sLocal == null || sLocal.Length == 0) ? "" : Path.Combine(sLocal, "Programs")}) {
if (sRoot == null || sRoot.Length == 0 || !Directory.Exists(sRoot)) continue;
string[] aCandidates;
try {
aCandidates = Directory.GetDirectories(sRoot, "*" + sName + "*");
}
catch (Exception) {
continue;
}
foreach (string sFolder in aCandidates) {
foreach (string sExt in aExtensions) {
foreach (string sTry in new string[] {
Path.Combine(sFolder, sName + sExt),
Path.Combine(sFolder, Path.Combine("bin", sName + sExt))}) {
bool bThere = File.Exists(sTry);
sbLog.Append("  " + sTry + ": " + (bThere ? "found" : "no") + "\r\n");
if (bThere) {
sSearchLog = sbLog.ToString();
return sTry;
}
}
}
}
}

// Last, the folder winget unpacks a portable package into. Its name carries
// the publisher and version, so it is searched rather than guessed.
if (sLocal != null && sLocal.Length > 0) {
string sPackages = Path.Combine(sLocal, Path.Combine("Microsoft", Path.Combine("WinGet", "Packages")));
try {
if (Directory.Exists(sPackages)) {
foreach (string sOne in Directory.GetDirectories(sPackages, "*" + sName + "*")) {
foreach (string sExe in Directory.GetFiles(sOne, sName + ".exe", SearchOption.AllDirectories)) {
sbLog.Append("  " + sExe + ": found\r\n");
sSearchLog = sbLog.ToString();
return sExe;
}
}
sbLog.Append("  " + sPackages + ": no folder matching " + sName + "\r\n");
}
}
catch (Exception) {
}
}
// LAST, THE PATH, for a copy somewhere none of the above covers. It comes
// last on purpose: everything above is a real location on disk and is true the
// moment an installer finishes, where the PATH of a running process is only as
// current as the moment that process started.
string sOnPath = findToolOfKind(sName, aExtensions);
sbLog.Append("  on the PATH: " + (sOnPath.Length > 0 ? sOnPath : "not found") + "\r\n");
sSearchLog = sbLog.ToString();
Homer.Log.info(sSearchLog.Replace("\r\n", " | "));
return sOnPath;
} // findInstalledOfKind method

public static string magickProgram() {
// ImageMagick's single command. Since version 7 everything goes through
// "magick"; the older "convert" name is not looked for, because Windows has
// its own convert.exe that formats disks, and picking that one up would be a
// spectacular way to fail.
return findInstalled("magick");
} // magickProgram method

public static string ffprobeProgram() {
return findInstalled("ffprobe");
} // ffprobeProgram method

public static List<string[]> readProperties(string sPath, out string sError) {
// Every metadata field ExifTool can see in one file, as name and value pairs.
//
// -s3 would give the values alone; the group-and-name form is wanted here, so
// the plain listing is parsed instead. -charset UTF8 matters: without it a
// caption in anything but the system code page comes back as nonsense.
// -a keeps duplicate tags rather than silently dropping all but one, and -G
// prefixes each with its group so two tags of the same name stay apart.
sError = "";
List<string[]> lsPairs = new List<string[]>();
string sExe = exifToolProgram();
if (sExe.Length == 0) {
sError = "ExifTool was not found, so only the Windows properties are shown.";
return lsPairs;
}
if (!File.Exists(sPath)) {
sError = "The file was not found.";
return lsPairs;
}
string sOut, sErr;
int iCode = run(sExe, "-a -G -charset UTF8 -m -q " + Homer.Util.stringQuote(sPath), out sOut, out sErr);
if (iCode != 0 && sOut.Trim().Length == 0) {
sError = sErr.Trim();
if (sError.Length == 0) sError = "ExifTool returned " + iCode + ".";
return lsPairs;
}
foreach (string sLine in sOut.Replace("\r\n", "\n").Split('\n')) {
int iColon = sLine.IndexOf(':');
if (iColon < 1) continue;
string sName = sLine.Substring(0, iColon).Trim();
string sValue = sLine.Substring(iColon + 1).Trim();
if (sName.Length == 0) continue;
lsPairs.Add(new string[] {sName, sValue});
}
return lsPairs;
} // readProperties method

// Field names whose value is a title of some kind. ExifTool reports thousands
// of tags across hundreds of formats and they disagree about what to call this:
// a PDF has Title, an MP3 has Title and Album, a photograph has ObjectName,
// Headline, Caption-Abstract and Description, an EPUB has BookName.
//
// So the name is matched rather than listed. Anything whose field name contains
// one of these words is a candidate, and the best candidate wins.
private static readonly string[] c_aTitleWords = {
"title", "headline", "caption", "objectname", "bookname", "songname",
"trackname", "documentname", "displayname", "description", "subject",
"episode", "movie", "name"
};

// Fields that name the COLLECTION a file belongs to rather than the file.
// Album, show and product are all title-like and all wrong: testing this
// against a real MP3, "Al Green Greatest Hits" beat "Let's Stay Together" on
// length alone, and named the song after the record it came from. Longest wins
// only among things that describe THIS file.
private static readonly string[] c_aCollectionWords = {"album", "show", "product"};

// Field names that CONTAIN a title word but are never a title. Without this
// list, a photograph gets named after its lens and a PDF after its software.
private static readonly string[] c_aNotTitles = {
"file name", "filename", "directory", "source file", "base name",
"software", "creator tool", "producer", "encoder", "handler",
"lens", "camera", "make", "model", "profile", "color", "colour",
"font", "charset", "mime", "format", "compressor", "codec",
"user comment", "warning", "error", "exiftool", "device",
"application", "generator", "toolkit", "os ", "platform"
};

public static string bestTitle(string sPath, out string sField, out string sError) {
// The longest title-like value in a file's metadata, within a length that
// makes a sensible file name.
//
// HOW THE FIELD IS CHOSEN. ExifTool reports thousands of tags across hundreds
// of formats, and they disagree about what a title is called: a PDF has Title,
// an MP3 has Title and Album, a photograph has ObjectName, Headline,
// Caption-Abstract and Description, an EPUB has BookName, a video has Title
// and Movie. So the NAME is matched rather than listed, and then the matches
// are filtered, because half the tags containing the word "name" are about the
// camera, the software or the file itself.
//
// THE LONGEST WINS. A photograph may carry "IMG_4021" in one field and "Sunset
// over the Cascades from Rattlesnake Ridge" in another. Length is a crude
// measure of how much somebody bothered to write, and for this it is a good
// one.
//
// BOUNDED AT BOTH ENDS. Under four characters is a code, not a title. Over 120
// is an abstract or a first paragraph, which Windows will not hold and nobody
// wants read aloud.
sField = "";
sError = "";
System.Collections.Generic.List<string[]> lsPairs = readProperties(sPath, out sError);
if (lsPairs.Count == 0) return "";
string sBest = "";
string sOwnRoot = Path.GetFileNameWithoutExtension(sPath);
foreach (string[] aPair in lsPairs) {
// ExifTool prefixes each field with its group, as "EXIF:ObjectName". The
// group is not part of the name being matched.
string sName = aPair[0];
int iColon = sName.LastIndexOf(':');
if (iColon >= 0) sName = sName.Substring(iColon + 1);
string sLowerName = sName.Trim().ToLower();

bool bTitleLike = false;
foreach (string sWord in c_aTitleWords)
if (sLowerName.IndexOf(sWord, StringComparison.Ordinal) >= 0) bTitleLike = true;
if (!bTitleLike) continue;
bool bCollection = false;
foreach (string sWord in c_aCollectionWords)
if (sLowerName.IndexOf(sWord, StringComparison.Ordinal) >= 0) bCollection = true;
if (bCollection) continue;

bool bExcluded = false;
foreach (string sNot in c_aNotTitles)
if (sLowerName.IndexOf(sNot, StringComparison.Ordinal) >= 0) bExcluded = true;
if (bExcluded) continue;

string sValue = aPair[1].Trim();
if (sValue.Length < 4 || sValue.Length > 120) continue;
// A value that merely repeats what the file is already called is no use.
if (Homer.Util.stringEquiv(sValue, sOwnRoot)) continue;
if (Homer.Util.stringEquiv(sValue, Path.GetFileName(sPath))) continue;
// Nor a value with no letters in it: a date, a serial number, a duration.
bool bHasLetter = false;
foreach (char c in sValue) if (Char.IsLetter(c)) bHasLetter = true;
if (!bHasLetter) continue;

if (sValue.Length > sBest.Length) {
sBest = sValue;
sField = sName.Trim();
}
}
if (sBest.Length == 0 && sError.Length == 0)
sError = "no title, caption or description was found in its metadata";
return sBest;
} // bestTitle method

public static int run(string sProgram, string sArguments, out string sOut, out string sErr) {
// A process with NO WINDOW, with both streams read before the wait: a full
// pipe buffer would otherwise deadlock it. The program and its arguments go
// in separately, so no command interpreter quoting rule applies.
sOut = "";
sErr = "";
try {
Process process = new Process();
process.StartInfo.FileName = sProgram;
process.StartInfo.Arguments = sArguments;
process.StartInfo.UseShellExecute = false;
process.StartInfo.RedirectStandardOutput = true;
process.StartInfo.RedirectStandardError = true;
process.StartInfo.CreateNoWindow = true;
process.StartInfo.StandardOutputEncoding = Encoding.UTF8;
process.StartInfo.StandardErrorEncoding = Encoding.UTF8;
process.Start();
sOut = process.StandardOutput.ReadToEnd();
sErr = process.StandardError.ReadToEnd();
process.WaitForExit();
Homer.Log.command(sProgram + " " + sArguments, process.ExitCode);
if (!string.IsNullOrEmpty(sErr)) Homer.Log.info("  said: " + sErr.Trim());
return process.ExitCode;
}
catch (Exception ex) {
sErr = ex.Message;
Homer.Log.info("Could not start " + sProgram + ": " + ex.Message);
return -1;
}
} // run method

} // Media class

} // Homer namespace
