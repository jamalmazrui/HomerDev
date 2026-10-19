// HomerDev.cs -- the HomerDev dialog: a tour of the Homer Development Kit, built from the kit's own classes.
//
// Copyright 2026 by Jamal Mazrui
// MIT License. See License.md, which carries the terms in full.
//
// WHAT THIS IS FOR
//
// A blind vibe coder installs HomerDev and presses Alt+Control+Shift+D. The dialog lists everything the kit holds --
// its documents, samples, skills, subagents, templates, scripts and shared code -- each with a line saying what it
// is, and opens whichever one is chosen: a page in the browser, a sample program to try, any text file in a window
// that reads line by line. Its other buttons play the kit's ten tutorials in the Homer Player, explain the inix
// format with a live reading by the kit's own reader, show Layout by Code and then a dialog that code builds, and
// ask the local AI about the kit, with a map of the kit as its context.
//
// THE KIT EATS ITS OWN COOKING. Nothing here is written for this program alone: the dialogs are LbcDialog, the
// player is MediaPlayer, the reader is HelpDialog, the AI is Ollama, the log is Log, the folders are Paths, the
// update check is Elevate. If one of them is wrong, this program shows it first.
//
// NO FOLDER IS CREATED BY THIS PROGRAM beyond the Homer per-user ones Paths makes under %LOCALAPPDATA%\HomerDev.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using Homer;

