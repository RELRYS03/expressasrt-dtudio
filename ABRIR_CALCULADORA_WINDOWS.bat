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
if "%SITE_URL%"=="" (
  echo O endereco do servidor nao foi encontrado.
  pause
  exit /b 1
)
start "" "%SITE_URL%/calculadora.html"
