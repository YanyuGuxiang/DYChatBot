@echo off
set SystemRoot=C:\Windows
set PATH=C:\Windows\System32;%PATH%
chcp 65001 >nul 2>&1
"%~dp0.venv\Scripts\python.exe" %*