@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 learn.py
) else (
    python learn.py
)
