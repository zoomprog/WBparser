import time
import random
from typing import List, Dict, Any, Optional
from parsing.base_parser import BaseParser
from database.models import Product
from utils.http_client import HTTPClient
from config.settings import Config


class WBParser(BaseParser):
    """Парсер для Wildberries"""

    def __init__(self, shard: str, query: str):
        self.shard = shard
        self.query = query
        self.base_url = f'https://catalog.wb.ru/catalog/{shard}/v2/catalog'
        self.params = {
            'ab_testing': 'false',
            'appType': '1',
            'curr': 'rub',
            'dest': '-3349429',
            'hide_dtype': '13',
            'lang': 'ru',
            'sort': 'popular',
            'spp': '30',
            **self._parse_query(query)
        }
        self.http_client = HTTPClient()
        self.config = Config.PARSER_CONFIG

    def _parse_query(self, query: str) -> Dict[str, str]:
        """Парсит строку параметров запроса"""
        params = {}
        if query:
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        return params

    def build_url(self, page: int) -> str:
        """Строит URL для запроса"""
        params = {**self.params, 'page': str(page)}
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}?{query_string}"

    def parse_response(self, response: Dict[str, Any]) -> List[Product]:
        """Парсит ответ от API и возвращает список товаров"""
        if not response:
            return []

        products_raw = response.get("data", {}).get("products") or []
        products = []

        for product_data in products_raw:
            # Извлекаем информацию о цене
            price_dict = {}
            for size in product_data.get("sizes", []):
                price_dict = size.get("price") or {}
                if price_dict:
                    break

            # Создаем объект товара
            product = Product(
                name=product_data.get("name"),
                price_no_discounts=float(price_dict.get("basic")) / 100 if price_dict.get("basic") else None,
                price_with_discount=price_dict.get("product") / 100 if price_dict.get("product") else None,
                rating=product_data.get("rating"),
                number_of_reviews=product_data.get("nmFeedbacks"),
                shard=self.shard,
                query_params=self.query
            )
            products.append(product)

        return products

    def parse_page(self, page: int) -> List[Product]:
        """Парсит одну страницу"""
        url = self.build_url(page)
        response = self.http_client.get_json(url)
        return self.parse_response(response)

    def find_last_page(self, start_page: int = 1, max_check: int = 500) -> int:
        """Находит последнюю доступную страницу методом бинарного поиска"""
        print(f"Ищем последнюю страницу, начиная с {start_page}...")

        left, right = start_page, start_page

        # Находим верхнюю границу
        while right <= max_check:
            print(f"Проверяем страницу {right}...")
            products = self.parse_page(right)

            if products:
                left = right
                right *= 2
                print(f"Страница {left} не пустая, проверяем дальше...")
            else:
                print(f"Страница {right} пустая, ищем между {left} и {right}")
                break

            time.sleep(1)

        # Бинарный поиск точной границы
        while left < right:
            mid = (left + right + 1) // 2
            print(f"Проверяем страницу {mid} (между {left} и {right})...")

            products = self.parse_page(mid)

            if products:
                left = mid
                print(f"Страница {mid} не пустая")
            else:
                right = mid - 1
                print(f"Страница {mid} пустая")

            time.sleep(1)

        print(f"Последняя страница: {left}")
        return left

    def parse_all_pages(self, delay: float = 0.5, skip_errors: bool = True,
                        max_pages: Optional[int] = None) -> List[Product]:
        """Парсит все доступные страницы"""
        all_products = []
        page = 1
        consecutive_errors = 0
        total_errors = 0
        max_consecutive_errors = self.config['max_consecutive_errors']

        if max_pages:
            print(f"Начинаем парсинг всех страниц (максимум {max_pages} страниц)...")
        else:
            print("Начинаем парсинг всех страниц...")

        while True:
            print(f"Парсим страницу {page}")

            # Проверяем лимит страниц
            if max_pages and page > max_pages:
                print(f"Достигнут лимит в {max_pages} страниц, завершаем парсинг")
                break

            try:
                products = self.parse_page(page)

                if not products:
                    print(f"Страница {page} пуста - завершаем парсинг")
                    break

                consecutive_errors = 0
                all_products.extend(products)
                print(f"Найдено {len(products)} товаров на странице {page}")

            except Exception as e:
                consecutive_errors += 1
                total_errors += 1
                print(f"Ошибка на странице {page} (подряд: {consecutive_errors}): {e}")

                if consecutive_errors >= max_consecutive_errors:
                    print(f"Слишком много ошибок подряд ({consecutive_errors})")
                    if not skip_errors:
                        break
                    consecutive_errors = 0
                    time.sleep(delay * 3)

                if skip_errors:
                    time.sleep(delay * 2)
                else:
                    break

            # Случайная задержка
            delay_time = delay + random.uniform(0, delay)
            time.sleep(delay_time)
            page += 1

        print(f"Парсинг завершён. Всего собрано {len(all_products)} товаров с {page - 1} страниц")
        print(f"Всего ошибок: {total_errors}")
        return all_products

    def close(self):
        """Закрывает HTTP клиент"""
        self.http_client.close()