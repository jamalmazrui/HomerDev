# UI Automation for Homer controls

What JAWS, NVDA and Narrator read from a Windows Forms control is its UI
Automation element: a name, a control type (its role), the patterns that say
what it can do, and its state. Lbc builds every dialog from standard Windows
Forms controls, so each one exposes the same element every time.

## What each control exposes

- **Button**: control type Button; the Invoke pattern (pressing it).
- **CheckBox**: control type CheckBox; the Toggle pattern, whose state is
  checked, unchecked or mixed.
- **ComboBox**: control type ComboBox; the ExpandCollapse pattern (its list
  open or closed), the Selection pattern, and the Value pattern when it can be
  typed in.
- **Label before a field**: control type Text. It gives the next field its
  name and is not itself a stop on the Tab key.
- **LinkLabel**: control type Hyperlink; the Invoke pattern.
- **ListBox**: control type List, with ListItem children; the Selection
  pattern (single or multiple), and Scroll for a long list.
- **ListView in details view**: control type List or DataGrid, with items and
  column headers; Selection, Grid and Table patterns, so a reader can say a
  cell's column.
- **RadioButton**: control type RadioButton; the SelectionItem pattern. A
  group of them sits in a GroupBox, whose caption names the group.
- **TabControl**: control type Tab, with TabItem children; the Selection
  pattern.
- **TextBox**: control type Edit; the Value pattern, and the Text pattern for
  a multi-line box, which lets a reader move by line, word and character.
- **TreeView**: control type Tree, with TreeItem children; the ExpandCollapse
  pattern on each item that has children.

## The four things to confirm

- **Name**: present, and the words shown on screen. Never an accessible name
  equal to the caption or label already there (it would be read twice).
- **Role**: the standard control for the job; a custom-drawn control that
  looks like a button but is not one has no Invoke pattern.
- **Value**: shown where the control has one, such as a text box's text or a
  combo box's choice.
- **State**: checked, expanded, selected or unavailable, as it really is.

And every one is reachable with Tab or the arrow keys, in the order the
person meets it, with its access letter where it has one.

## Looking at the tree

Accessibility Insights for Windows, free from Microsoft, shows the element
under the focus or the mouse with its name, control type, patterns and
states, and runs automated checks on a window. Inspect, from the Windows SDK,
shows the same tree. Either confirms what the tree says; only a pass with
JAWS and with NVDA confirms what the person hears.
