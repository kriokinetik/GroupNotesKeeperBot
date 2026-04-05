# GroupNotesKeeperBot

Telegram-бот для ведения заметок по группам внутри чатов.

Бот умеет:
- создавать и удалять группы заметок;
- добавлять записи в выбранную группу;
- просматривать историю записей;
- редактировать и удалять записи;
- управлять локальными администраторами чата;
- удалять сообщение по reply-команде;
- работать на `ru` и `en`.

## Команды

- `/start` — краткое описание бота;
- `/help` — список команд;
- `/groups` — просмотр, добавление и удаление групп;
- `/add` — добавление записи в группу;
- `/history` — просмотр истории записей группы;
- `/delete` — удаление сообщения по reply;
- `/admin` — управление локальными администраторами.

## Стек

- Python `>= 3.14`
- aiogram `3.27`
- Pydantic `2`
- aiofiles
- Babel

## Быстрый старт

### 1. Установка зависимостей

```bash
uv sync
```

### 2. Настройка `.env`

Создайте `.env` в корне проекта:

```env
TOKEN=your_telegram_bot_token
OWNERS=123456789,987654321
GROUP_LIMIT=5
DEFAULT_LANGUAGE=ru
```

Переменные:
- `TOKEN` — токен бота от BotFather.
- `OWNERS` — список Telegram user id через запятую.
- `GROUP_LIMIT` — максимум групп на чат.
- `DEFAULT_LANGUAGE` — язык по умолчанию, обычно `ru` или `en`.

### 3. Запуск

```bash
uv run python -m main
```

При старте приложение:
- проверяет и при необходимости мигрирует `data.json` до актуальной схемы;
- инициализирует хранилище;
- регистрирует локализованные команды бота;
- запускает polling.

## Хранилище

Проект использует файловое JSON-хранилище.

Актуальная схема: `v1`.

Пример структуры:

```json
{
  "schema_version": 1,
  "chats": {
    "-1001234567890": {
      "admins": ["111111111", "222222222"],
      "groups": [
        {
          "name": "physics",
          "records": [
            {
              "datetime": "2026-04-04T02:12:00+03:00",
              "content": "Проверка связи",
              "content_html": null,
              "creator": "sadie"
            }
          ]
        }
      ]
    }
  }
}
```

Подробнее:
- legacy `v0`: [docs/json_schema_v0.md](docs/json_schema_v0.md)
- текущая `v1`: [docs/json_schema_v1.md](docs/json_schema_v1.md)

### Что хранится в записи

Каждая запись содержит:
- `datetime` — timestamp записи;
- `content` — обычный текст;
- `content_html` — HTML-представление текста для Telegram или `null`;
- `creator` — username автора или `null`.

Если `content_html = null`, бот использует обычный `content`.

## Миграции

Сейчас поддерживается переход:
- `v0` -> `v1`

`v0` — legacy-формат без поля `schema_version`.

### Upgrade до актуальной схемы

```bash
uv run python -m migrations.migrate_data upgrade head
```

Или явно:

```bash
uv run python -m migrations.migrate_data upgrade 1
```

### Downgrade в legacy `v0`

```bash
uv run python -m migrations.migrate_data downgrade 0
```

Для конкретного файла:

```bash
uv run python -m migrations.migrate_data downgrade 0 --input data.json
```

Во время миграции рядом создаётся backup исходного файла.

## Локализация

Файлы переводов находятся в `locales/<lang>/LC_MESSAGES/`.

Исходники строк:
- `locales/ru/LC_MESSAGES/messages.po`
- `locales/en/LC_MESSAGES/messages.po`

Компиляция переводов:

```bash
uv run pybabel compile -d locales
```

Если нужно пересобрать только один язык:

```bash
uv run pybabel compile -d locales -l ru
uv run pybabel compile -d locales -l en
```

## Полезные команды

Запуск бота:

```bash
uv run python -m main
```

Форматирование:

```bash
uv run black src migrations
```

Upgrade хранилища:

```bash
uv run python -m migrations.migrate_data upgrade head
```

Downgrade хранилища:

```bash
uv run python -m migrations.migrate_data downgrade 0
```

Компиляция переводов:

```bash
uv run pybabel compile -d locales
```

## Архитектура

Проект собран как набор слоёв с явным composition root.

- `src/main.py` — точка входа, i18n, команды, polling.
- `src/bootstrap.py` — сборка зависимостей и регистрация их в `Dispatcher`.
- `src/telegram` — handlers, callbacks, keyboards, filters, FSM, middlewares.
- `src/use_cases` — прикладные сценарии.
- `src/storage` — фасад хранилища.
- `src/repositories` — контракты и JSON-репозитории.
- `src/models` — Pydantic-модели схемы хранения.
- `src/errors` — доменные и storage-ошибки.
- `src/settings` — конфигурация и логирование.
- `migrations` — upgrade/downgrade хранилища.

### Dependency injection

Зависимости собираются в `build_dependencies()` и регистрируются в `Dispatcher.workflow_data`.

За счёт этого handlers получают use cases и storage через аргументы функций, без отдельного DI-контейнера.

## Онбординг

Если вы только входите в проект, идите в таком порядке:

1. [src/main.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/main.py) — понять запуск приложения, i18n и регистрацию команд.
2. [src/bootstrap.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/bootstrap.py) — посмотреть composition root и wiring зависимостей.
3. [src/telegram/handlers/system.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/telegram/handlers/system.py), [src/telegram/handlers/group.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/telegram/handlers/group.py), [src/telegram/handlers/record.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/telegram/handlers/record.py), [src/telegram/handlers/admin.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/telegram/handlers/admin.py) — посмотреть пользовательские сценарии.
4. [src/use_cases](/D:/PycharmProjects/GroupNotesKeeperBot/src/use_cases) — понять прикладную логику без Telegram-слоя.
5. [src/storage/storage.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/storage/storage.py), [src/repositories/json/file_store.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/repositories/json/file_store.py) — посмотреть, как устроено JSON-хранилище.
6. [src/models/storage.py](/D:/PycharmProjects/GroupNotesKeeperBot/src/models/storage.py) — посмотреть реальную схему данных.
7. [migrations/runner.py](/D:/PycharmProjects/GroupNotesKeeperBot/migrations/runner.py) и [migrations/versions/v0001_v0_to_v1.py](/D:/PycharmProjects/GroupNotesKeeperBot/migrations/versions/v0001_v0_to_v1.py) — понять upgrade/downgrade схемы.

Что важно понять в первую очередь:
- бизнес-логика вынесена в `use_cases`;
- `telegram/handlers` отвечают только за transport/UI-flow;
- данные хранятся в `data.json` в схеме `v1`;
- старый формат без `schema_version` считается `v0`.

## Структура проекта

```text
GroupNotesKeeperBot/
├── docs/
│   ├── json_schema_v0.md
│   └── json_schema_v1.md
├── locales/
├── migrations/
│   ├── migrate_data.py
│   ├── runner.py
│   └── versions/
│       └── v0001_v0_to_v1.py
├── src/
│   ├── bootstrap.py
│   ├── main.py
│   ├── enums/
│   ├── errors/
│   ├── models/
│   ├── repositories/
│   ├── settings/
│   ├── storage/
│   ├── telegram/
│   └── use_cases/
├── data.json
├── pyproject.toml
└── README.md
```

## Замечания

- Хранилище валидируется через Pydantic.
- Запись в `data.json` идёт атомарно через временный файл и `replace`.
- Для локализации используется aiogram i18n и каталог `locales`.
