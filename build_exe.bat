rem ---------------------------------------------------------------------
rem This file executes the build command for the windows executable file.
rem It is here because I am lazy
rem ---------------------------------------------------------------------
del *.pyc
C:\Python27\python.exe py2exe_setup.py py2exe
rmdir /S /Q build
rmdir /S /Q dist\tcl
move dist dist32

del *.pyc
C:\Python27_64bit\python.exe py2exe_setup.py py2exe
rmdir /S /Q build
rmdir /S /Q dist\tcl
move dist dist64
pause