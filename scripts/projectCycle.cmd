@echo off
rem projectCycle.cmd -- runs projectCycle.py, the build or release step of build_release for a project that is
rem not an app: MyBooks, MyPages, AppHelpGuides, PodcastDirectories. Passes its arguments on.
python "%~dp0projectCycle.py" %*
exit /b %errorlevel%
