import asyncio
import re
import sys
import os
from typing import List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# Добавляем корневую папку проекта в путь для импортов
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from database.connection import DatabaseManager
from database.models import ProductRepository, Product
from parsing.wb_parser import WBParser
from app.utils.category_tree_loader import CategoryTreeLoader


class ParsingService:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.repository = ProductRepository(self.db_manager)
        self.tree_loader = CategoryTreeLoader()

    def find_category_by_id(self, category_id: int) -> Optional[any]:
        """Находит категорию по ID в дереве."""
        return self.tree_loader.get_category(category_id)

    def extract_category_params_from_json(self, category_url: str, category_name: str = None) -> Tuple[
        Optional[str], Optional[str]]:
        """Извлекает параметры shard и query из JSON файла по URL категории."""
        try:
            print(f"Ищем параметры для URL: {category_url}")
            print(f"Имя категории: {category_name}")

            category = None

            # Метод 1: Поиск по точному URL
            category = self.tree_loader.get_category_by_url(category_url)

            if not category:
                # Метод 2: Поиск по части URL (без домена)
                parsed_url = urlparse(category_url)
                path = parsed_url.path
                category = self.tree_loader.get_category_by_url(path)

            if not category:
                # Метод 3: Поиск по имени категории
                if category_name:
                    print(f"Ищем по имени категории: {category_name}")
                    for cat_id, cat_node in self.tree_loader.cat_index.items():
                        if cat_node.name.lower() == category_name.lower():
                            category = cat_node
                            print(f"Найдена категория по имени: {cat_node.name}")
                            break

            if not category:
                # Метод 4: Поиск по частичному совпадению URL
                category = self.tree_loader.find_best_match_url(category_url)

            if category:
                print(f"Найдена категория: {category.name}")
                print(f"ID: {category.id}")
                print(f"URL: {category.url}")
                print(f"Shard: {category.shard}, Query: {category.query}")

                # Проверяем, что у нас есть нужные параметры
                if category.shard and category.query:
                    return category.shard, category.query
                else:
                    print(f"У категории отсутствуют shard или query параметры")
                    print(f"Shard: {category.shard}, Query: {category.query}")
                    return category.shard, category.query
            else:
                print("Категория не найдена в JSON файле")
                return None, None

        except Exception as e:
            print(f"Ошибка при поиске параметров в JSON: {e}")
            return None, None

    def extract_category_params_from_url(self, category_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Извлекает параметры shard и query из URL категории (fallback метод)."""
        try:
            print(f"Извлекаем параметры из URL: {category_url}")

            # Парсим URL
            parsed_url = urlparse(category_url)
            path_parts = [p for p in parsed_url.path.split('/') if p]

            shard = None
            query = None

            # Извлекаем shard из пути
            if len(path_parts) >= 2 and path_parts[0] == 'catalog':
                shard = path_parts[1]

            # Извлекаем query параметры
            query_params = parse_qs(parsed_url.query)

            # Ищем различные типы параметров
            if 'cat' in query_params:
                query = f"cat={query_params['cat'][0]}"
            elif 'subject' in query_params:
                query = f"subject={query_params['subject'][0]}"
            elif 'kind' in query_params:
                query = f"kind={query_params['kind'][0]}"
            elif parsed_url.query:
                # Если есть query строка, но не нашли известные параметры
                query = parsed_url.query

            print(f"Извлечены параметры из URL: shard='{shard}', query='{query}'")
            return shard, query

        except Exception as e:
            print(f"Ошибка при извлечении параметров из URL: {e}")
            return None, None

    def get_category_params(self, category_url: str, category_name: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Получает параметры категории, сначала из JSON, затем из URL."""
        print(f"Получаем параметры для: {category_url}")
        print(f"Имя категории: {category_name}")

        # Сначала пытаемся получить из JSON
        shard, query = self.extract_category_params_from_json(category_url, category_name)

        # Если не нашли в JSON, пытаемся извлечь из URL
        if not shard or not query:
            print("Параметры не найдены в JSON, пытаемся извлечь из URL...")
            url_shard, url_query = self.extract_category_params_from_url(category_url)

            shard = shard or url_shard
            query = query or url_query

        # Логируем что получили
        print(f"Итоговые параметры: shard='{shard}', query='{query}'")

        # Если параметры все еще пустые, возвращаем None чтобы показать ошибку
        if not shard and not query:
            print("Не удалось получить ни shard, ни query параметры")
            return None, None

        return shard, query

    def test_parser_url(self, shard: str, query: str) -> str:
        """Создает тестовый URL для проверки."""
        base_url = f'https://catalog.wb.ru/catalog/{shard}/v2/catalog'
        params = {
            'ab_testing': 'false',
            'appType': '1',
            'curr': 'rub',
            'dest': '-3349429',
            'hide_dtype': '13',
            'lang': 'ru',
            'sort': 'popular',
            'spp': '30',
            'page': '1'
        }

        # Добавляем query параметры
        if query:
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        test_url = f"{base_url}?{query_string}"

        print(f"Тестовый URL: {test_url}")
        return test_url

    async def parse_category_products(self, category_url: str, category_name: str, max_pages: int = 3) -> bool:
        """Запускает парсинг товаров для выбранной категории."""
        try:
            print(f"Начинаем парсинг категории '{category_name}'")
            print(f"URL: {category_url}")

            # Получаем параметры категории
            shard, query = self.get_category_params(category_url, category_name)

            if not shard or not query:
                print("Не удалось получить параметры для парсинга")
                return False

            print(f"Используем параметры: shard='{shard}', query='{query}'")
            print(f"Максимум страниц: {max_pages}")

            # Создаем тестовый URL для проверки
            test_url = self.test_parser_url(shard, query)

            # Создаем парсер
            parser = WBParser(shard, query)

            try:
                # Создаем таблицы если их нет
                self.db_manager.create_tables()

                # Парсим данные (асинхронно в отдельном потоке чтобы не блокировать UI)
                products = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: parser.parse_all_pages(
                        delay=0.5,
                        skip_errors=True,
                        max_pages=max_pages
                    )
                )

                if not products:
                    print("Не удалось получить товары")
                    print("Возможные причины:")
                    print("1. Неправильные параметры shard/query")
                    print("2. Категория не содержит товаров")
                    print("3. Проблемы с доступом к API")
                    return False

                # Сохраняем в базу данных
                self.repository.save_products(products, if_exists='replace')

                print(f"Успешно спарсено и сохранено {len(products)} товаров")
                return True

            finally:
                parser.close()

        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
            return False

    def get_latest_products(self, limit: int = 50) -> List[Product]:
        """Получает последние спарсенные товары из базы данных."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Сначала проверяем структуру таблицы
                    cur.execute("""
                                SELECT column_name, data_type
                                FROM information_schema.columns
                                WHERE table_name = 'wb_products'
                                ORDER BY ordinal_position;
                                """)

                    columns = cur.fetchall()
                    print(f"Структура таблицы wb_products: {columns}")

                    # Определяем доступные столбцы
                    column_names = [col[0] for col in columns]

                    # Проверяем какой столбец с ценой существует
                    price_column = None
                    if 'price_with_discount' in column_names:
                        price_column = 'price_with_discount'
                    elif 'price_witch_discount' in column_names:
                        price_column = 'price_witch_discount'
                    else:
                        print("Не найден столбец с ценой со скидкой")
                        return []

                    # Строим запрос только для существующих столбцов
                    select_columns = []
                    if 'name' in column_names:
                        select_columns.append('name')
                    if 'price_no_discounts' in column_names:
                        select_columns.append('price_no_discounts')
                    if price_column:
                        select_columns.append(f'{price_column} as price_with_discount')
                    if 'rating' in column_names:
                        select_columns.append('rating')
                    if 'number_of_reviews' in column_names:
                        select_columns.append('number_of_reviews')

                    if not select_columns:
                        print("Не найдены необходимые столбцы в таблице")
                        return []

                    # Определяем столбец для сортировки
                    order_column = None
                    if 'created_at' in column_names:
                        order_column = 'created_at DESC'
                    elif any('serial' in col[1].lower() for col in columns):
                        # Ищем serial столбец (обычно это первичный ключ)
                        for col_name, col_type in columns:
                            if 'serial' in col_type.lower():
                                order_column = f'{col_name} DESC'
                                break
                    else:
                        # Используем первый столбец для сортировки
                        order_column = f'{column_names[0]} DESC'

                    # Выполняем запрос
                    query = f"""
                        SELECT {', '.join(select_columns)}
                        FROM wb_products 
                        ORDER BY {order_column}
                        LIMIT %s;
                    """

                    print(f"Выполняем запрос: {query}")
                    cur.execute(query, (limit,))
                    rows = cur.fetchall()

                    # Преобразуем в объекты Product
                    products = []
                    for row in rows:
                        product_data = {}
                        for i, col_name in enumerate(
                                ['name', 'price_no_discounts', 'price_with_discount', 'rating', 'number_of_reviews']):
                            if i < len(row):
                                if col_name in ['price_no_discounts', 'price_with_discount', 'rating']:
                                    product_data[col_name] = float(row[i]) if row[i] is not None else None
                                elif col_name == 'number_of_reviews':
                                    product_data[col_name] = int(row[i]) if row[i] is not None else None
                                else:
                                    product_data[col_name] = row[i]
                            else:
                                product_data[col_name] = None

                        products.append(Product(**product_data))

                    print(f"Получено {len(products)} товаров из БД")
                    return products

        except Exception as e:
            print(f"Ошибка при получении товаров из БД: {e}")
            import traceback
            traceback.print_exc()
            return []

    def debug_category_search(self, category_name: str) -> None:
        """Отладочный метод для поиска категории."""
        print(f"=== Отладка поиска категории '{category_name}' ===")

        # Показываем все категории с похожими именами
        matches = []
        for cat_id, cat_node in self.tree_loader.cat_index.items():
            if category_name.lower() in cat_node.name.lower():
                matches.append(cat_node)

        print(f"Найдено {len(matches)} категорий с похожими именами:")
        for cat in matches[:10]:  # Показываем первые 10
            print(f"  ID: {cat.id}, Имя: '{cat.name}', URL: '{cat.url}', Shard: '{cat.shard}', Query: '{cat.query}'")

    def __del__(self):
        if hasattr(self, 'db_manager'):
            self.db_manager.close()