@echo off
SET MPREMOTE=%USERPROFILE%\Downloads\python-3.12.9-embed-amd64\Scripts\mpremote.exe

echo Use Ctrl-D to soft reboot
%MPREMOTE% repl
