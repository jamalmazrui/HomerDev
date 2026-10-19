---
title: "Homer Command Echo"
author: "Jamal Mazrui"
---

This page records, for every menu command in the HomerDev frame, DbDo, EdSharp and FileDir, whether it says its own name as it starts. It was made on 19 October 2026 by applying the suite's rule to each command's menu caption, and is meant for review. A command in the wrong group is corrected in its app's code, or, on the frame, with bNoEcho.

## The Rule

A command's name is spoken as it starts if and only if nothing else would tell you at once that the command you meant is under way. The rule is KeyMap.shouldEcho in the kit, so every app decides alike. Each command falls in one of five groups:

- **Dialog:** its caption ends in "...". The dialog's title, close to the command's name, is the echo.
- **Focus:** it moves the focus, as an arrow key does, so the screen reader says where you landed. Its first word is Back, Bottom, Close, End, Exit, First, Forward, Go, Home, Jump, Last, Next, Open, Previous, Prior, Top, or any word is Find, Go, Jump, Keywords, Search.
- **Result:** a Say command or a toggle, which speaks its answer or its new state.
- **Spoken:** every other command says its name at once, before its work, because it changes something the screen reader does not announce, and may take a noticeable moment. Clear Filter is the example.
- **Window:** it opens a window or document that names itself. Its first word is Chat, Describe, Inspect, Mail, Pick, Play, Show, Statistics, Test, Where; its name ends in Console or Summary; or it is one of About, Developer Guide, Documentation, Frequently Asked Questions, History of Changes, Hotkeys, License, ReadMe, Tutorials, Tutorials Transcript.

## Where It Applies Now

- **DbDo and the HomerDev frame** follow the rule as of this release. DbDo's Command Echo Toggle and its setting are retired.
- **EdSharp and FileDir** still speak from their own handlers: EdSharp by a speak or silent mark on each menu item, FileDir by a line at the start of many handlers. The groups below show what the rule would do for them; their handlers move to it with their stage-4 work.
- **HomerView** follows in stage 5, where the browser speaks most results itself.

## For Review

- **Clipboard copies in DbDo,** such as Copy Cell to Clipboard on Control+C, are Spoken. If a handler already says what it copied, that handler's own words should go, or the command should join Result.
- **Delete Record in DbDo,** Control+D, is Spoken, and then asks to confirm. If the confirmation's title is enough, it should join Dialog by gaining "..." in its caption.

## DbDo

182 commands: 27 spoken, 58 dialog, 26 window, 28 focus, 43 result.

### DbDo: Spoken

- Announcement
- Append Cell to Clipboard (Alt+C)
- Append Record to Clipboard (Alt+Shift+C)
- Clear Bookmark (Control+Shift+B)
- Clear Filter (Control+Shift+F)
- Clear Sort
- Complete Mark (Shift+F8)
- Complete Unmark to Anchor (Alt+Shift+F8)
- Copy Cell to Clipboard (Control+C)
- Copy Column to Clipboard
- Copy Grid as TSV to Clipboard
- Copy Record (Control+Shift+C)
- Copy Visible Cells as TSV to Clipboard
- Delete Record (Control+D)
- Delete Without Confirmation (Control+Shift+D)
- Invert Marked (Alt+Shift+I)
- Mark All (Control+A)
- Mark Record (Control+M)
- Refresh View (F5)
- Reverse Order (Alt+Shift+O)
- Save (Control+S)
- Save Bookmark (Control+B)
- Start Mark (F8)
- Start Unmark (Alt+F8)
- Table Properties (Alt+Enter)
- Unmark All (Control+Shift+A)
- Unmark Record (Control+Shift+M)

### DbDo: Dialog

