# syntax=docker/dockerfile:1

# Стадия 1. base — общая основа: Python и виртуальное окружение поверх node:22-bookworm
FROM node:22-bookworm AS base
# Отключаем автоочистку apt, чтобы скачанные пакеты оставались в кеше BuildKit
RUN rm -f /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Стадия 2. deps — Python-зависимости (собирается параллельно со стадией browser)
FROM base AS deps
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Стадия 3. browser — скачивание Chromium (собирается параллельно со стадией deps)
FROM base AS browser
COPY requirements.txt .
# --only-shell: только headless-версия Chromium, полный браузер с окном не нужен
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt \
    && playwright install --only-shell chromium

# Стадия 4. final — итоговый образ
FROM base AS final
COPY --from=deps /venv /venv
# Системные библиотеки, нужные Chromium для запуска
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    playwright install-deps chromium
COPY --from=browser /ms-playwright /ms-playwright

WORKDIR /app
# Код копируется последним: его правка не пересобирает зависимости и браузер
COPY src/ ./src/
CMD ["python", "src/scraper.py"]
