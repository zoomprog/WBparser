from database.connection import DatabaseManager
from database.models import ProductRepository
from parsing.wb_parser import WBParser


def main():
    """Главная функция приложения"""
    # Инициализируем компоненты
    db_manager = DatabaseManager()
    repository = ProductRepository(db_manager)
    parser = WBParser('toys15', 'cat=8282')

    try:
        # Создаем таблицы
        db_manager.create_tables()

        # Парсим данные
        products = parser.parse_all_pages(
            delay=0.5,
            skip_errors=True,
            max_pages=5
        )

        # Сохраняем в базу данных
        repository.save_products(products)
        print("Данные успешно загружены в базу данных")

    except Exception as e:
        print(f"Ошибка: {e}")

    finally:
        # Закрываем соединения
        parser.close()
        db_manager.close()


if __name__ == '__main__':
    main()