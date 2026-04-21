@echo off
cd /d "%~dp0"

echo Остановка контейнера...
docker compose down
pause

