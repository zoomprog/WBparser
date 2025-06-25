
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routes.web_routes import router as web_router
from app.routes.api_routes import router as api_router

app = FastAPI(title="Категории из JSON")
templates = Jinja2Templates(directory="app/templates")

# Подключаем статику
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключаем маршруты
app.include_router(web_router)
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)