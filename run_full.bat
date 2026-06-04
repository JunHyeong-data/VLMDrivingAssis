@echo off
REM ============================================================
REM  DrivingAssis - FULL mode (personal launcher, 이지원)
REM  real YOLO + real VLM (Qwen2.5-VL-7B, 4-bit NF4).
REM
REM  팀 공용 run.bat = real YOLO + mock VLM (고정).
REM  이 파일만 USE_REAL_VLM=1 로 VLM 까지 실제 추론.
REM
REM  처음 실행 시 Qwen2.5-VL-7B (~16GB) 자동 다운로드됨.
REM  모델 바꾸려면:  set YOLO_MODEL=yolo26s_best.pt  후 실행.
REM ============================================================
chcp 65001 >NUL
cd /d "%~dp0"

set "USE_REAL_VLM=1"
if "%YOLO_MODEL%"=="" set "YOLO_MODEL=yolo26n_best.pt"

echo ----------------------------------------------
echo  DrivingAssis  [FULL: real YOLO + real VLM]
echo   YOLO_MODEL   : %YOLO_MODEL%
echo   USE_REAL_VLM : %USE_REAL_VLM%
echo   ^>  http://127.0.0.1:7865
echo ----------------------------------------------

py -3.13 app.py
