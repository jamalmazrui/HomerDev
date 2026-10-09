// MediaPlayer.cs -- the Homer Player dialog, shared by every Homer app.
//
// MOVED INTO THE KIT on 5 October 2026 from FileDir, where it was written, so
// that DbDo could play a radio station from a record. Four lines changed:
// the namespace, the data folder (Homer.Paths.data()), and the one voice
// (Say.sayForced, which a program's own silence switch does not stop, for
// the reason the SPEECH section gives). Everything else is as FileDir had it.
//
// WHAT IT IS
//
// A dialog that plays a queue of tracks. mpv does the playing, with no window,
// no keys and no focus of its own; every control here is an ordinary Windows
// control and each one becomes a command down mpv's pipe. Mpv.cs is that
// plumbing.
//
// THE LAYOUT
//
//   Tracks     the queue: name, presenter and length
//   Order      how the queue is sorted, then Next and Previous
//   Forward    Backward, and the Increment slider those two move by
//   Rate       and Volume
//   Go         Stop, Help, Close
//
// Five rows, each holding the controls that belong together, so Tab goes from
// a thing to the things that act on it rather than past the whole dialog.
//
// NAMES
//
// Not one control here has its AccessibleName set. A button carries its caption
// and a list carries the label above it, and setting the property to the same
// words makes some screen readers say them twice. Colons follow the labels that
// are separate controls -- Tracks, Order, Increment, Rate, Volume -- and never
// the buttons, which carry their own captions.
//
// SPEECH
//
// The reader announces the dialog, the control with focus, the list line under
// the cursor and a slider's value as it moves, so none of that is spoken here.
// What is spoken is what the reader cannot know: the track when playback moves
// on by itself, the position after a jump, the end of the queue.
//
// Speech goes out as global, which bypasses FileDir's Scroll Lock silence.
// That is deliberate: Scroll Lock is this dialog's play and pause key, so half
// the time it is on, and a player that fell silent on every other press of its
// own pause key would be unusable.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace Homer {

// One thing to play: what to hand mpv, and what to call it on screen.
public class MediaTrack {
// EVERYTHING KNOWN ABOUT THIS TRACK, one field to a value.
//
// Filled from whatever source had something to say: the play list line, the
// document the link came from -- these podcast directories carry a date, a
// duration, a summary and often the people involved -- and, for a file on this
// computer, ExifTool. Extra Info shows it, sorted, and Find searches it.
public Dictionary<string, string> dFacts = new Dictionary<string, string>();
public double dSeconds = -1;
// Whether ExifTool has been asked about this track. NOT a fact about the
// track, so not in the table: "Read by ExifTool: yes" was a line spent telling
// the person about the program's own housekeeping.
public bool bExifAsked = false;
public string sEpisode = "";
public string sName;
public string sPresenter = "";
public string sTarget;

public MediaTrack(string sTrackName, string sTrackTarget) {
sName = sTrackName == null ? "" : sTrackName.Trim();
sTarget = sTrackTarget == null ? "" : sTrackTarget.Trim();
if (sName.Length == 0) sName = shortName(sTarget);
sEpisode = episodeFrom(sName);
}

// episodeFrom: the episode number the podcaster put in the title, if they put
// one there.
//
// The number dropped from the list was FileDir's own counting -- first, second,
// third in the queue -- and nobody needs that on every line. An episode number
// is different: it is what the show calls that episode, and people remember
// shows by it. So it stays in the title where the show wrote it, and it is
// pulled out as a field of its own for Extra Info.
//
// Three shapes cover what podcasts actually write: "Episode 214", "#214", and a
// number after a bar at the end, which is how several of these directories end
// a title.
public static string episodeFrom(string sTitle) {
if (string.IsNullOrEmpty(sTitle)) return "";
Match oMatch = Regex.Match(sTitle, @"\bEpisode\s+(\d{1,5})\b", RegexOptions.IgnoreCase);
if (oMatch.Success) return oMatch.Groups[1].Value;
oMatch = Regex.Match(sTitle, @"#\s*(\d{1,5})\b");
if (oMatch.Success) return oMatch.Groups[1].Value;
oMatch = Regex.Match(sTitle, @"\|\s*(\d{1,5})\s*$");
if (oMatch.Success) return oMatch.Groups[1].Value;
return "";
}

// shortName: something to call a track that arrived with no name. The last
// part of an address, tidied, beats the whole address in a list.
public static string shortName(string sTarget) {
if (sTarget == null || sTarget.Length == 0) return "Untitled";
string sText = sTarget;
int iQuery = sText.IndexOf('?');
if (iQuery > 0) sText = sText.Substring(0, iQuery);
sText = sText.TrimEnd('/');
int iSlash = sText.LastIndexOfAny(new char[] { '/', '\\' });
if (iSlash >= 0 && iSlash < sText.Length - 1) sText = sText.Substring(iSlash + 1);
try { sText = Uri.UnescapeDataString(sText); }
catch (Exception) { }
if (sText.Length == 0) return sTarget;
return sText;
}

// sortTitle: the title as it should be compared -- case ignored, and a
// leading A, An or The set aside, which is how a shelf is ordered.
public string sortTitle() {
string sText = sName.Trim().ToLower();
foreach (string sWord in new string[] { "a ", "an ", "the " }) {
if (sText.StartsWith(sWord)) return sText.Substring(sWord.Length).Trim();
}
return sText;
}

// sortPresenter: by surname, case ignored, as a list of authors is ordered.
// The last word of a name is the surname often enough to be useful and is
// never worse than sorting by first name.
public string sortPresenter() {
string sText = sPresenter.Trim();
if (sText.Length == 0) return "zzzz";
int iSpace = sText.LastIndexOf(' ');
if (iSpace > 0) return sText.Substring(iSpace + 1).ToLower() + " " + sText.Substring(0, iSpace).ToLower();
return sText.ToLower();
}

// addFact: keep a field, unless something better is already there.
//
// A FIELD EARNS ITS LINE. Everything here is read one line at a time, aloud, so
// a line that says nothing costs as much to hear as a line that says something.
// Empty values, and the words programs use to mean empty, are not kept; nor are
// the fields that describe the file as a file rather than the recording as a
// recording, which is most of what ExifTool has to say about an audio file.
private static readonly string[] c_asEmptyWords = { "unknown", "n/a", "none", "null", "0" };
private static readonly string[] c_asDullFields = {
"ExifTool Version Number", "ExifToolVersion", "File Name", "FileName", "Directory",
"File Permissions", "FilePermissions", "File Access Date/Time", "FileAccessDate",
"File Inode Change Date/Time", "File Modification Date/Time", "FileModifyDate",
"File Type Extension", "MIME Type", "MIMEType", "SourceFile", "Warning",
"File Size", "FileSize"
};

public void addFact(string sField, string sValue) {
if (string.IsNullOrEmpty(sField) || string.IsNullOrEmpty(sValue)) return;
string sTidy = sValue.Trim();
if (sTidy.Length == 0) return;
foreach (string sEmpty in c_asEmptyWords)
if (string.Equals(sTidy, sEmpty, StringComparison.OrdinalIgnoreCase)) return;
foreach (string sDull in c_asDullFields)
if (string.Equals(sField, sDull, StringComparison.OrdinalIgnoreCase)) return;
if (!dFacts.ContainsKey(sField)) dFacts[sField] = sTidy;
}

// factLines: every field and value, sorted by field, as lines.
//
// Sorted because a list of twenty fields is looked through rather than read,
// and the same field is then in the same place whatever track it belongs to.
public List<string> factLines() {
Dictionary<string, string> dAll = new Dictionary<string, string>(dFacts);
if (sName.Length > 0 && !dAll.ContainsKey("Title")) dAll["Title"] = sName;
if (sPresenter.Length > 0 && !dAll.ContainsKey("Presenter")) dAll["Presenter"] = sPresenter;
if (sEpisode.Length > 0 && !dAll.ContainsKey("Episode")) dAll["Episode"] = sEpisode;
if (!dAll.ContainsKey("Address")) dAll["Address"] = sTarget;
if (dSeconds > 0 && !dAll.ContainsKey("Length")) dAll["Length"] = Homer.Mpv.formatTime(dSeconds);
// Duration and Length are the same fact in two notations, and the document's
// Duration is where Length came from. One line, not two.
if (dAll.ContainsKey("Length")) dAll.Remove("Duration");
List<string> lsKeys = new List<string>(dAll.Keys);
lsKeys.Sort(StringComparer.OrdinalIgnoreCase);
List<string> lsLines = new List<string>();
foreach (string sKey in lsKeys) lsLines.Add(sKey + ": " + dAll[sKey]);
return lsLines;
}

// searchable: the same thing as one line, for Find to look through.
public string searchable() {
StringBuilder sb = new StringBuilder();
foreach (string sLine in factLines()) { sb.Append(sLine); sb.Append("  "); }
return sb.ToString();
}

// display: one line of the Tracks list. Whatever is known, in the order a
// person would say it, with nothing invented for what is not known.
//
// THE NAME COMES FIRST, WITH NO NUMBER IN FRONT OF IT. A number at the head of
// every line stops a list dead for first-letter navigation: pressing T should
// reach the first track beginning with T, and it cannot when every line begins
// with a digit. Where a track sits in the queue is a question a screen reader
// answers on its own, and Alt+Shift+W answers it in words.
public string display() {
StringBuilder sb = new StringBuilder();
sb.Append(sName);
if (sPresenter.Length > 0) { sb.Append(", "); sb.Append(sPresenter); }
string sLength = Homer.Mpv.formatTime(dSeconds);
if (sLength.Length > 0) { sb.Append(", "); sb.Append(sLength); }
return sb.ToString();
}
} // MediaTrack class