- Add Table
- Alternate Menu (Alt+F10)
- Backup Database
- Choose Table (Control+T)
- Choose View
- Choose Visible Columns
- Compare Database
- Current Windows (F4)
- Edit Cell (F2)
- Edit Notes (Alt+Shift+N)
- Edit Settings (Alt+Shift+E)
- Edit Snippet (Control+Shift+E)
- Edit Tags (Alt+Shift+T)
- Edit URL (Alt+Shift+U)
- Edit View (Control+E)
- Elevate Version (F11)
- Email Log File
- Enter Child Table (Alt+Right)
- Evaluate Expression (Control+Oemplus)
- Export Data (Alt+X)
- Extract with Regex (Control+Shift+X)
- Facet Column
- File GitHub Issue
- Filter by Regex
- Filter Records (Control+F)
- Find Regex (Control+F3)
- Generate from Grid (Alt+Shift+G)
- Go to Record (Control+G)
- Graphics Column (Control+Shift+G)
- Import (Alt+I)
- Invoke Script (Control+Shift+I)
- Jump to Next Initial
- Jump to Record (Control+J)
- Keywords (Control+K)
- List Bookmarks (Alt+B)
- Merge Data (Alt+M)
- New Copy (Control+Shift+N)
- New Database
- New Record (Control+N)
- Open as Managed Copy
- Open Cell Value (Control+Enter)
- Open Database (Control+O)
- Open Table (Control+Shift+O)
- Open Table in New Window (Control+Shift+T)
- Open Template Database (Alt+Shift+D)
- Order Records (Alt+O)
- Print (Control+P)
- Query (Control+Q)
- Query History (Alt+Shift+Q)
- Recent Files (Alt+R)
- Regex Replace (Control+Shift+R)
- Related Records
- Replace Column (Control+R)
- Run Report (Alt+Shift+R)
- Save As (Control+Shift+S)
- Select Columns to Display (Alt+S)
- Transfer Import
- Update from Template

### DbDo: Window

- About (Alt+F1)
- Chat about Table (Shift+F12)
- Chat with AI (F12)
- Database Summary (Alt+D)
- Describe Table
- Developer Guide
- Documentation (F1)
- Frequently Asked Questions
- History of Changes (Shift+F1)
- Hotkey Summary (Alt+Shift+H)
- Hotkeys (Control+Shift+F1)
- Inspect Record (Control+I)
- License
- Mail Record
- Pick Value (Control+F2)
- Play Stream (Alt+Shift+P)
- Play Tutorials
- ReadMe (Alt+Shift+F1)
- Show Log Location
- Show Schema
- Sqlean Console (Control+Shift+Oemtilde)
- Statistics from Column (Alt+Shift+S)
- Table Summary (Alt+T)
- Test Integrity
- Tutorials Transcript
- Where Am I

### DbDo: Focus

- Close All But Current Window (Control+Shift+F4)
- Close Database
- Close Window (Control+F4)
- Exit Child Table (Alt+Left)
- Exit DbDo (Alt+F4)
- Exit to Root Table (Alt+Home)
- First Record
- Last Record
- Next Record
- Next Table or View (Control+F6)
- Next Visited Table (Alt+F6)
- Next Window (Control+Tab)
- Open Command Prompt (Control+OemQuestion)
- Open Dot Prompt (Control+Oemtilde)
- Open in Explorer (Alt+OemPipe)
- Open Script Folder
- Open Url (Control+Shift+U)
- Open Website
- Previous Record
- Previous Table or View (Control+Shift+F6)
- Previous Visited Table (Alt+Shift+F6)
- Previous Window (Control+Shift+Tab)
- Repeat Go To (Alt+G)
- Reverse Jump (Control+Shift+J)
- Reverse Keywords (Control+Shift+K)
- Reverse Regex Find (Control+Shift+F3)
- Search Next (F3)
- Search Previous (Shift+F3)

### DbDo: Result

