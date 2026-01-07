@echo off
SET MPREMOTE=%USERPROFILE%\Downloads\python-3.12.9-embed-amd64\Scripts\mpremote.exe

rem pushd
SET CD0=%CD%
rem chdir to the folder placed this file (=copy.bat)
cd %~dp0
cd src

%MPREMOTE% fs cp -r . :/ + df
SET errlvl=%errorlevel%

rem popd
cd %CD0%

if %errlvl% neq 0 (
    echo %0: FAILED
    exit /b 1
)
