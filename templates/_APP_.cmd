@echo off
rem _APP_.cmd -- run the program built in exec\, from the top of the project.
rem Typing _APP_ in the project folder then runs the fresh build, as it did
rem before programs moved into exec\. Arguments pass through.
"%~dp0exec\_APP_.exe" %*
