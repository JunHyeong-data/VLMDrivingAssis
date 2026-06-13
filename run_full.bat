@echo off
chcp 65001 >NUL
cd /d "%~dp0"

REM ============================================================
REM  DrivingAssis - FULL mode (personal launcher)
REM  real YOLO + real VLM (Qwen2.5-VL-7B, 4-bit NF4).
REM  Team-shared run.bat = real YOLO + mock VLM.
REM  This file sets USE_REAL_VLM=1 to enable real VLM coaching.
REM  First run downloads Qwen2.5-VL-7B (~16GB) automatically.
REM  Change model: set YOLO_MODEL=yolo26s_best.pt before running.
REM  (Comments kept ASCII so they never get mis-parsed under cp949.)
REM ============================================================

set "USE_REAL_VLM=1"
if "%YOLO_MODEL%"=="" set "YOLO_MODEL=yolo26s_best.pt"

echo ----------------------------------------------
echo  DrivingAssis  [FULL: real YOLO + real VLM]
echo   YOLO_MODEL   : %YOLO_MODEL%
echo   USE_REAL_VLM : %USE_REAL_VLM%
echo   ^>  http://127.0.0.1:7865
echo ----------------------------------------------

py -3.13 app.py
