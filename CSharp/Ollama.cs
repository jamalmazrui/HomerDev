// Ollama.cs -- talking to a local Ollama server, for Homer Tools.
//
// MOVED INTO THE KIT from FileDir, where it was written. One change was needed:
// FileDir's own Log class writes with write(); the kit's writes with line().
// Everything else compiles as it stood, which is the point of a shared class.
//
// Copyright 2006-2026 by Jamal Mazrui
// MIT License. See License.md, which carries the terms in full.
//
// WHAT THIS IS FOR
//
// FileDir's Translate File command sends the text of a file to a language
// model running on this computer and writes back the translation. Nothing
// leaves the machine: Ollama listens on localhost, and the model files sit in
// the user's own profile. That is the whole point of using it rather than a
// web service -- a person can translate a private document without handing it
// to anybody.
//
// TWO RULES THAT COST TIME TO LEARN, BOTH FROM EDSHARP
//
// 1. NEVER run the ollama command to ask a question. It starts the server in a
//    console of its own when the server is not already running, and that
//    window sits on screen looking like a fault. Ollama answers over a local
//    web interface at port 11434, which opens nothing. Only a download needs
//    the command, and the installer does that hidden.
//
// 2. Choose the model by what is installed rather than making anyone configure
//    anything. The list is asked once per session.
//
// The JSON here is written and read by hand. The alternative is a reference to
// System.Web.Extensions or System.Runtime.Serialization, and the whole
// exchange is one string in and one string out, which does not justify either.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;