namespace HomerDev
{

// One thing the kit holds: its kind, its name, the file that is it, and a line saying what it is.
public class KitItem
{
    public string sDescription, sKind, sName, sPath;
    public KitItem(string sKindIn, string sNameIn, string sPathIn, string sDescriptionIn)
    {
        sKind = sKindIn; sName = sNameIn; sPath = sPathIn; sDescription = sDescriptionIn ?? "";
    }
    public override string ToString()
    {
        string sLine = sKind + ": " + sName;
        if (sDescription.Length > 0) sLine += ", " + sDescription;
        return sLine;
    }
}

public static class Program
{

private const int iAiTimeoutMs = 300000;
private const int iContextCharsMost = 24000;
private const int iDescriptionCharsMost = 140;
private const string sAppName = "HomerDev";
private const string sOwner = "JamalMazrui";

// The models tried first for the chat, in order; any other installed model is used when none of these is there.
private static readonly string[] asPreferredModels = { "qwen2.5:7b", "llama3.1:8b", "llama3.2", "gemma2:9b", "mistral" };

private static List<KitItem> lsItems = new List<KitItem>();
private static string sKit = "";
private static string sVersion = "";

// ---- the kit's folder and version ----

// kitFolder: the folder the kit is in. The program runs from exec, so the kit is the folder above it, wherever that
// is -- C:\Program Files\HomerDev after setup, or C:\HomerDev, or any other place.
private static string kitFolder()
{
    string sExe = Application.ExecutablePath;
    string sExec = Path.GetDirectoryName(sExe);
    string sAbove = Path.GetDirectoryName(sExec);
    if (File.Exists(Path.Combine(sAbove, "version.txt"))) return sAbove;
    return Paths.installedFolder;
}

private static string readVersion()
{
    string sPath = Path.Combine(sKit, "version.txt");
    if (!File.Exists(sPath)) return "";
    return File.ReadAllText(sPath).Trim();
}

// ---- describing what the kit holds ----

// firstSentence: the opening sentence of a text, capped, with markup removed, for a list line.
private static string firstSentence(string sText)
{
    string sClean = Regex.Replace(sText ?? "", @"[`*_#>\[\]]", "");
    sClean = Regex.Replace(sClean, @"\s+", " ").Trim();
    int iEnd = sClean.IndexOf(". ");
    if (iEnd > 0) sClean = sClean.Substring(0, iEnd + 1);
    if (sClean.Length > iDescriptionCharsMost) sClean = sClean.Substring(0, iDescriptionCharsMost - 3).TrimEnd() + "...";
    return sClean;
}

// frontMatterDescription: the description: field of a skill's or subagent's front matter, which may run onto
// following lines after "description: >-".
private static string frontMatterDescription(string sPath)
{
    string[] aLines = File.ReadAllLines(sPath);
    bool bIn = false;
    StringBuilder sb = new StringBuilder();
    foreach (string sLine in aLines)
    {
        if (!bIn && sLine.StartsWith("description:"))
        {
            bIn = true;
            string sRest = sLine.Substring("description:".Length).Trim();
            if (sRest != ">-" && sRest != ">" && sRest != "|") sb.Append(sRest.Trim('"')).Append(' ');
            continue;
        }
        if (bIn && (sLine.Length == 0 || !char.IsWhiteSpace(sLine[0]))) break;
        if (bIn) sb.Append(sLine.Trim()).Append(' ');
    }
    return firstSentence(sb.ToString());
}

// firstParagraph: the first paragraph of a Markdown file that is not front matter, a heading or a blank line.
private static string firstParagraph(string sPath)
{
    if (!File.Exists(sPath)) return "";
    string[] aLines = File.ReadAllLines(sPath);
    bool bFront = aLines.Length > 0 && aLines[0].Trim() == "---";
    int iStart = 0;
    if (bFront) for (int i = 1; i < aLines.Length; i++) if (aLines[i].Trim() == "---") { iStart = i + 1; break; }
    for (int i = iStart; i < aLines.Length; i++)
    {
        string sLine = aLines[i].Trim();
        if (sLine.Length == 0 || sLine.StartsWith("#") || sLine.StartsWith("---") || sLine.StartsWith("title:")) continue;
        return firstSentence(sLine);
    }
    return "";
}

// leadingComment: what a source file says about itself in its opening comment or docstring.
private static string leadingComment(string sPath)
{
    StringBuilder sb = new StringBuilder();
    int iRead = 0;
    foreach (string sRaw in File.ReadAllLines(sPath))
    {
        string sLine = sRaw.Trim();
        if (++iRead > 12) break;
        if (sLine.StartsWith("//") || sLine.StartsWith("rem ") || sLine.StartsWith(";") || sLine.StartsWith("#")) sLine = sLine.TrimStart('/', ';', '#').Trim();
        else if (sLine.StartsWith("rem")) sLine = sLine.Substring(3).Trim();
        else if (sLine.StartsWith("\"\"\"")) sLine = sLine.Trim('"').Trim();
        else if (sLine.StartsWith("@echo")) continue;
        else if (sb.Length > 0) break;
        if (sLine.Length == 0) { if (sb.Length > 0) break; continue; }
        sb.Append(sLine).Append(' ');
    }
    string sText = sb.ToString();
    string sName = Path.GetFileName(sPath);
    if (sText.StartsWith(sName, StringComparison.OrdinalIgnoreCase)) sText = sText.Substring(sName.Length).TrimStart(' ', '-', ':');
    return firstSentence(sText);
}

private static bool addFiles(string sKind, string sFolder, string sPattern, bool bByComment)
{
    if (!Directory.Exists(sFolder)) return false;
    foreach (string sPath in Directory.GetFiles(sFolder, sPattern))
    {
        string sDescription = bByComment ? leadingComment(sPath) : firstParagraph(Path.ChangeExtension(sPath, ".md"));
        lsItems.Add(new KitItem(sKind, Path.GetFileName(sPath), sPath, sDescription));
    }
    return true;
}

// loadItems: everything the kit holds, sorted by kind and then by name, ignoring case.
private static bool loadItems()
{
    string sHelp = Path.Combine(sKit, "help");
    string sSamples = Path.Combine(sKit, "Templates", "samples");
    lsItems.Clear();
    // DOCUMENTS: every page, at the top and in help, opened in the browser. The tutorial scripts are heard, not read.
    foreach (string sFolder in new string[] { sKit, sHelp })
    {
        if (!Directory.Exists(sFolder)) continue;
        foreach (string sPath in Directory.GetFiles(sFolder, "*.htm"))
        {
            string sStem = Path.GetFileNameWithoutExtension(sPath);
            lsItems.Add(new KitItem("Document", sStem.Replace('_', ' '), sPath, firstParagraph(Path.ChangeExtension(sPath, ".md"))));
        }
    }
    // SAMPLES: the four fruit baskets, two ways of building one program in two languages.
    string[,] aSamples = {
        { "FruitBasketCs", "C#, one dialog: the smallest Homer program, a list you add to and take from" },
        { "FruitBasketMdiCs", "C#, several windows inside one: the same basket as a multiple-document program" },
        { "FruitBasketMdiPy", "Python, several windows inside one: the multiple-document basket, written in Python" },
        { "FruitBasketPy", "Python, one dialog: the one-dialog basket, written in Python, built on the same Lbc" } };
    for (int i = 0; i < aSamples.GetLength(0); i++)
    {
        string sExe = Path.Combine(sSamples, aSamples[i, 0] + ".exe");
        if (File.Exists(sExe)) lsItems.Add(new KitItem("Sample", aSamples[i, 0], sExe, aSamples[i, 1] + ". Open runs it."));
        string sSource = Path.Combine(sSamples, aSamples[i, 0] + (aSamples[i, 0].EndsWith("Py") ? ".py" : ".cs"));
        if (File.Exists(sSource)) lsItems.Add(new KitItem("Sample source", Path.GetFileName(sSource), sSource, "the code of " + aSamples[i, 0] + ", every decision explained in its comments"));
    }
    // SKILLS AND SUBAGENTS: what an AI assistant reads to work the Homer way.
    string sSkills = Path.Combine(sKit, ".claude", "skills");
    if (Directory.Exists(sSkills))
    {
        foreach (string sDir in Directory.GetDirectories(sSkills))
        {
            string sSkill = Path.Combine(sDir, "SKILL.md");
            if (File.Exists(sSkill)) lsItems.Add(new KitItem("Skill", Path.GetFileName(sDir), sSkill, frontMatterDescription(sSkill)));
        }
    }
    string sAgents = Path.Combine(sKit, ".claude", "agents");
    if (Directory.Exists(sAgents)) foreach (string sPath in Directory.GetFiles(sAgents, "*.md")) lsItems.Add(new KitItem("Subagent", Path.GetFileNameWithoutExtension(sPath), sPath, frontMatterDescription(sPath)));
    string sPlugin = Path.Combine(sKit, ".claude-plugin", "plugin.json");
    if (File.Exists(sPlugin)) lsItems.Add(new KitItem("Plugin", "plugin.json", sPlugin, "how Claude Code installs the kit's skills and subagents as one plugin"));
    // CODE: the templates a new app starts from, the scripts of the cycle, and the shared classes in both languages.
    addFiles("Template", Path.Combine(sKit, "Templates"), "*.*", true);
    addFiles("Script", Path.Combine(sKit, "scripts"), "*.py", true);
    addFiles("Shared code, C#", Path.Combine(sKit, "exec", "CSharp"), "*.cs", true);
    addFiles("Shared code, Python", Path.Combine(sKit, "exec", "Python"), "*.py", true);
    lsItems.RemoveAll(delegate(KitItem o) { return o.sKind == "Template" && o.sName.EndsWith(".ico", StringComparison.OrdinalIgnoreCase); });
    lsItems.Sort(delegate(KitItem a, KitItem b)
    {
        int iKind = string.Compare(a.sKind, b.sKind, StringComparison.OrdinalIgnoreCase);
        return iKind != 0 ? iKind : string.Compare(a.sName, b.sName, StringComparison.OrdinalIgnoreCase);
    });
    Log.info("Kit contents: " + lsItems.Count + " items from " + sKit);
    return true;
}

// ---- opening one ----

private static bool openItem(IWin32Window owner, KitItem oItem)
{
    if (oItem == null) return false;
    Log.info("Open: " + oItem.sKind + " " + oItem.sPath);
    try
    {
        if (oItem.sPath.EndsWith(".htm", StringComparison.OrdinalIgnoreCase) || oItem.sPath.EndsWith(".exe", StringComparison.OrdinalIgnoreCase))
        {
            ProcessStartInfo oStart = new ProcessStartInfo(oItem.sPath);
            oStart.UseShellExecute = true;
            oStart.WorkingDirectory = Path.GetDirectoryName(oItem.sPath);
            Process.Start(oStart);
            return true;
        }
        HelpDialog.show(owner, oItem.sName, File.ReadAllText(oItem.sPath));
    }
    catch (Exception oError)
    {
        Log.exception(oError);
        MessageBox.Show(owner, "Could not open " + oItem.sName + ": " + oError.Message, sAppName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
    }
    return true;
}

// ---- the inix format, explained and read live ----

private const string sInixExample =
    "; A comment line starts with a semicolon.\r\n" +
    "[Basket]\r\n" +
    "owner = Jamal\r\n" +
    "fruit = apple, banana, cherry\r\n" +
    "notes=\r\n" +
    "Picked on Saturday.\r\n" +
    "Kept in the cool room.\r\n" +
    "\r\n" +
    "[Recipe]\r\n" +
    "formula=`\r\n" +
    "total = apples + bananas\r\n" +
    "`\r\n";

private static bool showInix(IWin32Window owner)
{
    StringBuilder sb = new StringBuilder();
    sb.AppendLine("The inix format");
    sb.AppendLine();
    sb.AppendLine("Inix is the INI format every Windows user has seen -- sections in square brackets, then name = value lines -- with one addition: a value may run over several lines, so a list, a note or a block of text needs no special syntax. Homer programs and the kit use it for settings, tutorial scripts and data, and prefer it to JSON because a person can read and edit it in any text editor, line by line.");
    sb.AppendLine();
    sb.AppendLine("The rules, in brief:");
    sb.AppendLine("A line starting with a semicolon is a comment.");
    sb.AppendLine("A name with = and nothing after it starts a value of several lines, which runs to the next name or section.");
    sb.AppendLine("When a value of several lines holds an equals sign, it goes between backticks, so the equals sign is not read as a new name.");
    sb.AppendLine("A list is just a value with commas, which the program reading it splits.");
    sb.AppendLine("A value is kept exactly as written; trimming is the reading program's choice.");
    sb.AppendLine();
    sb.AppendLine("An example file:");
    sb.AppendLine();
    sb.Append(sInixExample);
    sb.AppendLine();
    sb.AppendLine("What the kit's own reader, InixCodec, made of it just now:");
    sb.AppendLine();
    List<InixCodec.Section> lsSections = InixCodec.parseLines(sInixExample.Replace("\r\n", "\n").Split('\n'));
    foreach (InixCodec.Section oSection in lsSections)
    {
        if (oSection.Name.Length == 0 && oSection.Pairs.Count == 0) continue;
        sb.AppendLine("Section " + oSection.Name + ", " + oSection.Pairs.Count + (oSection.Pairs.Count == 1 ? " value:" : " values:"));
        foreach (InixCodec.Pair oPair in oSection.Pairs)
        {
            string[] aLines = (oPair.Value ?? "").Replace("\r\n", "\n").TrimEnd('\n').Split('\n');
            sb.AppendLine("  " + oPair.Key + ", " + (aLines.Length == 1 ? "one line: " + aLines[0] : aLines.Length + " lines: " + string.Join(" / ", aLines)));
        }
    }
    sb.AppendLine();
    sb.AppendLine("The help folder's Inix document has the full specification, with the triple-quote form for a value that holds a backtick.");
    HelpDialog.show(owner, "The inix format", sb.ToString());
    return true;
}

// ---- Layout by Code, explained and then shown ----

private const string sLayoutCode =
    "using (LbcDialog dlg = new LbcDialog(\"Layout by Code demonstration\", null))\r\n" +
    "{\r\n" +
    "    dlg.addInputBox(\"&Name:\", \"\", \"Your name; it goes nowhere.\");\r\n" +
    "    dlg.addBand();\r\n" +
    "    dlg.addComboPickBox(\"&Fruit:\", new string[] { \"apple\", \"banana\", \"cherry\" }, \"apple\", \"A fruit.\");\r\n" +
    "    dlg.addCheckBox(\"&Ripe\", true, \"Whether it is ripe.\");\r\n" +
    "    dlg.endBand();\r\n" +
    "    dlg.addMemoBox(\"N&otes:\", \"\", \"Anything else.\");\r\n" +
    "    dlg.runWithButtons(new string[] { \"OK\", \"Cancel\" });\r\n" +
    "}\r\n";

private static bool showLayout(IWin32Window owner)
{
    StringBuilder sb = new StringBuilder();
    sb.AppendLine("Layout by Code");
    sb.AppendLine();
    sb.AppendLine("Layout by Code, Lbc for short, is how every Homer dialog is made: one line of code per control, in the order a person tabs through them. There are no pixel positions, no drag and drop and no tab order to set by hand. Lbc gives each control its label, its access key from the ampersand in its caption, its tip on the status line and in Help, and its place in the tab order -- which is simply the order of the lines.");
    sb.AppendLine();
    sb.AppendLine("A band puts the controls between addBand and endBand on one row, for things that belong together. Every Lbc dialog also gets, with no code: Control+Enter for OK from any control, Escape for Cancel, F1 for a Help window listing every control with its tip, Shift+F1 for the focused control's tip, and F7 for a list of the dialog's controls.");
    sb.AppendLine();
    sb.AppendLine("Here is the whole code of a small dialog. When you close this window, that dialog opens, so you can tab through it and hear that the order is the order of the lines:");
    sb.AppendLine();
    sb.Append(sLayoutCode);
    HelpDialog.show(owner, "Layout by Code", sb.ToString());
    // THE DEMONSTRATION IS THE CODE ABOVE, line for line, so what is heard is what was read.
    using (LbcDialog dlg = new LbcDialog("Layout by Code demonstration", owner))
    {
        dlg.addInputBox("&Name:", "", "Your name; it goes nowhere.");
        dlg.addBand();
        dlg.addComboPickBox("&Fruit:", new string[] { "apple", "banana", "cherry" }, "apple", "A fruit.");
        dlg.addCheckBox("&Ripe", true, "Whether it is ripe.");
        dlg.endBand();
        dlg.addMemoBox("N&otes:", "", "Anything else.");
        dlg.runWithButtons(new string[] { "OK", "Cancel" });
    }
    return true;
}

// ---- asking the local AI ----

// chooseModel: the first preferred model installed, else any installed model, else "".
private static string chooseModel()
{
    foreach (string sModel in asPreferredModels) if (Ollama.hasModel(sModel)) return sModel;
    string[] aNames = Ollama.modelList(false).Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
    foreach (string sName in aNames) if (sName.IndexOf("embed", StringComparison.OrdinalIgnoreCase) < 0) return sName;
    return "";
}

private static string readCapped(string sPath, int iMost)
{
    if (!File.Exists(sPath)) return "";
    string sText = File.ReadAllText(sPath);
    return sText.Length > iMost ? sText.Substring(0, iMost) + "\r\n[...]" : sText;
}

// plainText: an answer as a screen reader reads it best. A small model writes Markdown even when asked not to, and
// in a plain text box its asterisks and pound signs are read aloud as symbols (11 October 2026), so emphasis marks,
// heading marks and code ticks are removed; list numbers and dashes, which read naturally, stay.
private static string plainText(string sText)
{
    string sOut = sText ?? "";
    sOut = Regex.Replace(sOut, @"\*\*(.+?)\*\*", "$1");
    sOut = Regex.Replace(sOut, @"__(.+?)__", "$1");
    sOut = Regex.Replace(sOut, @"(?m)^\s*#{1,6}\s+", "");
    sOut = Regex.Replace(sOut, @"(?m)^(\s*)\*\s+", "$1- ");
    sOut = sOut.Replace("`", "");
    return sOut.Trim();
}

// kitContext: what the local AI is told before any question -- where the kit is, the kit's own map for AI agents
// (llms.txt and AGENTS.md), and the list this dialog shows, each item with its path. Capped, since a small model
// has a small window.
private static string kitContext()
{
    StringBuilder sb = new StringBuilder();
    sb.AppendLine("Write plain text only: no Markdown, no asterisks, no pound signs, no tables. Use short paragraphs, and a numbered list only for steps that have an order. Answer only what was asked; mention a skill or file only when it bears on the question.");
    sb.AppendLine("You answer questions about the Homer Development Kit, HomerDev, for a blind developer who uses a screen reader. Answer in plain language, briefly, and name the file or folder the person should open when that helps. If you do not know, say so; never invent a file.");
    sb.AppendLine("The kit is installed at " + sKit + ", version " + sVersion + ". Skills are in .claude\\skills, subagents in .claude\\agents, the Claude Code plugin in .claude-plugin, documents in help, templates in Templates, the samples in Templates\\samples, scripts in scripts, and the shared code in exec\\CSharp and exec\\Python.");
    sb.AppendLine();
    sb.AppendLine("The kit's map for AI agents (llms.txt):");
    sb.AppendLine(readCapped(Path.Combine(sKit, "llms.txt"), 6000));
    sb.AppendLine("The kit's instructions for AI agents (AGENTS.md):");
    sb.AppendLine(readCapped(Path.Combine(sKit, "AGENTS.md"), 6000));
    sb.AppendLine("Everything the kit holds, as kind: name, description, path:");
    foreach (KitItem oItem in lsItems)
    {
        if (sb.Length > iContextCharsMost) { sb.AppendLine("[the list continues]"); break; }
        sb.AppendLine(oItem.ToString() + " -- " + oItem.sPath.Substring(Math.Min(sKit.Length, oItem.sPath.Length)).TrimStart('\\'));
    }
    return sb.ToString();
}

// ---- the chat: the local AI, or Claude Code when it is installed (11 October 2026) ----
//
// TWO ENGINES. The local AI (Ollama) answers on this computer from the kit's own summary. Claude Code, when it is
// installed, answers from the kit itself: it runs headless (claude -p) in the kit's folder, where CLAUDE.md and the
// skills tell it what HomerDev is, in plan mode, so it reads and never changes a file. One dialog is one
// conversation: Claude Code's is named with --session-id at the first question and continued with --resume.
//
// ASKED BY VOICE, ANSWERED BY VOICE. An answer is always written into the conversation box; it is also spoken when
// the question was asked by voice and sent as heard, or when Speak answers is ticked.
//
// KEYS, after The Chat Place's (Kelly Ford's accessible companion for Claude Code): Control+Period stops waiting,
// Control+Shift+R says the last answer again, Control+Shift+C copies it. Enter sends, as before.
//
// PROGRESS. Every ten seconds a soft tick sounds and the wait is said and logged, so a log shows it ran even if
// speech was lost.

private static readonly HashSet<string> setStrippedVariables = new HashSet<string> {
    "CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT", "CLAUDE_AGENT_SDK_VERSION", "CLAUDE_PREVIEW_CLASSIFIER_FLOOR",
    "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_HOST_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH", "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_REFRESH_TOKEN", "CLAUDE_CODE_OAUTH_SCOPES", "CLAUDE_CODE_ACCOUNT_UUID",
    "CLAUDE_CODE_ORGANIZATION_UUID", "CLAUDE_CODE_USER_EMAIL", "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_DESKTOP_APP_VERSION", "CLAUDE_CODE_EXECPATH",
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_CUSTOM_HEADERS",
    "ANTHROPIC_BEDROCK_BASE_URL", "ANTHROPIC_VERTEX_BASE_URL", "ANTHROPIC_VERTEX_PROJECT_ID",
    "ANTHROPIC_FOUNDRY_API_KEY", "ANTHROPIC_FOUNDRY_BASE_URL", "ANTHROPIC_FOUNDRY_RESOURCE",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY" };

private static string claudeProgram()
{
    string sFound = "";
    foreach (string sDir in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(';'))
    {
        if (sDir.Trim().Length == 0) continue;
        foreach (string sName in new string[] { "claude.exe", "claude.cmd" })
        {
            try { string sPath = Path.Combine(sDir.Trim(), sName); if (File.Exists(sPath)) return sPath; } catch { }
        }
    }
    foreach (string sPath in new string[] {
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".local", "bin", "claude.exe"),
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "npm", "claude.cmd") })
        if (File.Exists(sPath)) { sFound = sPath; break; }
    return sFound;
}

// One question to Claude Code, the question on its standard input. The process is handed out through oRunning so
// Control+Period can end it.
private static string askClaude(string sProgram, string sQuestion, string sSession, bool bFirst, Process[] aRunning, out string sError)
{
    sError = "";
    // NAMED ON EVERY TURN, as The Chat Place does, so Claude's own session list shows it as HomerDev's.
    string sArgs = "-p --output-format text --permission-mode plan --name \"HomerDev questions\" " + (bFirst ? "--session-id " : "--resume ") + sSession;
    ProcessStartInfo oStart = new ProcessStartInfo();
    if (sProgram.EndsWith(".cmd", StringComparison.OrdinalIgnoreCase)) { oStart.FileName = "cmd.exe"; oStart.Arguments = "/c \"\"" + sProgram + "\" " + sArgs + "\""; }
    else { oStart.FileName = sProgram; oStart.Arguments = sArgs; }
    oStart.WorkingDirectory = sKit;
    oStart.UseShellExecute = false;
    oStart.CreateNoWindow = true;
    oStart.RedirectStandardInput = true;
    oStart.RedirectStandardOutput = true;
    oStart.RedirectStandardError = true;
    oStart.StandardOutputEncoding = Encoding.UTF8;
    oStart.StandardErrorEncoding = Encoding.UTF8;
    // A CLEAN ENVIRONMENT (from The Chat Place, Kelly Ford's AIChat): variables a host Claude Code session sets
    // describe that session, and some make a child wait for it; billing variables would move the turn off the
    // subscription to per-use charges or another endpoint. Each is removed, by name and by family.
    foreach (string sName in new List<string>(oStart.EnvironmentVariables.Keys.Cast<string>()))
    {
        string sUpper = sName.ToUpperInvariant();
        if (setStrippedVariables.Contains(sUpper) || sUpper.StartsWith("CLAUDE_CODE_SDK_") || sUpper.StartsWith("CLAUDE_CODE_HOST_") || sUpper.StartsWith("CLAUDE_CODE_MESSAGING_"))
        { oStart.EnvironmentVariables.Remove(sName); Log.info("Claude Code: left out the variable " + sName); }
    }
    Log.info("Claude Code: " + oStart.FileName + " " + oStart.Arguments + " in " + sKit);
    try
    {
        using (Process oProcess = Process.Start(oStart))
        {
            aRunning[0] = oProcess;
            var oOut = oProcess.StandardOutput.ReadToEndAsync();
            var oErr = oProcess.StandardError.ReadToEndAsync();
            oProcess.StandardInput.Write(sQuestion);
            oProcess.StandardInput.Close();
            if (!oProcess.WaitForExit(iAiTimeoutMs))
            {
                try { oProcess.Kill(); } catch { }
                sError = "no answer in " + (iAiTimeoutMs / 60000) + " minutes";
                return "";
            }
            oProcess.WaitForExit();
            string sOut = oOut.Result.Trim(), sErr = oErr.Result.Trim();
            Log.info("Claude Code exit " + oProcess.ExitCode + ", " + sOut.Length + " characters" + (sErr.Length > 0 ? "; stderr: " + sErr : ""));
            // A FAILED EXIT IS AN ERROR, WHATEVER WAS WRITTEN (14 October 2026, from an audit by another AI). It counted
            // as one only when nothing came out, so a run that wrote part of an answer and then failed was shown as a
            // complete answer. Any nonzero exit is now an error; the text is still returned, and the chat says it is
            // incomplete. An error also keeps a failed first turn from being taken for a session that can be resumed.
            if (oProcess.ExitCode != 0) sError = (sErr.Length > 0 ? sErr + " (exit code " + oProcess.ExitCode + ")" : "Claude Code stopped with exit code " + oProcess.ExitCode);
            return sOut;
        }
    }
    catch (Exception oError)
    {
        sError = oError.Message;
        return "";
    }
    finally
    {
        aRunning[0] = null;
    }
}

private static bool runChat(IWin32Window owner)
{
    string sContext = "", sModel, sClaude;
    sModel = chooseModel();
    sClaude = claudeProgram();
    Log.keyValue("Chat model", sModel.Length > 0 ? sModel : "(none)");
    Log.keyValue("Claude Code", sClaude.Length > 0 ? sClaude : "(not installed)");
    if (sModel.Length == 0 && sClaude.Length == 0)
    {
        MessageBox.Show(owner, "No AI is ready to answer: Ollama is not running or has no model, and Claude Code is not installed. HomerDev's setup program offers Ollama and a model; run it again and leave those boxes ticked.", sAppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
        return false;
    }
    if (sModel.Length > 0) { sContext = kitContext(); Log.keyValue("Chat context characters", "" + sContext.Length); }
    string sLocalName = "The local AI, " + sModel + ", on this computer", sClaudeName = "Claude Code, reading the kit itself";
    List<string> lsEngines = new List<string>();
    if (sModel.Length > 0) lsEngines.Add(sLocalName);
    if (sClaude.Length > 0) lsEngines.Add(sClaudeName);
    StringBuilder sbHistory = new StringBuilder();
    string sSession = Guid.NewGuid().ToString(), sLastAnswer = "", sHeard = "";
    bool bClaudeStarted = false;
    int iAsk = 0;
    Process[] aRunning = new Process[1];
    System.Windows.Forms.Timer oTicker = null;
    using (LbcDialog dlg = new LbcDialog("Ask about HomerDev", owner))
    {
        ComboBox cboEngine = dlg.addComboPickBox("Ask &with:", lsEngines, lsEngines[0], "Which AI answers. The local AI runs on this computer and nothing leaves it. Claude Code, when installed, reads the kit itself, in plan mode, so it changes nothing.");
        TextBox txtConversation = dlg.addMemoBox("&Conversation:", "", "Your questions and the answers, newest last. Control+Shift+R says the last answer again; Control+Shift+C copies it.");
        txtConversation.ReadOnly = true;
        dlg.addBand();
        TextBox txtQuestion = dlg.addInputBox("&Question:", "", "Ask about HomerDev: what a skill does, where a template is, how to start an app. Enter sends it; Control+Period stops waiting.");
        Button btnSend = dlg.addButton("&Send", "Ask the question.");
        Button btnVoice = dlg.addButton("&Voice", "Ask by voice: a rising tone, then speak; press Voice again, or simply stop talking, and Whisper writes what you said into the question. Escape throws a recording away. Everything stays on this computer.");
        dlg.endBand();
        CheckBox chkSendHeard = dlg.addCheckBox("Send &when heard", true, "Send a spoken question as soon as it is written. The answer to a question sent as heard is spoken too.");
        CheckBox chkSpeak = dlg.addCheckBox("Spea&k answers", false, "Speak every answer as well as writing it in the conversation, whether the question was typed or spoken.");
        MethodInvoker fnStopTicker = delegate()
        {
            if (oTicker == null) return;
            oTicker.Stop();
            oTicker.Dispose();
            oTicker = null;
        };
        btnSend.Click += delegate(object oSender, EventArgs evArgs)
        {
            string sQuestion = txtQuestion.Text.Trim();
            if (sQuestion.Length == 0 || !btnSend.Enabled) return;
            bool bByVoice = sHeard.Length > 0 && sQuestion == sHeard.Trim();
            sHeard = "";
            bool bSpeak = chkSpeak.Checked || bByVoice;
            bool bClaude = cboEngine.Text == sClaudeName;
            string sEngine = bClaude ? "Claude Code" : sModel;
            int iThis = ++iAsk;
            btnSend.Enabled = false;
            txtQuestion.ReadOnly = true;
            int iWaited = 0;
            oTicker = new System.Windows.Forms.Timer();
            oTicker.Interval = 10000;
            oTicker.Tick += delegate(object oTickSender, EventArgs evTick)
            {
                iWaited += 10;
                Log.info("Progress: waiting for " + sEngine + ", " + iWaited + " seconds");
                dlg.setStatusText("Waiting for " + sEngine + ", " + iWaited + " seconds");
                Console.Beep(880, 40);
                Say.say(iWaited + " seconds");
            };
            Say.say("Asking " + sEngine + "; it may take a minute");
            dlg.setStatusText("Waiting for " + sEngine);
            DateTime dtAsked = DateTime.Now;
            oTicker.Start();
            Log.info("Chat question (" + sEngine + (bByVoice ? ", by voice" : "") + "): " + sQuestion);
            bool bFirst = !bClaudeStarted;
            string sPrompt = bClaude ? sQuestion : sContext + "\r\n" + sbHistory.ToString() + "Question: " + sQuestion + "\r\nAnswer:";
            Thread oWorker = new Thread(delegate()
            {
                string sError = "";
                string sAnswer = "";
                // An error asking is an answer that did not come, never a crash.
                try { sAnswer = bClaude ? askClaude(sClaude, sPrompt, sSession, bFirst, aRunning, out sError) : Ollama.generate(sModel, sPrompt, iAiTimeoutMs, out sError); }
                catch (Exception oError) { Log.exception(oError); sError = oError.Message; }
                try
                {
                    if (dlg.form.IsDisposed) { Log.info("An answer came after the chat closed, and was set aside"); return; }
                    dlg.form.BeginInvoke((MethodInvoker) delegate()
                    {
                        if (iThis != iAsk) { Log.info("An answer came after Stop, and was set aside"); return; }
                        fnStopTicker();
                        // A SESSION EXISTS ONCE CLAUDE HAS ANSWERED (13 October 2026, from an audit). It was marked started
                        // when the first question was sent, so a first request that failed left every later one trying
                        // to resume a session that was never made. Now only a clean answer marks it.
                        if (bClaude && bFirst && string.IsNullOrEmpty(sError) && !string.IsNullOrEmpty(sAnswer)) bClaudeStarted = true;
                        // TEXT WITH AN ERROR IS AN INCOMPLETE ANSWER, AND SAYS SO before the text, so it is not read as whole.
                        bool bPartial = !string.IsNullOrEmpty(sAnswer) && !string.IsNullOrEmpty(sError);
                        if (string.IsNullOrEmpty(sAnswer)) sAnswer = "No answer came back" + (string.IsNullOrEmpty(sError) ? "." : ": " + sError);
                        else if (bPartial) sAnswer = "This answer may be incomplete: " + sEngine + " stopped with an error, " + sError + ". What it wrote before stopping:\n" + sAnswer;
                        sAnswer = plainText(sAnswer);
                        sLastAnswer = sAnswer;
                        Log.info("Chat answer: " + sAnswer.Length + " characters" + (string.IsNullOrEmpty(sError) ? "" : "; error " + sError));
                        if (!bClaude) sbHistory.Append("Question: ").Append(sQuestion).Append("\r\nAnswer: ").Append(sAnswer).Append("\r\n");
                        int iStart = txtConversation.TextLength;
                        txtConversation.AppendText((iStart > 0 ? "\r\n" : "") + "You: " + sQuestion + "\r\n" + sEngine + ": " + sAnswer.Replace("\n", "\r\n").Replace("\r\r\n", "\r\n") + "\r\n");
                        txtQuestion.Text = "";
                        txtQuestion.ReadOnly = false;
                        btnSend.Enabled = true;
                        txtConversation.Focus();
                        txtConversation.SelectionStart = iStart + (iStart > 0 ? 2 : 0);
                        txtConversation.SelectionLength = 0;
                        txtConversation.ScrollToCaret();
                        int iTook = (int) Math.Round((DateTime.Now - dtAsked).TotalSeconds);
                        string sDone = (bPartial ? "Incomplete answer, with an error, in " : "Answered in ") + iTook + (iTook == 1 ? " second" : " seconds");
                        dlg.setStatusText(sDone);
                        Say.say(sDone);
                        if (bSpeak) Say.sayForced(sAnswer);
                    });
                }
                catch (Exception oError) { Log.info("The answer could not be shown: " + oError.Message); }
            });
            oWorker.IsBackground = true;
            oWorker.Start();
        };
        // ---- VOICE: the convention of Windows+H; tones mark the start and the end ----
        VoiceRecorder oRecorder = null;
        System.Windows.Forms.Timer oListen = new System.Windows.Forms.Timer();
        oListen.Interval = 100;
        MethodInvoker fnFinish = null;
        fnFinish = delegate()
        {
            oListen.Stop();
            if (oRecorder == null) return;
            string sWav = oRecorder.stop(Paths.temp());
            bool bSpoke = oRecorder.HeardSpeech;
            oRecorder.Dispose();
            oRecorder = null;
            Console.Beep(660, 90); Console.Beep(440, 120);
            if (sWav.Length == 0 || !bSpoke)
            {
                dlg.setStatusText("Nothing was heard");
                Say.say("Nothing was heard");
                btnVoice.Focus();
                return;
            }
            dlg.setStatusText("Writing down what you said");
            Say.say("Writing it down");
            btnVoice.Enabled = false;
            Thread oScribe = new Thread(delegate()
            {
                // THE CHAT MAY CLOSE WHILE WHISPER WRITES (12 October 2026). Enter pressed Close in this dialog, and
                // a question spoken just before was still being written down; when Whisper finished, this thread
                // reached for the closed dialog and the error ended HomerDev without a word. Every step is now
                // guarded, and words that arrive after the chat closed are logged and set aside.
                string sError = "";
                string sText = "";
                try { sText = Voice.transcribe(sWav, 120000, out sError) ?? ""; }
                catch (Exception oError) { Log.exception(oError); sError = oError.Message; }
                try { File.Delete(sWav); } catch { }
                if (dlg.form.IsDisposed) { Log.info("Voice: written down after the chat closed, and set aside: " + sText); return; }
                try { dlg.form.BeginInvoke((MethodInvoker) delegate()
                {
                    btnVoice.Enabled = true;
                    if (sText.Length == 0)
                    {
                        string sWhy = sError.Length > 0 ? sError : "no words were recognized";
                        dlg.setStatusText("Not written down: " + sWhy);
                        Say.say("Not written down: " + sWhy);
                        btnVoice.Focus();
                        return;
                    }
                    sHeard = sText;
                    txtQuestion.Text = sText;
                    txtQuestion.Focus();
                    txtQuestion.SelectionStart = sText.Length;
                    dlg.setStatusText("Heard: " + sText);
                    Say.say("Heard: " + sText);
                    if (chkSendHeard.Checked) btnSend.PerformClick();
                }); }
                catch (Exception oError) { Log.info("Voice: the chat closed before the words could be shown: " + oError.Message); }
            });
            oScribe.IsBackground = true;
            oScribe.Start();
        };
        oListen.Tick += delegate(object oTickSender, EventArgs evTick)
        {
            if (oRecorder != null && oRecorder.poll()) fnFinish();
        };
        btnVoice.Click += delegate(object oSender, EventArgs evArgs)
        {
            if (oRecorder != null) { fnFinish(); return; }
            if (Voice.whisperProgram().Length == 0 || Voice.whisperModel().Length == 0)
            {
                MessageBox.Show(dlg.form, "Asking by voice needs Whisper, which turns speech into text on this computer. HomerDev's setup program offers it: run it again and leave Whisper ticked.", sAppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            oRecorder = new VoiceRecorder();
            Console.Beep(440, 90); Console.Beep(660, 120);
            string sProblem = oRecorder.start();
            if (sProblem.Length > 0)
            {
                oRecorder = null;
                MessageBox.Show(dlg.form, "Could not listen: " + sProblem + ".", sAppName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            dlg.setStatusText("Listening; press Voice again or stop talking to finish, Escape to cancel");
            oListen.Start();
        };
        dlg.commandKey = delegate(Keys keys)
        {
            // Escape while listening throws the recording away and keeps the dialog open; otherwise it closes.
            if (keys == Keys.Escape && oRecorder != null)
            {
                oListen.Stop();
                oRecorder.cancel();
                oRecorder.Dispose();
                oRecorder = null;
                Console.Beep(330, 150);
                dlg.setStatusText("Recording thrown away");
                Say.say("Cancelled");
                return true;
            }
            // Control+Period: stop waiting. A late answer is set aside, and Claude Code is ended.
            if (keys == (Keys.Control | Keys.OemPeriod))
            {
                if (btnSend.Enabled) { Say.say("Nothing is waiting"); return true; }
                iAsk++;
                fnStopTicker();
                try { if (aRunning[0] != null && !aRunning[0].HasExited) aRunning[0].Kill(); } catch { }
                txtQuestion.ReadOnly = false;
                btnSend.Enabled = true;
                txtQuestion.Focus();
                dlg.setStatusText("Stopped");
                Say.say("Stopped");
                Log.info("Chat: stopped by the user");
                return true;
            }
            if (keys == (Keys.Control | Keys.Shift | Keys.R))
            {
                Say.sayForced(sLastAnswer.Length > 0 ? sLastAnswer : "No answer yet");
                return true;
            }
            if (keys == (Keys.Control | Keys.Shift | Keys.C))
            {
                if (sLastAnswer.Length == 0) { Say.say("No answer yet"); return true; }
                try { Clipboard.SetText(sLastAnswer); Say.say("Copied the last answer"); }
                catch (Exception oError) { Say.say("Could not copy: " + oError.Message); }
                return true;
            }
            return false;
        };
        dlg.form.AcceptButton = btnSend;
        dlg.setInitialFocus(txtQuestion);
        dlg.runWithButtons(new string[] { "Close" });
        Log.info("Chat closed" + (oRecorder != null ? ", while listening" : "") + (!btnSend.Enabled ? ", while an answer was awaited" : ""));
        iAsk++;
        fnStopTicker();
        try { if (aRunning[0] != null && !aRunning[0].HasExited) aRunning[0].Kill(); } catch { }
        // Nothing keeps listening once the chat is gone.
        try { oListen.Stop(); oListen.Dispose(); } catch { }
        if (oRecorder != null) { try { oRecorder.cancel(); oRecorder.Dispose(); } catch { } oRecorder = null; }
    }
    return true;
}

// ---- connecting the AI tools ----


// ---- the Homer projects (kit 1.78.0) ----

// THE PROJECTS LIST. Every Homer project, from data\Projects.inix, so the dialog
// can install or download any of them: one list in data, read with the kit's
// InixCodec class, and adding a project there needs no change here. Each row is
// {name, summary, repo}, in lowercase alphabetical order by name.
private static List<string[]> loadProjects()
{
    List<string[]> lsRows = new List<string[]>();
    string sPath = Path.Combine(sKit, "data", "Projects.inix");
    try
    {
        foreach (InixCodec.Section oSection in InixCodec.read(sPath))
        {
            if (string.IsNullOrEmpty(oSection.Name)) continue;
            string sRepo = oSection.get("repo") ?? "";
            if (sRepo.Length == 0) continue;
            lsRows.Add(new string[] { oSection.Name, oSection.get("summary") ?? "", sRepo });
        }
    }
    catch (Exception oError) { Log.info("Projects list not read from " + sPath + ": " + oError.Message); }
    lsRows.Sort(delegate(string[] a, string[] b) { return string.Compare(a[0], b[0], StringComparison.OrdinalIgnoreCase); });
    Log.info("Projects list: " + lsRows.Count + (lsRows.Count == 1 ? " project" : " projects") + " from " + sPath);
    return lsRows;
}

// setupUrl: the project's newest installer, by GitHub's latest-release address,
// which always points at the newest release's file of that name.
private static string setupUrl(string[] aProject)
{
    return "https://github.com/" + aProject[2] + "/releases/latest/download/" + aProject[0] + "_setup.exe";
}

// fetchProject: download a project's installer on a background thread, so the
// dialog keeps answering, then on the dialog's own thread either run it (bRun)
// or say where it was saved. A large installer can take a minute; the dialog
// says what it is fetching first, and the two buttons wait until it is done.
private static void fetchProject(LbcDialog dlg, string[] aProject, bool bRun, Button btnSetup, Button btnDownload)
{
    string sUrl = setupUrl(aProject);
    string sDir = bRun ? Path.Combine(Path.GetTempPath(), "HomerDev-setup")
                       : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads");
    try { Directory.CreateDirectory(sDir); } catch (Exception) { }
    btnSetup.Enabled = false;
    btnDownload.Enabled = false;
    string sDoing = "Fetching the newest " + aProject[0] + " installer from GitHub";
    dlg.setStatusText(sDoing + " ...");
    Say.say(sDoing);
    Log.info((bRun ? "Run setup" : "Download") + ": " + aProject[0] + " from " + sUrl + " into " + sDir);
    Thread oWork = new Thread(delegate()
    {
        string sSaved = "";
        try { Web.configure(); sSaved = Web.download(sUrl, sDir, aProject[0] + "_setup.exe"); }
        catch (Exception oError) { Log.info("Download failed: " + oError.Message); }
        try
        {
            dlg.form.BeginInvoke((MethodInvoker) delegate()
            {
                btnSetup.Enabled = true;
                btnDownload.Enabled = true;
                if (sSaved.Length == 0 || !File.Exists(sSaved))
                {
                    Log.info("Not downloaded: " + sUrl);
                    dlg.setStatusText(aProject[0] + ": not downloaded");
                    MessageBox.Show(dlg.form, "The " + aProject[0] + " installer could not be downloaded from:\r\n" + sUrl
                        + "\r\n\r\nCheck the connection, or open the project's releases on GitHub. The log in %LOCALAPPDATA%\\HomerDev\\logs has the details.",
                        sAppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }
                Log.info("Downloaded " + sSaved + ", " + new FileInfo(sSaved).Length + " bytes");
                if (!bRun)
                {
                    dlg.setStatusText("Saved " + Path.GetFileName(sSaved) + " in Downloads");
                    Say.say("Saved " + Path.GetFileName(sSaved) + " in your Downloads folder");
                    return;
                }
                try
                {
                    ProcessStartInfo oStart = new ProcessStartInfo(sSaved);
                    oStart.UseShellExecute = true;
                    Process.Start(oStart);
                    dlg.setStatusText("Started " + Path.GetFileName(sSaved));
                    Log.info("Started " + sSaved);
                    // HomerDev's own setup replaces this program, so the dialog steps aside for it.
                    if (string.Equals(aProject[0], sAppName, StringComparison.OrdinalIgnoreCase)) dlg.close();
                }
                catch (Exception oError)
                {
                    // Most often the answer No to Windows' question whether to let the installer make changes.
                    Log.info("Setup not started: " + oError.Message);
                    dlg.setStatusText(aProject[0] + " setup not started");
                    Say.say(aProject[0] + " setup was not started");
                }
            });
        }
        catch (Exception oError) { Log.info("Download finished after the dialog closed: " + oError.Message); }
    });
    oWork.IsBackground = true;
    oWork.Start();
}

// ---- the dialog ----

private static bool runDialog()
{
    ListBox lbItems;
    List<string> lsLines = new List<string>();
    loadItems();
    foreach (KitItem oItem in lsItems) lsLines.Add(oItem.ToString());
    // THE VERSION IN THE TITLE (11 October 2026): the desktop hotkey opens the copy setup installed, which can lag the
    // kit -- 1.66.0 was heard after 1.68.0 was released, so neither its progress updates nor its Voice button were
    // there. The title, which the screen reader says as the dialog opens, now names the version.
    using (LbcDialog dlg = new LbcDialog(sAppName + " " + sVersion, null))
    {
        lbItems = dlg.addPickBox("&Kit contents:", lsLines, lsLines.Count > 0 ? lsLines[0] : "",
            "Everything the kit holds, by kind and then by name: documents open in your browser, samples run, and every other file opens in a window you read line by line. Enter opens the one you are on.");
        dlg.addBand();
        Button btnOpen = dlg.addButton("&Open", "Open the item you are on in the list.");
        Button btnPlay = dlg.addButton("&Play tutorials", "Play the kit's ten spoken tutorials in the Homer Player: Enter plays a walk, Down Arrow moves to the next.");
        dlg.endBand();
        // THE HOMER PROJECTS (kit 1.78.0): install or download any of them from here.
        List<string[]> lsProjects = loadProjects();
        List<string> lsProjectLines = new List<string>();
        foreach (string[] aProject in lsProjects) lsProjectLines.Add(aProject[0] + ": " + aProject[1]);
        ListBox lbProjects = dlg.addPickBox("&Homer projects:", lsProjectLines, lsProjectLines.Count > 0 ? lsProjectLines[0] : "",
            "Every Homer project, each with what it does. Run setup installs or updates the one you are on, from its newest release on GitHub; Download saves its installer in your Downloads folder.");
        dlg.addBand();
        Button btnSetup = dlg.addButton("Run &setup", "Download the project's newest installer from GitHub and run it. Windows asks whether to allow it, since a Homer program installs for every user of the computer.");
        Button btnDownload = dlg.addButton("&Download", "Save the project's newest installer in your Downloads folder, to run or share later.");
        dlg.endBand();
        dlg.addBand();
        Button btnInix = dlg.addButton("&Inix explained", "What the inix format is, with an example read by the kit's own reader.");
        Button btnLayout = dlg.addButton("&Layout by Code", "How every Homer dialog is made, then a dialog that code builds.");
        Button btnAsk = dlg.addButton("&Ask an AI", "Ask what the kit can do and how: the AI on this computer, or Claude Code when it is installed, typed or by voice.");
        dlg.endBand();

        btnOpen.Click += delegate(object oSender, EventArgs evArgs)
        {
            int iRow = dlg.listSourceIndex(lbItems, lbItems.SelectedIndex);
            if (iRow >= 0 && iRow < lsItems.Count) openItem(dlg.form, lsItems[iRow]);
        };
        btnPlay.Click += delegate(object oSender, EventArgs evArgs)
        {
            if (!MediaPlayer.playTutorials(dlg.form, sAppName, Path.Combine(sKit, "help")))
                MessageBox.Show(dlg.form, "No tutorial is installed in " + Path.Combine(sKit, "help", "tutorials") + ".", sAppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
        };
        btnSetup.Click += delegate(object oSender, EventArgs evArgs)
        {
            int iRow = dlg.listSourceIndex(lbProjects, lbProjects.SelectedIndex);
            if (iRow >= 0 && iRow < lsProjects.Count) fetchProject(dlg, lsProjects[iRow], true, btnSetup, btnDownload);
        };
        btnDownload.Click += delegate(object oSender, EventArgs evArgs)
        {
            int iRow = dlg.listSourceIndex(lbProjects, lbProjects.SelectedIndex);
            if (iRow >= 0 && iRow < lsProjects.Count) fetchProject(dlg, lsProjects[iRow], false, btnSetup, btnDownload);
        };
        // ENTER DOES WHAT THE LIST YOU ARE IN IS FOR: open a kit item, or run a project's setup.
        lbItems.Enter += delegate(object oSender, EventArgs evArgs) { dlg.form.AcceptButton = btnOpen; };
        lbProjects.Enter += delegate(object oSender, EventArgs evArgs) { dlg.form.AcceptButton = btnSetup; };
        btnInix.Click += delegate(object oSender, EventArgs evArgs) { showInix(dlg.form); };
        btnLayout.Click += delegate(object oSender, EventArgs evArgs) { showLayout(dlg.form); };
        btnAsk.Click += delegate(object oSender, EventArgs evArgs) { runChat(dlg.form); };

        // F11: is there a newer HomerDev on the web? (Elevate sounds like eleven.) Claimed before any control sees it.
        dlg.commandKey = delegate(Keys keys)
        {
            if (keys != Keys.F11) return false;
            Log.info("F11: checking the web for a newer version");
            if (Elevate.offer(dlg.form)) dlg.close();
            return true;
        };
        // Enter in the list opens what it is on; the buttons below the list keep their own Enter.
        dlg.form.AcceptButton = btnOpen;
        dlg.setInitialFocus(lbItems);
        dlg.setStatusText(lsItems.Count + (lsItems.Count == 1 ? " item" : " items") + " and " + lsProjects.Count + (lsProjects.Count == 1 ? " project" : " projects") + " in HomerDev " + sVersion);
        dlg.runWithButtons(new string[] { "Close" });
    }
    return true;
}

[STAThread]
public static int Main(string[] aArguments)
{
    Application.EnableVisualStyles();
    Application.SetCompatibleTextRenderingDefault(false);
    Paths.start(sAppName);
    Log.start(sAppName);
    sKit = kitFolder();
    sVersion = readVersion();
    Log.keyValue("Kit folder", sKit);
    Log.keyValue("Version", sVersion);
    try
    {
        Elevate.configure(sOwner, sAppName, sVersion);
        runDialog();
        Log.close();
        return 0;
    }
    catch (Exception oError)
    {
        Log.exception(oError);
        Log.close();
        MessageBox.Show("HomerDev stopped: " + oError.Message + "\r\nThe log in %LOCALAPPDATA%\\HomerDev\\logs has the details.", sAppName, MessageBoxButtons.OK, MessageBoxIcon.Error);
        return 1;
    }
}

} // class Program

} // namespace HomerDev
