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
{"FLAC audio, lossless", "flac"}, {"Ogg Vorbis audio", "ogg"}, {"Opus audio", "opus"}, {"Play list of these files", "m3u"}};
else if (sCategory == "video")
aTargets = new string[,] {{"MP4 video", "mp4"}, {"Matroska video", "mkv"}, {"WebM video", "webm"}, {"QuickTime video", "mov"},
{"AVI video", "avi"}, {"MP3 audio, sound only", "mp3"}, {"M4A audio, sound only", "m4a"}, {"WAV audio, sound only", "wav"},
{"Play list of these files", "m3u"}};
else if (sCategory == "image")
aTargets = new string[,] {{"PNG image", "png"}, {"JPEG image", "jpg"}, {"WebP image", "webp"}, {"BMP image", "bmp"},
{"GIF image", "gif"}, {"TIFF image", "tif"}, {"Windows icon", "ico"}, {"AVIF image", "avif"}};
} // mediaTargets method

static partial void mediaConvert(string sSource, string sTarget, ref bool bHandled, ref bool bMade, ref string sError) {
string sCategory = "";
mediaCategory(Path.GetExtension(sSource).ToLowerInvariant(), ref sCategory);
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
