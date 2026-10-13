// Marked-Calendar.js
// Build an iCalendar (.ics) file from the CURRENT view of the events table
// and save it as MySchedule.ics, ready to import into Google Calendar,
// Outlook, Apple Calendar, or any app that reads calendar files. This is the
// database counterpart of the web form that lets you tick the sessions you
// want and download a calendar: here you mark the sessions instead.
//
// How to use: first shape the view to the events you want to keep. The usual
// way is to mark the sessions of interest, then at the dot prompt type
//     filter marked = true
// (or filter to a single day, one track, and so on). Then run this file with
// Invoke Script. The script reads only the rows in the current view, so your
// filter is what decides which sessions land in the calendar -- the database
// equivalent of ticking checkboxes.
//
// A note on the extension: the importable standard is iCalendar, whose files
// end in .ics (RFC 5545), and that is what every calendar app reads, so this
// writes MySchedule.ics. A site that offers a ".icx" file is almost certainly
// producing the same iCalendar content under a slightly different name; if you
// ever need that exact name, just rename the file after it is written.
//
// Times are written as floating local times -- the wall-clock times shown in
// the agenda -- so a 07:15 session imports as 07:15 in the convention city,
// whatever time zone your device is set to. No third-party package is needed:
// an iCalendar file is plain text assembled by hand, which is all the format
// requires, and .NET Framework has no higher-level calendar writer to lean on.

var sOut = "MySchedule.ics";
var ci = System.Globalization.CultureInfo.InvariantCulture;

// icalText: escape a TEXT value per RFC 5545 -- backslash first, then
// semicolon, comma, and any line break collapsed to a literal \n.
function icalText(sVal) {
  if (sVal == null) return "";
  var s = String(sVal);
  s = s.split("\\").join("\\\\");
  s = s.split(";").join("\\;");
  s = s.split(",").join("\\,");
  s = s.split("\r\n").join("\\n").split("\n").join("\\n").split("\r").join("\\n");
  return s;
}

// addFolded: append one content line, folded so no line exceeds 75 octets
// (continuation lines begin with a single space), each terminated with CRLF
// as the format mandates.
function addFolded(sb, sLine) {
  var iMax = 73;
  while (sLine.length > iMax) {
    sb.Append(sLine.substr(0, iMax)); sb.Append("\r\n ");
    sLine = sLine.substr(iMax);
  }
  sb.Append(sLine); sb.Append("\r\n");
}

// nonEmpty: treat database nulls (which can arrive as "" or "null") as blank.
function nonEmpty(s) { return s != "" && s != "null"; }

var sb = new System.Text.StringBuilder();
var sStamp = System.DateTime.UtcNow.ToString("yyyyMMdd'T'HHmmss'Z'", ci);
var iCount = 0;

addFolded(sb, "BEGIN:VCALENDAR");
addFolded(sb, "VERSION:2.0");
addFolded(sb, "PRODID:-//DbDo//Convention//EN");
addFolded(sb, "CALSCALE:GREGORIAN");
addFolded(sb, "METHOD:PUBLISH");

db.moveFirst();
while (!db.eof) {
  var sId    = String(db.getFieldValue("event_id"));
  var sDate  = "" + db.getFieldValue("event_date");
  var sStart = "" + db.getFieldValue("start_time");
  var sEnd   = "" + db.getFieldValue("end_time");
  var sTitle = "" + db.getFieldValue("title");
  var sDetl  = "" + db.getFieldValue("details");
  var sUrl   = "" + db.getFieldValue("url");

  addFolded(sb, "BEGIN:VEVENT");
  addFolded(sb, "UID:convention-" + sId + "@dbdo");
  addFolded(sb, "DTSTAMP:" + sStamp);

  // A session with a start time becomes a timed event; one without (a date
  // with no clock time) becomes an all-day event for that date.
  var bTimed = false, dtStart, dtEnd;
  if (nonEmpty(sStart)) {
    try {
      dtStart = System.DateTime.Parse(sDate + " " + sStart, ci);
      if (nonEmpty(sEnd)) {
        dtEnd = System.DateTime.Parse(sDate + " " + sEnd, ci);
        if (System.DateTime.Compare(dtEnd, dtStart) <= 0) dtEnd = dtEnd.AddDays(1); // crossed midnight
      } else {
        dtEnd = dtStart.AddHours(1); // no end given -> default one hour
      }
      bTimed = true;
    } catch (e) { bTimed = false; }
  }
  if (bTimed) {
    addFolded(sb, "DTSTART:" + dtStart.ToString("yyyyMMdd'T'HHmmss", ci));
    addFolded(sb, "DTEND:" + dtEnd.ToString("yyyyMMdd'T'HHmmss", ci));
  } else {
    var dtDay = System.DateTime.Parse(sDate, ci);
    addFolded(sb, "DTSTART;VALUE=DATE:" + dtDay.ToString("yyyyMMdd", ci));
    addFolded(sb, "DTEND;VALUE=DATE:" + dtDay.AddDays(1).ToString("yyyyMMdd", ci));
  }

  addFolded(sb, "SUMMARY:" + icalText(sTitle));
  if (nonEmpty(sDetl)) addFolded(sb, "DESCRIPTION:" + icalText(sDetl));
  if (nonEmpty(sUrl))  addFolded(sb, "URL:" + icalText(sUrl));
  addFolded(sb, "END:VEVENT");
  iCount++;
  db.moveNext();
}

addFolded(sb, "END:VCALENDAR");
System.IO.File.WriteAllText(sOut, sb.ToString());

// The final expression is what Invoke Script reports back to you.
"Wrote " + iCount + " event(s) to " + sOut + ". Import it into your calendar app (Google Calendar, Outlook, or Apple Calendar) to add the sessions you marked.";
