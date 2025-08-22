@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem === RAIZ DO SISTEMA (fixo) ===
set "BASE=C:\sistema_recados"

rem === Subpastas e arquivos ===
set "SCRIPTS=%BASE%\scripts"
set "DIST=%BASE%\dist"
set "BACKUPS=%BASE%\backups"
set "LOGS=%BASE%\logs"

set "SQLITE=%SCRIPTS%\sqlite3.exe"
set "SRC=%DIST%\recados.db"
set "XLOG=%LOGS%\backup_last.log"

if not exist "%BACKUPS%\" mkdir "%BACKUPS%"
if not exist "%LOGS%\"    mkdir "%LOGS%"

rem --- timestamps para log e nome do backup ---
for /f "delims=" %%A in ('powershell -NoP -C "(Get-Date).ToString(\"yyyy-MM-dd HH:mm:ss\")"') do set "NOW=%%A"
for /f "delims=" %%A in ('powershell -NoP -C "(Get-Date).ToString(\"yyyy-MM-dd_HH-mm-ss\")"')  do set "TS=%%A"

> "%XLOG%" echo === BACKUP %NOW% ===
>>"%XLOG%" echo Usando DB: "%SRC%"
>>"%XLOG%" echo Saida:   "%BACKUPS%"

rem --- valida binário e banco ---
if not exist "%SQLITE%" (
  >>"%XLOG%" echo ERRO: sqlite3.exe nao encontrado em "%SQLITE%".
  echo ERRO: sqlite3.exe nao encontrado. & exit /b 9001
)
if not exist "%SRC%" (
  >>"%XLOG%" echo ERRO: banco recados.db nao encontrado em "%SRC%".
  echo ERRO: banco nao encontrado. & exit /b 9002
)

set "DST=%BACKUPS%\recados_%TS%.db"
>>"%XLOG%" echo Criando backup em: "%DST%"

rem --- cria o backup ---
"%SQLITE%" "%SRC%" ".bail on" ".timeout 60000" ".backup '%DST%'" 1>>"%XLOG%" 2>>&1

rem --- confirma que o arquivo apareceu e tem tamanho > 0 ---
if not exist "%DST%" (
  >>"%XLOG%" echo ERRO: backup nao apareceu em disco.
  type "%XLOG%"
  exit /b 101
)
set "SZ="
for %%Z in ("%DST%") do set "SZ=%%~zZ"
if not defined SZ set "SZ=0"
if %SZ% LSS 1 (
  >>"%XLOG%" echo ERRO: backup com tamanho zero.
  del "%DST%" >nul 2>&1
  type "%XLOG%"
  exit /b 103
)

rem --- checa integridade do ARQUIVO DE BACKUP ---
set "TMPCHK=%DST%.chk"
"%SQLITE%" "%DST%" "PRAGMA integrity_check;" > "%TMPCHK%" 2>>"%XLOG%"
set "RES="
if exist "%TMPCHK%" (
  set /p RES=<"%TMPCHK%"
  del "%TMPCHK%" >nul 2>&1
)
>>"%XLOG%" echo integrity_check: %RES%

if /i "%RES%"=="ok" (
  >>"%XLOG%" echo SUCESSO: backup OK em "%DST%"
  type "%XLOG%"
  echo SUCESSO: backup OK em "%DST%"
) else (
  >>"%XLOG%" echo ERRO: integrity_check retornou "%RES%". Apagando arquivo invalido...
  del "%DST%" >nul 2>&1
  type "%XLOG%"
  exit /b 102
)

