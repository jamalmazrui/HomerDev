// Marked-Contacts.js
// Build a vCard (.vcf) file from the CURRENT view of the contacts table and
// save it as MyContacts.vcf, ready to import into your phone, Outlook,
// Google Contacts, or Apple Contacts. It is the contact-card sibling of
// Marked-Schedule.js and Marked-Calendar.js: mark the people you want, then
// export them as standard cards.
//
// How to use: open the contacts table, mark the people of interest, then at
// the dot prompt type
//     filter marked = true
// (or filter however you like). Then run this file with Invoke Script. The
// script reads only the rows in the current view, so your filter decides
// exactly which contacts are written.
//
// The standard contact-card format is the vCard, whose files end in .vcf.
// This writes vCard 3.0, the version contact apps import most reliably, with
// one card per contact in a single file. As with the calendar script, no
// third-party package is needed -- a .vcf file is plain text in the vCard
// format, assembled here by hand. It uses only the columns common to every
// DbDo contacts table, so it works unchanged on the personal contacts.db
// sample (where the cards are rich) as well as on this convention database
// (where it exports presenter and sponsor cards). Contacts that are
// organizations rather than people are written with the organization name as
// the card name.

var c_sOut = "MyContacts.vcf";

// vcText: escape a vCard TEXT value -- backslash first, then semicolon,
// comma, and any line break collapsed to a literal \n. Structured values
// (N, ADR) escape each component this way before being joined with ';'.
function vcText(sVal) {
  if (sVal == null) return "";
  var s = String(sVal);
  s = s.split("\\").join("\\\\");
  s = s.split(";").join("\\;");
  s = s.split(",").join("\\,");
  s = s.split("\r\n").join("\\n").split("\n").join("\\n").split("\r").join("\\n");
  return s;
}

// vcUri: a URI value (URL) is not comma/semicolon escaped; just flatten any
// stray line break to a space.
function vcUri(sVal) {
  if (sVal == null) return "";
  return String(sVal).split("\r\n").join(" ").split("\n").join(" ").split("\r").join(" ");
}

// addFolded: append one content line, folded so no line exceeds 75 octets
// (continuation lines begin with a single space), terminated with CRLF.
function addFolded(sb, sLine) {
  var iMax = 73;
  while (sLine.length > iMax) {
    sb.Append(sLine.substr(0, iMax)); sb.Append("\r\n ");
    sLine = sLine.substr(iMax);
  }
  sb.Append(sLine); sb.Append("\r\n");
}

function nonEmpty(s) { return s != "" && s != "null"; }
function get(sName) { return "" + db.getFieldValue(sName); }

// collapse: trim and squeeze internal whitespace (for the display name).
function collapse(s) { return String(s).replace(/\s+/g, " ").replace(/^ +| +$/g, ""); }

var sb = new System.Text.StringBuilder();
var iCount = 0;

db.moveFirst();
while (!db.eof) {
  var sFirst = get("first_name"),  sMiddle = get("middle_name"), sLast = get("last_name");
  var sOrg   = get("enterprise"),  sJob    = get("job");
  var sCell  = get("wireless_phone"), sHome = get("home_phone");
  var sPmail = get("personal_email"),  sBmail = get("business_email");
  var sAddr  = get("address1"), sCity = get("city"), sState = get("state"),
      sZip   = get("zip"), sNation = get("nation");
  var sUrl   = get("url"), sNotes = get("notes"), sId = get("contact_id");

  // Normalise database nulls to blank.
  if (!nonEmpty(sFirst))  sFirst = "";  if (!nonEmpty(sMiddle)) sMiddle = "";
  if (!nonEmpty(sLast))   sLast = "";   if (!nonEmpty(sOrg))    sOrg = "";

  var sPerson = collapse(sFirst + " " + sMiddle + " " + sLast);
  var sFn = sPerson;
  if (sFn == "") sFn = sOrg;
  if (sFn == "") { db.moveNext(); continue; }   // nothing to name the card by

  addFolded(sb, "BEGIN:VCARD");
  addFolded(sb, "VERSION:3.0");
  if (nonEmpty(sId)) addFolded(sb, "UID:dbdo-contact-" + sId);
  if (sPerson != "")
    addFolded(sb, "N:" + vcText(sLast) + ";" + vcText(sFirst) + ";" + vcText(sMiddle) + ";;");
  else
    addFolded(sb, "N:" + vcText(sFn) + ";;;;");
  addFolded(sb, "FN:" + vcText(sFn));
  if (nonEmpty(sOrg))   addFolded(sb, "ORG:" + vcText(sOrg));
  if (nonEmpty(sJob))   addFolded(sb, "TITLE:" + vcText(sJob));
  if (nonEmpty(sCell))  addFolded(sb, "TEL;TYPE=CELL:" + vcText(sCell));
  if (nonEmpty(sHome))  addFolded(sb, "TEL;TYPE=HOME:" + vcText(sHome));
  if (nonEmpty(sPmail)) addFolded(sb, "EMAIL;TYPE=HOME:" + vcText(sPmail));
  if (nonEmpty(sBmail)) addFolded(sb, "EMAIL;TYPE=WORK:" + vcText(sBmail));
  if (nonEmpty(sAddr) || nonEmpty(sCity) || nonEmpty(sState) || nonEmpty(sZip) || nonEmpty(sNation))
    addFolded(sb, "ADR;TYPE=HOME:;;" + vcText(sAddr) + ";" + vcText(sCity) + ";"
      + vcText(sState) + ";" + vcText(sZip) + ";" + vcText(sNation));
  if (nonEmpty(sUrl))   addFolded(sb, "URL:" + vcUri(sUrl));
  if (nonEmpty(sNotes)) addFolded(sb, "NOTE:" + vcText(sNotes));
  addFolded(sb, "END:VCARD");
  iCount++;
  db.moveNext();
}

System.IO.File.WriteAllText(c_sOut, sb.ToString());

// The final expression is what Invoke Script reports back to you.
"Wrote " + iCount + " contact card(s) to " + c_sOut + ". Import it into your phone or contacts app to add the people you marked.";
