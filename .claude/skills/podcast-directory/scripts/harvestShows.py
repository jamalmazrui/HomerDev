#!/usr/bin/env python3
"""harvestShows.py - collect every public item of several shows into clean
per-show data files. Two kinds of target are supported:

  podcast   - resolves the RSS feed from the show's Apple Podcasts id and
              parses every episode.
  wordpress - reads every post from a WordPress site's REST API (like a blog).

Targets are harvested in parallel, one worker thread per target, so different
sites are fetched at the same time while each single site still sees a polite
delay between its own requests.

Run with no parameters to harvest all configured targets. Optional switches:
  --only=SLUG    harvest just one configured target by its output slug.
  --wppages=N    for WordPress targets, read at most N pages of 100 posts
                 (default 12). Raise it to go deeper into a large blog.

Each target writes <Slug>_Episodes.tsv (upload this) beside the script; podcast
targets also save the raw <Slug>_feed.xml. A log is written to harvestShows.log.
"""
import concurrent.futures, datetime, email.utils, html, json, os, platform
import re, sys, threading, time
import urllib.error, urllib.request
import xml.etree.ElementTree as ET

# name, slug, kind, ref, [wp rest base]
c_lShows = [
    ("Sword and Scale", "SwordAndScale", "podcast", "790487079"),
    ("The Poetry of Reality", "PoetryOfReality", "podcast", "1716337570"),
    ("Making Sense with Sam Harris", "MakingSense", "podcast", "733163012"),
    ("Access On", "AccessOn", "podcast", "1777481188"),
    ("Freedom Scientific FSCast", "FSCast", "podcast", "292355470"),
    ("Freedom Scientific Training Podcast", "FreedomScientificTraining", "podcast", "1521340640"),
    ("Science Friday", "ScienceFriday", "podcast", "73329284"),
    ("Overheard at National Geographic", "NationalGeographic", "podcast", "1466697207"),
    ("Sidedoor (Smithsonian)", "Sidedoor", "podcast", "1168154281"),
    ("There's More to That (Smithsonian)", "TheresMoreToThat", "podcast", "1694965155"),
    ("AirSpace (Smithsonian Air and Space)", "AirSpace", "podcast", "1329608216"),
    ("NASA's Curious Universe", "CuriousUniverse", "podcast", "1505624059"),
    ("Houston We Have a Podcast (NASA)", "HoustonWeHaveAPodcast", "podcast", "1262594123"),
    ("Small Steps, Giant Leaps (NASA)", "SmallStepsGiantLeaps", "podcast", "1445597915"),
    ("NOVA Now", "Nova", "podcast", "1526878803"),
    ("Blue Dot (Pale Blue Dot)", "PaleBlueDot", "podcast", "1070613910"),
    ("New Discourses (James Lindsay)", "NewDiscourses", "podcast", "1499880546"),
    ("The Glenn Show (Glenn Loury)", "TheGlennShow", "podcast", "505824976"),
    ("MrBallen Podcast: Strange, Dark & Mysterious Stories", "MrBallen", "podcast", "1608813794"),
    ("Crime Junkie", "CrimeJunkie", "podcast", "1322200189"),
    ("20/20 (ABC News)", "ABC2020", "podcast", "987967575"),
    ("Dateline NBC", "DatelineNBC", "podcast", "1464919521"),
    ("Unsolved Mysteries", "UnsolvedMysteries", "podcast", "1549903604"),
    ("Forensic Files", "ForensicFiles", "podcast", "1358793371"),
    ("American Scandal", "AmericanScandal", "podcast", "1435516849"),
    ("Against the Odds", "AgainstTheOdds", "podcast", "1553335461"),
    ("Real Survival Stories", "RealSurvivalStories", "podcast", "1698687674"),
    ("Out Alive from Backpacker", "OutAlive", "podcast", "1462484363"),
    ("Cautionary Tales with Tim Harford", "CautionaryTales", "podcast", "1484511465"),
    ("Our Fake History", "OurFakeHistory", "podcast", "1021703062"),
    ("Unobscured", "Unobscured", "podcast", "1409481160"),
    ("Noble Blood", "NobleBlood", "podcast", "1468332063"),
    ("Black Box Down", "BlackBoxDown", "podcast", "1503540842"),
    ("Flight Safety Detectives", "FlightSafetyDetectives", "podcast", "1477655202"),
    ("Take to the Sky: The Air Disaster Podcast", "TakeToTheSky", "podcast", "1506227593"),
    ("Tooth & Claw: True Stories of Animal Attacks", "ToothAndClaw", "podcast", "1530064872"),
    ("Kingdom of Fraud", "KingdomOfFraud", "podcast", "1896267437"),
    ("Love Trapped", "LoveTrapped", "podcast", "1878220033"),
    ("Deep Cover", "DeepCover", "podcast", "1520478402"),
    ("Dateline Originals", "DatelineOriginals", "podcast", "1721921086"),
    ("The Dishcast with Andrew Sullivan", "TheDishcast", "podcast", "1536984072"),
    ("Conversations with Coleman", "ConversationsWithColeman", "podcast", "1716338488"),
    ("Morbid", "Morbid", "podcast", "1379959217"),
    ("Dr. Death", "DrDeath", "podcast", "1421573955"),
    ("Betrayal Weekly", "BetrayalWeekly", "podcast", "1615637724"),
    ("Trace of Suspicion", "TraceOfSuspicion", "podcast", "1880711858"),
    ("The Binge Cases", "TheBingeCases", "podcast", "1525807626"),
    ("The Binge Crimes", "TheBingeCrimes", "podcast", "1578324041"),
    ("Crime Scene (from The Binge)", "CrimeScene", "podcast", "1621750804"),
    ("Burden of Proof", "BurdenOfProof", "podcast", "1801972935"),
    ("Burden of Proof Daily", "BurdenOfProofDaily", "podcast", "6800881535"),
    ("The Lindsay Clancy Trial: Commonwealth Confidential", "CommonwealthConfidential", "podcast", "1741467031"),
    ("TED Talks Daily", "TEDTalksDaily", "podcast", "160904630"),
    ("Best Book Summaries by StoryShots", "StoryShots", "podcast", "1542434445"),
    ("Living Blindfully", "LivingBlindfully", "podcast", "973360653"),
    ("The Disappearing Spoon", "TheDisappearingSpoon", "podcast", "1506994358"),
    ("American History Tellers", "AmericanHistoryTellers", "podcast", "1313596069"),
    ("Business Wars", "BusinessWars", "podcast", "1335814741"),
    ("Tides of History", "TidesOfHistory", "podcast", "1257202425"),
    ("Revisionist History", "RevisionistHistory", "podcast", "1119389968"),
    ("History Daily", "HistoryDaily", "podcast", "1591095413"),
    ("Against the Rules with Michael Lewis", "AgainstTheRules", "podcast", "1455379351"),
    ("American Innovations", "AmericanInnovations", "podcast", "1370092284"),
    ("Legacy", "Legacy", "podcast", "1711362652"),
    ("48 Hours", "48Hours", "podcast", "965818306"),
    ("Cold Case Files", "ColdCaseFiles", "podcast", "1241386674"),
    ("The First 48", "TheFirst48", "podcast", "6786011424"),
    ("Casefile True Crime", "Casefile", "podcast", "998568017"),
    ("Criminal", "Criminal", "podcast", "809264944"),
    ("In the Dark", "InTheDark", "podcast", "1148175292"),
    ("Bear Brook", "BearBrook", "podcast", "1423306695"),
    ("Radiolab", "Radiolab", "podcast", "152249110"),
    ("Dan Carlin's Hardcore History", "HardcoreHistory", "podcast", "173001861"),
    ("Throughline", "Throughline", "podcast", "1451109634"),
    ("Serial", "Serial", "podcast", "917918570"),
    ("Park Predators", "ParkPredators", "podcast", "1517651197"),
    ("CounterClock", "CounterClock", "podcast", "https://feeds.simplecast.com/MTPwrbcY"),
    ("The Constant", "TheConstant", "podcast", "1321926387"),
    ("Ologies with Alie Ward", "Ologies", "podcast", "1278815517"),
    ("Short Wave", "ShortWave", "podcast", "1482575855"),
    ("Planetary Radio", "PlanetaryRadio", "podcast", "91689834"),
    ("Frankly Fukuyama", "FranklyFukuyama", "podcast", "1853805152"),
    ("The Good Fight", "TheGoodFight", "podcast", "1198765424"),
    ("The Coffee Klatch with Robert Reich", "CoffeeKlatch", "podcast", "1635446643"),
    ("99% Invisible", "99PercentInvisible", "podcast", "394775318"),
    ("Freakonomics Radio", "Freakonomics", "podcast", "354668519"),
    ("The Rest Is History", "TheRestIsHistory", "podcast", "1537788786"),
    ("Legal Wars", "LegalWars", "podcast", "1436752562"),
    ("Gravity Assist", "GravityAssist", "podcast", "https://www.nasa.gov/feeds/podcasts/gravity-assist"),
    ("On a Mission", "OnAMission", "podcast", "https://www.nasa.gov/feeds/podcasts/on-a-mission"),
    ("The Invisible Network", "InvisibleNetwork", "podcast", "https://www.nasa.gov/feeds/podcasts/invisible-network"),
]
c_sLookup = "https://itunes.apple.com/lookup?id="
c_sUserAgent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShowDirectoryHarvester/1.2")
c_sLogName = "harvestShows.log"
c_iPageCap = 60
c_iWpPageCap = 12
c_iMaxWorkers = 6
c_nDelay = 0.4
c_dNs = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
         "content": "http://purl.org/rss/1.0/modules/content/",
         "atom": "http://www.w3.org/2005/Atom"}
