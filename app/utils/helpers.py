def get_level_name(level: int, parent_category_name: str = None) -> str:
    """Возвращает название уровня категории в зависимости от контекста."""
    if level == 1:
        return "Выберите основную категорию"
    elif level == 2:
        return "Выберите подкатегорию"
    elif level == 3:
        return "Выберите раздел"
    elif level == 4:
        return "Выберите подраздел"
    elif level == 5:
        return "Выберите группу товаров"
    else:
        return "Выберите категорию"