- Extra Speech Toggle (Alt+Shift+Z)
- Key Describer Toggle (Control+F1)
- Say Added (Shift+A)
- Say Bookmark (Shift+B)
- Say Cell (Shift+C)
- Say Clipboard (Alt+Apostrophe)
- Say Column as List (Alt+L)
- Say Column as List from Current (Control+L)
- Say Column as List from Current Marked (Control+Shift+L)
- Say Column as List of Marked (Alt+Shift+L)
- Say Database (Shift+D)
- Say Edited (Shift+E)
- Say Filter (Shift+F)
- Say Goto (Shift+G)
- Say Id (Shift+I)
- Say Jump (Shift+J)
- Say Keywords (Shift+K)
- Say Look (Shift+L)
- Say Mark Status (Shift+M)
- Say Marked
- Say Marked Rows (Shift+Space)
- Say Marked Yield
- Say Notes (Shift+N)
- Say Order (Shift+O)
- Say Position (Alt+Delete)
- Say Prime (Shift+P)
- Say Query (Shift+Q)
- Say Records Rest
- Say Records Rest Marked (Alt+Shift+M)
- Say Regex Replace (Shift+X)
- Say Related (Shift+R)
- Say Replacement Value (Shift+V)
- Say Select Columns (Shift+S)
- Say Sort and Filter (Shift+D8)
- Say Status (Shift+Z)
- Say Tables
- Say Tags (Shift+T)
- Say URL (Shift+U)
- Say Windows Open (Shift+F4)
- Say Yield (Shift+Y)
- Toggle Marked (Control+Space)
- Toggle Read Only (Control+Shift+Z)
- Window Toggle

## EdSharp

219 commands: 126 spoken, 41 dialog, 7 window, 44 focus, 1 result.

### EdSharp: Spoken

- Address (Alt+A)
- Align (Alt+Shift+A)
- Append from Clipboard (Alt+D7)
- Arrange Icons (Alt+F11)
- Braces (Alt+Shift+OemCloseBrackets)
- Burn to CD (Alt+Shift+B)
- Cascade (Control+F11)
- Check Markdown (Alt+F9)
- Chunk (Shift+Back)
- Clear Bookmark (Control+Shift+B)
- Clear Favorite (Control+Shift+L)
- Clipboard (Alt+OemQuotes)
- Command Prompt (Control+Oem5)
- Compile (Control+F5)
- Compiler (Alt+D0)
- Complete Selection (Shift+F8)
- Copy (Control+C)
- Copy All (Control+F8)
- Copy Append (Alt+C)
- Copy Log (Control+F12)
- Copy Rich Text (Control+Shift+C)
- Cut (Control+&X)
- Cut Append (Alt+X)
- Delete Down (Alt+Shift+Delete)
- Delete File (Alt+Shift+D)
- Delete Hard Line (Control+D)
- Delete Left (Control+Shift+Back)
- Delete Line (Alt+Back)
- Delete Paragraph (Control+Shift+D)
- Delete Right (Control+Shift+Delete)
- Delete Up (Alt+Shift+Back)
- Elevate Version (F11)
- Enter New Line (Enter)
- Evaluate Expression (Control+Oemplus)
- Explorer Folder (Alt+Oem5)
- Extra Speech Log (Alt+Shift+X)
- Font (Alt+OemMinus)
- Format Code (Control+D4)
- Guard Document (Control+F7)
- HTML Format (Control+H)
- HTML to Markdown
- HTML to Plain Text
- Indent (Tab)
- Indent Mode (Alt+Shift+I)
- Indent New Line (Shift+Enter)
- Indent New Line Prior (Alt+Shift+Enter)
- Indentation (Alt+I)
- Infer Indent (Alt+OemCloseBrackets)
- Insert Time (Alt+Shift+OemSemicolon)
- Invoke Snippet (Alt+V)
- Join Lines (Control+Shift+J)
- Keep Unique Items (Alt+Shift+K)
- Key Describer (Control+F1)
- Left Brace (Control+Shift+OemOpenBrackets)
- List Different Items (Alt+Shift+L)
- Lookup Term (Alt+F7)
- Lower Case (Control+Shift+U)
- Manual Options (Alt+Shift+M)
- Markdown to Plain Text
- New (Control+N)
- New from Clipboard (Control+Shift+N)
- No Guard (Control+Shift+F7)
- Order Items (Alt+Shift+O)
- Outdent (Shift+Tab)
- Paste (Control+&V)
- Path (Alt+P)
- Path List (Control+Shift+P)
- Path to Clipboard (Alt+Shift+P)
- Preview Markdown (Control+F9)
- Preview Markdown in Web Browser
- Print (Control+P)
- Prompt Command (Alt+F5)
- Proper Case (Alt+U)
- Properties (Alt+Enter)
- PyBrace (Alt+Shift+OemOpenBrackets)
- PyDent (Alt+OemOpenBrackets)
- Query Common Items (Alt+Shift+Q)
- Quote (Control+Q)
- Read All (Alt+F8)
- Redo (Control+Shift+Z)
- Repeat Line (Control+Y)
- Replace Tokens (Control+Shift+Oemplus)
- Reselect (Control+Shift+F8)
- Reset Configuration (Alt+Shift+D0)
- Reverse Items (Alt+Shift+Z)
- Review Output (Alt+Shift+F5)
- Right Brace (Control+Shift+OemCloseBrackets)
- Run (F5)
- Run Code Blocks (Alt+Shift+F9)
- Save (Control+S)
- Save Snippet (Alt+S)
- Section Break (Control+Enter)
- Select All (Control+A)
- Select Chunk (Control+Space)
- Selected (Shift+Space)
- Set Bookmark (Control+B)
- Set Favorite (Control+&L)
- Set on Favorite List (Control+L)
- Spell Check (F7)
- Start Selection (F8)
- Start Tag (Control+Shift+Oemcomma)
- Status (Alt+Z)
- Styles (Alt+OemQuestion)
- Swap Case (Alt+Shift+U)
- Text Combine (Control+Shift+T)
- Text Contents (Alt+Shift+T)
- Text Convert (Control+T)
- Thesaurus (Shift+F7)
- Tile Horizontal (Alt+Shift+F11)
- Tile Vertical (Control+Shift+F11)
- Time (Alt+OemSemicolon)
- Topic (Alt+T)
- Transform Files (Alt+Oemplus)
- Translate Language (Alt+Shift+F7)
- Trim Blanks (Control+Shift+Enter)
- Undo (Control+&Z)
- Unquote (Control+Shift+Q)
- Unselect All (Control+Shift+A)
- Unwrap (Control+Shift+W)
- Upper Case (Control+U)
- View Snippet (Alt+Shift+V)
- Web Download (Alt+Shift+W)
- Windows Open (Shift+F4)
- Word Wrap (Control+W)
- Yield (Alt+Y)
- Yield Encoding (Alt+Shift+Y)

