@echo off
setlocal

:: Caminho do banco
set SOURCE=C:\Users\Pedro\Documents\projetos\projeto_recados\sis_rec\recados.db

:: Pasta de destino
set BACKUP_DIR=C:\Users\Pedro\Documents\projetos\projeto_recados\sis_rec\backups

:: Criar a pasta se não existir
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

:: Nome do backup com data
set DATE=%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%

copy %SOURCE% %BACKUP_DIR%\recados_backup_%DATE%.db

echo Backup criado com sucesso.
endlocal
