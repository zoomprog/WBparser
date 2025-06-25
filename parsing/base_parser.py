from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from database.models import Product


class BaseParser(ABC):
    """Базовый класс для парсеров"""

    @abstractmethod
    def parse_page(self, page: int) -> List[Product]:
        """Парсит одну страницу и возвращает список товаров"""
        pass

    @abstractmethod
    def build_url(self, page: int) -> str:
        """Строит URL для запроса"""
        pass

    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> List[Product]:
        """Парсит ответ от API и возвращает список товаров"""
        pass