from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from services.category_service import CategoryService
from services.update_service import UpdateService


router = APIRouter()
templates = Jinja2Templates(directory="templates")
category_service = CategoryService()
update_service = UpdateService()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, selected_path: Optional[str] = None, update_status: Optional[str] = None):
    """Главная страница с выбором категорий."""
    context = category_service.build_page_context(request, selected_path, update_status)
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