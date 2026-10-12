---
name: homer-library-source
description: >-
  Adds a new book library to bookFido -- Apple Books, Libby, Everand, Hoopla, a
  public library's catalog -- or a new source to any Homer harvester, the way
  bookFido's five were added: research where the library lives and how a Windows
  program can reach it, prove each finding on a real sample, choose the kind of
  source (a signed-in browser page, an exported or copied file, an API), then
  build every touch point the existing libraries have, from the opening dialog's
  check box to the documents, the spreadsheet sheet, the state snapshot, the
  cross-library twins and DbDo's BookTrail. Use this skill whenever the user
  asks to add a library, a reading service or a store to bookFido, to catalog
  books from somewhere new, or to harvest a site or file into a catalog the way
  bookFido does.
---

# Adding a library source

bookFido catalogs Audible, Kindle, Goodreads, Bookshare and NLS (BARD). Each was added the same way, and the NLS
harvest, the newest, is the pattern to copy: in bookFido.cs it touches 26 functions. This skill is that pattern,
written down, so a sixth library costs a plan rather than a rediscovery.

## 1. Research first: where does the library live?

Write no code until these are answered, each from evidence -- a page the user is looking at, a file they can
share, documentation you have read -- and each answer marked confirmed, unconfirmed or estimate:

- **Where is the list kept?** A web page behind a sign-in; an export the service offers; a file or database an
  app keeps on a computer or phone; a documented API.
- **Can Windows reach it?** bookFido runs on Windows. A list that lives only in a Mac or phone app needs a copy
  brought across, and the user must have the device.
- **What does one book carry?** Ask for a real sample -- a saved page, a copy of the file -- and list its fields
  from that, never from memory. Note which field identifies a book (an ASIN, an NLS number, a store id).
- **What does the user see?** The count of books the service shows is the test the harvest must pass.

Ask the user what you cannot see: which devices they have, whether they will copy a file, what the page shows
when they are signed in. Their typed answer is as good as any button.

### Worked example: Apple Books

Apple Books keeps its library in Apple's apps, not on a web page, so the research decides everything. The
candidate routes, none yet confirmed on this user's devices:

- **The Mac's library database, copied to Windows.** Community tools report that Books on a Mac keeps a SQLite
  database, BKLibrary-*.sqlite, under ~/Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary, with a
  table of books (ZBKLIBRARYASSET) holding title, author, genre, reading progress and dates. If the user has a
  Mac, ask them to copy that folder and share the file; confirm the table and columns from the copy before
  relying on any of this. This route would be offline, complete and needs no sign-in.
- **Apple's purchase history in a signed-in browser.** Apple shows an account's purchases on the web; whether
  books appear there, with which fields, must be seen on the user's own account first.
- **iPhone or iPad only.** Its database is not reachable from Windows without a device backup tool; ask before
  pursuing it, and say plainly if it is out of reach.

Recommend the route the evidence supports, with what it gives and what it costs, and let the user choose.

## 2. Choose the kind of source

- **Browser source** (Audible, Kindle, Goodreads, Bookshare, NLS). bookFido drives its own Edge profile through
  the DevTools Protocol. Sign-in is the user's: never steer a site's sign-in or store a password. Test only
  whether the list is visible; if not, ask the user to sign in, with three choices -- done, clear this site's
  stored sign-in and start again, or skip this library this run. A sign-in can leave the list on another tab,
  so look across tabs (findNlsHistoryAcrossTargets). Walk pages with a safety cap, and wait for a page to show
  different books than the last, not for a fixed pause (waitForNlsPage). Read each page with one script that
  returns JSON, {"total": ..., "rows": [...]} (nlsScanScript).
- **File source** (the Apple Books database, any export). Open a copy, read-only, never the original. Check
  the table and columns are the ones expected, and log what was found; a missing column is a clear message,
  not a crash. Remember the file's path and modified time so a later run knows whether to read it again.
- **API source.** Use only a documented one, with the user's own key; never put the key in a log.

## 3. The touch points

Name the new library in every place the existing ones appear. For Apple Books, X below is Apple:

1. **The opening dialog**: a check box and bSearchX, checked by default, in showOpeningDialog; the "none
   chosen" test counts it.
2. **The start**: startUrlForRun for a browser source; a file chooser, remembered, for a file source.
3. **The harvest**: harvestXAsync, called from mainAsync in the same order as the others; any failure is
   announced and logged, and the run goes on with the other libraries.
4. **The row**: xRowFromItem builds one catalog row; xField reads a labelled field; keep the source's own id.
5. **Twins**: crossLibraryKey(title, first author) and crossLibraryMap let a book in two libraries share what
   was gathered; applyCachedBook fills a row from BookTrail or the snapshot so nothing is asked for twice.
6. **State**: aSavedXRows in saveState and loadState; materializeSavedRows when the library is unchecked, so
   its books still reach the documents and the twins.
7. **Documents**: buildXFiles and appendXEntry write X_Library.htm and .md -- contents, an introduction with
   statistics, each book, appendixes by author and the rest; the entries join buildConsolidatedFiles.
8. **Spreadsheet**: fillXSheet, one sheet of bookFido.xlsx, bold header row, ColumnTitle01 at A1, an empty
   cell for anything unknown.
9. **BookTrail**: a case in saveCopy -- source (and the source pick list, the way Goodreads was added in
   ensureSchema), format, catalog number, link, and status mapped onto want to read, reading and read.
10. **Words**: the closing summary, help\bookFido.md, History, and a tutorial step if one names the libraries.

## 4. Rules that hold for every source

- Read only; never change anything in the library or on the site.
- One request a second per service; honor rate limits; a safety cap on pages and rows.
- A detailed log: each page's address, count and first id; each skip and why.
- Titles in title order (ignoring A, An, The); authors by surname; "1 book", not "1 books".

## 5. Prove it

Keep a sample -- a saved page, a copy of the file -- and test the row builder on it offline. Compare the
harvest's count with the count the user sees. Run twice: the second run must ask for nothing already known.
Open BookTrail in DbDo and find the new source's rows by their source.
