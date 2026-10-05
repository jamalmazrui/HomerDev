// Mpv.cs -- Homer shared class: drive the mpv media player from another program.
//
// WHAT THIS IS FOR
//
// mpv can run as a service rather than as a window: started with --idle it sits
// waiting, and everything it does afterwards arrives down a named pipe as JSON,
// one message per line. That is mpv's own documented control channel, not a
// trick played on it, and it is what every graphical front end for mpv uses.
//
// A program that talks to mpv this way gets a player with no window of its own,
// no keys of its own, and no focus of its own -- which is the whole point for a
// screen reader user. Every key belongs to the dialog that owns this object, and
// the dialog turns it into a command.
//
// WHY A SEPARATE PROGRAM RATHER THAN THE LIBRARY
//
// mpv is GPL, and loading libmpv into your own process carries that licence into
// your program. Running mpv.exe as a separate program does not, and it has a
// second virtue: a media fault kills the player, not the file manager. This is a
// design note rather than legal advice.
//
// USING IT
//
//     Homer.Mpv player = new Homer.Mpv("");        // "" finds mpv itself
//     string sError;
//     if (!player.start(out sError)) { ... }
//     player.loadFile(sAddress, false);            // false replaces, true appends
//     player.togglePause();
//     double dWhere = player.position;             // seconds, or -1 when unknown
//     player.Dispose();                            // stops mpv
//
// Dispose ALWAYS ends the player. A dialog that opens one of these owns it for
// as long as it is open and no longer.
//
// THREADS
//
// One background thread does nothing but read the pipe. That is not optional:
// mpv keeps sending events, and a program that only writes will eventually fill
// the pipe and deadlock both ends. Property values arrive on that thread and are
// read on the interface thread, so every shared field is guarded by one lock.
//
// The caller never waits for mpv. Ask it once to report the properties that
// matter, keep the latest values here, and read them from the fields, so an
// announcement is instant even when the player is busy.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;