c_lPodFields = ["guid", "date", "title", "link", "duration", "season", "episode",
                "type", "explicit", "author", "keywords", "audio_url", "summary"]
c_lWpFields = ["slug", "date", "title", "link", "categories", "summary"]

oLog = None
oLogLock = threading.Lock()
g_iWpPages = c_iWpPageCap


def scriptDir(): return os.path.dirname(os.path.abspath(__file__))


def logLine(sMsg):
    sLine = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] " + sMsg
    with oLogLock:
        print(sLine)
        if oLog:
            oLog.write(sLine + "\r\n"); oLog.flush()
    return True


def sCount(iN, sNoun): return str(iN) + " " + (sNoun if iN == 1 else sNoun + "s")


def httpGet(sUrl):
    oReq = urllib.request.Request(sUrl, headers={"User-Agent": c_sUserAgent})
    try:
        oResp = urllib.request.urlopen(oReq, timeout=60)
        sBody = oResp.read().decode("utf-8", "replace")
        logLine("GET " + sUrl + " -> " + str(oResp.status) + " (" + sCount(len(sBody), "byte") + ")")
        return oResp.status, sBody
    except urllib.error.HTTPError as oErr:
        logLine("GET " + sUrl + " -> HTTP " + str(oErr.code)); return oErr.code, None
    except Exception as oExc:
        logLine("GET " + sUrl + " -> ERROR " + repr(oExc)); return 0, None


