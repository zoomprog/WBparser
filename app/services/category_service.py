from typing import Optional, Dict, Any, List
from fastapi import Request
from utils.category_tree_loader import CategoryTreeLoader
from utils.helpers import get_level_name


class CategoryService:
    """Сервис для работы с категориями."""

    def __init__(self):
        self.tree_loader = CategoryTreeLoader()

    def reload_data(self):
        """Перезагружает данные о категориях."""
        self.tree_loader = CategoryTreeLoader()

    def get_category(self, category_id: int):
        """Получает категорию по ID."""
        return self.tree_loader.get_category(category_id)

    def get_children(self, parent_id: int):
        """Получает дочерние категории."""
        return self.tree_loader.get_children(parent_id)

    def get_root_categories(self):
        """Получает корневые категории."""
        return self.tree_loader.get_root_categories()

    def build_page_context(self, request: Request, selected_path: Optional[str] = None,
                           update_status: Optional[str] = None) -> Dict[str, Any]:
        """Строит контекст для главной страницы."""
        context = {
            "request": request,
            "roots": self.get_root_categories(),
            "update_status": update_status
        }

        if selected_path:
            try:
                path_ids = [int(x) for x in selected_path.split(',') if x]
                context.update(self._build_path_context(path_ids))
            except (ValueError, IndexError):
                pass

        return context

    def _build_path_context(self, path_ids: List[int]) -> Dict[str, Any]:
        """Строит контекст для выбранного пути категорий."""
        context = {
            "selected_path": path_ids,
            "category_levels": [],
            "category_path": []
        }

        # Формируем путь с именами категорий для отображения
        for cat_id in path_ids:
            category = self.get_category(cat_id)
            if category:
                context["category_path"].append({"id": cat_id, "name": category.name})

        # Строим уровни категорий
        for i, cat_id in enumerate(path_ids):
            category = self.get_category(cat_id)
            if category:
                if i == 0:
                    # Первый уровень - корневые категории
                    context["category_levels"].append({
                        "level": i + 1,
                        "level_name": get_level_name(i + 1),
                        "categories": self.get_root_categories(),
                        "selected": cat_id
                    })
                else:
                    # Следующие уровни - дети предыдущего
                    parent_id = path_ids[i - 1]
                    parent_category = self.get_category(parent_id)
                    children = self.get_children(parent_id)
                    if children:
                        context["category_levels"].append({
                            "level": i + 1,
                            "level_name": get_level_name(i + 1, parent_category.name if parent_category else None),
                            "categories": children,
                            "selected": cat_id
                        })

                # Добавляем следующий уровень если есть дети
                if i == len(path_ids) - 1:  # Последний элемент в пути
                    children = self.get_children(cat_id)
                    if children:
                        context["category_levels"].append({
                            "level": i + 2,
                            "level_name": get_level_name(i + 2, category.name),
                            "categories": children,
                            "selected": None
                        })
                    else:
                        # Нет детей - показываем URL
                        context["selected_category"] = category
                        context["final_url"] = category.url

        return context

    def process_category_selection(self, level: int, category_id: Optional[int],
                                   current_path: str) -> str:
        """Обрабатывает выбор категории и возвращает URL для редиректа."""
        if not category_id:
            # Сброс выбора
            return "/"

        # Построение нового пути
        path_ids = [int(x) for x in current_path.split(',') if x] if current_path else []

        # Обрезаем путь до нужного уровня и добавляем новый выбор
        new_path = path_ids[:level - 1] + [category_id]
        path_str = ','.join(map(str, new_path))

        return f"/?selected_path={path_str}"