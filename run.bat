@echo off
chcp 65001 >NUL
cd /d "%~dp0"

REM ============================================================
REM  BackMirror launcher (Windows)
REM  Runs with Python 3.13 on purpose: ultralytics / torch are
REM  installed there, so real YOLO detection works.
REM  Launching app.py with a Python that lacks ultralytics (e.g.
REM  3.14) silently falls back to the mock detector ("[detector]
REM  ultralytics not installed"). The py launcher pins 3.13.
REM  (Comments kept ASCII so they never get mis-parsed under cp949.)
REM ============================================================

py -3.13 app.py
