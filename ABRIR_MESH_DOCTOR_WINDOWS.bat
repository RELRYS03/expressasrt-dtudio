@echo off
chcp 65001 >nul
setlocal
set "URL_FILE=%LOCALAPPDATA%\ExpressArteStudio\dados\URL_ATUAL.txt"
if not exist "%URL_FILE%" (
  echo Primeiro execute INICIAR_EXPRESSARTE_WINDOWS.bat.
  pause
  exit /b 1
)
set /p SITE_URL=<"%URL_FILE%"
start "" "%SITE_URL%/mesh-doctor.html"
