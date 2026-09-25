// Elevate.cs -- is there a newer version on the web, and would you like it?
//
// HomerDev shared class. "Elevate" is the Homer word for updating a program to
// its newest release (F11: elevate sounds like eleven). One class does it for
// every Homer app: ask GitHub for the latest release, compare it with the
// version this program was built from, and when asked, fetch the setup
// program and start it.
//
// AN APP CONFIGURES IT ONCE, at startup:
//
//   Elevate.configure("JamalMazrui", "HomerScribe", BuildVersion.Version);
//
// After that Lbc's Help box adds a version section and offers the update, and
// an app can call Elevate.check() or Elevate.update() from its own F11.
//
// THE CHECK NEVER HANGS THE PROGRAM. It uses its own request with a short
// timeout rather than Web.getPage's minute, because it runs inside a Help box
// on a machine that may be offline. A failed check is an answer ("could not
// be checked"), not an exception.
//
// WHAT COUNTS AS THE LATEST: the release GitHub marks latest, at
// api.github.com/repos/<owner>/<repo>/releases/latest. Its tag_name, with a
// leading "v" removed, is the version; its asset named <repo>_setup.exe is
// what update() fetches. The JSON is read with two small regular expressions
// rather than a parser, because those two fields are all that is wanted and a
// parser is a dependency.

