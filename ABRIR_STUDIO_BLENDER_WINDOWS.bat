@echo off
chcp 65001 >nul
setlocal
set "URL_FILE=%LOCALAPPDATA%\ExpressArteStudio\dados\URL_ATUAL.txt"
if not exist "%URL_FILE%" (
  echo Servidor ainda nao iniciado. Execute INICIAR_EXPRESSARTE_WINDOWS.bat primeiro.
  pause
  exit /b 1
)
set /p SITE_URL=<"%URL_FILE%"
echo Abrindo: %SITE_URL%/studio.html#blender
start "" "%SITE_URL%/studio.html#blender"
