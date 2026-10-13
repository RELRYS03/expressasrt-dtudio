@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Configurar Blender - Express'Arte
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 configurar_blender.py
) else (
    python configurar_blender.py
)
echo.
pause
