# The Shared Core: What Is Shared, and What Is Left

*5 November 2026, corrected the same day. Every statement here was checked in the code of DbDo, FileDir and HomerView; EdSharp's source was not at hand.*

The rule is Homer DRY: a capability any Homer app could use lives in the kit, and every app takes it from there.

## A correction

An earlier version of this page said that stages 3 to 5 of the integration plan had not been done. That was wrong. It was taken from the stage list in HomerSuite.md, which had not been updated after the October work, instead of from the code. The code shows that **DbDo has routed every key through the kit's router since 19 October 2026** (phase B, after an equivalence check found all 153 of its keys resolving to the same command), and that **FileDir routes every key through it too.** Both use the kit's shared commands.

## Shared and used

- **The router:** DbDo and FileDir route every key through Homer.KeyMap.route.
- **The shared commands:** both use SuiteCommands -- the clipboard family, Say Clipboard, Say Time and the help openers.
- **Dialogs:** Lbc, including Where Am I, Shift+F1 hints, patterns and LbcMessage.
- **Conversions:** every converting app uses the kit's, and the gate fails on private conversion code.
- **Speech:** both use the kit's Say, extra speech included.
- **Building, installing and releasing:** the scripts, the installer components and screen-reader script packaging.
- **HomerView,** an NVDA add-on driving a browser, hands Lbc to the kit and uses NVDA's input help in place of the Key Describer, as the plan agreed.

## Refinements left on what is shared

- **The Key Describer.** DbDo's older describer still answered before the router in describe mode, so the kit's never heard the key. Fixed in DbDo on 5 November 2026: one flag, the kit's; every command carries its menu item and DbDo's own reason when it cannot run; DbDo answers first only for grid keys such as Home and the arrows, which are not commands. *FileDir* still keeps a describer flag of its own beside the kit's, the same refinement to make there.
- **The window family.** The kit's MdiWindows exists, but neither DbDo nor FileDir uses it; each keeps its own frame for windows, F4 and Control+Tab.
- **Updating.** DbDo configures the kit's Elevate, but an older ElevateVersion class of its own is still in DbDo.cs, to be checked and retired.
- **Settings files.** DbDo reads some settings through its own readIniFromFile beside the kit's InixCodec.

## Not in the kit yet

Each of these is built separately by DbDo and FileDir, and EdSharp where it applies; each should be written once in the kit.

- **Marking a list:** one item, a range with F8, all, invert, next and previous marked.
- **The search family for an app's main list:** Lbc's dialog lists have Control+J, Control+K, F3 and Shift+F3, but DbDo's grid and FileDir's list each keep their own memory of the last search.
- **Recent files.**
- **The error window** with its copyable details, beside LbcMessage.
- **Where Am I in the main window:** every Lbc dialog and form answers it from the kit; main windows each answer in their own way.

## The order of work

DbDo's release comes first. After it: FileDir's describer flag; then the window family; then the new components -- marking, the main-list search family, recent files, the error window and main-window Where Am I -- each built once and taken by every app that has its own.

## Measured on 5 November 2026, evening: what each app still keeps of its own

EdSharp's source has now been checked too. Every app compiles the kit's classes from C:\HomerDev\exec\CSharp, not copies -- DbDo and FileDir 23 of the kit's files, EdSharp 12 -- but some still define a class the kit already provides, and use their own instead of the kit's:

- **DbDo:** KeyMap and KeyBinding (its KeyMap delegates its describer to the kit's), and a small Result class whose name the kit also uses.
- **EdSharp:** MdiFrame, MdiChild and Util. Its dialogs are mostly plain Windows Forms: one LbcDialog, so Shift+F1 hints and Control+Slash, which come with LbcForm, do not reach most of them.
- **FileDir:** MdiChild. Its dialogs are the kit's Lbc throughout.

Neither EdSharp nor FileDir has a Hints.inix yet, so Shift+F1 has little specific to say in either.

The shared check's **kit classes** finding lists these at every push, until none is left.

## The order of the rest, one step to a build

Each step is built and released before the next, so a fault is found where it was made:

1. **The window family:** FileDir's MdiChild, then EdSharp's MdiFrame and MdiChild, replaced by the kit's MdiWindows -- one frame for windows, F4 and Control+Tab in every app. *Begun 5 November 2026:* FileDir's Next and Previous Window, Close, Close All but Current and Windows Open now run the kit's MdiWindows. Still FileDir's own: its window list, F4, which shows folders by short name, sorted -- to move into MdiWindows for every app -- and its frame and window classes, which the kit's MdiChild cannot yet replace, since that needs the kit's MdiFrame as parent.
2. **EdSharp's Util:** any helper the kit's Util lacks is moved into the kit first; then EdSharp uses the kit's.
3. **EdSharp's dialogs on Lbc,** so Shift+F1 and Control+Slash reach them as in DbDo and FileDir.
4. **DbDo's KeyMap and KeyBinding:** the kit's, with DbDo's commands registered as FileDir's are.
5. **Hints.inix for EdSharp and FileDir,** written against their own dialogs, as complete as DbDo's.
6. **The components still built in each app** -- marking, the main-list search family, recent files, the error window and main-window Where Am I -- each written once in the kit and taken by every app.
