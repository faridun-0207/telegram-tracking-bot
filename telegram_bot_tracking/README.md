# Telegram бот: Отслеживание товаров

## Как развернуть на Render:

1. Создай PostgreSQL базу данных на Render и получи параметры подключения.
2. Задай переменные окружения:

- BOT_TOKEN
- DB_HOST
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_PORT

3. Залей проект на GitHub и подключи к Render как Web Service.
4. В `Start command` укажи:
```
python main.py
```

5. Убедись, что таблица создана:

```sql
CREATE TABLE IF NOT EXISTS packages (
    number TEXT PRIMARY KEY,
    status TEXT,
    requester_id BIGINT
);
```

Готово!