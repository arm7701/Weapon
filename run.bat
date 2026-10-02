@echo off
title Weapon 3D Tactical Simulator
echo ========================================================
echo   Launching Weapon 3D Tactical Strike Simulation
echo ========================================================
python was_test7.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
