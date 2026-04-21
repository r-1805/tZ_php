@echo off
cd /d "%~dp0"

echo Сборка и запуск контейнера...
docker compose up --build -d
if errorlevel 1 (
  echo.
  echo Не удалось запустить проект через Docker.
  echo Проверьте, что Docker Desktop установлен и запущен.
  pause
  exit /b 1
)

echo.
echo Проект запущен.
echo Откройте в браузере: http://localhost:8080
start http://localhost:8080
pause

