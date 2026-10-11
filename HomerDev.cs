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

private const int c_iAiTimeoutMs = 300000;
private const int c_iContextCharsMost = 24000;
private const int c_iDescriptionCharsMost = 140;
private const string c_sAppName = "HomerDev";
private const string c_sOwner = "JamalMazrui";

// The models tried first for the chat, in order; any other installed model is used when none of these is there.
private static readonly string[] c_asPreferredModels = { "qwen2.5:7b", "llama3.1:8b", "llama3.2", "gemma2:9b", "mistral" };

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
    if (sClean.Length > c_iDescriptionCharsMost) sClean = sClean.Substring(0, c_iDescriptionCharsMost - 3).TrimEnd() + "...";
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
        MessageBox.Show(owner, "Could not open " + oItem.sName + ": " + oError.Message, c_sAppName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
    }
    return true;
}

// ---- the inix format, explained and read live ----

private const string c_sInixExample =
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
    sb.Append(c_sInixExample);
    sb.AppendLine();
    sb.AppendLine("What the kit's own reader, InixCodec, made of it just now:");
    sb.AppendLine();
    List<InixCodec.Section> lsSections = InixCodec.parseLines(c_sInixExample.Replace("\r\n", "\n").Split('\n'));
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

private const string c_sLayoutCode =
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
    sb.Append(c_sLayoutCode);
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
    foreach (string sModel in c_asPreferredModels) if (Ollama.hasModel(sModel)) return sModel;
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
        if (sb.Length > c_iContextCharsMost) { sb.AppendLine("[the list continues]"); break; }
        sb.AppendLine(oItem.ToString() + " -- " + oItem.sPath.Substring(Math.Min(sKit.Length, oItem.sPath.Length)).TrimStart('\\'));
    }
    return sb.ToString();
}

