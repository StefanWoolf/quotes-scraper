# quotes-scraper

Скрапер на Python + Playwright. Открывает в Chromium страницу
https://quotes.toscrape.com/scroll (цитаты подгружаются JS при прокрутке),
собирает все цитаты (текст, автор, теги) и сохраняет их в `out/result.json`.

Приложение упаковано в Docker-образ вместе с браузером и всеми системными библиотеками.

## Структура

```
├─ Dockerfile                 # multistage-сборка образа
├─ Makefile                   # единственная точка входа: build, run, clean, ci
├─ requirements.txt           # Python-зависимости
├─ src/scraper.py             # код скрапера
├─ out/                       # результат (не коммитится)
└─ .github/workflows/ci.yml   # CI: вызывает make ci
```

## Локальное окружение для разработки

Нужен Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install --only-shell chromium
python src/scraper.py
```

Результат появится в `out/result.json`.

## Продакшн-образ

Нужны Docker и GNU make. На Windows команды `make` запускаются из Git Bash.

| Команда      | Что делает                                                  |
|--------------|-------------------------------------------------------------|
| `make build` | собирает образ `quotes-scraper`                             |
| `make run`   | собирает образ (из кеша) и запускает скрапер, результат — в `out/result.json` |
| `make clean` | удаляет образ и папку `out/`                                |
| `make ci`    | `run` + проверка, что `out/result.json` не пустой           |

### Стадии Dockerfile

1. `base` — `node:22-bookworm` + Python и виртуальное окружение `/venv`.
2. `deps` — установка Python-зависимостей из `requirements.txt`.
3. `browser` — скачивание headless-версии Chromium (`--only-shell`) в `/ms-playwright`.
4. `final` — итоговый образ: берёт `/venv` из `deps`, ставит системные библиотеки
   для Chromium, берёт браузер из `browser` и в самом конце копирует код.

Стадии `deps` и `browser` не зависят друг от друга, поэтому BuildKit собирает их параллельно.
Код копируется последним шагом, поэтому правка кода не пересобирает ни зависимости, ни браузер.
`make clean` удаляет только образ, а кеш сборки BuildKit остаётся — повторный `make build`
берёт слой с браузером из кеша и не качает его заново.

### Ускорение сборки

- Скачивания apt и pip хранятся в кеше BuildKit (`RUN --mount=type=cache`): при смене
  `requirements.txt` пакеты не скачиваются повторно.
- В CI кеш слоёв хранится в GitHub Actions: `make ci` получает
  `BUILD_FLAGS="--load --cache-from type=gha --cache-to type=gha,mode=max"`,
  поэтому браузер не скачивается при каждом запуске.

Результат достаётся из контейнера через bind mount: папка `out/` хоста
монтируется в `/app/out` контейнера.