namespace Homer {

public class Mpv : IDisposable {

// ---- constants ----------------------------------------------------------

// The property numbers mpv is asked to report. Any number would do; these are
// fixed so the reader can tell one answer from another.
private const int c_iIdDuration = 2;
private const int c_iIdIdle = 6;
private const int c_iIdPause = 3;
private const int c_iIdPlaylistPos = 5;
private const int c_iIdTitle = 4;
private const int c_iIdTimePos = 1;
private const int c_iIdChapters = 7;
private const int c_iIdChapter = 8;

// A volume below full by default, so the media does not drown the screen
// reader. Able Player sets 7 out of 10 for exactly this reason.
public const int c_iDefaultVolume = 70;

// ---- state --------------------------------------------------------------

// TWO LOCKS, AND NO INPUT OR OUTPUT UNDER EITHER OF THEM.
//
// The first version had one lock held over both the shared fields and the write
// to the pipe. That is a deadlock, and it happened: a write blocks when mpv is
// slow to read, the caller keeps the lock while it blocks, the reader thread
// then waits for that same lock instead of draining the pipe, mpv fills the
// pipe and stops reading -- and everything stops. Playback carried on, because
// mpv had already been given the list, while the dialog froze with no way to
// close it. The mpv developers warn about exactly this shape.
//
// So: oStateLock guards the handful of fields and is never held across a call
// that can block, and nothing writes to the pipe from a caller's thread at all.
// Commands go onto a queue and a writer thread sends them.
private readonly object oStateLock = new object();
private readonly Queue<string> qOutgoing = new Queue<string>();
private AutoResetEvent evOutgoing = new AutoResetEvent(false);
private Thread threadWriter;
private bool bDisposed;
private bool bIdleValue = true;
private bool bPausedValue;
private double dDurationValue = -1;
private double dPositionValue = -1;
private int iChapterCountValue = 0;
private int iChapterValue = -1;
private int iPlaylistPosValue = -1;
private NamedPipeClientStream pipe;
private Process oProcess;
private StreamReader reader;
private StreamWriter writer;
private string sLastError = "";
private string sPipeName = "";
private string sProgram = "";
private string sTitleValue = "";
private string sYtDlp = "";
private Thread threadReader;
private volatile bool bStopping;

// Raised when mpv moves to a different item in its play list, and when the
// list runs out. Both arrive on the reader thread, so a handler that touches
// controls must marshal to the interface thread itself.
public delegate void TrackNotice(int iIndex);
public delegate void PlainNotice();
public event TrackNotice trackChanged;
public event PlainNotice playbackEnded;

// ---- construction -------------------------------------------------------

// sProgramPath may be empty, in which case mpv is looked for. sYtDlpPath is
// optional: mpv reaches YouTube and the rest through yt-dlp, which it expects
// on the path, so a program holding its own copy should name it here.
public Mpv(string sProgramPath) {
sProgram = sProgramPath == null ? "" : sProgramPath;
if (sProgram.Length == 0) sProgram = findProgram();
}

public Mpv(string sProgramPath, string sYtDlpPath) : this(sProgramPath) {
sYtDlp = sYtDlpPath == null ? "" : sYtDlpPath;
}

// findProgram: mpv.exe where installers actually put it.
//
// THE FOLDER AN INSTALLER USES IS NOT THE COMMAND'S NAME. The winget package
// installs as "MPV Player" under Program Files, so looking only in a folder
// called "mpv" reports a player that is plainly there as missing.
public static string findProgram() {
string sProgramFiles = Environment.GetEnvironmentVariable("ProgramFiles");
string sProgramFiles86 = Environment.GetEnvironmentVariable("ProgramFiles(x86)");
List<string> lsFolders = new List<string>();
foreach (string sRoot in new string[] { sProgramFiles, sProgramFiles86 }) {
if (string.IsNullOrEmpty(sRoot)) continue;
lsFolders.Add(Path.Combine(sRoot, "MPV Player"));
lsFolders.Add(Path.Combine(sRoot, "MPV Media Player"));
lsFolders.Add(Path.Combine(sRoot, "mpv"));
lsFolders.Add(Path.Combine(Path.Combine(sRoot, "mpv"), "bin"));
lsFolders.Add(Path.Combine(sRoot, "mpv.net"));
lsFolders.Add(Path.Combine(sRoot, "WinGet\\Links"));
}
// MACHINE WIDE ONLY (5 October 2026). A Homer installer puts mpv in its own
// default folder under Program Files, where every program and every user
// finds one copy. The per-user folders a non-elevated winget would use are no
// longer searched: a player found there is not the one the installer put
// there, and the finish page's verb would then be wrong about it.
foreach (string sFolder in lsFolders) {
try {
string sPath = Path.Combine(sFolder, "mpv.exe");
if (File.Exists(sPath)) return sPath;
}
catch (Exception) { }
}
// Last, the path itself.
string sPathVar = Environment.GetEnvironmentVariable("PATH");
if (!string.IsNullOrEmpty(sPathVar)) {
foreach (string sFolder in sPathVar.Split(';')) {
try {
if (sFolder.Trim().Length == 0) continue;
string sPath = Path.Combine(sFolder.Trim(), "mpv.exe");
if (File.Exists(sPath)) return sPath;
}
catch (Exception) { }
}
}
return "";
}

// ---- what mpv can be given ----

// Extensions mpv plays. Not a complete list of what it CAN read -- that depends
// on how it was built -- but a list of what it is asked to read here.
private static readonly string[] c_asPlayable = {
".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".oga", ".opus", ".wma",
".aiff", ".aif", ".ape", ".mka", ".mid", ".midi", ".cda", ".ac3", ".dts",
".mp4", ".m4v", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mpg",
".mpeg", ".m2ts", ".ts", ".vob", ".ogv", ".3gp", ".divx",
".m3u", ".m3u8", ".pls"
};

// Sites yt-dlp can be relied on to turn into something playable. Not a
// complete list of what it supports -- that runs to a thousand -- but the ones
// worth guessing about without asking it.
private static readonly string[] c_asMediaSites = {
"youtube.com", "youtu.be", "vimeo.com", "soundcloud.com", "mixcloud.com",
"bandcamp.com", "archive.org", "dailymotion.com", "twitch.tv", "podbean.com",
"libsyn.com", "buzzsprout.com", "megaphone.fm", "simplecast.com", "anchor.fm",
"pinecast.com", "podtrac.com", "spreaker.com", "acast.com", "captivate.fm",
"transistor.fm", "fireside.fm", "redcircle.com", "art19.com", "omny.fm",
"blubrry.com", "audioboom.com", "whooshkaa.com", "chrt.fm", "pdst.fm"
};

// canPlay: whether to hand this to mpv at all.
//
// ASKING FIRST IS AN ACCESSIBILITY MATTER, not tidiness. mpv given something it
// cannot read puts an error on its own on-screen display, which is drawn rather
// than spoken: a screen reader user gets silence and a window that will not go
// away. Better to leave the thing out of the queue and say how many were left
// out.
//
// A WEB ADDRESS HAS TO LOOK LIKE MEDIA, which it did not have to before. Every
// http address was let through on the reasoning that yt-dlp knows more than an
// extension does. That is true of a page of podcast links and false of an email
// newsletter: one saved newsletter turned into a queue of a hundred and
// fifty-four tracking links, none of which was media, and the person was told
// none of that. So an address passes when its path names a media file, or its
// host is one of the sites above; anything else is left out and counted.
public static bool canPlay(string sTarget) {
if (string.IsNullOrEmpty(sTarget)) return false;
string sLower = sTarget.Trim().ToLowerInvariant();
if (sLower.StartsWith("http://") || sLower.StartsWith("https://")) {
// The extension may sit anywhere in the path, since a podcast address is
// often a chain of redirects ending in the real file name.
foreach (string sExt in c_asPlayable) {
if (sLower.Contains(sExt + "?") || sLower.EndsWith(sExt) || sLower.Contains(sExt + "&")) return true;
}
foreach (string sSite in c_asMediaSites) {
if (sLower.Contains("//" + sSite) || sLower.Contains("." + sSite)) return true;
}
return false;
}
try {
string sExtension = Path.GetExtension(sLower);
if (string.IsNullOrEmpty(sExtension)) return false;
return Array.IndexOf(c_asPlayable, sExtension) >= 0;
}
catch (Exception) { return false; }
}

// ---- starting and stopping ----------------------------------------------

public string program { get { return sProgram; } }
public string lastError { get { lock (oStateLock) { return sLastError; } } }
public bool running { get { return oProcess != null && !oProcess.HasExited; } }

// start: launch mpv as a service and connect to its pipe.
//
// --idle=yes           stay alive with nothing loaded, waiting for commands
// --no-terminal        no console, and no keys of its own to press
// --force-window=no    no window either: this is the audio case
// --input-ipc-server   the pipe everything else in this class talks to
public bool start(out string sError) {
sError = "";
if (sProgram.Length == 0) {
sError = "mpv was not found on this computer.";
return false;
}
try {
sPipeName = "homerMpv-" + Process.GetCurrentProcess().Id.ToString(CultureInfo.InvariantCulture)
+ "-" + Guid.NewGuid().ToString("N").Substring(0, 8);
StringBuilder sbArgs = new StringBuilder();
sbArgs.Append("--idle=yes --no-terminal --force-window=no --video=no ");
sbArgs.Append("--volume=" + c_iDefaultVolume.ToString(CultureInfo.InvariantCulture) + " ");
if (sYtDlp.Length > 0) {
sbArgs.Append("--script-opts=ytdl_hook-ytdl_path=\"");
sbArgs.Append(sYtDlp);
sbArgs.Append("\" ");
}
sbArgs.Append("--input-ipc-server=\\\\.\\pipe\\" + sPipeName);

ProcessStartInfo info = new ProcessStartInfo();
info.FileName = sProgram;
info.Arguments = sbArgs.ToString();
info.UseShellExecute = false;
info.CreateNoWindow = true;
info.WorkingDirectory = Path.GetDirectoryName(sProgram);
oProcess = Process.Start(info);

// mpv creates the pipe a moment after it starts, so the first attempts to
// connect are expected to fail. Five seconds is long enough for a cold
// start on a slow disk and short enough that a person notices nothing.
pipe = new NamedPipeClientStream(".", sPipeName, PipeDirection.InOut, PipeOptions.Asynchronous);
DateTime dtGiveUp = DateTime.Now.AddSeconds(5);
while (true) {
try { pipe.Connect(200); break; }
catch (Exception) {
if (DateTime.Now > dtGiveUp) {
sError = "mpv started but did not answer on its control pipe.";
stopProcess();
return false;
}
if (oProcess.HasExited) {
sError = "mpv stopped as soon as it started. Exit code " + oProcess.ExitCode.ToString(CultureInfo.InvariantCulture) + ".";
return false;
}
Thread.Sleep(100);
}
}
writer = new StreamWriter(pipe, new UTF8Encoding(false));
writer.AutoFlush = true;
reader = new StreamReader(pipe, new UTF8Encoding(false));

bStopping = false;
threadReader = new Thread(new ThreadStart(readLoop));
threadReader.IsBackground = true;
threadReader.Name = "homerMpvReader";
threadReader.Start();

threadWriter = new Thread(new ThreadStart(writeLoop));
threadWriter.IsBackground = true;
threadWriter.Name = "homerMpvWriter";
threadWriter.Start();

// Ask once for the handful of properties worth knowing, so nothing later
// has to wait for an answer.
sendRaw("{\"command\": [\"observe_property\", " + c_iIdTimePos + ", \"time-pos\"]}");
sendRaw("{\"command\": [\"observe_property\", " + c_iIdDuration + ", \"duration\"]}");
sendRaw("{\"command\": [\"observe_property\", " + c_iIdPause + ", \"pause\"]}");
sendRaw("{\"command\": [\"observe_property\", " + c_iIdTitle + ", \"media-title\"]}");
sendRaw("{\"command\": [\"observe_property\", " + c_iIdPlaylistPos + ", \"playlist-pos\"]}");
sendRaw("{\"command\": [\"observe_property\", " + c_iIdIdle + ", \"idle-active\"]}");
sendRaw("{\"command\": [\"observe_property\", " + c_iIdChapters + ", \"chapters\"]}");
sendRaw("{\"command\": [\"observe_property\", " + c_iIdChapter + ", \"chapter\"]}");
return true;
}
catch (Exception ex) {
sError = ex.Message;
lock (oStateLock) { sLastError = ex.Message; }
stopProcess();
return false;
}
}

private void stopProcess() {
try { if (oProcess != null && !oProcess.HasExited) oProcess.Kill(); }
catch (Exception) { }
}

public void Dispose() {
if (bDisposed) return;
bDisposed = true;
// The quit is queued while the writer thread is still running, and only then
// is everything stopped: a quit that never left the queue would leave mpv
// playing with no window and no way to reach it.
try {
lock (qOutgoing) { qOutgoing.Enqueue("{\"command\": [\"quit\"]}"); }
evOutgoing.Set();
}
catch (Exception) { }
try { Thread.Sleep(150); }
catch (Exception) { }
bStopping = true;
try { evOutgoing.Set(); }
catch (Exception) { }
try { if (threadWriter != null) threadWriter.Join(300); }
catch (Exception) { }
try { if (threadReader != null) threadReader.Join(300); }
catch (Exception) { }
try { if (writer != null) writer.Dispose(); }
catch (Exception) { }
try { if (pipe != null) pipe.Dispose(); }
catch (Exception) { }
// mpv is asked to quit first and made to quit second: a player that ignored
// the request must not be left running with no window and no way to reach it.
try {
if (oProcess != null && !oProcess.WaitForExit(700)) oProcess.Kill();
}
catch (Exception) { }
}

// ---- commands -----------------------------------------------------------

// command: the general form. Strings are quoted, numbers and true/false are
// written as they are, which is what mpv's protocol expects.
public bool command(params object[] aArgs) {
StringBuilder sb = new StringBuilder();
sb.Append("{\"command\": [");
for (int i = 0; i < aArgs.Length; i++) {
if (i > 0) sb.Append(", ");
sb.Append(jsonValue(aArgs[i]));
}
sb.Append("]}");
return sendRaw(sb.ToString());
}

// loadFile: play something. bAppend adds it to the end of the list instead of
// replacing what is there, which is how a whole play list is handed over.
public bool loadFile(string sTarget, bool bAppend) {
return command("loadfile", sTarget, bAppend ? "append-play" : "replace");
}

public bool playIndex(int iIndex) { return command("set_property", "playlist-pos", iIndex); }
public bool next() { return command("playlist-next", "force"); }
public bool previous() { return command("playlist-prev", "force"); }
public bool togglePause() { return command("cycle", "pause"); }
public bool setPause(bool bValue) { return command("set_property", "pause", bValue); }
// stop: STOP PLAYING AND STAY WHERE YOU ARE.
//
// Pausing, in other words, and nothing else -- not mpv's own "stop", which
// stops playback AND CLEARS THE PLAY LIST. A dialog that offers Stop and then
// cannot play anything again is the result, and that is what happened: the
// first Execute worked, Stop emptied the queue, and everything afterwards did
// nothing while sixty tracks still sat on screen.
//
// It does not rewind either. Losing your place is not what a listener asks for
// when they stop something; carrying on from where they stopped is.
public bool stop() { return setPause(true); }

// clearAndStop: mpv's own stop, play list and all. Not what the Stop button
// does; here for a caller that really does want the queue emptied.
public bool clearAndStop() { return command("stop"); }
// RECORDING IS ONE PROPERTY. mpv writes the stream it is receiving to a file
// while stream-record names one, and stops when it is set to nothing. A copy
// of the stream as it came, no re-encoding, no choices.
public bool startRecording(string sPath) { return command("set_property", "stream-record", sPath); }
public bool stopRecording() { return command("set_property", "stream-record", ""); }
public bool seekRelative(double dSeconds) { return command("seek", dSeconds, "relative"); }
public bool seekAbsolute(double dSeconds) { return command("seek", dSeconds, "absolute"); }
public bool setVolume(int iVolume) { return command("set_property", "volume", iVolume); }
public bool setSpeed(double dSpeed) { return command("set_property", "speed", dSpeed); }
public bool clearPlaylist() { return command("playlist-clear"); }

// setLoopPlaylist: play the list again when it ends. mpv wants the word "inf"
// rather than a number, and "no" to stop doing it.
public bool setLoopPlaylist(bool bValue) { return command("set_property", "loop-playlist", bValue ? "inf" : "no"); }

// The rest of what mpv's own player window offers, named after the commands
// its manual gives them.
public bool setMute(bool bValue) { return command("set_property", "mute", bValue); }
public bool nextChapter() { return command("add", "chapter", 1); }
public bool setChapter(int iChapter) { return command("set_property", "chapter", iChapter); }
public bool previousChapter() { return command("add", "chapter", -1); }

// revertSeek: mpv's own undo. A second call returns to where the undo came
// from, so it is a toggle rather than a stack, and it works only inside the
// track being played.
public bool revertSeek() { return command("revert-seek"); }

// quitRemembering: mpv's quit-watch-later, which writes down where playback had
// reached before it exits, so the same file can start there next time. This is
// what uppercase Q does in mpv's own window.
public bool quitRemembering() { return command("quit-watch-later"); }

// ---- what mpv last said -------------------------------------------------

public bool paused { get { lock (oStateLock) { return bPausedValue; } } }
public bool idle { get { lock (oStateLock) { return bIdleValue; } } }
public double duration { get { lock (oStateLock) { return dDurationValue; } } }
public double position { get { lock (oStateLock) { return dPositionValue; } } }
public int playlistIndex { get { lock (oStateLock) { return iPlaylistPosValue; } } }

// How many chapters this track has, as mpv last reported. Zero means none, and
// that is the ordinary case: most audio has no chapter marks at all.
public int chapterCount { get { lock (oStateLock) { return iChapterCountValue; } } }

// Which chapter is playing, counting from zero, or -1 when the track has none.
public int chapter { get { lock (oStateLock) { return iChapterValue; } } }
public string title { get { lock (oStateLock) { return sTitleValue; } } }

// formatTime: seconds as a person would say them. Negative or unknown gives
// an empty string rather than a misleading zero.
public static string formatTime(double dSeconds) {
if (dSeconds < 0 || double.IsNaN(dSeconds) || double.IsInfinity(dSeconds)) return "";
int iWhole = (int) Math.Floor(dSeconds);
int iHours = iWhole / 3600;
int iMinutes = (iWhole % 3600) / 60;
int iSecs = iWhole % 60;
if (iHours > 0) return iHours.ToString(CultureInfo.InvariantCulture) + ":" + iMinutes.ToString("00") + ":" + iSecs.ToString("00");
return iMinutes.ToString(CultureInfo.InvariantCulture) + ":" + iSecs.ToString("00");
}

// saySpan: a length of time in the words a person would use.
//
// "12:03" IS FOR THE EYE. Read aloud it becomes "twelve colon zero three", or
// "twelve oh three", and a listener has to work out which of the two numbers is
// which. "12 min 3 sec" says it. The units are one syllable each on purpose:
// this is spoken every time somebody jumps, so a syllable saved is saved often.
public static string saySpan(double dSeconds) {
if (dSeconds < 0 || double.IsNaN(dSeconds) || double.IsInfinity(dSeconds)) return "";
int iWhole = (int) Math.Round(dSeconds);
int iHours = iWhole / 3600;
int iMinutes = (iWhole % 3600) / 60;
int iSecs = iWhole % 60;
StringBuilder sb = new StringBuilder();
if (iHours > 0) { sb.Append(iHours.ToString(CultureInfo.InvariantCulture)); sb.Append(" hr"); }
if (iMinutes > 0) {
if (sb.Length > 0) sb.Append(" ");
sb.Append(iMinutes.ToString(CultureInfo.InvariantCulture));
sb.Append(" min");
}
// Seconds are dropped once an hour is involved: at that length nobody is
// counting them, and three numbers is a mouthful.
if (iSecs > 0 && iHours == 0) {
if (sb.Length > 0) sb.Append(" ");
sb.Append(iSecs.ToString(CultureInfo.InvariantCulture));
sb.Append(" sec");
}
if (sb.Length == 0) return "0 sec";
return sb.ToString();
}

// parseTime: "90", "1:30" and "1:05:00" all mean something to a person typing
// in a hurry. Returns -1 when the text is not a time at all.
public static double parseTime(string sText) {
if (sText == null) return -1;
sText = sText.Trim();
if (sText.Length == 0) return -1;
string[] aParts = sText.Split(':');
if (aParts.Length > 3) return -1;
double dTotal = 0;
foreach (string sPart in aParts) {
double dPart;
if (!double.TryParse(sPart.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out dPart)) return -1;
if (dPart < 0) return -1;
dTotal = dTotal * 60 + dPart;
}
return dTotal;
}

// ---- the pipe -----------------------------------------------------------

// sendRaw: hand a line to the writer thread and return at once.
//
// The caller is usually the interface thread, and the interface thread must
// never wait on a pipe. Whether the command reaches mpv is not something the
// caller can be told here, which is honest: the answer would be a lie either
// way, since mpv acknowledges asynchronously.
private bool sendRaw(string sJson) {
if (bStopping || writer == null) return false;
lock (qOutgoing) { qOutgoing.Enqueue(sJson); }
try { evOutgoing.Set(); }
catch (Exception) { return false; }
return true;
}

// writeLoop: the only thread that writes to the pipe.
private void writeLoop() {
try {
while (!bStopping) {
evOutgoing.WaitOne(200);
while (true) {
string sLine = null;
lock (qOutgoing) { if (qOutgoing.Count > 0) sLine = qOutgoing.Dequeue(); }
if (sLine == null) break;
try {
writer.Write(sLine);
writer.Write("\n");
}
catch (Exception ex) {
lock (oStateLock) { sLastError = ex.Message; }
return;
}
}
}
}
catch (Exception ex) {
lock (oStateLock) { sLastError = ex.Message; }
}
}

// readLoop: drain the pipe forever. Nothing else reads it, and a pipe nobody
// reads eventually blocks the end that writes.
private void readLoop() {
try {
while (!bStopping) {
string sLine = reader.ReadLine();
if (sLine == null) break;
if (sLine.Length == 0) continue;
handleLine(sLine);
}
}
catch (Exception ex) {
lock (oStateLock) { sLastError = ex.Message; }
}
}

private void handleLine(string sLine) {
string sEvent = jsonStringValue(sLine, "event");
if (sEvent.Length == 0) return;

if (sEvent == "property-change") {
string sName = jsonStringValue(sLine, "name");
// Parsed first, assigned second: the parsing is the slow half, and nothing
// slow belongs inside a lock the interface thread is waiting on.
if (sName == "time-pos") { double dNew = jsonNumberValue(sLine, "data"); lock (oStateLock) { dPositionValue = dNew; } }
else if (sName == "duration") { double dNew = jsonNumberValue(sLine, "data"); lock (oStateLock) { dDurationValue = dNew; } }
else if (sName == "pause") { bool bNew = jsonBoolValue(sLine, "data"); lock (oStateLock) { bPausedValue = bNew; } }
else if (sName == "idle-active") {
bool bIdleNow = jsonBoolValue(sLine, "data");
bool bWasPlaying;
lock (oStateLock) { bWasPlaying = !bIdleValue; bIdleValue = bIdleNow; }
if (bIdleNow && bWasPlaying && playbackEnded != null) playbackEnded();
}
else if (sName == "chapters") { int iNew = (int) jsonNumberValue(sLine, "data"); lock (oStateLock) { iChapterCountValue = (iNew > 0) ? iNew : 0; } }
else if (sName == "chapter") { int iNew = (int) jsonNumberValue(sLine, "data"); lock (oStateLock) { iChapterValue = iNew; } }
else if (sName == "media-title") { string sNew = jsonStringValue(sLine, "data"); lock (oStateLock) { sTitleValue = sNew; } }
else if (sName == "playlist-pos") {
int iNew = (int) jsonNumberValue(sLine, "data");
bool bChanged = false;
lock (oStateLock) {
if (iNew != iPlaylistPosValue) { iPlaylistPosValue = iNew; bChanged = true; }
}
if (bChanged && iNew >= 0 && trackChanged != null) trackChanged(iNew);
}
return;
}

// The end of the list is idle-active turning true, not end-file: end-file
// arrives for every item, including the ones another item follows.
}

// ---- a very small amount of JSON ---------------------------------------
//
// mpv's messages are one line each and shallow: a name, a value, sometimes an
// error. Reading them by hand keeps this class free of any dependency, which
// is the point of a Homer shared class. Nothing here pretends to be a general
// JSON parser, and it does not need to be.

private static string jsonValue(object oValue) {
if (oValue == null) return "null";
if (oValue is bool) return ((bool) oValue) ? "true" : "false";
if (oValue is int) return ((int) oValue).ToString(CultureInfo.InvariantCulture);
if (oValue is double) return ((double) oValue).ToString("0.###", CultureInfo.InvariantCulture);
return "\"" + jsonEscape(oValue.ToString()) + "\"";
}

private static string jsonEscape(string sText) {
StringBuilder sb = new StringBuilder();
foreach (char ch in sText) {
if (ch == '"') sb.Append("\\\"");
else if (ch == '\\') sb.Append("\\\\");
else if (ch == '\n') sb.Append("\\n");
else if (ch == '\r') sb.Append("\\r");
else if (ch == '\t') sb.Append("\\t");
else if (ch < ' ') sb.Append("\\u" + ((int) ch).ToString("x4"));
else sb.Append(ch);
}
return sb.ToString();
}

private static int valueStart(string sLine, string sKey) {
int iKey = sLine.IndexOf("\"" + sKey + "\"", StringComparison.Ordinal);
if (iKey < 0) return -1;
int iColon = sLine.IndexOf(':', iKey);
if (iColon < 0) return -1;
int i = iColon + 1;
while (i < sLine.Length && sLine[i] == ' ') i++;
return i;
}

private static string jsonStringValue(string sLine, string sKey) {
int i = valueStart(sLine, sKey);
if (i < 0 || i >= sLine.Length || sLine[i] != '"') return "";
StringBuilder sb = new StringBuilder();
i++;
while (i < sLine.Length) {
char ch = sLine[i];
if (ch == '\\' && i + 1 < sLine.Length) {
char chNext = sLine[i + 1];
if (chNext == 'n') sb.Append('\n');
else if (chNext == 'r') sb.Append('\r');
else if (chNext == 't') sb.Append('\t');
else if (chNext == 'u' && i + 5 < sLine.Length) {
int iCode;
if (int.TryParse(sLine.Substring(i + 2, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out iCode)) {
sb.Append((char) iCode);
i += 4;
}
}
else sb.Append(chNext);
i += 2;
continue;
}
if (ch == '"') break;
sb.Append(ch);
i++;
}
return sb.ToString();
}

private static double jsonNumberValue(string sLine, string sKey) {
int i = valueStart(sLine, sKey);
if (i < 0) return -1;
int iEnd = i;
while (iEnd < sLine.Length && (char.IsDigit(sLine[iEnd]) || sLine[iEnd] == '.' || sLine[iEnd] == '-' || sLine[iEnd] == '+' || sLine[iEnd] == 'e' || sLine[iEnd] == 'E')) iEnd++;
if (iEnd == i) return -1;
double dValue;
if (!double.TryParse(sLine.Substring(i, iEnd - i), NumberStyles.Float, CultureInfo.InvariantCulture, out dValue)) return -1;
return dValue;
}

private static bool jsonBoolValue(string sLine, string sKey) {
int i = valueStart(sLine, sKey);
if (i < 0) return false;
return string.CompareOrdinal(sLine, i, "true", 0, 4) == 0;
}

} // Mpv class

} // Homer namespace