public static class MediaPlayer {

// TWO SMALL DIALOGS FileDir kept in its own Lbc class -- a message box and a
// Save As -- are here as private helpers, so this file depends on nothing
// outside the kit. (The build failed in DbDo with "Lbc does not exist" the
// first time it was compiled away from FileDir, 5 October 2026.)
private static void showBox(string sText, string sTitle) {
MessageBox.Show(sText, sTitle);
}

private static string askSavePath(string sTitle, string sDefaultFile, string sFilter) {
SaveFileDialog dlg = new SaveFileDialog();
dlg.Title = sTitle;
dlg.AddExtension = true;
dlg.CheckFileExists = false;
dlg.CheckPathExists = true;
dlg.OverwritePrompt = true;
dlg.FileName = sDefaultFile;
dlg.Filter = (sFilter.Length == 0) ? "All files (*.*)|*.*" : sFilter;
dlg.FilterIndex = 1;
dlg.RestoreDirectory = true;
dlg.ValidateNames = true;
return (dlg.ShowDialog() == DialogResult.OK) ? dlg.FileName : "";
}

// SETTINGS BELONG TO A PLAY LIST, NOT TO THE PROGRAM.
//
// Volume, speed, the jump size and the order suit the thing being played: a
// lecture wants a different speed from music, and a podcast page wants its own
// order. So each queue keeps its own settings, in a section named after where
// the queue came from, in the player's own .inix file. A queue nobody has
// played before gets the built-in defaults, which is what Defaults restores by
// deleting the section.
private static string settingsPath() {
string sPath = Path.Combine(Paths.data(), "HomerPlayer.inix");
// SETTINGS KEPT WHEN A COPY BECOMES THE KIT'S (1.65.3): FileDir's own copy of
// this player kept its settings one folder up, beside data rather than in it.
// When the kit's player first runs there, it moves that file into data, once,
// and says so in the log, so nothing the user chose is lost.
string sOld = Path.Combine(Path.GetDirectoryName(Paths.data()), "HomerPlayer.inix");
if (!File.Exists(sPath) && File.Exists(sOld)) {
try {
File.Move(sOld, sPath);
Homer.Log.info("Player settings moved from " + sOld + " to " + sPath);
}
catch (Exception oError) {
Homer.Log.info("Player settings could not be moved from " + sOld + ": " + oError.Message);
}
}
return sPath;
}

// sectionFor: a name for this queue's settings. Where it came from, which is
// stable across sessions: the same document or play list played again finds
// its own settings, and a different one does not.
private static string sectionFor(string sSource, List<MediaTrack> lsTracks) {
string sName = (sSource == null) ? "" : sSource.Trim();
if (sName.Length == 0 && lsTracks.Count > 0) sName = lsTracks[0].sTarget;
if (sName.Length == 0) return "Queue";
StringBuilder sb = new StringBuilder();
foreach (char ch in sName) {
if (char.IsLetterOrDigit(ch) || ch == '.' || ch == '-' || ch == '_' || ch == ' ') sb.Append(ch);
else sb.Append('_');
}
string sClean = sb.ToString().Trim();
if (sClean.Length > 80) sClean = sClean.Substring(0, 80);
return (sClean.Length > 0) ? sClean : "Queue";
}

// How the Tracks list can be ordered. The first is the order the queue
// arrived in, which is what a play list is FOR: somebody chose that order.
private static readonly string[] c_asOrders = new string[] {
"Play list order", "Title", "Presenter", "Length, shortest first", "Length, longest first" };

// How far Forward and Backward move. In increasing order, because that is the
// order the sizes have -- alphabetical would put 15 minutes before 15 seconds.
// A list rather than a slider: a slider announces its position, so a person
// hears "4" where they need to hear "3 minutes".
private static readonly int[] c_aiSteps = new int[] { 15, 30, 60, 180, 300, 600, 900, 1800, 3600 };
private static readonly string[] c_asSteps = new string[] {
"15 seconds", "30 seconds", "1 minute", "3 minutes", "5 minutes",
"10 minutes", "15 minutes", "30 minutes", "1 hour" };
private const int c_iDefaultStep = 2;   // 1 minute
private const int c_iDefaultRate = 100;
private const int c_iDefaultOrder = 0;

// playTutorials: THE WALKS PLAY IN THE HOMER PLAYER (1.64.5). An app's Play
// Tutorials handed its playlist to Windows, so the walks opened in whatever
// player owned .m3u files, not here, where they open paused with the cursor on
// the first walk: Enter plays it, Down Arrow hears the next. The walks are the
// .mp3 files in sHelpFolder's tutorials folder, in the order of their one-digit
// prefix, each named as its walk is ("0 - Overview"). Without mpv, the playlist
// goes to Windows after all, which is better than nothing. Returns false when
// no walk is installed, so the app can say where they should be.
public static bool playTutorials(IWin32Window owner, string sAppName, string sHelpFolder) {
string sFolder = Path.Combine(sHelpFolder ?? "", "tutorials");
if (!Directory.Exists(sFolder)) return false;
string[] aFiles = Directory.GetFiles(sFolder, "*.mp3");
if (aFiles.Length == 0) return false;
Array.Sort(aFiles, StringComparer.OrdinalIgnoreCase);
List<MediaTrack> lsTracks = new List<MediaTrack>();
foreach (string sFile in aFiles) {
string sStem = Path.GetFileNameWithoutExtension(sFile);
Match oWalk = Regex.Match(sStem, @"^(\d)_(.+)$");
string sName = oWalk.Success ? oWalk.Groups[1].Value + " - " + oWalk.Groups[2].Value.Replace("_", " ") : sStem.Replace("_", " ");
lsTracks.Add(new MediaTrack(sName, sFile));
}
Homer.Log.info("Play Tutorials: " + lsTracks.Count + " walks from " + sFolder);
if (Homer.Media.mpvProgram().Length == 0) {
string[] aLists = Directory.GetFiles(sFolder, "*.m3u");
string sOpen = aLists.Length > 0 ? aLists[0] : aFiles[0];
Homer.Log.info("Play Tutorials: mpv is not installed, so Windows opens " + sOpen);
System.Diagnostics.ProcessStartInfo oStart = new System.Diagnostics.ProcessStartInfo(sOpen);
oStart.UseShellExecute = true;
System.Diagnostics.Process.Start(oStart);
return true;
}
run(owner, sAppName + " Tutorials", "tutorials", lsTracks);
return true;
}

// run: open the player on a queue of tracks. Returns when the dialog closes,
// by which time mpv has stopped and has written down where it had reached.
public static void run(IWin32Window owner, string sTitle, string sSource, List<MediaTrack> lsTracks) {
if (lsTracks == null || lsTracks.Count == 0) { Say.sayForced("0 tracks"); return; }

string sMpv = Homer.Media.mpvProgram();
if (sMpv.Length == 0) {
showBox("mpv is not installed, so there is nothing to play with.\r\n\r\n"
+ "Run installMpv in the program's scripts folder, or install the program again and tick the mpv box.",
"Player");
return;
}

string sSettings = sectionFor(sSource, lsTracks);
int iVolume = readNumber(sSettings, "volume", Homer.Mpv.c_iDefaultVolume, 0, 130);
int iRate = readNumber(sSettings, "rate", c_iDefaultRate, 25, 400);
int iStep = readNumber(sSettings, "step", c_iDefaultStep, 0, c_aiSteps.Length - 1);
int iOrder = readNumber(sSettings, "order", c_iDefaultOrder, 0, c_asOrders.Length - 1);

Homer.Mpv player = new Homer.Mpv(sMpv, Homer.Media.findInstalled("yt-dlp"));
string sError;
if (!player.start(out sError)) {
Homer.Log.info("Homer Player: mpv would not start. " + sError);
showBox("The player would not start.\r\n\r\n" + sError, "Player");
player.Dispose();
return;
}

// aOrder maps a row of the Tracks list to a place in mpv's own play list,
// which never changes. Sorting rearranges the rows and this map, and never
// the queue mpv is playing, so a sort during playback disturbs nothing.
int[] aOrder = new int[lsTracks.Count];
for (int i = 0; i < aOrder.Length; i++) aOrder[i] = i;
int iOrderNow = iOrder;
bool bMovingTimeline = false;
int iAnnounced = -1;
bool bWasPlaying = false;
bool bEndSaid = false;
DateTime dtLastSaid = DateTime.MinValue;
string sLastNote = "";
string sTitleNow = sTitle;
string sQueueName = sTitle;
DateTime dtLastNote = DateTime.MinValue;
bool bIdleLast = true;
bool bPausedLast = true;

Homer.LbcDialog dlg = new Homer.LbcDialog(sTitle, owner);
Homer.Mpv oPlayer = player;
List<MediaTrack> lsRef = lsTracks;

// ---- Tracks ----

dlg.addBand();
// THE LABEL IS A NAME, NOT A REPORT.
//
// It used to carry the count and the source: "Track list, 150 tracks from links
// in BlackBoxDown.md". A screen reader reads a control's label every time focus
// arrives, so every jump, every keyword search and every filter began by
// reciting how many tracks there were in total -- which is the one number the
// person had just moved away from caring about.
//
// The count belongs where it is asked for: spoken once as the dialog opens, and
// in the status line at any time after.
ListBox lstTracks = dlg.addPickBox("&Track list:", orderedNames(lsRef, aOrder), null,
"The queue, with each track's name, presenter and length where they are known. Moving through it chooses nothing; Enter plays the one you are on. Control+J jumps to a track by name, F3 jumps to the next, Control+F filters the list to what matches and Control+Shift+F clears the filter. Filter and Keywords take & for both words, a bar for either, and a star for anything. Alt+Shift+M writes what is showing, in the order shown, to a Markdown file.");

// EVERYTHING KNOWN ABOUT THE TRACK THE CURSOR IS ON, sorted by field.
//
// One Alt key away, read like any other text -- by character, word or line,
// selected, copied -- and nothing to close to get back. Filled when the cursor
// arrives, so it never speaks over anything and is current when it is read.
TextBox txtExtra = dlg.addMemoBox("E&xtra Info:", "",
"Everything known about the track the cursor is on, one field to a line, sorted by field. Read it by character, word or line; Control+C copies what is selected.");
txtExtra.ReadOnly = true;
dlg.endBand();

// ---- Order, Next, Previous ----

dlg.addBand();
ListBox lstOrder = dlg.addPickBox("&Order of list:", new List<string>(c_asOrders), c_asOrders[iOrder],
"How the list above is arranged. Sorting moves the rows only; the queue keeps playing in the order it was given.");
Button btnNext = dlg.addButton("&Next track", "Play the next track in the queue.");
Button btnPrevious = dlg.addButton("&Previous track", "Play the previous track in the queue.");
dlg.endBand();

// ---- Forward, Backward, Increment ----

dlg.addBand();
Button btnForward = dlg.addButton("&Forward in track", "Jump forward inside the current track by the increment.");
Button btnBackward = dlg.addButton("&Backward in track", "Jump backward inside the current track by the increment.");
ListBox lstIncrement = dlg.addPickBox("&Increment of jump:", new List<string>(c_asSteps), c_asSteps[iStep],
"How far Forward and Backward move. One minute to begin with. Choosing here changes nothing else: the next Forward or Backward uses whatever is chosen.");
dlg.endBand();

// ---- Rate, Volume ----

// Chapters and the timeline: moving about INSIDE one track, which is a
// different job from moving between tracks and belongs on its own row.
dlg.addBand();
// A PAIR SHOULD READ AS A PAIR. The first two names here were Chapter ahead
// and Chapter behind, one taking its letter from the second word and the other
// from the first, which is two things to remember instead of one. Same first
// word, contrasting second, and the letter always from the second: press the
// same shape of key for the same shape of command.
Button btnChapterAhead = dlg.addButton("Chapter &more", "Move to the next chapter of this track. Many tracks have no chapters, and nothing happens on those.");
Button btnChapterBehind = dlg.addButton("Chapter &less", "Move to the previous chapter of this track, which usually means the start of the one playing. Press it again for the one before.");
TrackBar barTimeline = dlg.addSlider("&Where in track:", 0, 0, 100, 5,
"How far through the track to move, as a percentage. Moving it moves the playback. It is set when you tab into it and does not follow along while playing, because a control that changed twice a second would be read out over everything else.",
delegate(int iPercent) { return iPercent.ToString(CultureInfo.InvariantCulture) + " percent"; });
dlg.endBand();

dlg.addBand();
TrackBar barRate = dlg.addSlider("&Rate percent:", iRate, 25, 400, 5,
"How fast to play, as a percentage of normal. The pitch is corrected, so speech stays understandable.",
delegate(int iPercent) { return iPercent.ToString(CultureInfo.InvariantCulture) + " percent"; });
TrackBar barVolume = dlg.addSlider("&Volume percent:", iVolume, 0, 130, 5,
"How loud. It starts below full so the media does not drown the screen reader; above 100 is louder than the recording.",
delegate(int iPercent) { return iPercent.ToString(CultureInfo.InvariantCulture) + " percent"; });
dlg.endBand();

// ---- Go, Stop, Help, Close ----

dlg.addBand();
// EXECUTE PLAYBACK, not Go.
//
// Go was the right word and the wrong key: Gemini claims Alt+G across the whole
// desktop, so the dialog never saw it. A global hotkey belongs to whoever
// registered it first and no dialog can take it back, so the button moved
// rather than the key. Run was the other candidate and collides with Rate;
// Start collides with Stop, which has no better name than Stop playback.
Button btnGo = dlg.addButton("&Execute playback", "Play the track the cursor is on, or resume what is paused, applying the order the cursor is on. Control+Enter does this from anywhere in the dialog, and so does Scroll Lock.");
Button btnStop = dlg.addButton("&Stop playback", "Stop playing and stay exactly where you are, in the queue and in the track. Execute playback carries on from there. It is a pause; the name is Stop because Previous track already has the P.");
// RECORDING HAS A START AND A STOP, as playing has Execute and Stop, and one
// key that does whichever applies, as Scroll Lock does for playing. The two
// buttons carry no trigger letter: R is the Rate slider's and S is Stop
// playback's, and a letter from inside a word is worse than none. They are
// reached by Tab or F7, and each is available only when it applies, so the
// reader says "unavailable" on the one that does not -- which is the state
// of the recording, told without a question asked.
Button btnRecord = dlg.addButton("Record", "Start keeping a copy of the stream as it arrives, in your Music folder under Homer Player, named for the track and the time. Alt+Shift+R does this from anywhere in the dialog, and stops it again.");
Button btnStopRecording = dlg.addButton("Stop recording", "Stop the recording and say how long it ran. Alt+Shift+R does this too while a recording is running.");
btnStopRecording.Enabled = false;
btnRecordNow = btnRecord; btnStopRecordingNow = btnStopRecording;
btnRecord.Click += delegate(object o, EventArgs e) { if (sRecordingPath.Length == 0) toggleRecording(dlg, oPlayer, lsRef); };
btnStopRecording.Click += delegate(object o, EventArgs e) { if (sRecordingPath.Length > 0) toggleRecording(dlg, oPlayer, lsRef); };
Button btnDefaults = dlg.addButton("&Default settings", "Forget what this queue has been set to and go back to the built-in settings: one minute, normal speed, the play list's own order.");
Button btnHelp = dlg.addButton("&Help", "What this dialog does and which keys do it, in one page.");
Button btnClose = dlg.addButton("Close", "Close the player. Where each track had reached is written down first, so playing it again starts there.");
dlg.endBand();

// ---- what the controls do ----

// MOVING THROUGH A LIST CHOOSES NOTHING. IT IS HOW A LIST IS READ.
//
// Arrowing down the Tracks list is how a screen reader user finds out what is
// in the queue, and arrowing down Order is how they find out what the orders
// are. If either acted as it was passed over, there would be no way to look
// without doing: every glance at the third order would sort the queue, and
// every glance at track nine would start playing it.
//
// So neither list has a SelectedIndexChanged handler. The cursor moves, the
// reader reads, and nothing happens. Go is what makes it happen -- it applies
// the order the cursor is on, and plays the track the cursor is on. Enter in
// either list does the same, which is what Enter means everywhere in FileDir.
//
// Stop is not needed first. Go on a queue that is already playing simply moves
// to what was chosen.
EventHandler ehGo = delegate(object o, EventArgs e) {
int iWantOrder = lstOrder.SelectedIndex;
if (iWantOrder >= 0 && iWantOrder != iOrderNow) {
iOrderNow = iWantOrder;
sortQueue(lsRef, aOrder, iWantOrder);
refillTracks(dlg, lstTracks, lsRef, aOrder);
writeValue(sSettings, "order", iWantOrder.ToString(CultureInfo.InvariantCulture));
say(dlg, "Ordered by " + c_asOrders[iWantOrder]);
}
goOrResume(dlg, oPlayer, lsRef, lstTracks, aOrder);
};

btnGo.Click += ehGo;
btnStop.Click += delegate(object o, EventArgs e) {
oPlayer.stop();
// Stopping is not the queue running out. Without this, pausing at the start of
// a track was announced as "End of queue" a moment later.
bWasPlaying = false;
bEndSaid = true;
say(dlg, "Stopped");
};
btnNext.Click += delegate(object o, EventArgs e) { oPlayer.next(); hear(oPlayer); };
btnPrevious.Click += delegate(object o, EventArgs e) { oPlayer.previous(); hear(oPlayer); };
btnForward.Click += delegate(object o, EventArgs e) {
oPlayer.seekRelative(stepSeconds(lstIncrement));
hear(oPlayer);
say(dlg, positionText(oPlayer));
};
btnBackward.Click += delegate(object o, EventArgs e) {
oPlayer.seekRelative(-stepSeconds(lstIncrement));
hear(oPlayer);
say(dlg, positionText(oPlayer));
};
btnChapterAhead.Click += delegate(object o, EventArgs e) { chapterMove(dlg, oPlayer, true); };
btnChapterBehind.Click += delegate(object o, EventArgs e) { chapterMove(dlg, oPlayer, false); };

// THE TIMELINE IS SET WHEN YOU ARRIVE AT IT, AND NOT AFTERWARDS.
//
// Reading its current place as the cursor lands on it is safe: a reader
// announces a slider's value when focus arrives anyway, so the number it
// announces may as well be true. Following playback while the cursor sits
// elsewhere is not safe, and is not done.
//
// bMovingTimeline keeps that refresh from being mistaken for a person dragging
// the slider, which would seek to where playback already was.
barTimeline.GotFocus += delegate(object o, EventArgs e) {
double dWhole = oPlayer.duration;
double dAt = oPlayer.position;
if (dWhole <= 0 || dAt < 0) return;
int iPercent = (int) ((dAt * 100.0) / dWhole);
if (iPercent < 0) iPercent = 0;
if (iPercent > 100) iPercent = 100;
bMovingTimeline = true;
try { barTimeline.Value = iPercent; }
finally { bMovingTimeline = false; }
};
barTimeline.ValueChanged += delegate(object o, EventArgs e) {
if (bMovingTimeline) return;
double dWhole = oPlayer.duration;
if (dWhole <= 0) { say(dlg, "No length known"); return; }
oPlayer.seekAbsolute((dWhole * barTimeline.Value) / 100.0);
hear(oPlayer);
};

btnHelp.Click += delegate(object o, EventArgs e) { showHelp(dlg.form); };
btnClose.Click += delegate(object o, EventArgs e) { dlg.close(); };

btnDefaults.Click += delegate(object o, EventArgs e) {
forgetSettings(sSettings);
bMovingTimeline = true;
try { barTimeline.Value = 0; }
finally { bMovingTimeline = false; }
lstIncrement.SelectedIndex = c_iDefaultStep;
barRate.Value = c_iDefaultRate;
barVolume.Value = Homer.Mpv.c_iDefaultVolume;
lstOrder.SelectedIndex = c_iDefaultOrder;
iOrderNow = c_iDefaultOrder;
sortQueue(lsRef, aOrder, c_iDefaultOrder);
refillTracks(dlg, lstTracks, lsRef, aOrder);
say(dlg, "Defaults restored");
};

// A slider is different from a list: moving it IS changing it, which is what
// its arrow keys have always meant in Windows. So these take effect at once,
// and are written down at once.
barRate.ValueChanged += delegate(object o, EventArgs e) {
oPlayer.setSpeed(((double) barRate.Value) / 100.0);
writeValue(sSettings, "rate", barRate.Value.ToString(CultureInfo.InvariantCulture));
};
barVolume.ValueChanged += delegate(object o, EventArgs e) {
oPlayer.setVolume(barVolume.Value);
writeValue(sSettings, "volume", barVolume.Value.ToString(CultureInfo.InvariantCulture));
};

// The increment is read when Forward or Backward is pressed, so choosing in
// this list changes nothing by itself either. It is written down when the
// dialog closes, along with whatever the cursor was left on.
lstTracks.KeyDown += delegate(object o, KeyEventArgs ev) {
if (ev.KeyCode != Keys.Enter || ev.Alt || ev.Control || ev.Shift) return;
ev.Handled = true;
ev.SuppressKeyPress = true;
ehGo(null, EventArgs.Empty);
};
lstOrder.KeyDown += delegate(object o, KeyEventArgs ev) {
if (ev.KeyCode != Keys.Enter || ev.Alt || ev.Control || ev.Shift) return;
ev.Handled = true;
ev.SuppressKeyPress = true;
ehGo(null, EventArgs.Empty);
};

// SCROLL LOCK IS PLAY AND PAUSE, from any control in this dialog and nowhere
// else.
//
// It is claimed through ProcessCmdKey rather than KeyDown. Scroll Lock is a
// toggle key: Windows acts on it and a KeyDown handler behind KeyPreview may
// never see it, which is why the first attempt did nothing. ProcessCmdKey runs
// ahead of the controls and ahead of that.
//
// It has a cost worth knowing: FileDir treats Scroll Lock as silence, so while
// it is on, ordinary FileDir speech is suppressed. That is why this dialog
// speaks globally.
// CONTROL AND AN ARROW IS THE TRANSPORT, and one sentence covers it:
// HORIZONTAL IS TIME INSIDE A TRACK, VERTICAL IS TRACKS IN THE QUEUE, THE PAGE
// KEYS ARE CHAPTERS, AND ADDING SHIFT MEANS ALL THE WAY.
//
//   Control+Left, Control+Right         back and forward by the increment
//   Control+Shift+Left, +Right          start and end of the track
//   Control+Up, Control+Down            previous and next track
//   Control+PageUp, Control+PageDown    previous and next chapter
//   Control+Shift+PageUp, +PageDown     first and last chapter
//   Control+Home, Control+End           first and last item: the LIST's own
//                                       keys, left to it
//   Space, Shift+Clear (keypad 5)       play or pause
//
// WHY CONTROL AND NOT SHIFT. The first version used Shift with these keys, and
// Shift is spoken for. In FileDir, Shift+Up and Shift+Down tag and move,
// Shift+Home and Shift+End tag to the top and bottom, and Alt+Shift with them
// untags the same span; DbDo and EdSharp mark with Shift too. Shift means
// MARKING throughout Homer Tools, and a player that made it mean seeking would
// contradict the pattern inside the very program it lives in.
//
// Control is the movement modifier in those same programs: Control+Home and
// Control+End are the first and last item, Control+Up and Control+Down step
// through the marked ones, Control+PageUp and Control+PageDown move between
// tables and windows. Moving among things is what a transport does.
//
// The players agree, which is a bonus rather than the argument. VLC seeks with
// the arrows and scales the jump with a modifier; iTunes and the usual
// foobar2000 setup change track with Control and an arrow; mpv and VLC both put
// chapters and titles on the Page keys. The one place this differs from them is
// the vertical pair, which they give to volume: here the queue is a vertical
// list of tracks, so vertical means tracks, and volume has a slider of its own
// with the keypad's plus and minus beside it.
//
// A single-selection list does nothing with Control and an arrow, so nothing
// visible is taken -- the same reasoning DbDo recorded for its own use of these
// chords. And with Num Lock off, which is how a screen reader leaves it, the
// keypad sends these very keys, so the two pads behave alike.
dlg.commandKey = delegate(Keys keyData) {
if (keyData == (Keys.Control | Keys.Left)) { oPlayer.seekRelative(-stepSeconds(lstIncrement)); hear(oPlayer); say(dlg, positionText(oPlayer)); return true; }
if (keyData == (Keys.Control | Keys.Right)) { oPlayer.seekRelative(stepSeconds(lstIncrement)); hear(oPlayer); say(dlg, positionText(oPlayer)); return true; }
if (keyData == (Keys.Control | Keys.Shift | Keys.Left)) { oPlayer.seekAbsolute(0); hear(oPlayer); say(dlg, "Start of track"); return true; }
if (keyData == (Keys.Control | Keys.Shift | Keys.Right)) { seekToEnd(dlg, oPlayer); hear(oPlayer); return true; }
if (keyData == (Keys.Control | Keys.Up)) { oPlayer.previous(); hear(oPlayer); return true; }
if (keyData == (Keys.Control | Keys.Down)) { oPlayer.next(); hear(oPlayer); return true; }
if (keyData == (Keys.Control | Keys.PageUp)) { chapterMove(dlg, oPlayer, false); return true; }
if (keyData == (Keys.Control | Keys.PageDown)) { chapterMove(dlg, oPlayer, true); return true; }
if (keyData == (Keys.Control | Keys.Shift | Keys.PageUp)) { firstChapter(dlg, oPlayer); hear(oPlayer); return true; }
if (keyData == (Keys.Control | Keys.Shift | Keys.PageDown)) { lastChapter(dlg, oPlayer); hear(oPlayer); return true; }
if (keyData == (Keys.Shift | Keys.Clear)) { oPlayer.togglePause(); say(dlg, oPlayer.paused ? "Playing" : "Paused"); return true; }

// SPACE PLAYS AND PAUSES, as it does in mpv's own window.
//
// Scroll Lock was meant to do this and never arrived -- it is a toggle key, and
// something between the keyboard and the dialog keeps it. Space is the key a
// person reaches for anyway.
//
// It is claimed everywhere in the dialog EXCEPT on a button, where Space is how
// Windows presses the thing with focus, and except in a box that takes typing.
// The Jump and Filter prompts are windows of their own, so a search term with a
// space in it is never in question here. In the queue, Space stops being
// type-ahead -- which is the trade mpv makes too, and Control+J is the better
// way to reach a track by name.
if (keyData == Keys.Space) {
// Space belongs to a button, which it presses, and to a box being TYPED in.
// A read-only box is neither: nothing can be typed into Extra Info, so Space
// there is free, and a person reading a track's details is exactly the person
// who wants to pause it.
Control ctlFocused = dlg.focusedControl();
TextBox tbFocused = ctlFocused as TextBox;
bool bTyping = (tbFocused != null && !tbFocused.ReadOnly) || (ctlFocused is ComboBox);
if (!(ctlFocused is Button) && !bTyping) {
oPlayer.togglePause();
say(dlg, oPlayer.paused ? "Playing" : "Paused");
return true;
}
}


// And the same commands on the digits, for a keyboard whose Num Lock is on.
// The grid reads as one sentence: the left column goes back, the right column
// goes forward, and each row is a different size of step -- chapters on top,
// the increment in the middle, whole tracks at the bottom.
if (keyData == Keys.NumPad5) { oPlayer.togglePause(); say(dlg, oPlayer.paused ? "Playing" : "Paused"); return true; }
if (keyData == Keys.NumPad0) { oPlayer.stop(); bWasPlaying = false; bEndSaid = true; say(dlg, "Stopped"); return true; }
if (keyData == Keys.NumPad4) { oPlayer.seekRelative(-stepSeconds(lstIncrement)); hear(oPlayer); say(dlg, positionText(oPlayer)); return true; }
if (keyData == Keys.NumPad6) { oPlayer.seekRelative(stepSeconds(lstIncrement)); hear(oPlayer); say(dlg, positionText(oPlayer)); return true; }
if (keyData == Keys.NumPad7) { chapterMove(dlg, oPlayer, false); return true; }
if (keyData == Keys.NumPad9) { chapterMove(dlg, oPlayer, true); return true; }
if (keyData == Keys.NumPad8) { oPlayer.seekAbsolute(0); hear(oPlayer); say(dlg, "Start of track"); return true; }
if (keyData == Keys.NumPad1) { oPlayer.previous(); hear(oPlayer); return true; }
if (keyData == Keys.NumPad3) { oPlayer.next(); hear(oPlayer); return true; }
if (keyData == Keys.NumPad2) { say(dlg, positionText(oPlayer)); return true; }
if (keyData == Keys.Decimal) { say(dlg, whereText(oPlayer, lsRef)); return true; }

// Control on a digit means all the way, matching Control+Shift on the
// navigation keys above.
if (keyData == (Keys.Control | Keys.NumPad4)) { oPlayer.seekAbsolute(0); hear(oPlayer); say(dlg, "Start of track"); return true; }
if (keyData == (Keys.Control | Keys.NumPad6)) { seekToEnd(dlg, oPlayer); hear(oPlayer); return true; }
if (keyData == (Keys.Control | Keys.NumPad1)) { oPlayer.playIndex(0); oPlayer.setPause(false); say(dlg, "First track"); return true; }
if (keyData == (Keys.Control | Keys.NumPad3)) { oPlayer.playIndex(lsRef.Count - 1); oPlayer.setPause(false); say(dlg, "Last track"); return true; }
if (keyData == (Keys.Control | Keys.NumPad7)) { firstChapter(dlg, oPlayer); hear(oPlayer); return true; }
if (keyData == (Keys.Control | Keys.NumPad9)) { lastChapter(dlg, oPlayer); hear(oPlayer); return true; }

if (keyData == Keys.Subtract) { barVolume.Value = Math.Max(barVolume.Minimum, barVolume.Value - 5); return true; }
if (keyData == Keys.Add) { barVolume.Value = Math.Min(barVolume.Maximum, barVolume.Value + 5); return true; }
if (keyData == Keys.Divide) { barRate.Value = Math.Max(barRate.Minimum, barRate.Value - 5); return true; }
if (keyData == Keys.Multiply) { barRate.Value = Math.Min(barRate.Maximum, barRate.Value + 5); return true; }

// CONTROL+ENTER IS ALWAYS GO, whatever the default button is at the time.
// The default button changes with what the player is doing -- Stop while
// something plays -- and a person who wants to start something should not
// have to work out which button Enter would press at that moment.
if (keyData == (Keys.Control | Keys.Enter)) {
ehGo(null, EventArgs.Empty);
return true;
}
if ((keyData & Keys.KeyCode) != Keys.Scroll) return false;
Homer.Log.info("Homer Player: Scroll Lock, play or pause");
oPlayer.togglePause();
// The property still holds the state from before the toggle, because the
// answer travels back over the pipe: it was playing, so it is now paused.
say(dlg, oPlayer.paused ? "Playing" : "Paused");
return true;
};

// The other keys are the commands no control expresses well. Alt+Shift with a
// letter, never a navigation key: in Windows, and in FileDir and DbDo in
// particular, Home, End, the arrows and the Page keys mean selecting and
// moving, and a player command wearing one of those is a false promise.
dlg.form.KeyPreview = true;
dlg.form.KeyDown += delegate(object o, KeyEventArgs ev) {
if (!ev.Alt || !ev.Shift) return;
bool bHandled = true;
switch (ev.KeyCode) {
case Keys.N: chapterMove(dlg, oPlayer, true); break;
case Keys.P: chapterMove(dlg, oPlayer, false); break;
case Keys.T: oPlayer.seekAbsolute(0); say(dlg, "Start of track"); break;
case Keys.Z: oPlayer.revertSeek(); say(dlg, positionText(oPlayer)); break;
case Keys.A: say(dlg, positionText(oPlayer)); break;
case Keys.W: say(dlg, whereText(oPlayer, lsRef)); break;
case Keys.O: sayOverview(dlg, lsRef, aOrder); break;
case Keys.C: copyAddress(dlg, oPlayer, lsRef, lstTracks, aOrder); break;
case Keys.L: saveList(dlg, lsRef, aOrder); break;
case Keys.M: saveReport(dlg, lstTracks, lsRef, aOrder); break;
case Keys.R: toggleRecording(dlg, oPlayer, lsRef); break;
default: bHandled = false; break;
}
if (bHandled) { ev.Handled = true; ev.SuppressKeyPress = true; }
};

// THE PLAYER NEVER MOVES THE CURSOR.
//
// The first version selected the playing track in the Tracks list as playback
// moved on. That looked helpful and was not: the cursor belongs to the person
// reading with it, and moving it under them means a Say Line in some other
// list reads a track instead, or an arrow key starts from somewhere they never
// put it. A track beginning is news; it is announced, and that is all.
//
// Nothing else is watched. A position that changes twice a second is not news,
// and a control that reports it is a control the reader talks over everything
// else to read.
// THE DEFAULT BUTTON FOLLOWS THE PLAYER.
//
// Nothing playing: Enter means Go, because starting is the only thing left to
// want. Something playing: Enter means Stop, because stopping is. Either way
// the answer to "what does Enter do here" is the obvious one, and Control+Enter
// is Go throughout for the person who wants to start something else while this
// one plays.
//
// Enter inside the Tracks or Order list still plays what the cursor is on:
// those two handle Enter themselves, and this default is for everything that
// does not.
bool bDefaultIsStop = false;
Timer tmrWatch = new Timer();
tmrWatch.Interval = 500;
tmrWatch.Tick += delegate(object o, EventArgs e) {
bool bPlayingNow = !oPlayer.idle && !oPlayer.paused;
if (bPlayingNow != bDefaultIsStop) {
bDefaultIsStop = bPlayingNow;
try { dlg.form.AcceptButton = bPlayingNow ? btnStop : btnGo; }
catch (Exception) { }
}
// The standing note on the status line. It is not a live region and nothing
// announces it: it is there to be read with the screen reader's own key for
// the status line, when the person wants it.
// Every five seconds, or whenever the state changes. A status bar rewritten
// twice a second is one a screen reader may decide to read out loud.
if ((DateTime.Now - dtLastNote).TotalMilliseconds >= 5000
|| oPlayer.idle != bIdleLast || oPlayer.paused != bPausedLast) {
dtLastNote = DateTime.Now;
bIdleLast = oPlayer.idle;
bPausedLast = oPlayer.paused;
string sNote = statusNote(oPlayer, lsRef);
if (sNote != sLastNote) { sLastNote = sNote; dlg.setStatusExtra(sNote); }
}

int iNow = oPlayer.playlistIndex;
bool bPlayingNow2 = !oPlayer.idle && !oPlayer.paused;

// THE TITLE SAYS WHAT IS PLAYING, OR WHAT THE QUEUE IS.
//
// It was set when a track started and never set back, so a title read after
// pausing named a track that had stopped playing. It follows the state now:
// the track's own line while something plays, the name of the play list when
// nothing does.
string sWantTitle = sQueueName;
if (bPlayingNow2 && iNow >= 0 && iNow < lsRef.Count) sWantTitle = lsRef[iNow].display();
if (sWantTitle != sTitleNow) {
sTitleNow = sWantTitle;
try { dlg.form.Text = sWantTitle; }
catch (Exception) { }
}
if (iNow >= 0 && iNow < lsRef.Count && bPlayingNow2) {
bWasPlaying = true;
bEndSaid = false;
if (iNow != iAnnounced) {
iAnnounced = iNow;
// THE TITLE SAYS WHAT IS PLAYING. A screen reader has a key for reading the
// window title, and that is the shortest way to ask "what is this?" without
// disturbing anything.

// At most one name every second and a half: a queue of addresses that
// will not play walks itself to the end in seconds, and a name for each
// is noise rather than news.
if ((DateTime.Now - dtLastSaid).TotalMilliseconds >= 1500) {
dtLastSaid = DateTime.Now;
say(dlg, lsRef[iNow].sName);
}
}
}
if (oPlayer.idle && bWasPlaying && !bEndSaid) {
bEndSaid = true;
say(dlg, "End of queue");
}
};

// Control+J and its relatives act on the queue from any control in this
// dialog, and leave the keyboard where it was.
txtExtra.GotFocus += delegate(object o, EventArgs e) {
int iRowNow = dlg.listSourceIndex(lstTracks, lstTracks.SelectedIndex);
int iTrackNow = (iRowNow >= 0 && iRowNow < aOrder.Length) ? aOrder[iRowNow] : -1;
if (iTrackNow < 0 || iTrackNow >= lsRef.Count) { txtExtra.Text = "No track"; return; }
MediaTrack trackNow = lsRef[iTrackNow];
// ExifTool is asked once per track, and only for a file on this computer: it
// is a program to start, and starting one on every arrival would be felt.
if (!trackNow.bExifAsked) {
trackNow.bExifAsked = true;
try { if (File.Exists(trackNow.sTarget)) addExifProperties(trackNow); }
catch (Exception) { }
}
txtExtra.Text = string.Join("\r\n", trackNow.factLines().ToArray());
};

dlg.primaryList = lstTracks;
// Jump and Filter look through everything known about a track, not only the
// line it shows.
dlg.setListItems(lstTracks, orderedNames(lsRef, aOrder), searchText(lsRef, aOrder));
dlg.setInitialFocus(lstTracks);
if (iOrder != 0) { sortQueue(lsRef, aOrder, iOrder); refillTracks(dlg, lstTracks, lsRef, aOrder); }

// The queue goes over once the dialog is up, not while the window is still
// being born, and mpv's own list operations then drive Next and Previous.
Homer.Mpv oLoader = player;
List<MediaTrack> lsToLoad = lsTracks;
int iStartVolume = iVolume;
int iStartRate = iRate;
// Said once, as the dialog opens, because a person arriving does want to know
// how much is here and where it came from.
string sOpening = Homer.Util.stringPlural("track", lsTracks.Count);
if (!string.IsNullOrEmpty(sSource)) sOpening = sOpening + " from " + sSource;
dlg.form.Shown += delegate(object o, EventArgs e) { say(dlg, sOpening); };

dlg.form.Shown += delegate(object o, EventArgs e) {
// PAUSED BEFORE ANYTHING IS LOADED. mpv starts playing the moment it is given
// a file, so the queue arriving was enough to start the first track talking
// over the dialog that had just opened. Nothing should play until somebody
// asks: Execute playback, Enter, or Scroll Lock all clear the pause.
oLoader.setPause(true);
for (int i = 0; i < lsToLoad.Count; i++) oLoader.loadFile(lsToLoad[i].sTarget, i > 0);
oLoader.setVolume(iStartVolume);
oLoader.setSpeed(((double) iStartRate) / 100.0);
};
tmrWatch.Start();

try {
// Go is the default button to start with, and Close is what Escape presses.
// The default changes to Stop while something plays; see the watcher above.
dlg.runPlain(btnGo, btnClose);

// ESCAPE SAVES. Everything here is written as it changes, so by now the file
// already holds it -- except the increment, which is read when Forward or
// Backward is pressed rather than watched. Written last, along with the order
// the list was left in, so the whole of what was chosen survives the exit
// however the dialog was closed.
if (lstIncrement.SelectedIndex >= 0)
writeValue(sSettings, "step", lstIncrement.SelectedIndex.ToString(CultureInfo.InvariantCulture));
if (lstOrder.SelectedIndex >= 0)
writeValue(sSettings, "order", lstOrder.SelectedIndex.ToString(CultureInfo.InvariantCulture));
if (barRate != null) writeValue(sSettings, "rate", barRate.Value.ToString(CultureInfo.InvariantCulture));
if (barVolume != null) writeValue(sSettings, "volume", barVolume.Value.ToString(CultureInfo.InvariantCulture));
}
finally {
tmrWatch.Stop();
tmrWatch.Dispose();
// WHERE EACH TRACK HAD REACHED IS WRITTEN DOWN, which is mpv's own
// quit-watch-later and what uppercase Q does in its player window. Playing
// the same thing again starts where it stopped, in this dialog or in mpv's.
// A recording still running when the dialog closes is stopped first, so
// the file is finished and said, not cut off in silence.
if (sRecordingPath.Length > 0) {
try { player.stopRecording(); Homer.Log.info("Homer Player: recording stopped at close: " + sRecordingPath); } catch (Exception) { }
sRecordingPath = "";
}
btnRecordNow = null; btnStopRecordingNow = null;
try { player.quitRemembering(); }
catch (Exception) { }
player.Dispose();
dlg.Dispose();
}
} // run method

// ---- the commands the buttons and keys share ----

// hear: after a command that MOVES somewhere, start playing.
//
// A person who cannot see the display finds out where they have landed by
// listening to it. Next track, a chapter, a jump, the timeline -- each of those
// is a question about where the media goes, and silence is not an answer. So
// every command that moves clears the pause; the ones that only report, like
// Alt+Shift+A, leave it alone.
private static void hear(Homer.Mpv player) {
// LOGGED, because playback has been reported starting when nobody asked for
// it. The caller's name turns "it just started" into a fact about which
// command did it.
Homer.Log.info("Homer Player: playing, asked by " + callerName());
player.setPause(false);
}

private static string callerName() {
try {
System.Diagnostics.StackTrace oTrace = new System.Diagnostics.StackTrace();
// Frame 0 is this method, frame 1 is hear, frame 2 is whoever wanted it.
if (oTrace.FrameCount > 2) return oTrace.GetFrame(2).GetMethod().Name;
}
catch (Exception) { }
return "unknown";
}

// stepSeconds: how far Forward and Backward move, read at the moment they are
// pressed rather than watched for changes.
private static int stepSeconds(ListBox lstIncrement) {
int iPick = lstIncrement.SelectedIndex;
if (iPick < 0 || iPick >= c_aiSteps.Length) iPick = c_iDefaultStep;
return c_aiSteps[iPick];
}

private static void goOrResume(Homer.LbcDialog dlg, Homer.Mpv player, List<MediaTrack> lsTracks,
ListBox lstTracks, int[] aOrder) {
// THE ROW IS NOT THE TRACK. Filtering the list with Control+F leaves fewer
// rows on screen than there are tracks, so which item a row really is has to
// be asked rather than assumed -- and then the sort order maps that to a place
// in the queue.
int iRow = dlg.listSourceIndex(lstTracks, lstTracks.SelectedIndex);
int iTrack = (iRow >= 0 && iRow < aOrder.Length) ? aOrder[iRow] : -1;
if (iTrack < 0) { say(dlg, "No track"); return; }
// Go on the track already playing means resume rather than start again,
// which is what a person pressing Go on a paused player wants.
if (iTrack == player.playlistIndex && player.paused) {
player.setPause(false);
say(dlg, "Playing");
return;
}
player.playIndex(iTrack);
player.setPause(false);
}

private static void sayOverview(Homer.LbcDialog dlg, List<MediaTrack> lsTracks, int[] aOrder) {
StringBuilder sb = new StringBuilder();
sb.Append(Homer.Util.stringPlural("track", lsTracks.Count));
for (int iRow = 0; iRow < aOrder.Length; iRow++) { sb.Append(". "); sb.Append(lsTracks[aOrder[iRow]].sName); }
say(dlg, sb.ToString());
}

private static void copyAddress(Homer.LbcDialog dlg, Homer.Mpv player, List<MediaTrack> lsTracks,
ListBox lstTracks, int[] aOrder) {
int iRow = dlg.listSourceIndex(lstTracks, lstTracks.SelectedIndex);
int iTrack = (iRow >= 0 && iRow < aOrder.Length) ? aOrder[iRow] : player.playlistIndex;
if (iTrack < 0 || iTrack >= lsTracks.Count) { say(dlg, "Nothing to copy"); return; }
try {
Clipboard.SetText(lsTracks[iTrack].sTarget);
say(dlg, "Address copied");
}
catch (Exception) { say(dlg, "Could not copy the address"); }
}

private static void saveList(Homer.LbcDialog dlg, List<MediaTrack> lsTracks, int[] aOrder) {
string sPath = askSavePath("Save Play List", "PlayList.m3u8",
"Play lists (*.m3u8)|*.m3u8|All files (*.*)|*.*");
if (sPath == null || sPath.Trim().Length == 0) return;
StringBuilder sb = new StringBuilder();
sb.Append("#EXTM3U\r\n");
// Saved in the order shown, because the order shown is the one just chosen.
for (int iRow = 0; iRow < aOrder.Length; iRow++) {
MediaTrack track = lsTracks[aOrder[iRow]];
sb.Append("#EXTINF:");
sb.Append(((int) (track.dSeconds > 0 ? track.dSeconds : -1)).ToString(CultureInfo.InvariantCulture));
sb.Append(",");
if (track.sPresenter.Length > 0) { sb.Append(track.sPresenter); sb.Append(" - "); }
sb.Append(track.sName);
sb.Append("\r\n");
sb.Append(track.sTarget);
sb.Append("\r\n");
}
try {
// UTF-8 WITHOUT a byte order mark, the one deliberate exception to the
// Homer text rule: several players read a mark at the head of a play list
// as part of the first entry and then cannot find it.
File.WriteAllText(sPath, sb.ToString(), new UTF8Encoding(false));
say(dlg, "Saved " + Path.GetFileName(sPath));
Homer.Log.info("Homer Player: saved " + lsTracks.Count + " tracks to " + sPath);
}
catch (Exception ex) {
Homer.Log.info("Homer Player: could not save " + sPath + ": " + ex.Message);
say(dlg, "Could not save the list");
}
}

// ---- the list and its order ----

private static List<string> orderedNames(List<MediaTrack> lsTracks, int[] aOrder) {
List<string> lsNames = new List<string>();
for (int iRow = 0; iRow < aOrder.Length; iRow++) lsNames.Add(lsTracks[aOrder[iRow]].display());
return lsNames;
}

// Through the dialog rather than into the control: setListItems is what tells
// the find and filter machinery that the list holds something else now.
private static void refillTracks(Homer.LbcDialog dlg, ListBox lstTracks, List<MediaTrack> lsTracks, int[] aOrder) {
dlg.setListItems(lstTracks, orderedNames(lsTracks, aOrder), searchText(lsTracks, aOrder));
}

// searchText: what Jump and Filter look through -- everything known about a
// track rather than the line it shows. A search for a presenter's surname, or
// for a word in an address, finds the track even though neither is on the line.
private static List<string> searchText(List<MediaTrack> lsTracks, int[] aOrder) {
List<string> lsText = new List<string>();
for (int iRow = 0; iRow < aOrder.Length; iRow++) lsText.Add(lsTracks[aOrder[iRow]].searchable());
return lsText;
}

// sortQueue: rearrange the ROWS, never the queue mpv is playing. A plain
// insertion sort, because a play list is short and a stable order matters
// more than speed: tracks that compare the same keep the order they came in.
private static void sortQueue(List<MediaTrack> lsTracks, int[] aOrder, int iOrder) {
for (int i = 0; i < aOrder.Length; i++) aOrder[i] = i;
if (iOrder == 0) return;
for (int i = 1; i < aOrder.Length; i++) {
int iHeld = aOrder[i];
int j = i - 1;
while (j >= 0 && comesAfter(lsTracks[aOrder[j]], lsTracks[iHeld], iOrder)) {
aOrder[j + 1] = aOrder[j];
j--;
}
aOrder[j + 1] = iHeld;
}
}

private static bool comesAfter(MediaTrack left, MediaTrack right, int iOrder) {
if (iOrder == 1) return string.CompareOrdinal(left.sortTitle(), right.sortTitle()) > 0;
if (iOrder == 2) return string.CompareOrdinal(left.sortPresenter(), right.sortPresenter()) > 0;
// A length nobody knows sorts last either way, rather than pretending to be
// zero and heading the list.
double dLeft = left.dSeconds >= 0 ? left.dSeconds : double.MaxValue;
double dRight = right.dSeconds >= 0 ? right.dSeconds : double.MaxValue;
if (iOrder == 3) return dLeft > dRight;
if (left.dSeconds < 0 || right.dSeconds < 0) return dLeft > dRight;
return dLeft < dRight;
}

// seekToEnd: the last few seconds rather than the very last instant, so the end
// can be heard instead of the next track starting.
private static void seekToEnd(Homer.LbcDialog dlg, Homer.Mpv player) {
double dWhole = player.duration;
if (dWhole <= 0) { say(dlg, "No length known"); return; }
double dTarget = dWhole - 3;
if (dTarget < 0) dTarget = 0;
player.seekAbsolute(dTarget);
say(dlg, "End of track");
}

// chapterMove: forwards or back by one chapter, and SAY WHAT HAPPENED.
//
// This is the question that could not be answered over the telephone: did that
// move by chapter, or did it do nothing? Saying the position afterwards cannot
// tell anybody -- a position is a position however it was reached. So the
// answer names the chapter and how many there are, and a track with none says
// so outright instead of leaving silence to be interpreted.
private static void chapterMove(Homer.LbcDialog dlg, Homer.Mpv player, bool bForward) {
int iCount = player.chapterCount;
Homer.Log.info("Homer Player: chapter " + (bForward ? "more" : "less")
+ ", track has " + iCount + " chapters, now at " + player.chapter);
if (iCount <= 0) { say(dlg, "No chapters in this track"); return; }
if (bForward) player.nextChapter(); else player.previousChapter();
hear(player);
// mpv answers over the pipe, so the new chapter number arrives a moment later.
// A short wait buys an announcement that is true rather than one step behind.
System.Threading.Thread.Sleep(120);
int iNow = player.chapter;
string sWhere = (iNow >= 0)
? ("Chapter " + (iNow + 1).ToString(CultureInfo.InvariantCulture) + " of " + iCount.ToString(CultureInfo.InvariantCulture))
: "Chapter";
say(dlg, sWhere + ", " + Homer.Mpv.saySpan(player.position));
}

private static void firstChapter(Homer.LbcDialog dlg, Homer.Mpv player) {
if (player.chapterCount <= 0) { say(dlg, "No chapters"); return; }
player.setChapter(0);
say(dlg, "First chapter");
}

private static void lastChapter(Homer.LbcDialog dlg, Homer.Mpv player) {
int iCount = player.chapterCount;
if (iCount <= 0) { say(dlg, "No chapters"); return; }
player.setChapter(iCount - 1);
say(dlg, "Last chapter");
}

// saveReport: write what is in the list, as it is in the list, to a Markdown
// file.
//
// AS IT IS IN THE LIST. The order chosen in Order of list, and only the tracks
// a filter has left showing: what is written is what is on screen, so the file
// answers the question the person had when they asked for it rather than some
// other question about the whole queue.
//
// One track to a heading, and under it only the fields that are known. A blank
// line saying "Presenter: unknown" is a line to listen to for nothing.
private static void saveReport(Homer.LbcDialog dlg, ListBox lstTracks,
List<MediaTrack> lsTracks, int[] aOrder) {
List<int> liShowing = new List<int>();
for (int iRow = 0; iRow < lstTracks.Items.Count; iRow++) {
int iInOrder = dlg.listSourceIndex(lstTracks, iRow);
if (iInOrder >= 0 && iInOrder < aOrder.Length) liShowing.Add(aOrder[iInOrder]);
}
if (liShowing.Count == 0) { say(dlg, "Nothing to write"); return; }

string sPath = askSavePath("Save Track Notes", "Tracks.md",
"Markdown (*.md)|*.md|All files (*.*)|*.*");
if (sPath == null || sPath.Trim().Length == 0) return;

StringBuilder sb = new StringBuilder();
sb.Append("# Tracks\r\n\r\n");
sb.Append(Homer.Util.stringPlural("track", liShowing.Count));
if (dlg.listIsFiltered(lstTracks)) sb.Append(", filtered from " + lsTracks.Count.ToString(CultureInfo.InvariantCulture));
sb.Append(", in the order shown.\r\n\r\n");
int iNumber = 0;
foreach (int iTrack in liShowing) {
MediaTrack track = lsTracks[iTrack];
iNumber = iNumber + 1;
sb.Append("## ");
sb.Append(iNumber.ToString(CultureInfo.InvariantCulture));
sb.Append(". ");
sb.Append(track.sName);
sb.Append("\r\n\r\n");
if (track.sPresenter.Length > 0) { sb.Append("- Presenter: "); sb.Append(track.sPresenter); sb.Append("\r\n"); }
string sLength = Homer.Mpv.formatTime(track.dSeconds);
if (sLength.Length > 0) { sb.Append("- Length: "); sb.Append(sLength); sb.Append("\r\n"); }
sb.Append("- Address: ");
sb.Append(track.sTarget);
sb.Append("\r\n\r\n");
}
try {
Homer.Util.string2File(sb.ToString(), sPath);
say(dlg, "Wrote " + Path.GetFileName(sPath));
Homer.Log.info("Homer Player: wrote notes for " + liShowing.Count + " tracks to " + sPath);
}
catch (Exception ex) {
Homer.Log.info("Homer Player: could not write " + sPath + ": " + ex.Message);
say(dlg, "Could not write the file");
}
}

// ---- everything known about one track ----


// addExifProperties: ask ExifTool, which reads far more formats than anything
// built in and prints one field per line. -S gives "Field: value" with no
// padding, which is exactly the shape wanted here.
private static void addExifProperties(MediaTrack track) {
string sPath = track.sTarget;
string sExif = Homer.Media.findInstalled("exiftool");
if (sExif.Length == 0) { track.addFact("Note", "ExifTool is not installed, so only the basics are known"); return; }
string sOut = "";
try {
System.Diagnostics.ProcessStartInfo info = new System.Diagnostics.ProcessStartInfo();
info.FileName = sExif;
info.Arguments = "-S -charset filename=UTF8 " + Homer.Util.stringQuote(sPath);
info.UseShellExecute = false;
info.CreateNoWindow = true;
info.RedirectStandardOutput = true;
info.RedirectStandardError = true;
System.Diagnostics.Process oExif = System.Diagnostics.Process.Start(info);
// Both streams drained at once, so neither can fill and hang ExifTool (8 October 2026).
System.Threading.Tasks.Task<string> taskExifErr = oExif.StandardError.ReadToEndAsync();
sOut = oExif.StandardOutput.ReadToEnd();
if (!oExif.WaitForExit(20000)) { try { oExif.Kill(); } catch (Exception) { } }
}
catch (Exception ex) {
Homer.Log.info("Homer Player: ExifTool failed. " + ex.Message);
track.addFact("Note", "ExifTool could not read this file");
return;
}
foreach (string sLine in sOut.Split('\n')) {
string sTrimmed = sLine.Trim();
if (sTrimmed.Length == 0) continue;
int iColon = sTrimmed.IndexOf(':');
if (iColon <= 0) continue;
string sField = sTrimmed.Substring(0, iColon).Trim();
string sValue = sTrimmed.Substring(iColon + 1).Trim();
if (sField.Length == 0 || sValue.Length == 0) continue;
track.addFact(sField, sValue);
}
}

// showHelp: what this dialog does and which keys do it, in one page.
//
// Lbc's own help lists the fields and their descriptions, which is right for a
// form being filled in. A player is a set of commands, and what a person wants
// from its help is the keys -- especially the ones with no control to tab to.
// Short lines, grouped, no prose.
// RECORDING, AS SIMPLY AS IT CAN BE DONE. Alt+Shift+R starts writing the
// stream as it arrives -- no re-encoding, no settings -- to Music\Homer
// Player\<track>-<date>-<time>.<ext>, and says the file; Alt+Shift+R again
// stops and says how long it ran. One key, one file, one message each way.
// Anyone making audio to publish has a studio program for that and should
// use it; this is for keeping a programme to hear later, which is all a
// player should offer.
private static string sRecordingPath = "";
private static DateTime dtRecordingStart = DateTime.MinValue;
private static Button btnRecordNow = null;
private static Button btnStopRecordingNow = null;

private static void showRecordingState() {
try {
if (btnRecordNow != null) btnRecordNow.Enabled = (sRecordingPath.Length == 0);
if (btnStopRecordingNow != null) btnStopRecordingNow.Enabled = (sRecordingPath.Length > 0);
} catch { }
}

private static void toggleRecording(LbcDialog dlg, Mpv oPlayer, List<MediaTrack> lsRef) {
if (sRecordingPath.Length > 0) {
oPlayer.stopRecording();
TimeSpan ts = DateTime.Now - dtRecordingStart;
// WHAT IS SAID IS SHORT: a file name with a time stamp is for the folder, not
// the ear. The log has the path.
string sDone = "Recording stopped after " + ((ts.TotalMinutes >= 1) ? ((int) ts.TotalMinutes) + " minutes" : ((int) ts.TotalSeconds) + " seconds")
+ ". It is in Music, Homer Player.";
Homer.Log.info("Homer Player: " + sDone);
sRecordingPath = "";
showRecordingState();
say(dlg, sDone);
return;
}
int iNow = oPlayer.playlistIndex;
string sName = (iNow >= 0 && iNow < lsRef.Count) ? lsRef[iNow].display() : "Recording";
foreach (char c in Path.GetInvalidFileNameChars()) sName = sName.Replace(c, '_');
if (sName.Length > 60) sName = sName.Substring(0, 60);
string sFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyMusic), "Homer Player");
try { Directory.CreateDirectory(sFolder); } catch (Exception ex) { say(dlg, "Could not make the recordings folder: " + ex.Message); return; }
// The container follows the stream: an MP3 stream copied is an MP3 file; anything
// else is written as a transport stream, which every player opens.
string sExt = ".ts";
try {
string sUrl = (iNow >= 0 && iNow < lsRef.Count) ? lsRef[iNow].sTarget.ToLowerInvariant() : "";
if (sUrl.Contains("mp3") || sUrl.EndsWith(".mp3")) sExt = ".mp3";
else if (sUrl.Contains("aac")) sExt = ".aac";
} catch { }
sRecordingPath = Path.Combine(sFolder, sName + "-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + sExt);
if (!oPlayer.startRecording(sRecordingPath)) { say(dlg, "The player would not start recording."); sRecordingPath = ""; return; }
dtRecordingStart = DateTime.Now;
showRecordingState();
Homer.Log.info("Homer Player: recording to " + sRecordingPath);
say(dlg, "Recording " + sName + ". Alt Shift R stops.");
}

