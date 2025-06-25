import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class CategoryNode:
    """Упрощённый узел дерева."""
    id: int
    name: str
    url: Optional[str] = None
    shard: Optional[str] = None
    query: Optional[str] = None
    children: List["CategoryNode"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class CategoryTreeLoader:
    """Класс для загрузки и работы с деревом категорий."""

    def __init__(self, data_file: str = "app/json/main-menu-ru-ru-v3.json"):
        self.data_file = data_file
        self.cat_index: Dict[int, CategoryNode] = {}
        self.root_ids: List[int] = []
        self.url_index: Dict[str, CategoryNode] = {}  # Индекс по URL
        self._load_tree()

    def _load_tree(self) -> None:
        """Загружает дерево категорий из JSON-файла."""
        with open(self.data_file, encoding="utf-8") as f:
            data = json.load(f)

        # Строим все узлы
        for raw_root in data:
            root = self._build_node(raw_root)
            self._index_node(root)

        # Находим корневые узлы
        all_ids = set(self.cat_index.keys())
        child_ids = {ch.id for node in self.cat_index.values() for ch in node.children}
        self.root_ids = sorted(all_ids - child_ids)

    def _build_node(self, data: Dict[str, Any]) -> CategoryNode:
        """Рекурсивно строит узел дерева из JSON-данных."""
        return CategoryNode(
            id=data["id"],
            name=data["name"],
            url=data.get("url"),
            shard=data.get("shard"),
            query=data.get("query"),
            children=[self._build_node(child) for child in data.get("childs", [])]
        )

    def _index_node(self, node: CategoryNode) -> None:
        """Добавляет узел и его детей в индекс."""
        self.cat_index[node.id] = node
        if node.url:
            self.url_index[node.url] = node
        for child in node.children:
            self._index_node(child)

    def get_category(self, category_id: int) -> Optional[CategoryNode]:
        """Возвращает категорию по ID."""
        return self.cat_index.get(category_id)

    def get_category_by_url(self, url: str) -> Optional[CategoryNode]:
        """Возвращает категорию по URL."""
        return self.url_index.get(url)

    def get_root_categories(self) -> List[CategoryNode]:
        """Возвращает список корневых категорий."""
        return [self.cat_index[cat_id] for cat_id in self.root_ids]

    def get_children(self, parent_id: int) -> List[CategoryNode]:
        """Возвращает дочерние категории для указанного родителя."""
        parent = self.get_category(parent_id)
        return parent.children if parent else []

    def get_category_url(self, category_id: int) -> Optional[str]:
        """Возвращает URL категории по её ID."""
        category = self.get_category(category_id)
        return category.url if category else None

    def get_category_params(self, category_id: int) -> tuple[Optional[str], Optional[str]]:
        """Возвращает shard и query для категории по её ID."""
        category = self.get_category(category_id)
        if category:
            return category.shard, category.query
        return None, None

    def get_category_params_by_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Возвращает shard и query для категории по её URL."""
        category = self.get_category_by_url(url)
        if category:
            return category.shard, category.query
        return None, None

    def get_category_path(self, category_id: int) -> List[CategoryNode]:
        """Возвращает путь от корня до указанной категории."""

        def find_path(node: CategoryNode, target_id: int, path: List[CategoryNode]) -> Optional[List[CategoryNode]]:
            path.append(node)
            if node.id == target_id:
                return path.copy()

            for child in node.children:
                result = find_path(child, target_id, path)
                if result:
                    return result

            path.pop()
            return None

        for root_id in self.root_ids:
            root = self.cat_index[root_id]
            path = find_path(root, category_id, [])
            if path:
                return path
        return []

    def find_best_match_url(self, target_url: str) -> Optional[CategoryNode]:
        """Находит наиболее подходящую категорию по части URL."""
        # Очищаем URL от доменов и протоколов
        clean_target = target_url.split('/')[-1] if '/' in target_url else target_url
        clean_target = clean_target.split('?')[0]  # Убираем параметры

        best_match = None
        best_score = 0

        for url, category in self.url_index.items():
            if not url:
                continue

            clean_url = url.split('/')[-1] if '/' in url else url

            # Простое сравнение по совпадению частей URL
            if clean_target in clean_url or clean_url in clean_target:
                score = len(clean_url) if clean_target in clean_url else len(clean_target)
                if score > best_score:
                    best_score = score
                    best_match = category

        return best_match