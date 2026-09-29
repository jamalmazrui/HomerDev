// Paths.cs -- part of the shared Homer toolkit (namespace Homer).
//
// WHERE A HOMER APP PUTS ITS FILES, AND WHY THE NAMES ARE WHAT THEY ARE.
//
// A screen reader user moves through a folder listing by first letter. Nine
// folders whose names all begin with the same letter cost nine keystrokes each
// time; nine whose initials differ cost one. So every folder in the Homer
// layout starts with a different letter, and the letter is the fast way in:
//
//     c  configs     settings that decide how the program starts
//     d  data        databases and seed data
//     h  help        the documents: the guide, the tutorials, the history
//     e  exec        the program itself: .exe, .dll, .py, .vbs
//     s  scripts     scripts, add-ons and plugins that change behaviour later
//     l  logs        one file per session
//     r  results     what the program produced
//     //     t  temp        scratch, deletable at the start of the next run
//     t  templates   files a user copies and fills in
//
// TWO t NAMES, AND THEY NEVER MEET. temp exists only in the per-user tree;
// templates exists only in the installed tree. A listing therefore never holds
// both, and first-letter navigation stays exact. The rule is worth keeping
// deliberately: a temp folder under Program Files could not be written to
// anyway, since that is the whole reason the per-user tree exists.
//
// THREE TREES, AND WHAT EACH HOLDS.
//
//   The INSTALLED tree, C:\Program Files\<App>, read-only to the user:
//       <App>\configs  <App>\data  <App>\exec  <App>\help
//       <App>\scripts  <App>\templates
//       and the documents at its root, where a person looking for the ReadMe
//       expects to find it.
//
//   The PER-USER tree, %LOCALAPPDATA%\<App>, which the program owns and writes:
//       <App>\configs  <App>\data  <App>\scripts  <App>\logs
//       <App>\results  <App>\temp
//       No exec, no templates: those are shipped, not made.
//
//   The DEVELOPMENT folder, C:\<App>, stays flat. It is a git repository, and
//   every tool that reads one -- the compiler, the installer script, the
//   release script -- expects the source at the top. The structure is what the
//   build SHIPS INTO, not what the developer works in.
//
// READING AND WRITING. A setting shipped with the program is read from the
// installed tree; the user's own copy is written to the per-user tree and read
// first. configFile below does exactly that, which is the pattern every Homer
// app needs and none should write twice.
//
//     using Homer;
//     Paths.start("JobDo");
//     string sInix = Paths.configFile("JobDo.inix");   // the user's, else the shipped one
//     string sOut  = Paths.results();                  // where output goes
//     Paths.clearTemp();                               // at startup, once
//
// Nothing here throws. A folder that cannot be made comes back as a path that
// does not exist, and the caller's own error handling deals with it.

using System;
using System.IO;
using System.Reflection;

namespace Homer {

public static class Paths
{
    private static string sAppName = "";

    // ------- starting -------

    // start: name the app, which is all this class needs. Call it once, beside
    // Log.start. Without it the name is taken from the running executable.
    public static bool start(string sAppNameGiven)
    {
        sAppName = (sAppNameGiven ?? "").Trim();
        return sAppName != "";
    }

    public static string appName
    {
        get
        {
            if (sAppName != "") return sAppName;
            try
            {
                Assembly oAssembly = Assembly.GetEntryAssembly();
                if (oAssembly != null)
                    sAppName = Path.GetFileNameWithoutExtension(oAssembly.Location);
            }
            catch (Exception)
            {
            }
            if (sAppName == "") sAppName = "Homer";
            return sAppName;
        }
    }

    // ------- the two trees -------

    // installedFolder: where the program was installed, which is the folder the
    // executable sits in, or its parent when the executable is in exec.
    public static string installedFolder
    {
        get
        {
            string sHere = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
            if (string.Equals(Path.GetFileName(sHere), "exec", StringComparison.OrdinalIgnoreCase))
                return Path.GetDirectoryName(sHere);
            return sHere;
        }
    }

    // userFolder: %LOCALAPPDATA%\<App>, which the program owns.
    public static string userFolder
    {
        get
        {
            return Path.Combine(Environment.GetFolderPath(
                Environment.SpecialFolder.LocalApplicationData), appName);
        }
    }

    // ------- the folders, by the letter a user types -------
    //
    // Each returns a path in the PER-USER tree and makes it when it is missing,
    // because these are the ones a program writes to. The shipped counterparts
    // are below, and they are never created.

    public static string configs() { return madeUnder(userFolder, "configs"); }
    public static string data() { return madeUnder(userFolder, "data"); }
    public static string scripts() { return madeUnder(userFolder, "scripts"); }
    public static string logs() { return madeUnder(userFolder, "logs"); }
    public static string results() { return madeUnder(userFolder, "results"); }
    public static string temp() { return madeUnder(userFolder, "temp"); }

    // The shipped folders, read-only, never created here: a program that has to
    // create its own templates folder has no templates.
    public static string shippedConfigs() { return Path.Combine(installedFolder, "configs"); }
    public static string shippedData() { return Path.Combine(installedFolder, "data"); }
    public static string shippedExec() { return Path.Combine(installedFolder, "exec"); }
    public static string shippedHelp() { return Path.Combine(installedFolder, "help"); }
    public static string shippedScripts() { return Path.Combine(installedFolder, "scripts"); }
        public static string shippedTemplates() { return Path.Combine(installedFolder, "templates"); }

    private static string madeUnder(string sParent, string sChild)
    {
        string sPath = Path.Combine(sParent, sChild);
        try { Directory.CreateDirectory(sPath); } catch (Exception) { }
        return sPath;
    }

    // ------- the pattern every app needs -------

    // configFile: the user's copy of a settings file, falling back to the one
    // that shipped with the program.
    //
    // This is the whole of "read the shipped default, write the user's change",
    // and it is written here once rather than in every app. The answer is always
    // a path in the per-user tree when one exists there, so a caller may write
    // to what it gets back.
    public static string configFile(string sFileName)
    {
        string sUser = Path.Combine(configs(), sFileName);
        if (File.Exists(sUser)) return sUser;
        string sShipped = Path.Combine(shippedConfigs(), sFileName);
        if (File.Exists(sShipped))
        {
            try { File.Copy(sShipped, sUser); return sUser; } catch (Exception) { }
            return sShipped;
        }
        return sUser;
    }

    // clearTemp: empty the temp folder, at startup, once.
    //
    // Anything still in there is what a previous run could not clean up after
    // itself, which is exactly what the folder is for: a crash leaves its
    // half-written files somewhere known rather than somewhere shared.
    public static int clearTemp()
    {
        int iRemoved = 0;
        try
        {
            DirectoryInfo oTemp = new DirectoryInfo(temp());
            foreach (FileInfo oFile in oTemp.GetFiles())
            {
                try { oFile.Delete(); iRemoved++; } catch (Exception) { }
            }
            foreach (DirectoryInfo oFolder in oTemp.GetDirectories())
            {
                try { oFolder.Delete(true); iRemoved++; } catch (Exception) { }
            }
        }
        catch (Exception)
        {
        }
        return iRemoved;
    }

    // tempFile: a name inside temp that nothing else is using.
    public static string tempFile(string sExtension)
    {
        if (sExtension == null) sExtension = ".tmp";
        if (!sExtension.StartsWith(".")) sExtension = "." + sExtension;
        return Path.Combine(temp(), appName + "-" +
            DateTime.Now.ToString("yyyyMMdd-HHmmss-fff") + sExtension);
    }
}

} // namespace Homer (Paths.cs)