private static void showHelp(IWin32Window owner) {
StringBuilder sb = new StringBuilder();
sb.Append("PLAYER\r\n\r\n");
sb.Append("Every control has its own Alt key, the letter underlined in its name.\r\n");
sb.Append("These commands have no control, so they are listed first.\r\n\r\n");
sb.Append("FINDING A TRACK\r\n");
sb.Append("Control+J          jump to a track by name, as the list shows it\r\n");
sb.Append("Control+Shift+J    jump back\r\n");
sb.Append("Control+K          keywords: search everything known about the tracks\r\n");
sb.Append("Control+Shift+K    keywords, backwards\r\n");
sb.Append("F3, Shift+F3       repeat the last jump or keyword search\r\n");
sb.Append("Control+F          filter the list to what matches\r\n");
sb.Append("Control+Shift+F    clear the filter\r\n\r\n");
sb.Append("Keywords and Filter share one syntax: red & blue means both words,\r\n");
sb.Append("red | blue means either, and chap* means anything starting that way.\r\n");
sb.Append("Case never matters. Jump is a plain substring, as in the file list.\r\n");
sb.Append("Keywords looks at the title, the presenter, the episode, the address,\r\n");
sb.Append("and whatever the source document said -- the date, the summary, the\r\n");
sb.Append("people. Jump looks only at the line the list shows.\r\n\r\n");
sb.Append("MOVING AND PLAYING\r\n");
sb.Append("Space          play or pause, from anywhere but a button\r\n");
sb.Append("Enter          in the queue, play the track the cursor is on\r\n");
sb.Append("Control+Enter  execute playback, from anywhere\r\n");
sb.Append("Control+Left, Control+Right   jump back and forward by the increment\r\n");
sb.Append("Control+Shift+Left, Right     start and end of the track\r\n");
sb.Append("Control+Up, Control+Down      previous and next track\r\n");
sb.Append("Control+PageUp, PageDown      previous and next chapter\r\n");
sb.Append("Control+Shift+PageUp, PageDown  first and last chapter\r\n");
sb.Append("Control+Home, Control+End     first and last track in the list\r\n\r\n");
sb.Append("Sideways is time inside a track, up and down is tracks in the queue,\r\n");
sb.Append("the Page keys are chapters, and adding Shift means all the way.\r\n\r\n");
sb.Append("TELLING YOU WHERE YOU ARE\r\n");
sb.Append("Alt+Shift+A    say the position\r\n");
sb.Append("Alt+Shift+W    say the track, its number and the position\r\n");
sb.Append("Alt+Shift+O    say how many tracks, then their names\r\n");
sb.Append("Alt+X          extra info: everything known about this track\r\n\r\n");
sb.Append("THE REST\r\n");
sb.Append("Alt+Shift+C    copy the address of the track\r\n");
sb.Append("Alt+Shift+L    save the queue as a play list\r\n");
sb.Append("Alt+Shift+M    write track notes to a Markdown file\r\n");
sb.Append("Alt+Shift+R    record, or stop recording: the Record and Stop recording buttons do the same, one at a time\r\n");
sb.Append("Alt+Shift+Z    undo the last jump within a track\r\n");
sb.Append("Escape         close, remembering where each track had reached\r\n\r\n");
sb.Append("F7 lists the controls; F1 lists them with their descriptions.\r\n");

Homer.LbcDialog dlgHelp = new Homer.LbcDialog("Player Help", owner);
TextBox txtHelp = dlgHelp.addMemo(sb.ToString(),
"The keys this dialog answers to. Read it by line, or Control+C to copy.");
txtHelp.ReadOnly = true;
Button btnOk = dlgHelp.addButton("&OK", "Go back to the player.");
btnOk.Click += delegate(object o, EventArgs e) { dlgHelp.close(); };
dlgHelp.setInitialFocus(txtHelp);
try { dlgHelp.runPlain(btnOk, btnOk); }
finally { dlgHelp.Dispose(); }
}

