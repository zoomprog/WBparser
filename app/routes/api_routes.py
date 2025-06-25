from fastapi import APIRouter, HTTPException
from fastapi import APIRouter
from app.services.category_service import CategoryService

router = APIRouter()

category_service = CategoryService()


@router.get("/categories/{parent_id}")
def get_children(parent_id: int):
    """API для получения дочерних категорий."""
    children_list = category_service.get_children(parent_id)
    if not children_list and not category_service.get_category(parent_id):
        raise HTTPException(404, detail="Категория не найдена")
    return [{"id": ch.id, "name": ch.name} for ch in children_list]