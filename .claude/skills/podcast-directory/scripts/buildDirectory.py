#!/usr/bin/env python3
"""buildDirectory.py - build one screen-reader-friendly podcast directory
(.md, plus .htm via Pandoc) from a harvested episodes TSV.

The TSV (one row per episode) must have these columns, tab-separated, UTF-8:
  guid  date  title  link  duration  season  episode  type  audio_url  summary
`date` is ISO (YYYY-MM-DD...) or RFC-822; `type` = "trailer" for trailers/promos;
`audio_url` is the direct media URL that the title should play.

Output goes beside the TSV: <Slug>.md and <Slug>.htm. A detailed log is written
beside THIS script (buildDirectory-<slug>-YYYYmmdd-HHMMSS.log).

Run:
  buildDirectory.cmd --tsv Casefile_Episodes.tsv --slug Casefile ^
      --name "Casefile True Crime" --title "Casefile True Crime Directory" ^
      --subtitle "A Screen-Reader-Friendly Guide to Casefile" ^
      --intro "Casefile presents meticulously researched accounts of real crimes."
Options: --by-guest (extract a Guest/Speaker field + appendix from a "Title | Name"
title), --brief (one-sentence summaries), --nosummary, --noappendix.
"""
import argparse, csv, datetime, html, os, re, shutil, subprocess, sys

c_lMonths = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
oLog = None


def scriptDir():
    return os.path.dirname(os.path.abspath(__file__))


def logLine(sMsg):
    sLine = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] " + sMsg
    print(sLine)
    if oLog:
        oLog.write(sLine + "\r\n"); oLog.flush()
    return True


def parseDate(s):
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try: return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError: return None
    try:
        return datetime.datetime.strptime(s[:25].strip(), "%a, %d %b %Y %H:%M:%S").date()
    except Exception:
        m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", s)
        if m:
            try: return datetime.datetime.strptime(m.group(0), "%d %b %Y").date()
            except Exception: return None
    return None


def tkey(s):
    return re.sub(r"^(a|an|the)\s+", "", (s or "").strip().lower())


def slug(s, n=70):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (s or "").lower())).strip("-")[:n].strip("-")


