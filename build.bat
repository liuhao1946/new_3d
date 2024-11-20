@echo off
echo Starting to package the application...
pyinstaller -wD -i 3D.ico 3D.py
echo Packaging complete!
pause
