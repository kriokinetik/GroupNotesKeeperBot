# JSON Schema v1

Новый формат хранения после миграции из legacy `v0`.

## Структура

```json
{
  "schema_version": 1,
  "chats": {
    "<chat_id>": {
      "admins": ["<admin_id>", "<admin_id>"],
      "groups": [
        {
          "name": "<group_name>",
          "records": [
            {
              "datetime": "<ISO datetime string>",
              "content": "<text>",
              "content_html": "<telegram html>" | null,
              "creator": "<telegram_username>" | null
            }
          ]
        }
      ]
    }
  }
}
```

## Описание полей

- `schema_version`: версия схемы хранения.
- `chats`: словарь чатов.
- `<chat_id>`: ID чата Telegram в виде строки.
- `admins`: список ID администраторов в виде строк.
- `groups`: список групп чата.
- `name`: название группы.
- `records`: список записей группы.
- `datetime`: дата и время записи в формате ISO 8601 с timezone offset.
- `content`: текст записи.
- `content_html`: HTML-представление текста для Telegram или `null`.
- `creator`: username автора записи или `null`, если данных нет.

## Пример

```json
{
  "schema_version": 1,
  "chats": {
    "330979467": {
      "admins": [],
      "groups": [
        {
          "name": "group_name",
          "records": [
            {
              "datetime": "2026-04-04T02:12:00+03:00",
              "content": "message",
              "content_html": null,
              "creator": "author"
            }
          ]
        }
      ]
    }
  }
}
```
