# Python
import requests
import json
from pathlib import Path
from pprint import pprint

# URL исходного JSON
URL = "https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json"

# Названия, которые хотим удалить (в нижнем регистре)
BAD_NAMES = {
    "скидки wb клуба",
    "сертификаты wildberries",
    "тренды",
    "авиабилеты",
    "wibes",
}

def clean_nodes(nodes: list[dict]) -> list[dict]:
    """Рекурсивно удаляет элементы с именами из BAD_NAMES."""
    cleaned = []
    for node in nodes:
        name = node.get("name", "").strip().lower()
        if name in BAD_NAMES:
            continue                    # пропускаем этот узел

        if "childs" in node:            # чистим подкатегории
            node["childs"] = clean_nodes(node["childs"])
        cleaned.append(node)
    return cleaned


def main() -> None:
    response = requests.get(URL, timeout=10)
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return

    data_raw = response.json()
    data_clean = clean_nodes(data_raw)

    out_path = Path("../app/json/main-menu-ru-ru-v3.json")
    out_path.write_text(
        json.dumps(data_clean, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Файл {out_path.name} успешно создан")

if __name__ == "__main__":
    main()