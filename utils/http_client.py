import requests
import time
import random
from typing import Optional, Dict, Any
from config.settings import Config


class HTTPClient:
    """HTTP клиент для выполнения запросов"""

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.session = requests.Session()
        self.config = Config.PARSER_CONFIG

        # Устанавливаем заголовки
        if headers:
            self.session.headers.update(headers)
        else:
            self.session.headers.update(Config.DEFAULT_HEADERS)

    def get_json(self, url: str, retries: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Выполняет GET запрос и возвращает JSON"""
        if retries is None:
            retries = self.config['retries']

        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=self.config['timeout'])

                if response.status_code == 200:
                    if response.text.strip():
                        return response.json()
                    else:
                        print(f"Пустой ответ, попытка {attempt + 1}")
                elif response.status_code == 429:
                    print("Слишком много запросов, ждём...")
                    time.sleep(self.config['rate_limit_delay'])
                else:
                    print(f"HTTP {response.status_code}, попытка {attempt + 1}")

            except requests.exceptions.Timeout:
                print(f"Таймаут, попытка {attempt + 1}")
            except requests.exceptions.JSONDecodeError:
                print(f"Некорректный JSON, попытка {attempt + 1}")
            except Exception as e:
                print(f"Ошибка запроса, попытка {attempt + 1}: {e}")

            # Ждём перед повторной попыткой
            if attempt < retries - 1:
                delay_range = self.config['delay_range']
                time.sleep(random.uniform(delay_range[0], delay_range[1]))

        return None

    def close(self):
        """Закрывает сессию"""
        self.session.close()