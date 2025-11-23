@echo off
echo Launching via Python 3.8.2...

REM === Путь к Python 3.8 ===
set PYTHON="C:\Users\cookie\AppData\Local\Programs\Python\Python38\python.exe"

REM === Переход в папку игры ===
cd /d "%~dp0"

REM === Запуск ===
%PYTHON% main.py

echo.
pause