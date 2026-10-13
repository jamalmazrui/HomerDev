// Marked-Schedule.js
// Build a clean, accessible HTML schedule from the CURRENT view of the
// events table and save it as MySchedule.html.
//
// How to use: first shape the view to what you want to keep. For example,
// at the dot prompt type
//     filter marked = true
// to keep only the events you marked of interest, or filter to a single
// day. Then run this file with Invoke Script. Unlike the plain Export
// command, this script groups the events under a heading for each day and
// writes one navigable table per day -- a friendlier read than a single
// flat table.
//
// The script reads only the rows in the current view, so the filter and
// sort you set beforehand decide exactly what lands in the file.

var c_sOut = "MySchedule.html";

// esc: minimal HTML escaping for any field value that might contain
// an ampersand or angle bracket (event titles sometimes do).
function esc(sVal) {
  if (sVal == null) return "";
  return String(sVal).split("&").join("&amp;").split("<").join("&lt;").split(">").join("&gt;");
}

var iCount = 0, sb = new System.Text.StringBuilder(), sLastDate = null;
sb.AppendLine("<!DOCTYPE html>");
sb.AppendLine("<html lang=\"en\"><head><meta charset=\"utf-8\"><title>My Convention Schedule</title></head><body>");
sb.AppendLine("<h1>My Convention Schedule</h1>");

db.moveFirst();
while (!db.eof) {
  var sDate = "" + db.getFieldValue("event_date");
  if (sDate != sLastDate) {
    if (sLastDate != null) sb.AppendLine("</tbody></table>");
    sb.AppendLine("<h2>" + esc(sDate) + "</h2>");
    sb.AppendLine("<table border=\"1\"><caption>Events on " + esc(sDate) + "</caption>");
    sb.AppendLine("<thead><tr><th scope=\"col\">Start</th><th scope=\"col\">End</th><th scope=\"col\">Title</th></tr></thead><tbody>");
    sLastDate = sDate;
  }
  sb.AppendLine("<tr><td>" + esc(db.getFieldValue("start_time")) + "</td><td>"
    + esc(db.getFieldValue("end_time")) + "</td><td>"
    + esc(db.getFieldValue("title")) + "</td></tr>");
  iCount++;
  db.moveNext();
}
if (sLastDate != null) sb.AppendLine("</tbody></table>");
sb.AppendLine("</body></html>");
System.IO.File.WriteAllText(c_sOut, sb.ToString());

// The final expression is what Invoke Script reports back to you.
"Wrote " + iCount + " events to " + c_sOut + ".";