private static bool runChat(IWin32Window owner)
{
    string sContext, sModel;
    sModel = chooseModel();
    if (sModel.Length == 0)
    {
        MessageBox.Show(owner, "The local AI is not answering: Ollama is not running, or it has no model. HomerDev's setup program offers Ollama and a model; run it again and leave those boxes ticked.", c_sAppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
        return false;
    }
    sContext = kitContext();
    Log.keyValue("Chat model", sModel);
    Log.keyValue("Chat context characters", "" + sContext.Length);
    StringBuilder sbHistory = new StringBuilder();
    using (LbcDialog dlg = new LbcDialog("Ask the local AI about HomerDev", owner))
    {
        TextBox txtConversation = dlg.addMemoBox("&Conversation:", "", "Your questions and " + sModel + "'s answers, newest last. It runs on this computer; nothing leaves it.");
        txtConversation.ReadOnly = true;
        dlg.addBand();
        TextBox txtQuestion = dlg.addInputBox("&Question:", "", "Ask about HomerDev: what a skill does, where a template is, how to start an app. Enter sends it.");
        Button btnSend = dlg.addButton("&Send", "Ask the local AI the question.");
        Button btnVoice = dlg.addButton("&Voice", "Ask by voice: a rising tone, then speak; press Voice again, or simply stop talking, and Whisper writes what you said into the question. Escape throws a recording away. Everything stays on this computer.");
        dlg.endBand();
        CheckBox chkSendHeard = dlg.addCheckBox("Send &when heard", false, "Send a spoken question as soon as it is written, instead of letting you check it first.");
        btnSend.Click += delegate(object oSender, EventArgs evArgs)
        {
            string sQuestion = txtQuestion.Text.Trim();
            if (sQuestion.Length == 0) return;
            btnSend.Enabled = false;
            txtQuestion.ReadOnly = true;
            // PROGRESS WHILE IT THINKS (11 October 2026): a local model can take a minute or more, and the first question
            // longer while the model loads, so silence sounded like a hang. Every ten seconds the dialog says how long it
            // has waited -- briefly, the one thing the reader cannot know -- and the status line says the same.
            int iWaited = 0;
            System.Windows.Forms.Timer oTicker = new System.Windows.Forms.Timer();
            oTicker.Interval = 10000;
            oTicker.Tick += delegate(object oTickSender, EventArgs evTick)
            {
                iWaited += 10;
                dlg.setStatusText("Waiting for " + sModel + ", " + iWaited + " seconds");
                Say.say(iWaited + " seconds");
            };
            Say.say("Asking " + sModel + "; it may take a minute");
            dlg.setStatusText("Waiting for " + sModel);
            DateTime dtAsked = DateTime.Now;
            oTicker.Start();
            string sPrompt = sContext + "\r\n" + sbHistory.ToString() + "Question: " + sQuestion + "\r\nAnswer:";
            Log.info("Chat question: " + sQuestion);
            Thread oWorker = new Thread(delegate()
            {
                string sError;
                string sAnswer = Ollama.generate(sModel, sPrompt, c_iAiTimeoutMs, out sError);
                dlg.form.BeginInvoke((MethodInvoker) delegate()
                {
                    oTicker.Stop();
                    oTicker.Dispose();
                    if (string.IsNullOrEmpty(sAnswer)) sAnswer = "No answer came back" + (string.IsNullOrEmpty(sError) ? "." : ": " + sError);
                    sAnswer = plainText(sAnswer);
                    Log.info("Chat answer: " + sAnswer.Length + " characters" + (string.IsNullOrEmpty(sError) ? "" : "; error " + sError));
                    sbHistory.Append("Question: ").Append(sQuestion).Append("\r\nAnswer: ").Append(sAnswer).Append("\r\n");
                    int iStart = txtConversation.TextLength;
                    txtConversation.AppendText((iStart > 0 ? "\r\n" : "") + "You: " + sQuestion + "\r\n" + sModel + ": " + sAnswer.Replace("\n", "\r\n").Replace("\r\r\n", "\r\n") + "\r\n");
                    txtQuestion.Text = "";
                    txtQuestion.ReadOnly = false;
                    btnSend.Enabled = true;
                    // The answer is read where it begins: focus goes to its first line, so Down Arrow reads it.
                    txtConversation.Focus();
                    txtConversation.SelectionStart = iStart + (iStart > 0 ? 2 : 0);
                    txtConversation.SelectionLength = 0;
                    txtConversation.ScrollToCaret();
                    int iTook = (int) Math.Round((DateTime.Now - dtAsked).TotalSeconds);
                    dlg.setStatusText("Answered in " + iTook + (iTook == 1 ? " second" : " seconds"));
                    Say.say("Answered in " + iTook + (iTook == 1 ? " second" : " seconds"));
                });
            });
            oWorker.IsBackground = true;
            oWorker.Start();
        };
        // ---- VOICE (11 October 2026) ----
        // The convention of Windows+H: one key starts and stops; silence after speech also stops; Escape cancels.
        // Tones, not speech, mark the start and the end, so the screen reader is not recorded into the question.
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
                string sError;
                string sText = Voice.transcribe(sWav, 120000, out sError);
                try { File.Delete(sWav); } catch { }
                dlg.form.BeginInvoke((MethodInvoker) delegate()
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
                    txtQuestion.Text = sText;
                    txtQuestion.Focus();
                    txtQuestion.SelectionStart = sText.Length;
                    dlg.setStatusText("Heard: " + sText);
                    Say.say("Heard: " + sText);
                    if (chkSendHeard.Checked) btnSend.PerformClick();
                });
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
                MessageBox.Show(dlg.form, "Asking by voice needs Whisper, which turns speech into text on this computer. HomerDev's setup program offers it: run it again and leave Whisper ticked.", c_sAppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            oRecorder = new VoiceRecorder();
            Console.Beep(440, 90); Console.Beep(660, 120);
            string sProblem = oRecorder.start();
            if (sProblem.Length > 0)
            {
                oRecorder = null;
                MessageBox.Show(dlg.form, "Could not listen: " + sProblem + ".", c_sAppName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            dlg.setStatusText("Listening; press Voice again or stop talking to finish, Escape to cancel");
            oListen.Start();
        };
        // Escape while listening throws the recording away and keeps the dialog open; otherwise it closes, as ever.
        dlg.commandKey = delegate(Keys keys)
        {
            if (keys != Keys.Escape || oRecorder == null) return false;
            oListen.Stop();
            oRecorder.cancel();
            oRecorder.Dispose();
            oRecorder = null;
            Console.Beep(330, 150);
            dlg.setStatusText("Recording thrown away");
            Say.say("Cancelled");
            return true;
        };
        dlg.form.AcceptButton = btnSend;
        dlg.setInitialFocus(txtQuestion);
        dlg.runWithButtons(new string[] { "Close" });
    }
    return true;
}

// ---- connecting the AI tools ----

// connectAiTools: runs scripts\\connectAI, which tells Claude Code, Codex, Gemini CLI and Antigravity where the kit is,
// and shows what it said. Its own log has the detail.
private static bool connectAiTools(IWin32Window owner)
{
    string sScript = Path.Combine(sKit, "scripts", "connectAI.cmd");
    if (!File.Exists(sScript))
    {
        MessageBox.Show(owner, "scripts\\connectAI.cmd is not in the kit at " + sKit + ".", c_sAppName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
        return false;
    }
    Say.say("Connecting");
    ProcessStartInfo oStart = new ProcessStartInfo("cmd.exe", "/c \"\"" + sScript + "\"\"");
    oStart.UseShellExecute = false;
    oStart.CreateNoWindow = true;
    oStart.RedirectStandardOutput = true;
    oStart.RedirectStandardError = true;
    oStart.WorkingDirectory = sKit;
    string sOut;
    int iCode;
    using (Process oRun = Process.Start(oStart))
    {
        sOut = oRun.StandardOutput.ReadToEnd() + oRun.StandardError.ReadToEnd();
        oRun.WaitForExit();
        iCode = oRun.ExitCode;
    }
    Log.command("connectAI", iCode);
    HelpDialog.show(owner, "Connect AI tools", sOut.Trim() + "\r\n\r\nTo undo it, run scripts\\connectAI --remove in the kit's folder.");
    return iCode == 0;
}

// ---- the dialog ----

private static bool runDialog()
{
    ListBox lbItems;
    List<string> lsLines = new List<string>();
    loadItems();
    foreach (KitItem oItem in lsItems) lsLines.Add(oItem.ToString());
    using (LbcDialog dlg = new LbcDialog(c_sAppName, null))
    {
        lbItems = dlg.addPickBox("&Kit contents:", lsLines, lsLines.Count > 0 ? lsLines[0] : "",
            "Everything the kit holds, by kind and then by name: documents open in your browser, samples run, and every other file opens in a window you read line by line. Enter opens the one you are on.");
        dlg.addBand();
        Button btnOpen = dlg.addButton("&Open", "Open the item you are on in the list.");
        Button btnPlay = dlg.addButton("&Play tutorials", "Play the kit's ten spoken tutorials in the Homer Player: Enter plays a walk, Down Arrow moves to the next.");
        dlg.endBand();
        dlg.addBand();
        Button btnInix = dlg.addButton("&Inix explained", "What the inix format is, with an example read by the kit's own reader.");
        Button btnLayout = dlg.addButton("&Layout by Code", "How every Homer dialog is made, then a dialog that code builds.");
        Button btnAsk = dlg.addButton("&Ask the local AI", "Ask the AI on this computer what the kit can do and how, with a map of the kit as its context.");
        Button btnConnect = dlg.addButton("Connect AI &tools", "Tell Claude Code, Codex, Gemini CLI and Antigravity where the kit is, once, so in any project they find its skills and code when you mention Homer.");
        dlg.endBand();

        btnOpen.Click += delegate(object oSender, EventArgs evArgs)
        {
            int iRow = dlg.listSourceIndex(lbItems, lbItems.SelectedIndex);
            if (iRow >= 0 && iRow < lsItems.Count) openItem(dlg.form, lsItems[iRow]);
        };
        btnPlay.Click += delegate(object oSender, EventArgs evArgs)
        {
            if (!MediaPlayer.playTutorials(dlg.form, c_sAppName, Path.Combine(sKit, "help")))
                MessageBox.Show(dlg.form, "No tutorial is installed in " + Path.Combine(sKit, "help", "tutorials") + ".", c_sAppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
        };
        btnInix.Click += delegate(object oSender, EventArgs evArgs) { showInix(dlg.form); };
        btnLayout.Click += delegate(object oSender, EventArgs evArgs) { showLayout(dlg.form); };
        btnAsk.Click += delegate(object oSender, EventArgs evArgs) { runChat(dlg.form); };
        btnConnect.Click += delegate(object oSender, EventArgs evArgs) { connectAiTools(dlg.form); };

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
        dlg.setStatusText(lsItems.Count + (lsItems.Count == 1 ? " item" : " items") + " in HomerDev " + sVersion);
        dlg.runWithButtons(new string[] { "Close" });
    }
    return true;
}

[STAThread]
public static int Main(string[] aArguments)
{
    Application.EnableVisualStyles();
    Application.SetCompatibleTextRenderingDefault(false);
    Paths.start(c_sAppName);
    Log.start(c_sAppName);
    sKit = kitFolder();
    sVersion = readVersion();
    Log.keyValue("Kit folder", sKit);
    Log.keyValue("Version", sVersion);
    try
    {
        Elevate.configure(c_sOwner, c_sAppName, sVersion);
        runDialog();
        Log.close();
        return 0;
    }
    catch (Exception oError)
    {
        Log.exception(oError);
        Log.close();
        MessageBox.Show("HomerDev stopped: " + oError.Message + "\r\nThe log in %LOCALAPPDATA%\\HomerDev\\logs has the details.", c_sAppName, MessageBoxButtons.OK, MessageBoxIcon.Error);
        return 1;
    }
}

} // class Program

} // namespace HomerDev
