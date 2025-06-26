# Навигатор по категориям товаров

## Быстрый запуск

###  Настройка базы данных

Создайте файл `.env` в корне проекта с настройками PostgreSQL:

```dotenv
HOST=YOURS_NAME
DATABASE=YOURS_NAME
USER=YOURS_NAME
PASSWORD=YOURS_NAME
port=YOURS_NAME
```
### Зависимости
```
pip install -r requirements.txt
```
### Запуск приложения
```
uvicorn app.app:app --reload
```