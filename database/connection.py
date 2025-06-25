import psycopg2
from sqlalchemy import create_engine
from contextlib import contextmanager
from typing import Generator
from config.settings import Config


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self):
        self.db_config = Config.DB_CONFIG
        self.engine = None
        self._init_engine()

    def _init_engine(self):
        """Инициализирует SQLAlchemy engine"""
        connection_string = Config.get_connection_string()
        self.engine = create_engine(connection_string)

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Контекстный менеджер для получения соединения с БД"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def create_tables(self):
        """Создает необходимые таблицы в базе данных"""
        create_table_query = """
                             CREATE TABLE IF NOT EXISTS wb_products (
                                id SERIAL PRIMARY KEY,
                                name TEXT,
                                price_no_discounts DECIMAL(10, 2),
                                price_with_discount DECIMAL(10, 2),
                                rating DECIMAL(3, 2),
                                number_of_reviews INTEGER,
                                shard TEXT,
                                query_params TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                 );"""



        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_query)

        print("Таблицы созданы успешно")

    def close(self):
        """Закрывает соединение с базой данных"""
        if self.engine:
            self.engine.dispose()
            print("Соединение с базой данных закрыто")