// ---- the words the dialog says ----

// say: speak it and keep it.
//
// Global, so Scroll Lock -- this dialog's play and pause key -- does not
// silence the player it is driving. The status line keeps every message, so a
// screen reader's say-status-bar key can read back what was said.
private static void say(Homer.LbcDialog dlg, string sText) {
Say.sayForced(sText);
if (dlg != null) dlg.appendStatus(sText);
}

// statusNote: what is playing and how far in, in one line, for the status bar.
// Read on demand with a screen reader's status key; never spoken.
// THE NOTE CHANGES WHEN SOMETHING CHANGES, NOT WHEN THE CLOCK MOVES.
//
// The position was in it, so it was rewritten twice a second, and a status bar
// that changes twice a second is one a screen reader may decide to read. It now
// carries the track, the count and whether it is playing -- facts that change
// when the person does something -- and the position is left to Alt+Shift+A and
// to the Where in track slider, which are asked rather than announced.
// statusNote: where playback is, in one short line.
//
// The track's NAME is not here: it is in the window title, which a screen
// reader reads with its own key, and repeating it in both places wastes the
// line. What is here is what the title cannot say -- which of how many, whether
// it is going, and how far in.
//
//   Playing 3 of 60, 12 min 3 sec of 45 min
private static string statusNote(Homer.Mpv player, List<MediaTrack> lsTracks) {
// ONE SENTENCE, IN THE ORDER A PERSON ASKS IT. What is it doing, which track
// of how many, how far in. Nothing else: the track's name is in the window
// title, which the reader has its own key for.
//
//   Playing track 3 of 60, 12 min 3 sec of 45 min
//   Paused at track 3 of 60, 12 min 3 sec of 45 min
//   Nothing playing, 60 tracks
int iNow = player.playlistIndex;
StringBuilder sb = new StringBuilder();
if (player.idle || iNow < 0 || iNow >= lsTracks.Count) {
sb.Append("Nothing playing, ");
sb.Append(Homer.Util.stringPlural("track", lsTracks.Count));
return sb.ToString();
}
sb.Append(player.paused ? "Paused at track " : "Playing track ");
sb.Append((iNow + 1).ToString(CultureInfo.InvariantCulture));
sb.Append(" of ");
sb.Append(lsTracks.Count.ToString(CultureInfo.InvariantCulture));
string sAt = Homer.Mpv.saySpan(player.position);
if (sAt.Length > 0) {
sb.Append(", ");
sb.Append(sAt);
string sOf = Homer.Mpv.saySpan(player.duration);
if (sOf.Length > 0) { sb.Append(" of "); sb.Append(sOf); }
}
return sb.ToString();
}

