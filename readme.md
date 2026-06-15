# СКАИД task

Синхронизация схемы PostgreSQL базы данных по образцу другой.  
Первая БД (source) - образец. Вторая БД (target) - корректируется по первой.  
Данные в target не затрагиваются.

## Установка

```bash
pip install sqlalchemy alembic psycopg2-binary
```

## Настройка

Открой `main.py` и укажи DSN обеих баз:

```python
SOURCE_DSN = "postgresql://user:password@host:port/source_db"
TARGET_DSN = "postgresql://user:password@host:port/target_db"
```

## Запуск

```bash
python main.py
```

Программа выведет список обнаруженных изменений и запросит подтверждение:

```
DB Schema Synchronizer
source → localhost:5432/test_db
target → localhost:5433/prod_db

Обнаружены изменения:

  Создать таблицу: orders
  Создать индекс: idx_orders_user_id
  Добавить колонку: created_at
  Изменить колонку: email

Применить изменения к основной БД? [Y/n]:
```

`y` - применить. Любой другой ввод - отмена без изменений.

## Локальная проверка через Docker

Поднять две базы:

```bash
docker run -d --name source_db -e POSTGRES_PASSWORD=pass -e POSTGRES_DB=test_db -p 5432:5432 postgres:16
docker run -d --name target_db -e POSTGRES_PASSWORD=pass -e POSTGRES_DB=prod_db  -p 5433:5432 postgres:16
```

Создать схему в source:

```bash
docker exec source_db psql -U postgres -d test_db -c "CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255) NOT NULL, created_at TIMESTAMP DEFAULT NOW());"
docker exec source_db psql -U postgres -d test_db -c "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT REFERENCES users(id) ON DELETE CASCADE, amount NUMERIC(10,2) NOT NULL, status VARCHAR(50) DEFAULT 'pending');"
docker exec source_db psql -U postgres -d test_db -c "CREATE INDEX idx_orders_user_id ON orders(user_id);"
```

Создать устаревшую схему в target с данными:

```bash
docker exec target_db psql -U postgres -d prod_db -c "CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(100));"
docker exec target_db psql -U postgres -d prod_db -c "INSERT INTO users (email) VALUES ('test@example.com'), ('user@mail.ru');"
```

Запустить синхронизацию:

```bash
python main.py
```

Проверить результат:

```bash
# схема обновилась
docker exec target_db psql -U postgres -d prod_db -c "\d users"
docker exec target_db psql -U postgres -d prod_db -c "\dt"

# данные целы
docker exec target_db psql -U postgres -d prod_db -c "SELECT * FROM users;"
```

Остановить контейнеры:

```bash
docker rm -f source_db target_db
```