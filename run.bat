@echo off
title MM-Chatbot Local Server
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo Starting MM-Chatbot servers...
.\.venv\Scripts\python.exe run_local.py
pause
