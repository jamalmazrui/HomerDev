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

// demoted: a document's headings moved down two levels, under "## What is said" or "## What can be
// seen", so the combined document keeps one outline.
private static string demoted(string sMarkdown) {
return System.Text.RegularExpressions.Regex.Replace(sMarkdown.Replace("\r\n", "\n"), @"(?m)^(#{1,4})(\s)", "##$1$2").Replace("\n", "\r\n").Trim();
} // demoted method

// THE MEDIA SCRIPT (kit 1.219.0, the author's request of 12 November 2026): HomerScribe's transcribing and describing,
// now the kit's, so BatCon and every Homer app transcribe and describe with no other Homer app installed. Held word
// for word in conversion.py as sMediaScript; the kit's build fails if the two differ.
public const string sMediaScript =
@"import base64, glob, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request
# THE MEDIA SCRIPT (kit 1.219.0, the author's request of 12 November 2026): what HomerScribe did, now the kit's, so
# BatCon and every Homer app transcribe and describe with no other Homer app installed. Both languages run THIS SAME
# SCRIPT, held word for word in conversion.py and Conversion.cs as sMediaScript; the kit's build fails if they differ.
#   python <script> <source> <target>
#   sound to a text target: the transcript, as Markdown, paragraphs by pause, a time heading every five minutes
#   video to a text target:  what is said and what is seen, in time order, a heading at each scene, as Markdown
#   video to a sound target: the sound with each scene's description spoken in a pause made for it -- extended
#                            description, so the programme is never talked over -- at the end of a sentence
# A text target is written as Markdown at the target's path; the caller turns it into .docx, .htm, .pdf and the rest
# by the kit's own conversion, so every transcript is as accessible as anything else the kit makes.
# Tools, all machine-wide and approved: ffmpeg; Whisper (whisper-cli) for speech; Ollama's local vision model for
# pictures, over its local web interface, never its command; Windows speech for the spoken descriptions.
lsAudio = ['aac', 'aif', 'aiff', 'flac', 'm4a', 'mp3', 'ogg', 'opus', 'wav', 'wma']
lsVideo = ['3gp', 'avi', 'flv', 'm2ts', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ogv', 'ts', 'webm', 'wmv']
lsVisionModels = ['qwen2.5vl', 'gemma3', 'llama3.2-vision', 'llava', 'minicpm-v', 'moondream']
iNoWindow = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
sOllama = 'http://127.0.0.1:11434'


def note(sText):
    sys.stderr.write(time.strftime('%H:%M:%S ') + sText + '\n'); sys.stderr.flush()


def tool(lsCommand, iMinutes):
    oDone = subprocess.run(lsCommand, capture_output=True, text=True, errors='replace', timeout=iMinutes * 60, creationflags=iNoWindow)
    if oDone.returncode != 0: raise RuntimeError('%s failed (exit code %d): %s' % (os.path.basename(lsCommand[0]), oDone.returncode, (oDone.stderr or oDone.stdout).strip()[-300:]))
    return (oDone.stdout or '') + (oDone.stderr or '')


def findProgram(sName, lsPlaces):
    for sPath in lsPlaces:
        if sPath and os.path.isfile(sPath): return sPath
    return shutil.which(sName) or ''


def ffmpegPath():
    sFiles, sLocal = os.environ.get('ProgramFiles', r'C:\Program Files'), os.environ.get('LOCALAPPDATA', '')
    return findProgram('ffmpeg', [os.path.join(sFiles, 'ffmpeg', 'bin', 'ffmpeg.exe'), os.path.join(sLocal, 'Microsoft', 'WinGet', 'Links', 'ffmpeg.exe')])


def whisperPaths():
    sProgram = findProgram('whisper-cli', [os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'Whisper', 'whisper-cli.exe')])
    if not sProgram: return '', ''
    lsModels = [s for s in sorted(glob.glob(os.path.join(os.path.dirname(sProgram), 'ggml-*.bin'))) if 'silero' not in os.path.basename(s).lower()]
    lsModels.sort(key=lambda s: (0 if 'large-v3-turbo' in s else 1 if 'large' in s else 2 if 'medium' in s else 3))
    return sProgram, (lsModels[0] if lsModels else '')


