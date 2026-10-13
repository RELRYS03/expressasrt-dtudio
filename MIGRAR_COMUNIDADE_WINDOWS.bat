@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Express'Arte - Migrar Publicacoes da Comunidade
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 migrar_dados.py
) else (
    python migrar_dados.py
)
echo.
pause