### EdSharp: Dialog

- About (Alt+F1)
- Alternate Menu (Alt+F10)
- Baseline (Alt+Shift+D6)
- Calculate Date (Control+Shift+OemSemicolon)
- Configuration Options (Alt+Shift+C)
- Context Menu (Shift+F10)
- Current Windows (F4)
- Environment Variables (Control+E)
- Export Format (Alt+Shift+E)
- Extract with Regular Expression (Control+Shift+E)
- File Find (Alt+Shift+F)
- Forward Find (Control+F)
- Forward Find with Regular Expression (Control+F3)
- Go to Percent (Control+G)
- Hard Line Break (Control+Shift+H)
- Jump to Line (Control+J)
- Justify (Alt+Shift+J)
- List Favorites (Alt+L)
- Mail Attachment (Control+Shift+M)
- Mail Body (Control+M)
- Number Items (Alt+Shift+N)
- Open (Control+O)
- Open Other Format (Control+Shift+O)
- Paste File (Control+Shift+V)
- Recent Files (Alt+R)
- Rename (Alt+Shift+R)
- Replace (Control+R)
- Replace with Regular Expression (Control+Shift+R)
- Reverse Find (Control+Shift+F)
- Reverse Find with Regular Expression (Control+Shift+F3)
- Run at Cursor (Shift+F5)
- Sample Programs (Control+Shift+F2)
- Save As (Control+Shift+S)
- Save Copy (Alt+Shift+S)
- Search for Topic (Control+F6)
- SendTo Menu (Control+F10)
- Set Default Font and Color (Alt+Shift+Oemplus)
- Set Selection Font (Alt+Shift+OemMinus)
- Special Character (F2)
- Style (Alt+Shift+OemQuestion)
- Yield with Regular Expression (Control+Shift+Y)

### EdSharp: Window

