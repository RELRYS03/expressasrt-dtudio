@echo off
chcp 65001 >nul
title ExpressArte Studio V7.3.2 - Formas Profissionais
cd /d "%~dp0"
if not exist "site\studio.html" (
  echo ERRO: Extraia o ZIP inteiro; arquivo site\studio.html ausente.
  pause
  exit /b 1
)
if not exist "server.py" (
  echo ERRO: server.py ausente; extraia a pasta inteira.
  pause
  exit /b 1
)
echo.
echo ================================================
echo EXPRESS'ARTE V7.3.2 - 30 FORMAS + PROJETOS SALVOS
 echo ================================================
echo Seu projeto fica salvo em %%LOCALAPPDATA%%\ExpressArteStudio\dados
echo A calculadora continua acessivel no menu superior.
echo Porta inicial 8774. Nao confunda com a V7.2 antiga na porta 8765.
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py --port 8774 --auto-port --open --open-forms
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python server.py --port 8774 --auto-port --open --open-forms
  ) else (
    echo ERRO: Python 3 nao encontrado. Instale Python 3.
  )
)
echo.
echo Servidor encerrado ou houve erro. Leia a mensagem acima.
pause