// SPOKEN, NOT SHOWN. "12:03" read aloud is two numbers and a colon to
// disentangle; "12 min 3 sec" is the answer. The list keeps the short written
// form, which is for the eye.
private static string positionText(Homer.Mpv player) {
string sAt = Homer.Mpv.saySpan(player.position);
string sOf = Homer.Mpv.saySpan(player.duration);
if (sAt.Length == 0) return "Not playing";
if (sOf.Length == 0) return sAt;
return sAt + " of " + sOf;
}

private static string whereText(Homer.Mpv player, List<MediaTrack> lsTracks) {
int iNow = player.playlistIndex;
string sName = (iNow >= 0 && iNow < lsTracks.Count) ? lsTracks[iNow].sName : player.title;
if (sName.Length == 0) return "Nothing playing";
string sCount = "";
if (iNow >= 0) sCount = ", track " + (iNow + 1).ToString(CultureInfo.InvariantCulture)
+ " of " + lsTracks.Count.ToString(CultureInfo.InvariantCulture);
string sRec = "";
if (sRecordingPath.Length > 0) {
TimeSpan ts = DateTime.Now - dtRecordingStart;
sRec = ", recording for " + ((ts.TotalMinutes >= 1) ? ((int) ts.TotalMinutes) + " minutes" : ((int) ts.TotalSeconds) + " seconds");
}
return sName + sCount + ", " + positionText(player) + sRec;
}