- Chat about Document (Shift+F12)
- Chat with AI (F12)
- Documentation (F1)
- History of Changes (Shift+F1)
- Hotkey Summary (Alt+Shift+H)
- Pick Compiler (Control+Shift+F5)
- Tutorials (Control+Shift+F1)

### EdSharp: Focus

- Close All but Current Window (Control+Shift+F4)
- Close Window (Control+F4)
- End Character (Alt+End)
- End Tag (Control+Shift+OemPeriod)
- Exit EdSharp (Alt+F4)
- Forward Find Again (F3)
- Forward Find at Cursor (Alt+F3)
- Go to Bookmark (Alt+B)
- Go to Contents (Shift+F6)
- Go to Environment (Control+Shift+G)
- Go to Folder (Control+D0)
- Go to Part (Alt+Shift+G)
- Go to Percent Again (Alt+G)
- Go to Section (F6)
- Go to Special Folder (Control+Shift+D0)
- Go to Start of Selection (Alt+Shift+F8)
- Home Character (Alt+Home)
- Jump to Line Again (Alt+J)
- Next Alignment (Control+OemCloseBrackets)
- Next Baseline (Control+D6)
- Next Chunk (Alt+Right)
- Next Font (Control+OemMinus)
- Next Indent (Control+I)
- Next Paragraph (Control+Down)
- Next Part (Alt+PageDown)
- Next Section (Control+PageDown)
- Next Sentence (Alt+Down)
- Next Style (Control+OemQuestion)
- Next Window (Control+Tab)
- Open Again (Alt+O)
- Prior Alignment (Control+OemOpenBrackets)
- Prior Baseline (Control+Shift+D6)
- Prior Chunk (Alt+Left)
- Prior Font (Control+Shift+OemMinus)
- Prior Indent (Control+Shift+I)
- Prior Paragraph (Control+Up)
- Prior Part (Alt+PageUp)
- Prior Section (Control+PageUp)
- Prior Sentence (Alt+Up)
- Prior Style (Control+Shift+OemQuestion)
- Prior Window (Control+Shift+Tab)
- Reverse Find Again (Shift+F3)
- Reverse Find at Cursor (Alt+Shift+F3)
- Search for Topic Again (Alt+F6)

### EdSharp: Result

- Extra Speech Toggle (Control+Shift+X)

## FileDir

211 commands: 131 spoken, 43 dialog, 11 window, 22 focus, 4 result.

### FileDir: Spoken