def seconds(sClock):
    h, m, s = sClock.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def clock(nSeconds):
    i = int(nSeconds); h, m, s = i // 3600, (i % 3600) // 60, i % 60
    return '%d:%02d:%02d' % (h, m, s) if h else '%d:%02d' % (m, s)


def speech(sSource, sWork):
    """"""[(start, end, words)] for what is said, by Whisper; [] when nothing is said.""""""
    sFfmpeg = ffmpegPath()
    if not sFfmpeg: raise RuntimeError('ffmpeg is not installed, and it is what takes the sound out')
    sProgram, sModel = whisperPaths()
    if not sProgram: raise RuntimeError(""Whisper is not installed; HomerDev's setup program offers it"")
    if not sModel: raise RuntimeError(""Whisper has no speech model; run HomerDev's setup program again and leave Whisper marked"")
    sWav = os.path.join(sWork, 'sound.wav')
    note('Taking the sound out.')
    tool([sFfmpeg, '-nostdin', '-y', '-i', sSource, '-vn', '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', sWav], 240)
    note('Listening with Whisper; a long recording takes a while.')
    sBase = os.path.join(sWork, 'words')
    tool([sProgram, '-m', sModel, '-f', sWav, '-l', 'auto', '-osrt', '-of', sBase, '-np'], 600)
    sSrt = open(sBase + '.srt', encoding='utf-8', errors='replace').read() if os.path.isfile(sBase + '.srt') else ''
    lOut = []
    for oCue in re.finditer(r'(\d+:\d+:\d+[,.]\d+)\s*-->\s*(\d+:\d+:\d+[,.]\d+)\s*\n(.*?)(?:\n\s*\n|\Z)', sSrt.replace('\r\n', '\n'), re.S):
        sWords = re.sub(r'\s+', ' ', oCue.group(3)).strip()
        if sWords and not re.fullmatch(r'\[[^\]]*\]|\([^)]*\)', sWords): lOut.append((seconds(oCue.group(1)), seconds(oCue.group(2)), sWords))
    note('%d stretches of speech heard.' % len(lOut))
    return lOut


def visionModel():
    try:
        with urllib.request.urlopen(sOllama + '/api/tags', timeout=10) as oResponse: lsNames = [d.get('name', '') for d in json.load(oResponse).get('models', [])]
    except Exception:
        raise RuntimeError(""Ollama is not running, and it is what describes pictures; HomerDev's setup program offers it"")
    for sWant in lsVisionModels:
        for sName in lsNames:
            if sName == sWant or sName.startswith(sWant + ':'): return sName
    raise RuntimeError('Ollama has no model that sees pictures; one such as %s is needed' % lsVisionModels[0])


def scenes(sSource, sWork):
    """"""[(time, picture)] at each change of scene, at least one every 30 seconds, never two within 6.""""""
    sFfmpeg = ffmpegPath()
    sDir = os.path.join(sWork, 'frames'); os.makedirs(sDir, exist_ok=True)
    sSelect = ""select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,30)+gt(scene\\,0.3)*gte(t-prev_selected_t\\,6)',scale=768:-2,showinfo""
    note('Finding the scenes.')
    sLog = tool([sFfmpeg, '-nostdin', '-y', '-i', sSource, '-vf', sSelect, '-vsync', 'vfr', '-q:v', '4', os.path.join(sDir, 'f%05d.jpg')], 600)
    lnTimes = [float(s) for s in re.findall(r'pts_time:([\d.]+)', sLog)]
    lsFiles = sorted(glob.glob(os.path.join(sDir, 'f*.jpg')))
    note('%d scenes to look at.' % min(len(lnTimes), len(lsFiles)))
    return list(zip(lnTimes, lsFiles))


def describe(sModel, sPicture, sBefore):
    sPrompt = ('You describe a video for a listener who is blind. In one to three plain sentences, in the present tense, say what '
               'can be seen in this frame that matters: the people, what they do, the setting, and any words shown on screen. '
               'Do not begin with ""The image shows"" or anything like it. ' + ('Just before, the listener heard: ""%s"". If nothing '
               'that matters has changed since then, answer only SAME.' % sBefore if sBefore else ''))
    dBody = {'model': sModel, 'prompt': sPrompt, 'images': [base64.b64encode(open(sPicture, 'rb').read()).decode('ascii')], 'stream': False}
    oRequest = urllib.request.Request(sOllama + '/api/generate', data=json.dumps(dBody).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(oRequest, timeout=600) as oResponse: sText = json.load(oResponse).get('response', '').strip()
    sText = re.sub(r'^(?:the |this )?(?:image|picture|frame|scene|screenshot)\s+(?:shows|depicts|displays)\s+', '', sText, flags=re.I)
    return sText[:1].upper() + sText[1:] if sText else ''


def descriptions(sSource, sWork):
    """"""[(time, words)] for what is seen, a scene that has not changed left out.""""""
    sModel = visionModel()
    lScenes, lOut, sBefore, nStarted = scenes(sSource, sWork), [], '', time.time()
    for i, (nTime, sPicture) in enumerate(lScenes, 1):
        sText = describe(sModel, sPicture, sBefore)
        if sText and not re.fullmatch(r'same\.?', sText.strip(), re.I): lOut.append((nTime, sText)); sBefore = sText
        if time.time() - nStarted > 10 or i == len(lScenes):
            note('Described %d of %d scenes, %d%%.' % (i, len(lScenes), 100 * i // max(1, len(lScenes)))); nStarted = time.time()
    return lOut


def paragraphs(lSpeech):
    """"""Speech as paragraphs: a new one after a pause of two seconds or more, or once one runs past 600 characters.""""""
    lOut, sNow, nEnd = [], '', None
    for nStart, nStop, sWords in lSpeech:
        if sNow and (nStart - nEnd >= 2 or len(sNow) > 600): lOut.append(sNow); sNow = ''
        sNow = (sNow + ' ' + sWords).strip(); nEnd = nStop
    return lOut + ([sNow] if sNow else [])


def transcript(sTitle, lSpeech):
    lsOut = ['# ' + sTitle, '', 'What is said in the recording, as heard by Whisper.', '']
    nLength = lSpeech[-1][1] if lSpeech else 0
    if nLength <= 600:
        lsOut += [s + '\n' for s in paragraphs(lSpeech)]
        return '\n'.join(lsOut)
    for iBlock in range(0, int(nLength // 300) + 1):
        lPart = [t for t in lSpeech if iBlock * 300 <= t[0] < (iBlock + 1) * 300]
        if lPart: lsOut += ['## ' + clock(iBlock * 300), ''] + [s + '\n' for s in paragraphs(lPart)]
    return '\n'.join(lsOut)


def integrated(sTitle, lSpeech, lSeen):
    """"""What is said and what is seen, in time order: a heading at each described scene, its description, then the
    speech until the next one. Speech before the first scene sits under 0:00.""""""
    lsOut = ['# ' + sTitle, '', 'What is said and what can be seen, in time order. Each heading is the time a scene begins; '
             '""Seen"" is what a vision model saw there, and the paragraphs after it are what is said.', '']
    lnMarks = [0.0] + [t for t, _ in lSeen if t > 0]
    dSeen = dict(lSeen)
    for i, nMark in enumerate(lnMarks):
        nNext = lnMarks[i + 1] if i + 1 < len(lnMarks) else float('inf')
        lPart = [t for t in lSpeech if nMark <= t[0] < nNext]
        sSeen = dSeen.get(nMark, '')
        if not sSeen and not lPart: continue
        lsOut += ['## ' + clock(nMark), '']
        if sSeen: lsOut += ['*Seen:* ' + sSeen, '']
        lsOut += [s + '\n' for s in paragraphs(lPart)]
    return '\n'.join(lsOut)


def speak(sText, sWav):
    sTxt = sWav + '.txt'
    open(sTxt, 'w', encoding='utf-8-sig').write(sText)
    sScript = (""Add-Type -AssemblyName System.Speech; $o = New-Object System.Speech.Synthesis.SpeechSynthesizer; ""
               ""$o.SetOutputToWaveFile('%s'); $o.Speak([IO.File]::ReadAllText('%s')); $o.SetOutputToNull(); $o.Dispose()""
               % (sWav.replace(""'"", ""''""), sTxt.replace(""'"", ""''"")))
    tool(['powershell', '-NoProfile', '-NonInteractive', '-Command', sScript], 5)


def insertionPoints(lSpeech, lSeen):
    """"""Each description's place: its scene's time, moved to the end of the sentence being spoken there.""""""
    lOut = []
    for nTime, sText in lSeen:
        for nStart, nStop, _ in lSpeech:
            if nStart < nTime < nStop: nTime = nStop; break
        lOut.append((nTime, sText))
    return sorted(lOut)


def describedSound(sSource, sTarget, lSpeech, lSeen, sWork):
    sFfmpeg = ffmpegPath()
    sAll = os.path.join(sWork, 'all.wav')
    tool([sFfmpeg, '-nostdin', '-y', '-i', sSource, '-vn', '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', sAll], 240)
    lsParts, nFrom = [], 0.0
    for i, (nAt, sText) in enumerate(insertionPoints(lSpeech, lSeen)):
        if nAt > nFrom:
            sPart = os.path.join(sWork, 'part%05d.wav' % (2 * i))
            tool([sFfmpeg, '-nostdin', '-y', '-ss', '%.3f' % nFrom, '-to', '%.3f' % nAt, '-i', sAll, '-c:a', 'pcm_s16le', sPart], 30)
            lsParts.append(sPart)
        sSaid, sSaid2 = os.path.join(sWork, 'said%05d.wav' % i), os.path.join(sWork, 'part%05d.wav' % (2 * i + 1))
        speak(sText, sSaid)
        tool([sFfmpeg, '-nostdin', '-y', '-i', sSaid, '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', sSaid2], 5)
        lsParts.append(sSaid2); nFrom = nAt
    sRest = os.path.join(sWork, 'rest.wav')
    tool([sFfmpeg, '-nostdin', '-y', '-ss', '%.3f' % nFrom, '-i', sAll, '-c:a', 'pcm_s16le', sRest], 30)
    lsParts.append(sRest)
    sList = os.path.join(sWork, 'parts.txt')
    open(sList, 'w', encoding='utf-8').write(''.join(""file '%s'\n"" % s.replace(""'"", ""'\\''"") for s in lsParts))
    note('Joining the sound and %d spoken descriptions.' % len(lSeen))
    tool([sFfmpeg, '-nostdin', '-y', '-f', 'concat', '-safe', '0', '-i', sList, sTarget], 120)


def main():
    sSource, sTarget = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    sFrom, sTo = os.path.splitext(sSource)[1].lower().lstrip('.'), os.path.splitext(sTarget)[1].lower().lstrip('.')
    sTitle = os.path.splitext(os.path.basename(sSource))[0].replace('_', ' ')
    sWork = tempfile.mkdtemp(prefix='homerMedia-')
    try:
        if sFrom in lsVideo and sTo in lsAudio:
            lSpeech = speech(sSource, sWork)
            describedSound(sSource, sTarget, lSpeech, descriptions(sSource, sWork), sWork)
        elif sFrom in lsVideo:
            lSpeech = speech(sSource, sWork)
            try: lSeen = descriptions(sSource, sWork)
            except Exception as oError: note('No descriptions: %s; the transcript alone.' % oError); lSeen = []
            if not lSpeech and not lSeen: raise RuntimeError('nothing was heard or seen')
            open(sTarget, 'w', encoding='utf-8-sig', newline='\r\n').write(integrated(sTitle, lSpeech, lSeen) if lSeen else transcript(sTitle, lSpeech))
        elif sFrom in lsAudio:
            lSpeech = speech(sSource, sWork)
            if not lSpeech: raise RuntimeError('Whisper heard no words')
            open(sTarget, 'w', encoding='utf-8-sig', newline='\r\n').write(transcript(sTitle, lSpeech))
        else:
            raise RuntimeError('%s is neither sound nor video' % os.path.basename(sSource))
    except Exception as oError:
        sys.stderr.write(str(oError) + '\n'); sys.exit(1)
    finally:
        shutil.rmtree(sWork, ignore_errors=True)


if __name__ == '__main__':
    main()
";

// mediaScriptTo: sound or video to a document, or video to described sound, by the media script. A text target is
// made as Markdown, then by the kit's own conversion, so a transcript is as accessible as anything else the kit makes.
// Ten hours at most, as HomerScribe had: a long film is described scene by scene by a local vision model.
private static bool mediaScriptTo(string sSource, string sTarget, out string sError) {
sError = "";
string sPython = pythonProgram();
if (sPython == "") { sError = "Python is not installed; installPdfTools.cmd installs it"; return false; }
string sToType = typeOf(sTarget);
bool bText = Array.IndexOf(aTranscriptTargets, sToType) >= 0;
string sMade = bText ? tempPath(sSource, ".md") : sTarget;
string sScript = Path.Combine(Path.GetTempPath(), "homerMedia_" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".py");
try {
File.WriteAllText(sScript, sMediaScript, new UTF8Encoding(false));
string sOut, sErr;
int iCode = Media.run(sPython, Util.stringQuote(sScript) + " " + Util.stringQuote(sSource) + " " + Util.stringQuote(sMade), out sOut, out sErr, 600);
foreach (string sLine in (sErr ?? "").Split('\n')) if (sLine.Trim().Length > 0) Log.info("media: " + sLine.Trim());
if (iCode != 0 || !File.Exists(sMade)) { sError = lastLine(sErr ?? "") ; if (sError == "") sError = "the media script failed (exit code " + iCode + ")"; return false; }
if (!bText) return true;
if (sToType == "md" || sToType == "txt") { File.Copy(sMade, sTarget, true); return true; }
return convert(sMade, sTarget, out sError);
}
catch (Exception oError) { sError = "the media script could not run: " + oError.Message; return false; }
finally { try { File.Delete(sScript); } catch (Exception) { } if (bText) try { File.Delete(sMade); } catch (Exception) { } }
} // mediaScriptTo method



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
// SOUND AND VIDEO TO WORDS, AND VIDEO TO DESCRIBED SOUND (kit 1.219.0): sound to a document is its transcript;
// video to a document is what is said and seen, in time order; video to sound is the sound with each scene described
// in a pause made for it. A video that cannot be described still gives its sound, and the reason is logged.
if ((sCategory == "audio" || sCategory == "video") && Array.IndexOf(aTranscriptTargets, sToType) >= 0) {
bHandled = true; bMade = mediaScriptTo(sSource, sTarget, out sError); return;
}
if (sCategory == "video" && Array.IndexOf(new string[] { "aac", "flac", "m4a", "mp3", "ogg", "opus", "wav", "wma" }, sToType) >= 0) {
bHandled = true;
bMade = mediaScriptTo(sSource, sTarget, out sError);
if (bMade) return;
Log.info("Described sound: " + sError + "; the sound alone instead");
bMade = convertMedia(sSource, sTarget, out sError); return;
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
+ "Install the program again and mark the image tools box. ffmpeg cannot read this format.";
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
// because it is already installed and already marked; ImageMagick is asked for
// only when it is the only one that can do the job.
bool bNeedMagick = Array.IndexOf(aMagickSources, sSourceExt) >= 0
|| Array.IndexOf(aMagickSources, sWantExt) >= 0;
if (bNeedMagick) return convertWithMagick(sSource, sTarget, out sError);

string sExe = Media.ffmpegProgram();
if (sExe.Length == 0) {
sError = "ffmpeg was not found, so audio, video and pictures cannot be converted. Install the program again and mark the media tools box.";
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