// ---- settings ----

private static int readNumber(string sSection, string sKey, int iDefault, int iMinimum, int iMaximum) {
try {
string sPath = settingsPath();
if (!File.Exists(sPath)) return iDefault;
foreach (Homer.InixCodec.Section section in Homer.InixCodec.read(sPath)) {
if (!string.Equals(section.Name, sSection, StringComparison.OrdinalIgnoreCase)) continue;
int iValue;
if (!int.TryParse(section.get(sKey), out iValue)) return iDefault;
if (iValue < iMinimum || iValue > iMaximum) return iDefault;
return iValue;
}
}
catch (Exception ex) { Homer.Log.info("Homer Player: could not read settings. " + ex.Message); }
return iDefault;
}

// Written the moment it changes, so a session that ends any other way still
// leaves the answer behind.
private static void writeValue(string sSection, string sKey, string sValue) {
try { Homer.InixCodec.writeValue(settingsPath(), sSection, sKey, sValue); }
catch (Exception ex) { Homer.Log.info("Homer Player: could not save " + sKey + ". " + ex.Message); }
}

// forgetSettings: remove this queue's section entirely, so the next time it is
// played it starts from the built-in defaults. Deleting beats writing the
// defaults back: a default that changes later should reach a queue that never
// asked for anything else.
private static void forgetSettings(string sSection) {
try {
string sPath = settingsPath();
if (!File.Exists(sPath)) return;
List<Homer.InixCodec.Section> lsKeep = new List<Homer.InixCodec.Section>();
foreach (Homer.InixCodec.Section section in Homer.InixCodec.read(sPath)) {
if (!string.Equals(section.Name, sSection, StringComparison.OrdinalIgnoreCase)) lsKeep.Add(section);
}
Homer.InixCodec.writeAsConfig(sPath, lsKeep);
}
catch (Exception ex) { Homer.Log.info("Homer Player: could not clear settings. " + ex.Message); }
}