- Alpha Order (Alt+A)
- Append to Clipboard (Shift+A)
- Arrange Icons (Alt+F11)
- Batch Mail (Control+Shift+B)
- Beginning File (Alt+B)
- Beginning Tagged (Shift+B or Control+Home)
- Burn to CD (Alt+Shift+B)
- Cascade (Control+F11)
- Character Encoding (Shift+2 or @)
- Clear Clipboard (Alt+Shift+')
- Clear Filter (Control+Shift+F)
- Clipboard (Alt+')
- Command Prompt (Control+/)
- Complete Tag (Shift+F8)
- Complete Untag (Alt+Shift+F8)
- Configuration Options (Alt+Shift+C)
- Configure Timer (Control+F12)
- Convert Encoding (Control+2)
- Copy (Control+C)
- Copy Append (Alt+C)
- Copy Log (Control+F12)
- Copy Name (Control+Shift+C)
- Copy Path Tagged to Clipboard (Alt+C)
- Copy to Folder (Shift+C)
- Cut (Control+X)
- Date (Shift+D)
- Date Order (Alt+D)
- Delete (Delete)
- Delete and Recycle (Control+Delete)
- Delete and Recycle File Now (Control+D)
- Delete File Now (Control+Shift+D)
- Delete without Recycle (Shift+Delete)
- Drive A (Alt+1)
- Drive B (Alt+2)
- Drive C (Alt+3)
- Drive D (Alt+4)
- Drive E (Alt+5)
- Drive F (Alt+6)
- Drive G (Alt+7)
- Drive H (Alt+8)
- Drive I (Alt+9)
- Elevate Version (F11)
- Explorer Directory (Alt+/)
- Extension Change (Shift+X)
- Extra Speech Log (Alt+Shift+X)
- Extract with Regular Expression (Control+Shift+E)
- Filter and Order (Shift+8)
- Folder (Control+')
- Folder Name (Shift+')
- Folder to Clipboard (Control+Shift+')
- General ({)
- Hide ())
- Homer Player (Control+Shift+H)
- Initial Change (Shift+I)
- Invert Tagged (Control+I)
- Item Name (')
- Key Describer (Control+F1)
- List (Control+L)
- List Files (Alt+L)
- List Tagged (Shift+L)
- Manual Options (Alt+Shift+M)
- Move to Folder (Shift+M)
- New Item Copy (Control+Shift+N)
- Output Type (Shift+O)
- Paste (Control+V)
- Paste Copy (Alt+V)
- Paste Move (Alt+Shift+V)
- Path (Alt+P)
- Path List to Clipboard (Control+Shift+P)
- Path to Clipboard (Alt+Shift+P)
- Percent Through (Shift+5 or %)
- Print (Control+P)
- ReadOnly (])
- ReadWrite ([)
- Recycle Bin (Control+B)
- Refresh Folder (. or F5)
- Rename to Identify Content (Control+Shift+I)
- Reorder Names (Alt+Shift+K)
- Restart Windows (Alt+Shift+F4)
- Restore Tags (Control+Shift+S)
- Reverse Alpha Order (Alt+Shift+A)
- Reverse Date Order (Alt+Shift+D)
- Reverse Size Order (Alt+Shift+S)
- Reverse Type Order (Alt+Shift+T)
- Save Tags (Control+S)
- Selected (Shift+Space)
- Send to Text Editor (Control+T)
- Send to Word Processor (Control+W)
- Short Path to Clipboard (~)
- Size (Shift+S)
- Size Order (Alt+S)
- Start Tag or Untag (F8)
- Status (Alt+Z)
- Stop Timer
- System (})
- Tag (; or Shift+NumPad5)
- Tag All (Control+A)
- Tag All Files (Alt+.)
- Tag and Next (> or Shift+DownArrow)
- Tag and Previous (Shift+UpArrow)
- Tag Duplicate Files (Alt+Shift+.)
- Tag Similar Files (Alt+Shift+,)
- Tag to Bottom (Shift+End)
- Tag to Top (Shift+Home)
- Tile Horizontal (Alt+Shift+F11)
- Tile Vertical (Control+Shift+F11)
- Time (Alt+;)
- Timer
- Translate File (Alt+Shift+F7)
- Type (Shift+T)
- Type Extended (Control+Shift+T)
- Type Order (Alt+T)
- Unarchive (Shift+U)
- Unarchive Password (Alt+Shift+U)
- Unarchive Test (Alt+U)
- Unarchive to Same Name (Control+Shift+U)
- Unarchive without Subfolders (Control+U)
- Untag (/ or Alt+Shift+NumPad5)
- Untag All (Control+Shift+A)
- Untag All But Current (Alt+,)
- Untag and Next (< or Alt+Shift+DownArrow)
- Untag and Previous (Alt+Shift+UpArrow)
- Untag to Bottom (Alt+Shift+End)
- Untag to Top (Alt+Shift+Home)
- What Content (?)
- Windows Open (Shift+F4 or Alt+NumPad5)
- Yield (Control+Y)
- Yield Files (Alt+Y)
- Yield in Operating System (Alt+Shift+Y)
- Yield on Drive (Control+Shift+Y)
- Yield Tagged (Shift+Y)

### FileDir: Dialog

- Alternate Menu (Alt+F10)
- Context Menu (Shift+F10)
- Convert Units (Shift+3)
- Current Windows (F4)
- Environment Variables (Control+E)
- Evaluate Expression (Control+Equals)
- Explorer Menu (Alt+Shift+F10)
- Export Clipboard to File (Alt+Shift+E)
- File Find (Alt+Shift+F)
- FTP Put (Shift+F)
- Get FTP (Shift+G)
- Go to Drive (Alt+G)
- Go to Folder (Control+G)
- Go to Special Folder (Control+Shift+G)
- Go to Virtual Folder (Alt+Shift+G)
- Inquire Differences (Alt+Shift+I)
- Iterate Processes (Alt+I)
- Jump (Control+J)
- Keywords (Control+K)
- Network Connections (Alt+Shift+N)
- New Folder (Control+N)
- Open Drive (Alt+O)
- Open Folder (Control+O)
- Open Special Folder (Control+Shift+O)
- Open Virtual Folder (Alt+Shift+O)
- Properties (Alt+Enter)
- Quick Shortcut (Shift+Q)
- Quick URL (Alt+Shift+Q)
- Recent Folders (Alt+R)
- Rename (Shift+R or F2)
- Rename with Regular Expression (Control+Shift+R)
- Rename with Wildcards (Control+R)
- SendTo Menu (Control+F10)
- Set Filter (Control+F)
- Stamp with Date and Time (Shift+1 or !)
- Start Timer
- Tag with Regular Expression (Control+Shift+.)
- Volume Format (Control+Shift+V)
- Web Download (Alt+Shift+W)
- Windows Control Panel (Control+Shift+W)
- Zip (Shift+Z)
- Zip List (Control+Shift+Z)
- Zip then Delete (Control+Z)

### FileDir: Window

- About (Alt+F1)
- Chat about File (Shift+F12)
- Chat with AI (F12)
- Documentation (F1)
- History of Changes (Shift+F1)
- Hotkey Summary (Alt+Shift+H)
- Mail Attachment (Control+Shift+M)
- Mail Body (Control+M)
- Play List (Control+Shift+L)
- Play Media (Alt+Shift+L)
- Show (()

### FileDir: Focus

- Close All But Current Window (Control+Shift+F4)
- Close Window (Control+F4)
- End Tagged (Shift+E or Control+End)
- Exit FileDir (Alt+F4)
- Find Duplicates in Tree (Alt+Shift+J)
- Go Back (Alt+LeftArrow)
- Go Forward (Alt+RightArrow)
- Go to Item (Shift+Enter)
- Go to Parent Folder (, or Shift+Backspace)
- Go to Quick Folder (`)
- Jump Again (Alt+J)
- Keywords Again (Alt+K)
- Next Tagged (Shift+N or Control+DownArrow)
- Next Window (Control+Tab)
- Open Item (Enter)
- Open Parent Folder (Backspace)
- Open Quick Folder (Control+Q)
- Previous Tagged (Shift+P or Control+UpArrow)
- Previous Window (Control+Shift+Tab)
- Reverse Keywords (Control+Shift+K)
- Reverse Search Again (Shift+F3)
- Search Again (F3)

### FileDir: Result

- Extra Speech Toggle (Alt+Shift+Z)
- Recycle Toggle (Alt+Shift+R)
- Toggle Tag (Space)
- Window Toggle (Shift+W)

## HomerDev frame

24 commands: 0 spoken, 8 dialog, 6 window, 4 focus, 6 result.

### HomerDev frame: Dialog

- Alternate Menu (Alt+F10)
- Append Clipboard (Control+Shift+Apostrophe)
- Current Windows (F4)
- Edit Settings (Alt+Shift+E)
- Elevate Version (F11)
- Invoke Script (Control+Shift+I)
- Play Tutorials
- Save Clipboard (Control+Apostrophe)

### HomerDev frame: Window

- About (Alt+F1)
- Documentation (F1)
- History of Changes (Shift+F1)
- Hotkey Summary (Alt+Shift+H)
- Hotkeys (Control+Shift+F1)
- ReadMe (Alt+Shift+F1)

### HomerDev frame: Focus

- Close All But Current Window (Control+Shift+F4)
- Close Window (Control+F4)
- Next Window (Control+Tab)
- Previous Window (Control+Shift+Tab)

### HomerDev frame: Result

- Clear Clipboard (Alt+Shift+Apostrophe)
- Copy Log (Control+F12)
- Key Describer Toggle (Control+F1)
- Say Clipboard (Alt+Apostrophe)
- Say Time (Alt+SemiColon)
- Say Windows Open (Shift+F4)
