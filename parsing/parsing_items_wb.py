import requests
from pprint import pprint
import pandas as pd
import time
import random
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class WBparse:
    def __init__(self, shard: str, query: str):
        self.shard = shard
        self.query = query
        self.base_url = f'https://catalog.wb.ru/catalog/{shard}/v2/catalog?ab_testing=false&appType=1&curr=rub&dest=-3349429&hide_dtype=13&lang=ru&sort=popular&spp=30&{query}'
        self.session = requests.Session()
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'ru,en;q=0.9',
            'accept-language': 'ru,en;q=0.9',
            'origin': 'https://www.wildberries.ru',
            'priority': 'u=1, i',
            'referer': 'https://www.wildberries.ru/catalog/aksessuary/zonty',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "YaBrowser";v="25.4", "Yowser";v="2.5"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 YaBrowser/25.4.0.0 Safari/537.36',
            'x-captcha-id': 'Catalog 1|1|1750864338|AA==|18c938833668494a92caa964628525ea|L8rBAtah4DqyzLyhp7fBXvG1sY91R9AXvlgjzG34PqP'
        })

        # Конфигурация базы данных из .env файла
        self.db_config = {
            'host': os.getenv('HOST', 'localhost'),
            'database': os.getenv('DATABASE', 'postgres'),
            'user': os.getenv('USER', 'postgres'),
            'password': os.getenv('PASSWORD', '123'),
            'port': int(os.getenv('PORT', 5432))
        }

        # Инициализация подключения к БД
        self.init_database()

    def init_database(self):
        """Инициализирует подключение к базе данных и создает таблицу если её нет"""
        try:
            # Создаем подключение для выполнения DDL операций
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            # Создаем таблицу если она не существует
            create_table_query = """
            CREATE TABLE IF NOT EXISTS wb_products (
                id SERIAL PRIMARY KEY,
                name TEXT,
                price_no_discounts DECIMAL(10, 2),
                price_witch_discount DECIMAL(10, 2),
                rating DECIMAL(3, 2),
                number_of_reviews INTEGER
                );
            """

            cur.execute(create_table_query)
            conn.commit()
            cur.close()
            conn.close()

            # Создаем SQLAlchemy engine для pandas
            connection_string = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.engine = create_engine(connection_string)

            print("Подключение к базе данных установлено")

        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            raise

    def get_gds_in_json(self, page: int = 1, retries: int = 3):
        url = f"{self.base_url}&page={page}"

        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)

                # Проверяем статус ответа
                if response.status_code == 200:
                    if response.text.strip():
                        return response.json()
                    else:
                        print(f"Пустой ответ на странице {page}, попытка {attempt + 1}")
                elif response.status_code == 429:
                    print(f"Слишком много запросов, ждём...")
                    time.sleep(20)
                else:
                    print(f"HTTP {response.status_code} на странице {page}, попытка {attempt + 1}")

            except requests.exceptions.Timeout:
                print(f"Таймаут на странице {page}, попытка {attempt + 1}")
            except requests.exceptions.JSONDecodeError:
                print(f"Некорректный JSON на странице {page}, попытка {attempt + 1}")
            except Exception as e:
                print(f"Ошибка на странице {page}, попытка {attempt + 1}: {e}")

            # Ждём перед повторной попыткой
            if attempt < retries - 1:
                time.sleep(random.uniform(2, 5))

        return None

    def prparse_gds(self, response: dict):
        if not response:
            return []

        products_raw = response.get("data", {}).get("products") or []
        result: list[dict] = []

        for product in products_raw:
            price_dict = {}
            for size in product.get("sizes", []):
                price_dict = size.get("price") or {}
                if price_dict:
                    break

            result.append({
                "name": product.get("name"),
                "price_no_discounts": float(price_dict.get("basic")) / 100 if price_dict.get("basic") else None,
                "price_witch_discount": price_dict.get("product") / 100 if price_dict.get("product") else None,
                "rating": product.get("rating"),
                "number_of_reviews": product.get("nmFeedbacks"),
                "shard": self.shard,
                "query_params": self.query
            })
        return result

    def find_last_page(self, start_page: int = 1, max_check: int = 500):
        """Ищет последнюю доступную страницу методом бинарного поиска"""
        print(f"Ищем последнюю страницу, начиная с {start_page}...")

        # Сначала находим примерную верхнюю границу
        left, right = start_page, start_page

        # Увеличиваем правую границу до тех пор, пока не найдём пустую страницу
        while right <= max_check:
            print(f"Проверяем страницу {right}...")
            response = self.get_gds_in_json(right)

            if response and self.prparse_gds(response):
                left = right
                right *= 2
                print(f"Страница {left} не пустая, проверяем дальше...")
            else:
                print(f"Страница {right} пустая, ищем между {left} и {right}")
                break

            time.sleep(1)

        # Теперь бинарным поиском находим точную последнюю страницу
        while left < right:
            mid = (left + right + 1) // 2
            print(f"Проверяем страницу {mid} (между {left} и {right})...")

            response = self.get_gds_in_json(mid)

            if response and self.prparse_gds(response):
                left = mid
                print(f"Страница {mid} не пустая")
            else:
                right = mid - 1
                print(f"Страница {mid} пустая")

            time.sleep(1)

        print(f"Последняя страница: {left}")
        return left

    def parse_all_pages(self, delay: float = 0.5, skip_errors: bool = True, max_consecutive_errors: int = 5,
                        max_pages: int = None):
        """Парсит все доступные страницы"""
        all_items = []
        page = 1
        consecutive_errors = 0
        total_errors = 0

        if max_pages:
            print(f"Начинаем парсинг всех страниц (максимум {max_pages} страниц)...")
        else:
            print("Начинаем парсинг всех страниц...")

        while True:
            print(f"Парсим страницу {page}")

            # Проверяем лимит страниц перед запросом
            if max_pages and page > max_pages:
                print(f"Достигнут лимит в {max_pages} страниц, завершаем парсинг")
                break

            response = self.get_gds_in_json(page)

            if response is None:
                consecutive_errors += 1
                total_errors += 1
                print(f"Ошибка на странице {page} (подряд: {consecutive_errors})")

                if consecutive_errors >= max_consecutive_errors:
                    print(f"Слишком много ошибок подряд ({consecutive_errors}), переходим к следующей странице")
                    consecutive_errors = 0  # Сбрасываем счетчик и продолжаем
                    page += 1
                    time.sleep(delay * 3)  # Увеличиваем задержку после серии ошибок
                    continue

                if skip_errors:
                    page += 1
                    time.sleep(delay * 2)  # Увеличиваем задержку после ошибки
                    continue
                else:
                    break

            items = self.prparse_gds(response)

            if not items:
                print(f"Страница {page} пуста - завершаем парсинг")
                break  # Завершаем при первой же пустой странице
            else:
                consecutive_errors = 0  # Сбрасываем счётчик ошибок только при успешном получении данных
                all_items.extend(items)
                print(f"Найдено {len(items)} товаров на странице {page}")

            # Случайная задержка для более естественного поведения
            delay_time = delay + random.uniform(0, delay)
            time.sleep(delay_time)

            page += 1

        print(f"Парсинг завершён. Всего собрано {len(all_items)} товаров с {page - 1} страниц")
        print(f"Всего ошибок: {total_errors}")
        return all_items

    def save_to_database(self, items: list[dict],
                         table_name: str = 'wb_products',
                         if_exists: str = 'append'):
        """Сохраняет список товаров в базу данных PostgreSQL"""
        if not items:
            print("Нет данных для сохранения")
            return

        try:
            df = pd.DataFrame(items)

            # Столбцы, которые действительно существуют в таблице
            expected_cols = [
                'name',
                'price_no_discounts',
                'price_witch_discount',
                'rating',
                'number_of_reviews'
            ]
            df = df[expected_cols]

            # Приведение типов (NaN → NULL в базе)
            float_cols = ['price_no_discounts', 'price_witch_discount', 'rating']
            for col in float_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Сохраняем данные
            df.to_sql(
                name=table_name,
                con=self.engine,
                if_exists=if_exists,
                index=False,
                method='multi'
            )

            print(f"Данные успешно сохранены в таблицу {table_name}. Записей: {len(df)}")

        except Exception as e:
            print(f"Ошибка при сохранении в базу данных: {e}")
            raise

    def parse_and_save_all(self, table_name: str = 'wb_products', delay: float = 1.0, skip_errors: bool = True,
                           max_pages: int = None):
        """Парсит все страницы и сохраняет результат в базу данных"""
        all_items = self.parse_all_pages(delay, skip_errors, max_pages=max_pages)

        if not all_items:
            print("Не удалось извлечь товары")
            return

        # Сохраняем в базу данных
        self.save_to_database(all_items, table_name)
        print("Данные успешно загружены в базу данных")

    def close_connection(self):
        """Закрывает соединение с базой данных"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            print("Соединение с базой данных закрыто")


# Пример использования
if __name__ == '__main__':
    try:
        parser = WBparse('toys15', 'cat=8282')

        # Парсим и сохраняем в базу данных
        parser.parse_and_save_all(
            table_name='wb_products',
            delay=0.5,
            skip_errors=True,
            max_pages=5
        )

    except Exception as e:
        print(f"Ошибка: {e}")

    finally:
        # Закрываем соединение
        if 'parser' in locals():
            parser.close_connection()