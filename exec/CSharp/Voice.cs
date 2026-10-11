// Voice.cs -- Homer shared class: record a spoken question and turn it into text, all on this computer.
//
// Copyright 2026 by Jamal Mazrui
// MIT License. See License.md, which carries the terms in full.
//
// WHAT IT IS FOR
//
// A screen reader user asks a question aloud instead of typing it. VoiceRecorder records from the default
// microphone through Windows' own audio input (winmm's waveIn, present on every Windows), and knows when the person
// has finished: after they have spoken, a stretch of silence ends the recording, as Windows' own voice typing does.
// Voice.transcribe then hands the recording to Whisper (whisper.cpp's whisper-cli), which the Homer installers offer
// as a component and which runs locally, so nothing said leaves the computer.
//
// WHY NOT A WAKE WORD (researched 11 October 2026). Starting by a spoken word needs a wake-word model. The free one,
// openWakeWord, ships its trained models under CC BY-NC-SA 4.0, which forbids commercial use and so does not fit the
// kit's MIT license; the strong alternatives are commercial. So recording starts by a key, and stops by the same key,
// by silence, or by Escape to throw it away -- the convention of Windows+H voice typing.
//
// HOW SILENCE IS JUDGED. The first fifth of a second sets the room's noise floor; speech is a tenth of a second whose
// loudness (root mean square) is well above that floor; once speech has been heard, a stretch of quiet as long as
// SilenceMilliseconds ends the recording. No model is needed for that, and it reacts within a tenth of a second.
//
// POLLED, NOT CALLED BACK. The recorder is driven by poll(), from a WinForms timer on the window's own thread, rather
// than by winmm calling back on a thread of its own: no locking, and nothing touches the window from elsewhere.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace Homer {