namespace Homer {

public static class Ollama {

// The local server. Ollama binds this by default and every program on the
// machine shares it, which is why one installation serves EdSharp, DbDo and
// FileDir alike.
public const string c_sHost = "http://localhost:11434";

// Models in the order FileDir prefers them for translation. qwen2.5:7b is
// markedly better at languages; llama3.2 is smaller, quicker, and good enough
// to try the feature with. Naming them matters: "a stronger model" tells
// nobody what they are getting or what to look for in Ollama afterwards.
public static readonly string[] c_aTranslateModels = {"qwen2.5:7b", "llama3.2"};

private static string sModelListCache = null;

public static string modelList(bool bRefresh) {
// The names Ollama reports, separated by spaces, or an empty string when the
// server is not answering. Asked once and remembered: a cold server takes a
// second or more to reply, and several commands ask.
if (!bRefresh && sModelListCache != null) return sModelListCache;
string sJson = get("/api/tags", 10000);
StringBuilder sb = new StringBuilder();
// Each model appears as "name":"<something>". Reading just those is enough
// to answer "is this model here", which is all anyone asks of the list.
int i = 0;
while (true) {
int iAt = sJson.IndexOf("\"name\"", i);
if (iAt < 0) break;
int iColon = sJson.IndexOf(':', iAt);
if (iColon < 0) break;
int iOpen = sJson.IndexOf('"', iColon);
if (iOpen < 0) break;
int iClose = endOfJsonString(sJson, iOpen);
if (iClose < 0) break;
sb.Append(jsonDecode(sJson.Substring(iOpen + 1, iClose - iOpen - 1)));
sb.Append(' ');
i = iClose + 1;
}
sModelListCache = sb.ToString();
return sModelListCache;
} // modelList method

public static bool isRunning() {
return modelList(false).Length > 0;
} // isRunning method

public static bool hasModel(string sModel) {
if (sModel == null || sModel.Length == 0) return false;
return modelList(false).IndexOf(sModel, StringComparison.OrdinalIgnoreCase) >= 0;
} // hasModel method

public static string bestTranslateModel() {
// The best installed model for translation, or an empty string when none of
// the known ones is there. The caller decides what to say about that; this
// never invents a name.
foreach (string sModel in c_aTranslateModels) if (hasModel(sModel)) return sModel;
return "";
} // bestTranslateModel method

public static string generate(string sModel, string sPrompt, int iTimeoutMs, out string sError) {
// One prompt in, one answer out, with streaming off so the reply arrives as a
// single response rather than a sequence this would have to reassemble.
sError = "";
StringBuilder sbBody = new StringBuilder();
sbBody.Append("{\"model\":\"");
sbBody.Append(jsonEncode(sModel));
sbBody.Append("\",\"prompt\":\"");
sbBody.Append(jsonEncode(sPrompt));
sbBody.Append("\",\"stream\":false}");
Homer.Log.line("Ollama: asking " + sModel + " a prompt of " + sPrompt.Length + " characters.");
string sReply = post("/api/generate", sbBody.ToString(), iTimeoutMs, out sError);
if (sError.Length > 0) {
Homer.Log.line("Ollama: " + sError);
return "";
}
Homer.Log.line("Ollama: answered.");
return fieldOf(sReply, "response");
} // generate method

public static string fieldOf(string sJson, string sField) {
// The value of one top-level string field. Enough for the single field this
// exchange needs, and honest about being no more than that.
if (sJson == null) return "";
int iAt = sJson.IndexOf("\"" + sField + "\"");
if (iAt < 0) return "";
int iColon = sJson.IndexOf(':', iAt);
if (iColon < 0) return "";
int iOpen = sJson.IndexOf('"', iColon);
if (iOpen < 0) return "";
int iClose = endOfJsonString(sJson, iOpen);
if (iClose < 0) return "";
return jsonDecode(sJson.Substring(iOpen + 1, iClose - iOpen - 1));
} // fieldOf method

private static int endOfJsonString(string sJson, int iOpenQuote) {
// The closing quote of a JSON string that starts at iOpenQuote, skipping any
// quote that a backslash escapes. Counting backslashes matters: a string may
// legitimately end in one that is itself escaped.
for (int i = iOpenQuote + 1; i < sJson.Length; i++) {
if (sJson[i] != '"') continue;
int iSlashes = 0;
int j = i - 1;
while (j > iOpenQuote && sJson[j] == '\\') { iSlashes++; j--; }
if (iSlashes % 2 == 0) return i;
}
return -1;
} // endOfJsonString method

public static string jsonEncode(string sText) {
if (sText == null) return "";
StringBuilder sb = new StringBuilder(sText.Length + 32);
foreach (char c in sText) {
if (c == '"') sb.Append("\\\"");
else if (c == '\\') sb.Append("\\\\");
else if (c == '\n') sb.Append("\\n");
else if (c == '\r') sb.Append("\\r");
else if (c == '\t') sb.Append("\\t");
else if (c < ' ') sb.Append("\\u").Append(((int) c).ToString("x4"));
else sb.Append(c);
}
return sb.ToString();
} // jsonEncode method

public static string jsonDecode(string sText) {
if (sText == null) return "";
StringBuilder sb = new StringBuilder(sText.Length);
for (int i = 0; i < sText.Length; i++) {
char c = sText[i];
if (c != '\\') { sb.Append(c); continue; }
i++;
if (i >= sText.Length) break;
char cNext = sText[i];
if (cNext == 'n') sb.Append('\n');
else if (cNext == 'r') sb.Append('\r');
else if (cNext == 't') sb.Append('\t');
else if (cNext == 'b') sb.Append('\b');
else if (cNext == 'f') sb.Append('\f');
else if (cNext == 'u' && i + 4 < sText.Length) {
int iCode = 0;
if (int.TryParse(sText.Substring(i + 1, 4), System.Globalization.NumberStyles.HexNumber, System.Globalization.CultureInfo.InvariantCulture, out iCode)) {
sb.Append((char) iCode);
i += 4;
}
}
else sb.Append(cNext);
}
return sb.ToString();
} // jsonDecode method

private static string get(string sPath, int iTimeoutMs) {
// Failure is silence here on purpose: every caller of this treats "no answer"
// as "Ollama is not running", which is the only thing a failed /api/tags can
// mean that the person can act on.
try {
HttpWebRequest request = (HttpWebRequest) WebRequest.Create(c_sHost + sPath);
request.Method = "GET";
request.Timeout = iTimeoutMs;
request.ReadWriteTimeout = iTimeoutMs;
using (HttpWebResponse response = (HttpWebResponse) request.GetResponse())
using (StreamReader reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8))
return reader.ReadToEnd();
}
catch {
return "";
}
} // get method

private static string post(string sPath, string sBody, int iTimeoutMs, out string sError) {
sError = "";
try {
HttpWebRequest request = (HttpWebRequest) WebRequest.Create(c_sHost + sPath);
request.Method = "POST";
request.ContentType = "application/json";
request.Timeout = iTimeoutMs;
request.ReadWriteTimeout = iTimeoutMs;
byte[] aBody = Encoding.UTF8.GetBytes(sBody);
request.ContentLength = aBody.Length;
using (Stream stream = request.GetRequestStream()) stream.Write(aBody, 0, aBody.Length);
using (HttpWebResponse response = (HttpWebResponse) request.GetResponse())
using (StreamReader reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8))
return reader.ReadToEnd();
}
catch (WebException ex) {
// A refused connection is the ordinary case -- Ollama is not running -- and
// deserves a sentence a person can act on rather than a stack trace.
if (ex.Status == WebExceptionStatus.ConnectFailure)
sError = "Ollama is not running. Start it, or install it with installOllama.cmd in the FileDir folder.";
else if (ex.Status == WebExceptionStatus.Timeout)
sError = "The model did not answer in time. A large file may need a longer setting, or a smaller model.";
else
sError = ex.Message;
return "";
}
catch (Exception ex) {
sError = ex.Message;
return "";
}
} // post method

public static List<string> splitForModel(string sText, int iMaxChars) {
// Break text into pieces a model can hold, on blank lines where possible so a
// paragraph is never cut in half, and on line ends otherwise. A piece longer
// than the limit with no break in it is passed whole rather than chopped
// mid-word: the model handles that better than a broken sentence.
List<string> lsParts = new List<string>();
if (sText == null || sText.Length == 0) return lsParts;
string[] aParagraphs = sText.Replace("\r\n", "\n").Split(new string[] {"\n\n"}, StringSplitOptions.None);
StringBuilder sbPart = new StringBuilder();
foreach (string sParagraph in aParagraphs) {
if (sbPart.Length > 0 && sbPart.Length + sParagraph.Length + 2 > iMaxChars) {
lsParts.Add(sbPart.ToString());
sbPart.Length = 0;
}
if (sbPart.Length > 0) sbPart.Append("\n\n");
sbPart.Append(sParagraph);
}
if (sbPart.Length > 0) lsParts.Add(sbPart.ToString());
return lsParts;
} // splitForModel method

} // Ollama class

} // Homer namespace