// ---- turning what FileDir has into tracks ----

// fromPlaylistLines: the m3u lines FileDir already builds, read back as
// tracks. #EXTINF carries a length and the name a document gave the link, and
// by long convention a name written as "Presenter - Title" means exactly that.
public static List<MediaTrack> fromPlaylistLines(IList<string> lsLines) {
List<MediaTrack> lsTracks = new List<MediaTrack>();
string sPending = "";
double dPending = -1;
foreach (string sRaw in lsLines) {
string sLine = sRaw == null ? "" : sRaw.Trim();
if (sLine.Length == 0) continue;
if (sLine.StartsWith("#EXTINF", StringComparison.OrdinalIgnoreCase)) {
sPending = "";
dPending = -1;
int iColon = sLine.IndexOf(':');
int iComma = sLine.IndexOf(',');
if (iComma >= 0 && iComma < sLine.Length - 1) sPending = sLine.Substring(iComma + 1).Trim();
if (iColon >= 0 && iComma > iColon) {
double dSeconds;
if (double.TryParse(sLine.Substring(iColon + 1, iComma - iColon - 1).Trim(),
NumberStyles.Float, CultureInfo.InvariantCulture, out dSeconds) && dSeconds > 0) dPending = dSeconds;
}
continue;
}
if (sLine.StartsWith("#")) continue;
MediaTrack track = new MediaTrack(sPending, sLine);
track.dSeconds = dPending;
int iDash = sPending.IndexOf(" - ", StringComparison.Ordinal);
if (iDash > 0 && iDash < sPending.Length - 3) {
track.sPresenter = sPending.Substring(0, iDash).Trim();
track.sName = sPending.Substring(iDash + 3).Trim();
}
lsTracks.Add(track);
sPending = "";
dPending = -1;
}
return lsTracks;
}

// fromFiles: plain file names, named by their own file names.
public static List<MediaTrack> fromFiles(IList<string> lsPaths) {
List<MediaTrack> lsTracks = new List<MediaTrack>();
foreach (string sPath in lsPaths) {
if (sPath == null || sPath.Length == 0) continue;
lsTracks.Add(new MediaTrack(Path.GetFileName(sPath), sPath));
}
return lsTracks;
}

} // MediaPlayer class

} // FileDir namespace
