rem ---------------------------------------------------------------------
rem This file executes the build command for the windows executable file.
rem It is here because I am lazy
rem ---------------------------------------------------------------------
del *.pyc
C:\Python27_32\python.exe py2exe_setup.py py2exe
rmdir /S /Q build
move dist dist32
pause

del *.pyc
C:\Python27_64\python.exe py2exe_setup.py py2exe
rmdir /S /Q build
move dist dist64
pause