def surname(sName):
    p = (sName or "").split(";")[0].strip().split()
    return p[-1] if p else "Unknown"


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or ""); s = html.unescape(s)
    s = re.sub(r"https?://\S+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def brief(s):
    s = clean(s); m = re.match(r"(.{0,220}?[.!?])(\s|$)", s)
    return (m.group(1) if m else s[:200]).strip()


def guestFromTitle(sTitle):
    # "Book Summary | Author Name" or "Talk title | Speaker" -> the segment after the first pipe
    parts = [p.strip() for p in (sTitle or "").split("|")[1:]]
    for p in parts:
        if p and len(p.split()) <= 6 and not p.lower().startswith(("part ", "episode", "ep ")):
            return p
    return ""


def build(cfg, rows):
    g_brief = cfg["brief"]; g_nosum = cfg["nosummary"]; g_noapp = cfg["noappendix"]; g_guest = cfg["by_guest"]
    for r in rows:
        r["_dt"] = parseDate(r.get("date"))
        r["_title"] = clean(r.get("title")) or "(untitled)"
        r["_trailer"] = (r.get("type") or "").strip().lower() == "trailer"
        r["_guest"] = guestFromTitle(r["_title"]) if g_guest else ""
    seen = {}
    for r in rows:
        a = cfg["slug"].lower() + "-" + slug(r["_title"])
        seen[a] = seen.get(a, 0) + 1
        r["_anchor"] = a if seen[a] == 1 else a + "-" + str(seen[a])
    linkcount = {}
    for r in rows:
        lk = (r.get("link") or "").strip()
        if lk: linkcount[lk] = linkcount.get(lk, 0) + 1

    eps = [r for r in rows if not r["_trailer"]]
    trailers = [r for r in rows if r["_trailer"]]
    years = sorted({r["_dt"].year for r in eps if r["_dt"]})
    yrep = {y: sorted([r for r in eps if r["_dt"] and r["_dt"].year == y],
                      key=lambda r: (r["_dt"], tkey(r["_title"]))) for y in years}
    yspan = (str(years[0]) + " to " + str(years[-1])) if years else ""
    out = []
    def w(s=""): out.append(s)
    w("---")
    w('title: "' + cfg["title"] + '"')
    w('subtitle: "' + cfg["subtitle"] + '"')
    w('author: "' + cfg["author"] + '"')
    w('date: "' + datetime.datetime.now().strftime("%B %Y") + '"')
    w('version: "v1.0.0"')
    w("lang: en-US")
    w("toc: false")
    w("abstract: |")
    w("  A screen-reader-friendly directory of the podcast " + cfg["name"] + ", covering " + str(len(rows)))
    w("  public episodes from " + yspan + ". Each episode links to its audio and lists its")
    w("  metadata in separate, alphabetically sorted fields.")
    w("---")
    w()
    w("# " + cfg["title"])
    w()
    w(cfg["intro"])
    w()
    sFields = "**Date**, **Duration**, **Episode**, " + ("**Guest**, " if g_guest else "") + "**Season**, and **Summary**"
    w("This directory covers **" + str(len(rows)) + " public episodes**, " + yspan + ". Each episode's title "
      "link plays its audio; an **Episode page** link follows the title when the show offers a separate page; "
      "and the metadata on record appears one kind per field, in alphabetical order: " + sFields + ", each shown "
      'only when available. Titles ignore a leading "A", "An", or "The"; people are sorted by surname; all '
      "sorting ignores case.")
    w()
    w("Episodes are grouped by year, earliest first, and within each group they are in date order, oldest first. "
      "Appendixes reorder them by date (newest first)" + (", by title, and by guest." if g_guest else " and by title."))
    w()
    w("This directory was compiled by " + cfg["author"] + " from the show's public feed.")
    w()
    w("## Table of Contents")
    w()
    for y in years: w("- [" + str(y) + " (" + str(len(yrep[y])) + ")](#" + str(y) + ")")
    if trailers: w("- [Trailers and Cross-Promotions (" + str(len(trailers)) + ")](#trailers-and-cross-promotions)")
    w()
    w("- [Appendix A: Episodes by Date](#appendix-a-episodes-by-date)")
    w("- [Appendix B: Episodes by Title](#appendix-b-episodes-by-title)")
    if g_guest: w("- [Appendix C: Episodes by Guest](#appendix-c-episodes-by-guest)")
    w()
    def emit(r):
        au = (r.get("audio_url") or "").strip() or (r.get("link") or "").strip()
        w("### [" + r["_title"] + "](" + au + ") {#" + r["_anchor"] + "}"); w()
        lk = (r.get("link") or "").strip()
        if lk and lk != au and not lk.lower().endswith(".mp3") and linkcount.get(lk, 0) == 1 \
           and len(re.sub(r"^https?://[^/]+", "", lk).strip("/").split("/")) >= 2:
            w("[Episode page](" + lk + ")"); w()
        if r["_dt"]: w("**Date:** " + c_lMonths[r["_dt"].month - 1] + " " + str(r["_dt"].day) + ", " + str(r["_dt"].year)); w()
        if (r.get("duration") or "").strip(): w("**Duration:** " + r["duration"].strip()); w()
        if (r.get("episode") or "").strip(): w("**Episode:** " + r["episode"].strip()); w()
        if g_guest and r["_guest"]: w("**Guest:** " + r["_guest"]); w()
        if (r.get("season") or "").strip(): w("**Season:** " + r["season"].strip()); w()
        if not g_nosum:
            sm = brief(r.get("summary")) if g_brief else clean(r.get("summary"))
            if sm: w("**Summary:** " + sm[:600] + ("..." if len(sm) > 600 else "")); w()
    for y in years:
        w("## " + str(y) + " (" + str(len(yrep[y])) + ") {#" + str(y) + "}"); w()
        for r in yrep[y]: emit(r)
    if trailers:
        w("## Trailers and Cross-Promotions (" + str(len(trailers)) + ") {#trailers-and-cross-promotions}"); w()
        for r in sorted(trailers, key=lambda r: r["_dt"] or datetime.date(1900, 1, 1)): emit(r)
    w("## Appendix A: Episodes by Date {#appendix-a-episodes-by-date}"); w()
    w("Every episode in publication order, newest first, grouped by year."); w()
    for y in sorted(years, reverse=True):
        w("### " + str(y)); w()
        for r in sorted(yrep[y], key=lambda r: r["_dt"], reverse=True):
            w("- [" + r["_title"] + "](#" + r["_anchor"] + ") \u2014 " + c_lMonths[r["_dt"].month - 1] + " " + str(r["_dt"].day))
        w()
    w("## Appendix B: Episodes by Title {#appendix-b-episodes-by-title}"); w()
    w('Every episode in order by title, ignoring a leading "A", "An", or "The".'); w()
    for r in sorted(eps, key=lambda r: tkey(r["_title"])):
        w("- [" + r["_title"] + "](#" + r["_anchor"] + ")")
    w()
    if g_guest and not g_noapp:
        byg = {}
        for r in eps:
            if r["_guest"]: byg.setdefault(r["_guest"], []).append(r)
        if byg:
            w("## Appendix C: Episodes by Guest {#appendix-c-episodes-by-guest}"); w()
            for name in sorted(byg, key=lambda n: (surname(n).lower(), n.lower())):
                w("- **" + name + "**")
                for r in sorted(byg[name], key=lambda x: tkey(x["_title"])):
                    w("  - [" + r["_title"] + "](#" + r["_anchor"] + ")")
            w()
    return "\n".join(out) + "\n"


def main():
    global oLog
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--intro", default="")
    ap.add_argument("--author", default="Jamal Mazrui")
    ap.add_argument("--by-guest", action="store_true", dest="by_guest")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--nosummary", action="store_true")
    ap.add_argument("--noappendix", action="store_true")
    a = ap.parse_args()

    oLog = open(os.path.join(scriptDir(),
               "buildDirectory-" + a.slug + "-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"),
               "w", encoding="utf-8", newline="")
    logLine("buildDirectory starting")
    logLine("python " + sys.version.replace("\n", " ") + " | cwd " + os.getcwd())
    logLine("args: " + repr(vars(a)))
    if not os.path.exists(a.tsv):
        logLine("ERROR: TSV not found: " + a.tsv); oLog.close(); return 1
    rows = list(csv.DictReader(open(a.tsv, encoding="utf-8-sig"), delimiter="\t", quoting=csv.QUOTE_NONE))
    logLine("read " + str(len(rows)) + " rows from " + a.tsv)
    cfg = dict(slug=a.slug, name=a.name, title=a.title, subtitle=a.subtitle, intro=a.intro,
               author=a.author, by_guest=a.by_guest, brief=a.brief, nosummary=a.nosummary, noappendix=a.noappendix)
    sMd = build(cfg, rows)
    sOut = os.path.join(os.path.dirname(os.path.abspath(a.tsv)), a.slug + ".md")
    open(sOut, "wb").write(b"\xef\xbb\xbf" + sMd.replace("\n", "\r\n").encode("utf-8"))
    logLine("wrote " + sOut)
    # verify
    t = sMd
    d = set(re.findall(r"\{#([^}]+)\}", t)); u = set(re.findall(r"\]\(#([^)]+)\)", t))
    bare = len(re.findall(r"(?<!\]\()https?://", t))
    logLine("verify: broken-anchors=" + str(len(u - d)) + " bare-urls=" + str(bare))
    if shutil.which("pandoc"):
        sHtm = sOut[:-3] + ".htm"
        subprocess.run(["pandoc", sOut, "-f", "markdown", "-t", "html5", "-s", "-M", "toc=false", "-o", sHtm], check=False)
        try:
            b = open(sHtm, "rb").read()
            if b[:3] == b"\xef\xbb\xbf": b = b[3:]
            open(sHtm, "wb").write(b"\xef\xbb\xbf" + b.decode("utf-8").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
            logLine("wrote " + sHtm)
        except Exception as oExc:
            logLine("htm normalize error: " + repr(oExc))
    else:
        logLine("Pandoc not found; .htm not built.")
    logLine("DONE.")
    oLog.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
