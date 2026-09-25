#!/usr/bin/env python3
"""cleanDir.py -- kept for the scripts that still call it; the work is homerTidy's.

Cleaning and tidying were folded into one tool, homerTidy, on 21 September
2026. This file forwards to it with the same arguments (--do-it means the
same in both), so an older build script or a habit that runs cleanDir still
works, and it says so once. homerTidy works out the project from where it
sits -- run from scripts, exec or the project folder -- and logs to
logs\\<App>-tidy-yyyyMMdd-HHmmss.log. cleanDir used to take the folder it was
run in for the project and to write cleanDir.log beside itself: run from
scripts, it judged scripts, found no installer, and stopped.
"""

import os, subprocess, sys

sHere = os.path.dirname(os.path.abspath(__file__))
print("cleanDir is homerTidy now; running homerTidy with the same arguments.")
sys.exit(subprocess.call([sys.executable, os.path.join(sHere, "homerTidy.py")] + sys.argv[1:]))
