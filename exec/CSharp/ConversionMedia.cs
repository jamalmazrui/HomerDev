// ConversionMedia.cs -- audio, video and picture conversions, the media half of
// the kit's Conversion class (kit 1.74.0).
//
// A separate file because it needs Media.cs (ffmpeg and ImageMagick), and an app
// that converts only documents should not have to compile the media code. When
// this file is left out, Conversion.cs's partial methods compile to nothing, and
// media files are simply not offered.
//
// Moved from FileDir's Convert.cs, unchanged in what it does.
//
// Copyright 2006-2026 by Jamal Mazrui. MIT License.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace Homer {

public static partial class Conversion {

private static readonly string[] aAudioSources = {
".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma", ".aiff", ".aif"
};

private static readonly string[] aVideoSources = {
".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".flv", ".m4v", ".mpg",
".mpeg", ".ts", ".m2ts", ".3gp", ".ogv"
};

private static readonly string[] aImageSources = {
".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"
};

private static readonly string[] aMagickSources = {
".heic", ".heif", ".avif",
".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf", ".pef", ".srw",
".svg", ".ico", ".psd", ".xcf", ".tga", ".pcx", ".pnm", ".ppm", ".pgm", ".dds",
".jp2", ".jxl", ".exr", ".hdr"
};

static partial void mediaCategory(string sExt, ref string sCategory) {
if (Array.IndexOf(aAudioSources, sExt) >= 0) sCategory = "audio";
else if (Array.IndexOf(aVideoSources, sExt) >= 0) sCategory = "video";
else if (Array.IndexOf(aImageSources, sExt) >= 0 || Array.IndexOf(aMagickSources, sExt) >= 0) sCategory = "image";
} // mediaCategory method

static partial void mediaTargets(string sCategory, ref string[,] aTargets) {
if (sCategory == "audio")
aTargets = new string[,] {{"MP3 audio", "mp3"}, {"M4A audio (AAC)", "m4a"}, {"WAV audio, uncompressed", "wav"},
{"FLAC audio, lossless", "flac"}, {"Ogg Vorbis audio", "ogg"}, {"Opus audio", "opus"}, {"Play list of these files", "m3u"},
{"Transcript, Markdown document", "md"}, {"Transcript, plain text", "txt"}, {"Transcript, web page", "htm"}, {"Transcript, Word document", "docx"}, {"Transcript, PDF document", "pdf"}};
else if (sCategory == "video")
aTargets = new string[,] {{"MP4 video", "mp4"}, {"Matroska video", "mkv"}, {"WebM video", "webm"}, {"QuickTime video", "mov"},
{"AVI video", "avi"}, {"MP3 audio, sound only", "mp3"}, {"M4A audio, sound only", "m4a"}, {"WAV audio, sound only", "wav"},
{"Play list of these files", "m3u"},
{"Transcript, Markdown document", "md"}, {"Transcript, plain text", "txt"}, {"Transcript, web page", "htm"}, {"Transcript, Word document", "docx"}, {"Transcript, PDF document", "pdf"}};
else if (sCategory == "image")
aTargets = new string[,] {{"PNG image", "png"}, {"JPEG image", "jpg"}, {"WebP image", "webp"}, {"BMP image", "bmp"},
{"GIF image", "gif"}, {"TIFF image", "tif"}, {"Windows icon", "ico"}, {"AVIF image", "avif"}};
} // mediaTargets method

// ------- speech to text, and text to speech (kit 1.84.0) -------
//
// THE UNCONVENTIONAL CONVERSIONS, the author's request of 20 October 2026: sound and video
// become documents by transcription, and documents become sound or video by speech, all
// through the kit's one conversion technique, so BatCon and every app share them.
//   audio or video -> txt, md, htm, docx, pdf, odt, rtf, epub, doc: ffmpeg takes the sound as
//     the 16 kHz mono WAV Whisper wants; Voice.transcribe runs Whisper on this computer; the
//     transcript becomes Markdown, which the route table takes to the target.
//   a document -> mp3, m4a, wav, ogg, flac, opus: its text, by the route table; Windows' own
//     speech synthesis speaks it into a WAV; ffmpeg encodes it.
//   a document -> mp4, mkv, webm, mov: the same speech over a plain black picture, since the kit
//     makes no pictures of its own.
//   video -> any of those, DESCRIBED (1.85.2): HomerScribe, when installed, is the kit's engine
//     for what a video shows, as Pandoc and Office are engines for documents. It is asked for
//     both halves -- what is said and what can be seen -- and the two become one document. Its
//     description is the suite's one technique for it, kept in one program rather than copied
//     here; without HomerScribe, a video gets the transcript alone, and the log says why.
private static readonly string[] aTranscriptTargets = { "doc", "docx", "epub", "htm", "md", "odt", "pdf", "rtf", "txt" };
private static readonly string[] aSpeechAudioTargets = { "flac", "m4a", "mp3", "ogg", "opus", "wav" };
private static readonly string[] aSpeechVideoTargets = { "mkv", "mov", "mp4", "webm" };

// textAvailable: whether the kit can take a file's words out as text.
private static bool textAvailable(string sSource) {
string sType = typeOf(sSource);
if (sType == "txt" || sType == "md") return true;
return hasRoute(sSource, "x.txt") || hasRoute(sSource, "x.md");
} // textAvailable method

static partial void mediaCan(string sSource, string sTarget, ref bool bCan) {
string sCategory = "";
mediaCategory(Path.GetExtension(sSource).ToLowerInvariant(), ref sCategory);
string sTo = typeOf(sTarget);
if ((sCategory == "audio" || sCategory == "video") && Array.IndexOf(aTranscriptTargets, sTo) >= 0) { bCan = true; return; }
if (sCategory == "" && (Array.IndexOf(aSpeechAudioTargets, sTo) >= 0 || Array.IndexOf(aSpeechVideoTargets, sTo) >= 0)) { bCan = textAvailable(sSource); return; }
if (sCategory == "") return;
string[,] aTargets = null;
mediaTargets(sCategory, ref aTargets);
if (aTargets != null) for (int i = 0; i < aTargets.GetLength(0); i++) if (aTargets[i, 1] == sTo) { bCan = true; return; }
} // mediaCan method

static partial void mediaAllTargets(List<string[]> lsAll) {
foreach (string sCategory in new string[] { "audio", "video", "image" }) {
string[,] aTargets = null;
mediaTargets(sCategory, ref aTargets);
if (aTargets == null) continue;
for (int i = 0; i < aTargets.GetLength(0); i++) if (aTargets[i, 1] != "m3u") lsAll.Add(new string[] { aTargets[i, 0], aTargets[i, 1] });
}
} // mediaAllTargets method

// describeVideoTo: what a video says and shows, as one document, by HomerScribe. A context file
// named after the video, beside it, is found by HomerScribe itself, as in its guide.
private static bool describeVideoTo(string sSource, string sTarget, out string sError) {
sError = "";
string sScribe = Paths.homerProgram("HomerScribe");
if (sScribe.Length == 0) { sError = "HomerScribe is not installed"; return false; }
string sDir = Path.Combine(Path.GetTempPath(), "HomerDescribe-" + Guid.NewGuid().ToString("N").Substring(0, 8));
string sMd = tempPath(sSource, ".md");
try {
Directory.CreateDirectory(sDir);
string sOut, sErr;
// Ten hours at most: a long film is described scene by scene by a local vision model.
int iCode = Media.run(sScribe, "\"" + sSource + "\" --describe --transcribe --output-dir \"" + sDir + "\"", out sOut, out sErr, 600);
string sFolder = Path.Combine(sDir, Path.GetFileNameWithoutExtension(sSource));
string sDescribed = Path.Combine(sFolder, "described.md"), sTranscribed = Path.Combine(sFolder, "transcribed.md");
if (!File.Exists(sDescribed)) {
sError = "HomerScribe made no description (exit code " + iCode + ")";
Log.info("HomerScribe: " + (sErr + " " + sOut).Trim());
return false;
}
StringBuilder oMd = new StringBuilder("# " + Path.GetFileNameWithoutExtension(sSource) + "\r\n\r\n");
if (File.Exists(sTranscribed)) oMd.Append("## What is said\r\n\r\n" + demoted(decodeText(File.ReadAllBytes(sTranscribed))) + "\r\n\r\n");
oMd.Append("## What can be seen\r\n\r\n" + demoted(decodeText(File.ReadAllBytes(sDescribed))) + "\r\n");
File.WriteAllText(sMd, oMd.ToString(), new UTF8Encoding(true));
string sTo = typeOf(sTarget);
if (sTo == "md" || sTo == "txt") { File.Copy(sMd, sTarget, true); return true; }
return convert(sMd, sTarget, out sError);
}
catch (Exception oError) { sError = "HomerScribe could not be used: " + oError.Message; return false; }
finally { try { Directory.Delete(sDir, true); } catch (Exception) { } try { File.Delete(sMd); } catch (Exception) { } }
} // describeVideoTo method

// demoted: a document's headings moved down two levels, under "## What is said" or "## What can be
// seen", so the combined document keeps one outline.
private static string demoted(string sMarkdown) {
return System.Text.RegularExpressions.Regex.Replace(sMarkdown.Replace("\r\n", "\n"), @"(?m)^(#{1,4})(\s)", "##$1$2").Replace("\n", "\r\n").Trim();
} // demoted method

// transcribeTo: the words spoken in a recording, as a document of the target's type.
private static bool transcribeTo(string sSource, string sTarget, out string sError) {
sError = "";
string sFfmpeg = Media.ffmpegProgram();
if (sFfmpeg.Length == 0) { sError = "ffmpeg is not installed, and it is what takes the sound out for Whisper"; return false; }
string sWav = tempPath(sSource, ".wav");
string sMd = tempPath(sSource, ".md");
try {
string sOut, sErr;
int iCode = Media.run(sFfmpeg, "-nostdin -y -i \"" + sSource + "\" -vn -ar 16000 -ac 1 -c:a pcm_s16le \"" + sWav + "\"", out sOut, out sErr, 120);
if (iCode != 0 || !File.Exists(sWav)) { sError = "ffmpeg could not take the sound out (exit code " + iCode + ")"; Log.info("ffmpeg: " + sErr.Trim()); return false; }
// Six hours is the longest a recording may take to transcribe; Whisper runs at many times real time.
string sText = Voice.transcribe(sWav, 6 * 60 * 60 * 1000, out sError);
if (sText.Length == 0) { if (sError == "") sError = "Whisper heard no words"; return false; }
StringBuilder oMd = new StringBuilder("# Transcript of " + Path.GetFileNameWithoutExtension(sSource) + "\r\n\r\n");
string[] aSentences = System.Text.RegularExpressions.Regex.Split(sText, @"(?<=[.!?])\s+");
for (int i = 0; i < aSentences.Length; i += 5)
oMd.Append(string.Join(" ", aSentences, i, Math.Min(5, aSentences.Length - i)) + "\r\n\r\n");
File.WriteAllText(sMd, oMd.ToString(), new UTF8Encoding(true));
string sTo = typeOf(sTarget);
if (sTo == "md" || sTo == "txt") { File.Copy(sMd, sTarget, true); return true; }
return convert(sMd, sTarget, out sError);
}
finally { try { File.Delete(sWav); } catch (Exception) { } try { File.Delete(sMd); } catch (Exception) { } }
} // transcribeTo method

// speakTo: a document's words spoken by Windows' speech synthesis, as sound or as video.
// Reached by reflection, so no app's build needs a reference to System.Speech.
private static bool speakTo(string sSource, string sTarget, out string sError) {
sError = "";
string sFfmpeg = Media.ffmpegProgram();
if (sFfmpeg.Length == 0) { sError = "ffmpeg is not installed, and it is what encodes the speech"; return false; }
string sTxt = tempPath(sSource, ".txt");
string sWav = tempPath(sSource, ".wav");
try {
string sText;
string sType = typeOf(sSource);
if (sType == "txt" || sType == "md") sText = decodeText(File.ReadAllBytes(sSource));
else {
if (!convert(sSource, sTxt, out sError)) return false;
sText = decodeText(File.ReadAllBytes(sTxt));
}
if (sType == "md") sText = System.Text.RegularExpressions.Regex.Replace(sText, @"(?m)^#+\s*|[*_`>|]", "");
if (sText.Trim().Length == 0) { sError = "the document has no words to speak"; return false; }
Type oSynthType = Type.GetType("System.Speech.Synthesis.SpeechSynthesizer, System.Speech, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35");
if (oSynthType == null) { sError = "Windows speech synthesis is not available"; return false; }
object oSynth = Activator.CreateInstance(oSynthType);
try {
oSynthType.GetMethod("SetOutputToWaveFile", new Type[] { typeof(string) }).Invoke(oSynth, new object[] { sWav });
oSynthType.GetMethod("Speak", new Type[] { typeof(string) }).Invoke(oSynth, new object[] { sText });
oSynthType.GetMethod("SetOutputToNull").Invoke(oSynth, null);
}
finally { ((IDisposable) oSynth).Dispose(); }
if (!File.Exists(sWav) || new FileInfo(sWav).Length < 1000) { sError = "Windows speech synthesis made no sound"; return false; }
string sTo = typeOf(sTarget);
string sArgs;
if (Array.IndexOf(aSpeechVideoTargets, sTo) >= 0)
sArgs = "-nostdin -y -f lavfi -i color=c=black:s=1280x720:r=1 -i \"" + sWav + "\" -shortest "
+ (sTo == "webm" ? "-c:v libvpx-vp9 -c:a libopus " : "-c:v libx264 -tune stillimage -pix_fmt yuv420p -c:a aac ") + "\"" + sTarget + "\"";
else sArgs = "-nostdin -y -i \"" + sWav + "\" \"" + sTarget + "\"";
string sOut, sErr;
int iCode = Media.run(sFfmpeg, sArgs, out sOut, out sErr, 120);
if (iCode != 0 || !File.Exists(sTarget)) { sError = "ffmpeg could not encode the speech (exit code " + iCode + ")"; Log.info("ffmpeg: " + sErr.Trim()); return false; }
return true;
}
catch (Exception oError) { sError = "speech synthesis failed: " + (oError.InnerException != null ? oError.InnerException.Message : oError.Message); return false; }
finally { try { File.Delete(sTxt); } catch (Exception) { } try { File.Delete(sWav); } catch (Exception) { } }
} // speakTo method

static partial void mediaConvert(string sSource, string sTarget, ref bool bHandled, ref bool bMade, ref string sError) {
string sCategory = "";
mediaCategory(Path.GetExtension(sSource).ToLowerInvariant(), ref sCategory);
string sToType = typeOf(sTarget);
if (sCategory == "video" && Array.IndexOf(aTranscriptTargets, sToType) >= 0) {
bHandled = true;
bMade = describeVideoTo(sSource, sTarget, out sError);
if (!bMade) { Log.info("Described video: " + sError + "; the transcript alone instead"); bMade = transcribeTo(sSource, sTarget, out sError); }
return;
}
if (sCategory == "audio" && Array.IndexOf(aTranscriptTargets, sToType) >= 0) {
bHandled = true; bMade = transcribeTo(sSource, sTarget, out sError); return;
}
if (sCategory == "" && (Array.IndexOf(aSpeechAudioTargets, sToType) >= 0 || Array.IndexOf(aSpeechVideoTargets, sToType) >= 0) && textAvailable(sSource)) {
bHandled = true; bMade = speakTo(sSource, sTarget, out sError); return;
}
if (sCategory == "") return;
bHandled = true;
bMade = convertMedia(sSource, sTarget, out sError);
} // mediaConvert method

private static bool convertWithMagick(string sSource, string sTarget, out string sError) {
// ImageMagick, for the pictures ffmpeg cannot reach.
//
//   magick "in.heic" "out.jpg"
//
// The command works out both formats from the two names, as ffmpeg does, so
// nothing else has to be passed. Two exceptions are worth the extra option.
sError = "";
string sExe = Media.magickProgram();
if (sExe.Length == 0) {
string sExt = Path.GetExtension(sSource).ToLower();
sError = "ImageMagick was not found, and it is what reads " + sExt + " files. "
+ "Install the program again and tick the image tools box. ffmpeg cannot read this format.";
return false;
}
StringBuilder sbArgs = new StringBuilder();
string sSourceExt = Path.GetExtension(sSource).ToLower();
string sWantExt = Path.GetExtension(sTarget).ToLower();

// A drawing has no size of its own until it is drawn, and ImageMagick's default
// of 72 dots per inch turns a full page into a postage stamp.
if (sSourceExt == ".svg") sbArgs.Append("-density 300 ");

sbArgs.Append(Util.stringQuote(sSource));

// A raw file, a PSD and an animated GIF all hold several images, and without
// this every one of them is written as its own numbered file. The first is the
// picture; the rest are thumbnails and layers.
if (sSourceExt != ".gif" && sWantExt != ".gif" && sWantExt != ".ico")
sbArgs.Append("[0]");

// An icon holds several sizes, and Windows picks the one it needs. Written
// without this, it holds whatever size the source happened to be.
if (sWantExt == ".ico") sbArgs.Append(" -define icon:auto-resize=256,128,64,48,32,16");
// A format with no transparency needs something behind a transparent picture,
// or the clear parts come out black.
if (sWantExt == ".jpg" || sWantExt == ".jpeg" || sWantExt == ".bmp")
sbArgs.Append(" -background white -flatten");

sbArgs.Append(" ");
sbArgs.Append(Util.stringQuote(sTarget));
string sOut, sErr;
int iCode = Media.run(sExe, sbArgs.ToString(), out sOut, out sErr, iConverterMinutes);
if (iCode == 0 && File.Exists(sTarget)) return true;
sError = firstLine((sErr + "\n" + sOut).Trim());
if (sError.Length == 0) sError = "ImageMagick returned " + iCode + ".";
return false;
} // convertWithMagick method

private static bool convertMedia(string sSource, string sTarget, out string sError) {
// ffmpeg works out both formats from the two file names, so the command stays
// short and the same line serves audio, video and pictures.
//
//   -y            overwrite without asking; the caller already made the name unique
//   -nostdin      never wait for a keypress, which would hang a batch for ever
//   -loglevel     errors only, since nothing reads the progress here
//   -vn           on an audio target from a video, or ffmpeg tries to carry the
//                 pictures into a file that cannot hold them
sError = "";
string sSourceExt = Path.GetExtension(sSource).ToLower();
string sWantExt = Path.GetExtension(sTarget).ToLower();

// WHICH TOOL. ImageMagick when either end is a format ffmpeg cannot handle,
// ffmpeg otherwise. ffmpeg stays the default for the ordinary picture formats
// because it is already installed and already ticked; ImageMagick is asked for
// only when it is the only one that can do the job.
bool bNeedMagick = Array.IndexOf(aMagickSources, sSourceExt) >= 0
|| Array.IndexOf(aMagickSources, sWantExt) >= 0;
if (bNeedMagick) return convertWithMagick(sSource, sTarget, out sError);

string sExe = Media.ffmpegProgram();
if (sExe.Length == 0) {
sError = "ffmpeg was not found, so audio, video and pictures cannot be converted. Install the program again and tick the media tools box.";
return false;
}
string sTargetExt = Path.GetExtension(sTarget).ToLower();
bool bAudioTarget = Array.IndexOf(aAudioSources, sTargetExt) >= 0;
StringBuilder sbArgs = new StringBuilder();
sbArgs.Append("-y -nostdin -loglevel error -i ");
sbArgs.Append(Util.stringQuote(sSource));
if (bAudioTarget && categoryOf(sSource) == "video") sbArgs.Append(" -vn");
sbArgs.Append(" ");
sbArgs.Append(Util.stringQuote(sTarget));
string sOut, sErr;
int iCode = Media.run(sExe, sbArgs.ToString(), out sOut, out sErr, iConverterMinutes);
if (iCode == 0 && File.Exists(sTarget)) return true;
sError = sErr.Trim();
if (sError.Length == 0) sError = "ffmpeg returned " + iCode + ".";
// ffmpeg is talkative when it fails; the first line is the useful one.
int iBreak = sError.IndexOf('\n');
if (iBreak > 0) sError = sError.Substring(0, iBreak).Trim();
return false;
} // convertMedia method

} // Conversion class

} // namespace Homer
