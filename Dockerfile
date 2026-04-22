FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# The repo was developed on Windows, but the app resolves lowercase asset paths.
# Normalize directory names for Linux containers to avoid missing assets at runtime.
RUN set -eux; \
    if [ -d /app/backend/assets/Fonts ] && [ ! -d /app/backend/assets/fonts ]; then mv /app/backend/assets/Fonts /app/backend/assets/fonts; fi; \
    if [ -d /app/backend/assets/Photos ] && [ ! -d /app/backend/assets/photos ]; then mv /app/backend/assets/Photos /app/backend/assets/photos; fi; \
    mkdir -p /app/backend/storage/builds/_preview

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
