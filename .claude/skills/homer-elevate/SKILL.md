---
name: homer-elevate
description: >-
  Adds or fixes the Elevate Version feature of a Homer Tools app: F11 checks
  GitHub for a newer release and offers to fetch and run its installer, from
  the Help menu of a multiple-document (MDI) app or from the Help box of a
  single-dialog app, in C# or Python, through the kit's Elevate class. Use when
  an app needs an update check, when F11 or "Elevate Version" misbehaves, or
  when the Help box or Help menu should report the version.
---

# Elevate Version

"Elevate" is the Homer word for updating a program to its newest release, and
F11 is its key (elevate sounds like eleven). One kit class does it for every
app: C# `Elevate` (exec/CSharp/Elevate.cs) and Python `elevate`
(exec/Python/elevate.py), the same functions and sentences in both.

## Configure once, at startup

Right after the log starts, with the version the build stamped:

```csharp
Elevate.configure("JamalMazrui", "<App>", BuildVersion.Version);
```

```python
import elevate
elevate.configure("JamalMazrui", "<App>", sVersion)
```

The repository name must be the app's; the release asset it fetches is
`<App>_setup.exe`, matched in any case (EdSharp's is `EdSharp_Setup.exe`).

## A multiple-document app: the Help menu

The Help menu carries **Elevate Version**, F11, beside the F1 family (F1 guide,
Shift+F1 history, Alt+F1 About, Control+F1 key describer). Its trigger letter
is V, the first letter of a word of its name, unless an earlier item on the
menu claimed it. Add it to the app's KeyMap table so the key describer and the
hotkey list know it, and handle it with the one call:

```csharp
void helpElevateClicked(object oSender, EventArgs e) { Elevate.offer(this); }
```

## A single-dialog app: the Help box

An Lbc dialog's Help box (F1, or its Guide or Help button) ends with the
version when Elevate is configured: "This is version 1.19.6, the newest on
the web" or "Version 1.19.7 is on the web". Its buttons become Yes and No --
Yes the default when a newer version exists, No when this one is newest -- and
Yes fetches and starts the installer. Nothing more is needed than
`configure`. F11 in the dialog goes straight to the same question:

```csharp
dlg.commandKey = k => {
    if (k != Keys.F11) return false;
    if (Elevate.offer(dlg.form)) { dlg.form.DialogResult = DialogResult.Cancel; dlg.form.Close(); }
    return true;
};
```

A Python program calls `elevate.offer(hOwner)` with its window's handle
(`frame.GetHandle()` in wx, `form.Handle.ToInt64()` in WinForms, 0 for none).

## What the user hears

`offer` asks GitHub once, with an eight-second limit, so an offline machine
gets "The web could not be checked for a newer one" rather than a hang. Then a
Yes/No box titled "Version": the version found, and "Update to it now?". On
Yes the installer is fetched into the temporary folder and started; it asks
for elevation itself and closes the running app when it needs to, so the app
closes its own dialog and lets it. If the fetch fails, the box names the
releases page.

## Checklist

- `configure` is called at startup with the build's version, not a literal.
- MDI: Help menu item "Elevate Version", F11, in KeyMap, calling `offer`.
- Single dialog: the Help box reports the version; F11 calls `offer`.
- The release on GitHub is marked latest and carries `<App>_setup.exe`
  (the release script confirms both).
- Log the check: "F11: checking the web for a newer version", and the outcome.
