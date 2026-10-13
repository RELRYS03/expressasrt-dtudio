@echo off
chcp 65001 >nul
title Express'Arte - Instalar GitHub Copilot SDK
cd /d "%~dp0"
echo.
echo  EXPRESS'ARTE - INSTALACAO OPCIONAL DO COPILOT SDK
 echo =================================================
echo O SDK e o runtime serao baixados dos canais oficiais GitHub/PyPI.
echo Isso requer internet. Nenhuma senha sera solicitada por este script.
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON=python"
  ) else (
    echo ERRO: Python nao instalado. Instale Python 3.11 ou mais recente.
    pause
    exit /b 1
  )
)
%PYTHON% -c "import sys; assert sys.version_info >= (3,11), 'O Copilot SDK precisa do Python 3.11+'"
if errorlevel 1 (
  echo ATENCAO: atualize o Python para 3.11 ou superior.
  pause
  exit /b 1
)
echo Instalando SDK oficial... 
%PYTHON% -m pip install --upgrade github-copilot-sdk
if errorlevel 1 (
  echo Falha ao instalar SDK. Verifique sua internet e o Python ativo.
  pause
  exit /b 1
)
echo Baixando runtime oficial verificado do Copilot... 
%PYTHON% -m copilot download-runtime
if errorlevel 1 (
  echo Falha no runtime. Consulte COPILOT_COMO_CONECTAR.md
  pause
  exit /b 1
)
echo.
echo SDK e runtime instalados neste Python.
echo Agora autentique sua conta GitHub seguindo COPILOT_COMO_CONECTAR.md.
echo Depois reinicie a Express'Arte e entre em Studio ^> IA Express'Arte.
echo.
pause