def cleanHtml(sRaw):
    if not sRaw: return ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", sRaw)
    s = re.sub(r"(?i)<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    for mk in ["Hosted by Simplecast", "Hosted on Acast", "See pcm.adswizz",
               "See omnystudio", "Learn more about your ad choices",
               "Advertising Inquiries", "Privacy & Opt-Out",
               "Get instant access to all episodes", "See acast.com/privacy",
               "If the Making Sense podcast logo", "Continue reading"]:
        i = s.find(mk)
        if i != -1: s = s[:i]
    s = re.sub(r"https?://\S+", " ", s)
    return re.sub(r"\s+", " ", s).strip(" .;,-")


def writeTsv(sSlug, lFields, lRecords, sKeyField):
    dSeen = {}; lUnique = []
    for d in lRecords:
        k = d.get(sKeyField) or d.get("link") or d.get("title")
        if k in dSeen: continue
        dSeen[k] = True; lUnique.append(d)
    lUnique.sort(key=lambda d: d.get("date", ""), reverse=True)
    sPath = os.path.join(scriptDir(), sSlug + "_Episodes.tsv")
    with open(sPath, "wb") as f:
        f.write(b"\xef\xbb\xbf")
        f.write(("\t".join(lFields) + "\r\n").encode("utf-8"))
        for d in lUnique:
            cells = [(d.get(k, "") or "").replace("\t", " ").replace("\r", " ").replace("\n", " ") for k in lFields]
            f.write(("\t".join(cells) + "\r\n").encode("utf-8"))
    logLine("wrote " + sCount(len(lUnique), "item") + " to " + sPath)
    lDated = [d["date"][:10] for d in lUnique if d.get("date")]
    if lDated: logLine(sSlug + " date range: " + min(lDated) + " to " + max(lDated))
    return len(lUnique)


