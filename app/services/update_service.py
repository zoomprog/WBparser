import subprocess
import sys
from pathlib import Path
from services.category_service import CategoryService


class UpdateService:
    """Сервис для обновления категорий."""

    def __init__(self):
        self.category_service = CategoryService()

    async def update_categories(self, current_path: str = "") -> str:
        """Обновляет базу категорий из внешнего источника и возвращает URL для редиректа."""
        try:
            # Запускаем скрипт
            result = subprocess.run(
                [sys.executable, str(Path("../parsing/search_category_json.py").resolve())],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            if result.returncode == 0:
                # Перезагружаем данные
                self.category_service.reload_data()

                # Перенаправляем с параметром успеха
                redirect_url = "/?update_status=success"
                if current_path:
                    redirect_url += f"&selected_path={current_path}"
                return redirect_url
            else:
                # Ошибка выполнения скрипта
                error_msg = result.stderr or "Неизвестная ошибка при выполнении скрипта"
                return self._build_error_url(error_msg, current_path)

        except Exception as e:
            # Общая ошибка
            return self._build_error_url(str(e), current_path)

    def _build_error_url(self, error_msg: str, current_path: str) -> str:
        """Строит URL для редиректа при ошибке."""
        redirect_url = f"/?update_status=error&error_msg={error_msg}"
        if current_path:
            redirect_url += f"&selected_path={current_path}"
        return redirect_url