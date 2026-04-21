# Генератор PHP-микросайтов

Проект упакован в Docker так, чтобы его можно было развернуть без ручной настройки Python, Node.js и зависимостей.

## Самый простой запуск на Windows

1. Установить Docker Desktop.
2. Запустить Docker Desktop и дождаться, пока он полностью стартует.
3. Открыть папку проекта.
4. Дважды нажать [start.bat](./start.bat).
5. Открыть в браузере `http://localhost:8080`.

Для остановки проекта достаточно дважды нажать [stop.bat](./stop.bat).

## Универсальный запуск через Docker Compose

Из корня проекта:

```bash
docker compose up --build -d
```

После запуска открыть:

```text
http://localhost:8080
```

Остановить проект:

```bash
docker compose down
```

## Что запускается

- React/Vite интерфейс собирается внутри Docker
- FastAPI backend запускается в контейнере и раздаёт собранный frontend
- экспортированные ZIP-архивы сохраняются в Docker volume, поэтому не пропадают при перезапуске контейнера

## Полезные команды

Посмотреть логи:

```bash
docker compose logs -f
```

Пересобрать проект после изменений:

```bash
docker compose up --build -d
```

Остановить и удалить контейнер:

```bash
docker compose down
```

Остановить и удалить контейнер вместе с сохранёнными экспортами:

```bash
docker compose down -v
```

## API

- `GET /api/catalog`
- `POST /api/preview`
- `POST /api/export`
- `GET /api/builds/{id}`
- `GET /api/builds/{id}/download`

## Локальная разработка без Docker

### Backend

```powershell
cd backend
py -m pip install -r requirements-dev.txt
py -m uvicorn app.main:app --reload --port 8001
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Тесты

```powershell
cd backend
py -m pytest
```