public class VoiceRecorder : IDisposable {

private const int c_iBitsPerSample = 16;
private const int c_iBufferCount = 10;
private const int c_iBufferMilliseconds = 100;
private const int c_iChannels = 1;
private const int c_iFloorMilliseconds = 200;
private const int c_iSampleRate = 16000;
private const int c_iWaveMapper = -1;
private const int c_iWhdrDone = 1;

public int MaxMilliseconds = 60000;
public int SilenceMilliseconds = 1500;

[StructLayout(LayoutKind.Sequential, Pack = 2)]
private struct WaveFormatEx {
    public short wFormatTag;
    public short nChannels;
    public int nSamplesPerSec;
    public int nAvgBytesPerSec;
    public short nBlockAlign;
    public short wBitsPerSample;
    public short cbSize;
}

[StructLayout(LayoutKind.Sequential)]
private struct WaveHdr {
    public IntPtr lpData;
    public int dwBufferLength;
    public int dwBytesRecorded;
    public IntPtr dwUser;
    public int dwFlags;
    public int dwLoops;
    public IntPtr lpNext;
    public IntPtr reserved;
}

[DllImport("winmm.dll")] private static extern int waveInOpen(out IntPtr hWaveIn, int iDeviceId, ref WaveFormatEx oFormat, IntPtr pCallback, IntPtr pInstance, int iFlags);
[DllImport("winmm.dll")] private static extern int waveInPrepareHeader(IntPtr hWaveIn, IntPtr pHdr, int iSize);
[DllImport("winmm.dll")] private static extern int waveInUnprepareHeader(IntPtr hWaveIn, IntPtr pHdr, int iSize);
[DllImport("winmm.dll")] private static extern int waveInAddBuffer(IntPtr hWaveIn, IntPtr pHdr, int iSize);
[DllImport("winmm.dll")] private static extern int waveInStart(IntPtr hWaveIn);
[DllImport("winmm.dll")] private static extern int waveInStop(IntPtr hWaveIn);
[DllImport("winmm.dll")] private static extern int waveInReset(IntPtr hWaveIn);
[DllImport("winmm.dll")] private static extern int waveInClose(IntPtr hWaveIn);

private bool bHeardSpeech;
private bool bOpen;
private double nFloor;
private IntPtr hWaveIn = IntPtr.Zero;
private int iElapsedMs, iFloorSamples, iHdrSize, iQuietMs;
private List<IntPtr> lpData = new List<IntPtr>();
private List<IntPtr> lpHdr = new List<IntPtr>();
private MemoryStream oPcm = new MemoryStream();

public bool HeardSpeech { get { return bHeardSpeech; } }
public bool IsRecording { get { return bOpen; } }

// start: opens the default microphone and begins recording. Returns "" or what went wrong, in words.
public string start() {
    WaveFormatEx oFormat = new WaveFormatEx();
    int iBytes, iCode;
    oFormat.wFormatTag = 1;
    oFormat.nChannels = c_iChannels;
    oFormat.nSamplesPerSec = c_iSampleRate;
    oFormat.wBitsPerSample = c_iBitsPerSample;
    oFormat.nBlockAlign = (short) (c_iChannels * c_iBitsPerSample / 8);
    oFormat.nAvgBytesPerSec = c_iSampleRate * oFormat.nBlockAlign;
    oFormat.cbSize = 0;
    iCode = waveInOpen(out hWaveIn, c_iWaveMapper, ref oFormat, IntPtr.Zero, IntPtr.Zero, 0);
    if (iCode != 0) return "the microphone could not be opened (waveInOpen error " + iCode + "); check that one is connected and that Windows lets apps use it";
    iHdrSize = Marshal.SizeOf(typeof(WaveHdr));
    iBytes = oFormat.nAvgBytesPerSec * c_iBufferMilliseconds / 1000;
    for (int i = 0; i < c_iBufferCount; i++) {
        IntPtr pData = Marshal.AllocHGlobal(iBytes);
        IntPtr pHdr = Marshal.AllocHGlobal(iHdrSize);
        lpData.Add(pData);
        lpHdr.Add(pHdr);
        queueBuffer(pHdr, pData, iBytes);
    }
    iCode = waveInStart(hWaveIn);
    if (iCode != 0) { freeAll(); return "recording could not start (waveInStart error " + iCode + ")"; }
    bOpen = true;
    Log.info("Voice: recording started, " + c_iSampleRate + " Hz mono, silence ends it after " + SilenceMilliseconds + " ms");
    return "";
}

private bool queueBuffer(IntPtr pHdr, IntPtr pData, int iBytes) {
    WaveHdr oHdr = new WaveHdr();
    oHdr.lpData = pData;
    oHdr.dwBufferLength = iBytes;
    Marshal.StructureToPtr(oHdr, pHdr, false);
    waveInPrepareHeader(hWaveIn, pHdr, iHdrSize);
    return waveInAddBuffer(hWaveIn, pHdr, iHdrSize) == 0;
}

// poll: gathers what the microphone has recorded since the last call, and judges speech and silence. Call it every
// tenth of a second while recording. Returns true when the recording should end: silence after speech, or the cap.
public bool poll() {
    if (!bOpen) return false;
    harvest(true);
    if (bHeardSpeech && iQuietMs >= SilenceMilliseconds) { Log.info("Voice: " + iQuietMs + " ms of silence after speech; ending"); return true; }
    if (iElapsedMs >= MaxMilliseconds) { Log.info("Voice: the " + MaxMilliseconds + " ms limit was reached; ending"); return true; }
    return false;
}

// harvest: copies every filled buffer into the recording and judges it; with bRequeue, hands each buffer back to the
// microphone. The final harvest, after the microphone is reset, does not requeue: a buffer queued then could still
// be held by Windows when its memory is freed.
private bool harvest(bool bRequeue) {
    int iFlagsAt = (int) Marshal.OffsetOf(typeof(WaveHdr), "dwFlags");
    int iRecordedAt = (int) Marshal.OffsetOf(typeof(WaveHdr), "dwBytesRecorded");
    for (int i = 0; i < lpHdr.Count; i++) {
        IntPtr pHdr = lpHdr[i];
        if ((Marshal.ReadInt32(pHdr, iFlagsAt) & c_iWhdrDone) == 0) continue;
        int iGot = Marshal.ReadInt32(pHdr, iRecordedAt);
        byte[] aChunk = new byte[iGot];
        if (iGot > 0) Marshal.Copy(lpData[i], aChunk, 0, iGot);
        oPcm.Write(aChunk, 0, iGot);
        judge(aChunk);
        Marshal.WriteInt32(pHdr, iFlagsAt, Marshal.ReadInt32(pHdr, iFlagsAt) & ~c_iWhdrDone);
        if (!bRequeue) continue;
        int iLength = Marshal.ReadInt32(pHdr, (int) Marshal.OffsetOf(typeof(WaveHdr), "dwBufferLength"));
        waveInUnprepareHeader(hWaveIn, pHdr, iHdrSize);
        queueBuffer(pHdr, lpData[i], iLength);
    }
    return true;
}

// judge: one chunk's loudness against the room's noise floor.
private bool judge(byte[] aChunk) {
    int iSamples = aChunk.Length / 2;
    if (iSamples == 0) return false;
    double nSum = 0;
    for (int i = 0; i + 1 < aChunk.Length; i += 2) {
        short iValue = (short) (aChunk[i] | (aChunk[i + 1] << 8));
        nSum += (double) iValue * iValue;
    }
    double nRms = Math.Sqrt(nSum / iSamples);
    int iMs = iSamples * 1000 / c_iSampleRate;
    iElapsedMs += iMs;
    if (iFloorSamples < c_iFloorMilliseconds) { nFloor = Math.Max(nFloor, nRms); iFloorSamples += iMs; return false; }
    bool bLoud = nRms > Math.Max(nFloor * 3, 500);
    if (bLoud) { if (!bHeardSpeech) Log.info("Voice: speech heard at " + iElapsedMs + " ms"); bHeardSpeech = true; iQuietMs = 0; }
    else if (bHeardSpeech) iQuietMs += iMs;
    return bLoud;
}

// stop: ends the recording and writes it as a WAV file in sFolder. Returns the file's path, or "" when nothing was
// recorded.
public string stop(string sFolder) {
    if (!bOpen) return "";
    harvest(true);
    waveInStop(hWaveIn);
    waveInReset(hWaveIn);
    harvest(false);
    freeAll();
    if (oPcm.Length == 0) return "";
    Directory.CreateDirectory(sFolder);
    string sPath = Path.Combine(sFolder, "voice-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".wav");
    writeWave(sPath, oPcm.ToArray());
    Log.info("Voice: recorded " + iElapsedMs + " ms into " + sPath);
    return sPath;
}

// cancel: ends the recording and keeps nothing.
public bool cancel() {
    if (bOpen) { waveInStop(hWaveIn); waveInReset(hWaveIn); freeAll(); }
    oPcm.SetLength(0);
    Log.info("Voice: recording cancelled");
    return true;
}

private bool freeAll() {
    if (hWaveIn != IntPtr.Zero) {
        // Reset first, so Windows returns every buffer it holds before any is unprepared or freed.
        waveInReset(hWaveIn);
        foreach (IntPtr pHdr in lpHdr) waveInUnprepareHeader(hWaveIn, pHdr, iHdrSize);
        waveInClose(hWaveIn);
        hWaveIn = IntPtr.Zero;
    }
    foreach (IntPtr p in lpHdr) Marshal.FreeHGlobal(p);
    foreach (IntPtr p in lpData) Marshal.FreeHGlobal(p);
    lpHdr.Clear();
    lpData.Clear();
    bOpen = false;
    return true;
}

private static bool writeWave(string sPath, byte[] aPcm) {
    using (BinaryWriter w = new BinaryWriter(File.Create(sPath))) {
        int iBlock = c_iChannels * c_iBitsPerSample / 8;
        w.Write(Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + aPcm.Length); w.Write(Encoding.ASCII.GetBytes("WAVE"));
        w.Write(Encoding.ASCII.GetBytes("fmt ")); w.Write(16); w.Write((short) 1); w.Write((short) c_iChannels);
        w.Write(c_iSampleRate); w.Write(c_iSampleRate * iBlock); w.Write((short) iBlock); w.Write((short) c_iBitsPerSample);
        w.Write(Encoding.ASCII.GetBytes("data")); w.Write(aPcm.Length); w.Write(aPcm);
    }
    return true;
}

public void Dispose() { if (bOpen) cancel(); }

} // class VoiceRecorder

public static class Voice {

// The Whisper models tried, smallest good one first; any other ggml model in Whisper's folder is used when none is.
private static readonly string[] c_asModels = { "ggml-small.bin", "ggml-small.en.bin", "ggml-base.bin", "ggml-base.en.bin", "ggml-medium.bin", "ggml-large-v3-turbo.bin" };

// whisperProgram: whisper-cli.exe from Whisper's own machine-wide folder, where the Homer installers put it, or on
// the PATH. "" when it is not installed.
public static string whisperProgram() {
    string sPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Whisper", "whisper-cli.exe");
    if (File.Exists(sPath)) return sPath;
    foreach (string sDir in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(';')) {
        try { string sTry = Path.Combine(sDir.Trim(), "whisper-cli.exe"); if (sDir.Trim().Length > 0 && File.Exists(sTry)) return sTry; } catch { }
    }
    return "";
}

// whisperModel: a speech model beside whisper-cli, preferring the ones in c_asModels. "" when there is none.
public static string whisperModel() {
    string sProgram = whisperProgram();
    if (sProgram.Length == 0) return "";
    string sDir = Path.GetDirectoryName(sProgram);
    foreach (string sName in c_asModels) { string sPath = Path.Combine(sDir, sName); if (File.Exists(sPath)) return sPath; }
    string[] aAny = Directory.GetFiles(sDir, "ggml-*.bin");
    foreach (string sPath in aAny) if (Path.GetFileName(sPath).IndexOf("silero", StringComparison.OrdinalIgnoreCase) < 0) return sPath;
    return "";
}

// transcribe: the words in a WAV recording, through whisper-cli on this computer. "" with sError set when it fails.
public static string transcribe(string sWav, int iTimeoutMs, out string sError) {
    sError = "";
    string sProgram = whisperProgram();
    string sModel = whisperModel();
    if (sProgram.Length == 0) { sError = "Whisper is not installed; HomerDev's setup program offers it"; return ""; }
    if (sModel.Length == 0) { sError = "Whisper has no speech model; run HomerDev's setup program again and leave Whisper ticked"; return ""; }
    ProcessStartInfo oStart = new ProcessStartInfo(sProgram, "-m \"" + sModel + "\" -f \"" + sWav + "\" -nt -np -l auto");
    oStart.UseShellExecute = false;
    oStart.CreateNoWindow = true;
    oStart.RedirectStandardOutput = true;
    oStart.RedirectStandardError = true;
    oStart.StandardOutputEncoding = Encoding.UTF8;
    Stopwatch oClock = Stopwatch.StartNew();
    using (Process oRun = Process.Start(oStart)) {
        string sErr = "";
        System.Threading.Thread oErr = new System.Threading.Thread(delegate() { sErr = oRun.StandardError.ReadToEnd(); });
        oErr.IsBackground = true;
        oErr.Start();
        string sOut = oRun.StandardOutput.ReadToEnd();
        if (!oRun.WaitForExit(iTimeoutMs)) { try { oRun.Kill(); } catch { } sError = "Whisper took too long"; return ""; }
        oErr.Join(2000);
        Log.command("whisper-cli -m " + Path.GetFileName(sModel) + " " + Path.GetFileName(sWav), oRun.ExitCode, oClock.ElapsedMilliseconds);
        if (oRun.ExitCode != 0) { sError = "Whisper stopped with exit code " + oRun.ExitCode; Log.info("Whisper: " + sErr.Trim()); return ""; }
        string sText = System.Text.RegularExpressions.Regex.Replace(sOut, @"\s+", " ").Trim();
        // Whisper marks silence and noise in brackets, such as [BLANK_AUDIO]; those are not words.
        sText = System.Text.RegularExpressions.Regex.Replace(sText, @"\[[A-Z_ ]+\]|\([a-z ]+\)", "").Trim();
        return sText;
    }
}

} // class Voice

} // namespace Homer