# --- podcast ---------------------------------------------------------------
def resolveFeed(sAppleId):
    if sAppleId.startswith("http"): return sAppleId
    iStatus, sBody = httpGet(c_sLookup + sAppleId)
    if iStatus != 200 or not sBody: return ""
    try: dData = json.loads(sBody)
    except Exception: return ""
    for d in dData.get("results", []):
        if d.get("feedUrl"): return d["feedUrl"]
    return ""


def itemText(oItem, sPath):
    v = oItem.findtext(sPath, default="", namespaces=c_dNs)
    return v.strip() if v else ""


def parseDate(sRaw):
    if not sRaw: return ""
    try: return email.utils.parsedate_to_datetime(sRaw).date().isoformat()
    except Exception: return ""


def parseItem(oItem):
    d = {k: "" for k in c_lPodFields}
    d["title"] = itemText(oItem, "title"); d["link"] = itemText(oItem, "link")
    d["guid"] = itemText(oItem, "guid"); d["date"] = parseDate(itemText(oItem, "pubDate"))
    d["duration"] = itemText(oItem, "itunes:duration"); d["season"] = itemText(oItem, "itunes:season")
    d["episode"] = itemText(oItem, "itunes:episode"); d["type"] = itemText(oItem, "itunes:episodeType")
    d["explicit"] = itemText(oItem, "itunes:explicit")
    d["author"] = itemText(oItem, "itunes:author") or itemText(oItem, "author")
    d["keywords"] = itemText(oItem, "itunes:keywords")
    oEnc = oItem.find("enclosure")
    if oEnc is not None: d["audio_url"] = oEnc.get("url", "")
    d["summary"] = cleanHtml(itemText(oItem, "content:encoded") or itemText(oItem, "description")
                             or itemText(oItem, "itunes:summary") or itemText(oItem, "itunes:subtitle"))
    return d


def harvestPodcast(sName, sSlug, sAppleId):
    sFeed = resolveFeed(sAppleId)
    if not sFeed:
        logLine(sName + ": could not resolve a feed"); return 0
    logLine(sName + " feed: " + sFeed)
    lRecords = []; sUrl = sFeed; iPage = 0
    while sUrl and iPage < c_iPageCap:
        iPage += 1
        iStatus, sBody = httpGet(sUrl)
        if iStatus != 200 or not sBody: break
        open(os.path.join(scriptDir(), sSlug + "_feed" + (("_p" + str(iPage)) if iPage > 1 else "") + ".xml"),
             "w", encoding="utf-8", newline="").write(sBody)
        try: oRoot = ET.fromstring(sBody.encode("utf-8"))
        except Exception as oExc:
            logLine(sSlug + " XML error: " + repr(oExc)); break
        oCh = oRoot.find("channel")
        if oCh is None: break
        lItems = oCh.findall("item")
        for oItem in lItems: lRecords.append(parseItem(oItem))
        logLine(sName + " page " + str(iPage) + ": " + sCount(len(lItems), "item") + "; total " + str(len(lRecords)))
        sNext = ""
        for oL in oCh.findall("atom:link", c_dNs):
            if oL.get("rel") == "next": sNext = oL.get("href", "")
        sUrl = sNext
        if sUrl: time.sleep(c_nDelay)
    if not lRecords: return 0
    return writeTsv(sSlug, c_lPodFields, lRecords, "guid")


