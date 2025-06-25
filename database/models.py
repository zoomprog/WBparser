from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import pandas as pd
from database.connection import DatabaseManager


@dataclass
class Product:
    """Модель товара"""
    name: Optional[str]
    price_no_discounts: Optional[float]
    price_with_discount: Optional[float]  # Внутреннее представление
    rating: Optional[float]
    number_of_reviews: Optional[int]
    shard: Optional[str] = None
    query_params: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Создает объект Product из словаря"""
        return cls(
            name=data.get('name'),
            price_no_discounts=data.get('price_no_discounts'),
            price_with_discount=data.get('price_with_discount'),
            rating=data.get('rating'),
            number_of_reviews=data.get('number_of_reviews'),
            shard=data.get('shard'),
            query_params=data.get('query_params')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь"""
        return {
            'name': self.name,
            'price_no_discounts': self.price_no_discounts,
            'price_with_discount': self.price_with_discount,
            'rating': self.rating,
            'number_of_reviews': self.number_of_reviews,
            'shard': self.shard,
            'query_params': self.query_params
        }


class ProductRepository:
    """Репозиторий для работы с товарами в базе данных"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Проверяет существование столбца в таблице"""
        query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s \
                  AND column_name = %s; \
                """

        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (table_name, column_name))
                return cur.fetchone() is not None

    def save_products(self, products: List[Product], table_name: str = 'wb_products',
                      if_exists: str = 'append') -> None:
        """Сохраняет список товаров в базу данных"""
        if not products:
            print("Нет данных для сохранения")
            return

        try:
            # Преобразуем список товаров в DataFrame
            data = [product.to_dict() for product in products]
            df = pd.DataFrame(data)

            # Проверяем, какой столбец существует в базе данных
            old_column_exists = self._check_column_exists(table_name, 'price_witch_discount')
            new_column_exists = self._check_column_exists(table_name, 'price_with_discount')

            if old_column_exists and not new_column_exists:
                # Используем старое имя столбца
                print("Используется старая схема БД с столбцом 'price_witch_discount'")
                expected_cols = [
                    'name',
                    'price_no_discounts',
                    'price_witch_discount',  # Старое имя
                    'rating',
                    'number_of_reviews'
                ]
                # Переименовываем столбец в DataFrame для совместимости с БД
                df = df.rename(columns={'price_with_discount': 'price_witch_discount'})
                float_cols = ['price_no_discounts', 'price_witch_discount', 'rating']
            else:
                # Используем новое имя столбца
                expected_cols = [
                    'name',
                    'price_no_discounts',
                    'price_with_discount',
                    'rating',
                    'number_of_reviews'
                ]
                float_cols = ['price_no_discounts', 'price_with_discount', 'rating']

            df_to_save = df[expected_cols].copy()

            # Приведение типов
            for col in float_cols:
                if col in df_to_save.columns:
                    df_to_save[col] = pd.to_numeric(df_to_save[col], errors='coerce')

            # Сохраняем данные
            df_to_save.to_sql(
                name=table_name,
                con=self.db_manager.engine,
                if_exists=if_exists,
                index=False,
                method='multi'
            )

            print(f"Данные успешно сохранены в таблицу {table_name}. Записей: {len(df_to_save)}")

        except Exception as e:
            print(f"Ошибка при сохранении в базу данных: {e}")
            raise