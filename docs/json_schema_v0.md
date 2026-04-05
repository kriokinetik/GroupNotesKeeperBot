# JSON Schema v1

Текущий старый формат хранения до миграции.

## Структура

```json
{
  "<chat_id>": {
    "admins": [<admin_id>, <admin_id>],
    "records": {
      "<group_name>": [
        {
          "datetime": "<datetime string>",
          "content": "<text>"
        }
      ]
    }
  }
}
```

## Описание полей

- `<chat_id>`: ID чата Telegram в виде строки.
- `admins`: список локальных администраторов чата.
- `records`: словарь групп.
- `<group_name>`: название группы.
- `datetime`: строка даты и времени записи.
- `content`: текст записи.

## Пример

```json
{
  "330979467": {
    "admins": [],
    "records": {
      "group_name": [
        {
          "datetime": "04.04.26 02:12",
          "content": "test message"
        }
      ]
    }
  }
}
```