# --- wordpress -------------------------------------------------------------
def wpCategories(sSite):
    dMap = {}; iPage = 1
    while iPage <= 20:
        iStatus, sBody = httpGet(sSite + "/wp-json/wp/v2/categories?per_page=100&page="
                                 + str(iPage) + "&_fields=id,name")
        if iStatus != 200 or not sBody: break
        try: lItems = json.loads(sBody)
        except Exception: break
        if not lItems: break
        for d in lItems: dMap[d.get("id")] = d.get("name", "")
        if len(lItems) < 100: break
        iPage += 1; time.sleep(c_nDelay)
    return dMap


def harvestWordpress(sName, sSlug, sSite, sBase):
    dCat = wpCategories(sSite)
    lRecords = []; iPage = 1
    while iPage <= g_iWpPages:
        sUrl = (sSite + "/wp-json/wp/v2/" + sBase + "?per_page=100&page=" + str(iPage)
                + "&_fields=slug,link,date,title,excerpt,categories")
        iStatus, sBody = httpGet(sUrl)
        if iStatus == 400: logLine(sName + ": reached last page at " + str(iPage)); break
        if iStatus != 200 or not sBody: break
        try: lItems = json.loads(sBody)
        except Exception: break
        if not lItems: break
        for d in lItems:
            cats = "; ".join(sorted(dCat.get(c, "") for c in d.get("categories", []) if dCat.get(c)))
            lRecords.append(dict(slug=d.get("slug", ""), link=d.get("link", ""),
                                 date=(d.get("date") or "")[:10],
                                 title=cleanHtml((d.get("title") or {}).get("rendered", "")),
                                 categories=cats,
                                 summary=cleanHtml((d.get("excerpt") or {}).get("rendered", ""))))
        logLine(sName + " page " + str(iPage) + ": " + sCount(len(lItems), "post") + "; total " + str(len(lRecords)))
        if len(lItems) < 100: break
        iPage += 1; time.sleep(c_nDelay)
    if not lRecords: return 0
    return writeTsv(sSlug, c_lWpFields, lRecords, "slug")


def harvestOne(tShow):
    sName, sSlug, sKind = tShow[0], tShow[1], tShow[2]
    logLine("=== " + sName + " (" + sKind + ") ===")
    try:
        if sKind == "podcast":
            return sSlug, harvestPodcast(sName, sSlug, tShow[3])
        if sKind == "wordpress":
            return sSlug, harvestWordpress(sName, sSlug, tShow[3], tShow[4])
    except Exception as oExc:
        logLine(sSlug + " worker error: " + repr(oExc))
    return sSlug, 0


def main():
    global oLog, g_iWpPages
    sOnly = ""
    for sArg in sys.argv[1:]:
        if sArg.startswith("--only="): sOnly = sArg.split("=", 1)[1].strip()
        elif sArg.startswith("--wppages="):
            try: g_iWpPages = int(sArg.split("=", 1)[1])
            except ValueError: pass
    oLog = open(os.path.join(scriptDir(), c_sLogName), "w", encoding="utf-8", newline="")
    logLine("harvestShows starting")
    logLine("script: " + os.path.abspath(__file__))
    logLine("python: " + sys.version.replace("\n", " "))
    logLine("platform: " + platform.platform())
    logLine("working directory: " + os.getcwd())
    logLine("command line: " + " ".join(sys.argv))
    logLine("wordpress page cap: " + str(g_iWpPages))
    lShows = [t for t in c_lShows if (not sOnly or t[1] == sOnly)]
    logLine("harvesting " + sCount(len(lShows), "target") + " with "
            + sCount(min(len(lShows), c_iMaxWorkers), "worker"))
    iTotal = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(lShows), c_iMaxWorkers)) as oPool:
        lFut = [oPool.submit(harvestOne, t) for t in lShows]
        for oFut in concurrent.futures.as_completed(lFut):
            iTotal += oFut.result()[1]
    logLine("done: " + sCount(iTotal, "item") + " across all targets; upload the .tsv files")
    oLog.close()
    return 0 if iTotal else 1


if __name__ == "__main__":
    sys.exit(main())
