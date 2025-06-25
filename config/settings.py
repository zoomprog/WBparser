import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()


class Config:
    """Класс для управления конфигурацией приложения"""

    # База данных
    DB_CONFIG = {
        'host': os.getenv('HOST', 'localhost'),
        'database': os.getenv('DATABASE', 'postgres'),
        'user': os.getenv('USER', 'postgres'),
        'password': os.getenv('PASSWORD', '123'),
        'port': int(os.getenv('PORT', 5432))
    }

    # Настройки парсера
    PARSER_CONFIG = {
        'timeout': 10,
        'retries': 3,
        'max_consecutive_errors': 5,
        'delay_range': (2, 5),
        'rate_limit_delay': 20
    }

    # HTTP заголовки
    DEFAULT_HEADERS = {
        'accept': '*/*',
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
    }

    @classmethod
    def get_connection_string(cls) -> str:
        """Возвращает строку подключения к базе данных"""
        config = cls.DB_CONFIG
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"