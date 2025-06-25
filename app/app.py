from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.category_tree_loader import CategoryTreeLoader
from typing import Optional

app = FastAPI(title="Категории из JSON")
templates = Jinja2Templates(directory="templates")

# Подключаем статику
app.mount("/static", StaticFiles(directory="static"), name="static")

# Создаем экземпляр загрузчика категорий
tree_loader = CategoryTreeLoader()

def get_level_name(level: int, parent_category_name: str = None) -> str:
    """Возвращает название уровня категории в зависимости от контекста."""
    if level == 1:
        return "Выберите основную категорию"
    elif level == 2:
        return f"Выберите подкатегорию"
    elif level == 3:
        return f"Выберите раздел"
    elif level == 4:
        return f"Выберите подраздел"
    elif level == 5:
        return f"Выберите группу товаров"
    else:
        return f"Выберите категорию"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, selected_path: Optional[str] = None):
    """Главная страница с выбором категорий."""
    context = {
        "request": request,
        "roots": tree_loader.get_root_categories()
    }

    # Если есть выбранный путь, восстанавливаем состояние
    if selected_path:
        try:
            path_ids = [int(x) for x in selected_path.split(',') if x]
            context["selected_path"] = path_ids
            context["category_levels"] = []

            # Формируем путь с именами категорий для отображения
            category_path = []
            for cat_id in path_ids:
                category = tree_loader.get_category(cat_id)
                if category:
                    category_path.append({"id": cat_id, "name": category.name})
            context["category_path"] = category_path

            for i, cat_id in enumerate(path_ids):
                category = tree_loader.get_category(cat_id)
                if category:
                    if i == 0:
                        # Первый уровень - корневые категории
                        context["category_levels"].append({
                            "level": i + 1,
                            "level_name": get_level_name(i + 1),
                            "categories": tree_loader.get_root_categories(),
                            "selected": cat_id
                        })
                    else:
                        # Следующие уровни - дети предыдущего
                        parent_id = path_ids[i - 1]
                        parent_category = tree_loader.get_category(parent_id)
                        children = tree_loader.get_children(parent_id)
                        if children:
                            context["category_levels"].append({
                                "level": i + 1,
                                "level_name": get_level_name(i + 1, parent_category.name if parent_category else None),
                                "categories": children,
                                "selected": cat_id
                            })

                    # Добавляем следующий уровень если есть дети
                    if i == len(path_ids) - 1:  # Последний элемент в пути
                        children = tree_loader.get_children(cat_id)
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
        except (ValueError, IndexError):
            pass

    return templates.TemplateResponse("index.html", context)


@app.post("/select-category")
async def select_category(
        request: Request,
        level: int = Form(...),
        category_id: Optional[int] = Form(None),
        current_path: str = Form("")
):
    """Обработка выбора категории."""
    if not category_id:
        # Сброс выбора
        return RedirectResponse(url="/", status_code=303)

    # Построение нового пути
    path_ids = [int(x) for x in current_path.split(',') if x] if current_path else []

    # Обрезаем путь до нужного уровня и добавляем новый выбор
    new_path = path_ids[:level - 1] + [category_id]
    path_str = ','.join(map(str, new_path))

    return RedirectResponse(url=f"/?selected_path={path_str}", status_code=303)


@app.get("/api/categories/{parent_id}")
def children(parent_id: int):
    """API для получения дочерних категорий (для обратной совместимости)."""
    children_list = tree_loader.get_children(parent_id)
    if not children_list and not tree_loader.get_category(parent_id):
        raise HTTPException(404, detail="Категория не найдена")
    return [{"id": ch.id, "name": ch.name} for ch in children_list]