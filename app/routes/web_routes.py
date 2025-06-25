from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app.services.category_service import CategoryService
from app.services.update_service import UpdateService
from app.services.parsing_service import ParsingService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
category_service = CategoryService()
update_service = UpdateService()
parsing_service = ParsingService()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, selected_path: Optional[str] = None, update_status: Optional[str] = None,
                parsing_status: Optional[str] = None, error_message: Optional[str] = None):
    """Главная страница с выбором категорий."""
    context = category_service.build_page_context(request, selected_path, update_status)

    # Добавляем информацию о статусе парсинга
    if parsing_status:
        context.update({
            'parsing_status': parsing_status,
            'error_message': error_message
        })

    # Если есть данные о товарах, добавляем их
    if parsing_status == 'success':
        products = parsing_service.get_latest_products()
        context['products'] = products

    return templates.TemplateResponse("index.html", context)


@router.post("/select-category")
async def select_category(
        request: Request,
        level: int = Form(...),
        category_id: Optional[int] = Form(None),
        current_path: str = Form("")
):
    """Обработка выбора категории."""
    redirect_url = category_service.process_category_selection(level, category_id, current_path)
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/update-categories")
async def update_categories(current_path: str = Form("")):
    """Обновление базы категорий из внешнего источника."""
    redirect_url = await update_service.update_categories(current_path)
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/parse-products")
async def parse_products(
        category_url: str = Form(...),
        category_name: str = Form(...),
        selected_path: str = Form(""),
        max_pages: int = Form(3)
):
    """Запуск парсинга товаров для выбранной категории."""
    try:
        print(f"Запрос на парсинг: URL={category_url}, страниц={max_pages}")
        print(f"Имя категории: {category_name}")
        print(f"Путь: {selected_path}")

        # Получаем ID категории из пути
        category_id = None
        if selected_path:
            try:
                path_ids = [int(x) for x in selected_path.split(',') if x]
                if path_ids:
                    category_id = path_ids[-1]  # Берем последний ID из пути
                    print(f"ID категории: {category_id}")
            except ValueError:
                pass

        # Отладка поиска категории
        if category_name:
            parsing_service.debug_category_search(category_name)

        # Запускаем парсинг
        success = await parsing_service.parse_category_products(category_url, category_name, max_pages)

        if success:
            redirect_url = f"/?selected_path={selected_path}&parsing_status=success"
        else:
            redirect_url = f"/?selected_path={selected_path}&parsing_status=error&error_message=Не удалось получить данные. Проверьте параметры категории."

    except Exception as e:
        print(f"Ошибка в parse_products: {e}")
        redirect_url = f"/?selected_path={selected_path}&parsing_status=error&error_message={str(e)}"

    return RedirectResponse(url=redirect_url, status_code=303)