using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace Homer
{
    public static class Elevate
    {
        // The outcome of a check, so callers can word themselves.
        public const int c_iNotConfigured = -2;
        public const int c_iCheckFailed = -1;
        public const int c_iCurrent = 0;
        public const int c_iNewer = 1;

        const int c_iTimeoutMs = 8000;
        const string c_sApiFormat = "https://api.github.com/repos/{0}/{1}/releases/latest";

        static string sLatestFound = "";
        static string sOwner = "";
        static string sRepo = "";
        static string sSetupUrlFound = "";
        static string sThisVersion = "";

        public static bool isConfigured
        {
            get { return sOwner != "" && sRepo != "" && sThisVersion != ""; }
        }

        public static string thisVersion { get { return sThisVersion; } }
        public static string latestVersion { get { return sLatestFound; } }
        public static string setupUrl { get { return sSetupUrlFound; } }

        public static string repoUrl
        {
            get { return "https://github.com/" + sOwner + "/" + sRepo; }
        }

        public static bool configure(string sOwnerIn, string sRepoIn, string sVersionIn)
        {
            sOwner = (sOwnerIn ?? "").Trim();
            sRepo = (sRepoIn ?? "").Trim();
            sThisVersion = (sVersionIn ?? "").Trim();
            sLatestFound = "";
            sSetupUrlFound = "";
            return isConfigured;
        }

        public static int check()
        {
            // Asks GitHub once. Returns one of the c_i outcomes; on c_iCurrent
            // or c_iNewer, latestVersion and setupUrl are filled in.
            Match oAsset, oTag;
            string sBody, sJsonTag, sJsonUrl;
            if (!isConfigured) return c_iNotConfigured;
            sBody = fetch(string.Format(c_sApiFormat, sOwner, sRepo));
            if (sBody == "") return c_iCheckFailed;
            oTag = Regex.Match(sBody, "\"tag_name\"\\s*:\\s*\"([^\"]+)\"");
            if (!oTag.Success) return c_iCheckFailed;
            sJsonTag = oTag.Groups[1].Value.Trim();
            if (sJsonTag.StartsWith("v") || sJsonTag.StartsWith("V")) sJsonTag = sJsonTag.Substring(1);
            sLatestFound = sJsonTag;
            // The setup program among the assets: <repo>_setup.exe, any case.
            oAsset = Regex.Match(sBody, "\"browser_download_url\"\\s*:\\s*\"([^\"]*" + Regex.Escape(sRepo) + "_setup\\.exe)\"", RegexOptions.IgnoreCase);
            sJsonUrl = oAsset.Success ? oAsset.Groups[1].Value : "";
            sSetupUrlFound = sJsonUrl;
            return isNewer(sLatestFound, sThisVersion) ? c_iNewer : c_iCurrent;
        }

        public static bool isNewer(string sRemote, string sLocal)
        {
            // True when sRemote is a later version than sLocal. Versions that do
            // not parse compare as text, so a strange tag still gets an answer.
            Version oLocal, oRemote;
            if (Version.TryParse(sRemote, out oRemote) && Version.TryParse(sLocal, out oLocal)) return oRemote > oLocal;
            return string.CompareOrdinal(sRemote, sLocal) > 0;
        }

        public static string describe(int iOutcome)
        {
            // The sentence the Help box shows for an outcome of check().
            if (iOutcome == c_iNotConfigured) return "";
            if (iOutcome == c_iCheckFailed) return "This is version " + sThisVersion + ". The web could not be checked for a newer one.";
            if (iOutcome == c_iNewer) return "This is version " + sThisVersion + ". Version " + sLatestFound + " is on the web.";
            return "This is version " + sThisVersion + ", the newest on the web.";
        }

        public static bool update()
        {
            // Fetches the setup program found by check() into the temporary
            // folder and starts it. The setup program asks for elevation itself
            // and closes this program when it needs to. Returns false when
            // nothing could be started; the caller says so.
            string sFile;
            if (sSetupUrlFound == "" && check() < c_iCurrent) return false;
            if (sSetupUrlFound == "") return false;
            sFile = Path.Combine(Path.GetTempPath(), sRepo + "_setup.exe");
            try
            {
                if (File.Exists(sFile)) File.Delete(sFile);
                using (WebClient oClient = new WebClient())
                {
                    oClient.Headers[HttpRequestHeader.UserAgent] = Web.userAgent();
                    oClient.DownloadFile(sSetupUrlFound, sFile);
                }
                if (!File.Exists(sFile) || new FileInfo(sFile).Length == 0) return false;
                Process.Start(sFile);
                return true;
            }
            catch { return false; }
        }

        public static bool offer(IWin32Window oOwner)
        {
            // The whole conversation in one call, for an F11 handler: check,
            // say what was found, and update if the person says yes. Returns
            // true when the setup program was started.
            DialogResult oAnswer;
            int iOutcome;
            iOutcome = check();
            if (iOutcome == c_iNotConfigured) return false;
            if (iOutcome == c_iCheckFailed)
            {
                MessageBox.Show(oOwner, describe(iOutcome), "Version", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return false;
            }
            oAnswer = MessageBox.Show(oOwner, describe(iOutcome) + "\r\n\r\nUpdate to it now?", "Version",
                MessageBoxButtons.YesNo, MessageBoxIcon.Question,
                iOutcome == c_iNewer ? MessageBoxDefaultButton.Button1 : MessageBoxDefaultButton.Button2);
            if (oAnswer != DialogResult.Yes) return false;
            if (update()) return true;
            MessageBox.Show(oOwner, "The setup program could not be fetched. It is at " + repoUrl + "/releases.", "Version",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }

        static string fetch(string sUrl)
        {
            // GitHub's API refuses a request with no User-Agent, so one is
            // sent; the short timeout is the point of this method.
            try
            {
                Web.configure();
                HttpWebRequest oRequest = (HttpWebRequest)WebRequest.Create(sUrl);
                oRequest.Method = "GET";
                oRequest.UserAgent = Web.userAgent();
                oRequest.Accept = "application/vnd.github+json";
                oRequest.Timeout = c_iTimeoutMs;
                oRequest.ReadWriteTimeout = c_iTimeoutMs;
                using (HttpWebResponse oResponse = (HttpWebResponse)oRequest.GetResponse())
                using (StreamReader oReader = new StreamReader(oResponse.GetResponseStream()))
                {
                    return oReader.ReadToEnd();
                }
            }
            catch { return ""; }
        }
    }
}
