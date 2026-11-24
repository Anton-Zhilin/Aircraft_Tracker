from abc import ABC, abstractmethod
from typing import Any, Dict, List

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPENSKY_URL = "https://opensky-network.org/api/states/all"
REQUEST_TIMEOUT = 15


class BaseAirspaceAPI(ABC):
    """
    Абстрактный базовый класс для работы с API воздушного пространства.
    """

    @abstractmethod
    def get_country_coordinates(self, country: str) -> List[str]:
        """
        Получает географические координаты (bounding box) страны.
        :param country: Название страны (рекомендуется на английском языке).
        :return: Список из 4-х строк: [minlat, maxlat, minlon, maxlon].
        """
        pass

    @abstractmethod
    def get_aeroplanes(self, country: str) -> Dict[str, Any]:
        """
        Получает информацию о самолетах в воздушном пространстве страны.
        :param country: Название страны.
        :return: Словарь с сырыми данными от API OpenSky (включая ключ 'states').
        """
        pass


class AeroplanesAPI(BaseAirspaceAPI):
    """
    Конкретная реализация API для связки Nominatim + OpenSky Network.
    """

    def __init__(self) -> None:
        self.nominatim_url = NOMINATIM_URL
        self.opensky_url = OPENSKY_URL

        self.headers_nominatim = {
            "User-Agent": "Aircraft_Tracker/1.0 (educational project)",
            "Accept-Language": "en",  # Гарантирует предсказуемость ответов Nominatim
        }

    def get_country_coordinates(self, country: str) -> List[str]:
        params = {
            "country": country,
            "format": "json",
            "limit": 1,
        }

        response = requests.get(
            url=self.nominatim_url, params=params, headers=self.headers_nominatim, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError(
                f"Страна '{country}' не найдена. Попробуйте ввести название на английском языке (например, 'Germany')."
            )

        boundingbox = data[0].get("boundingbox")
        if not boundingbox or len(boundingbox) != 4:
            raise ValueError(f"Не удалось получить корректный boundingbox для страны '{country}'.")

        return boundingbox

    def get_aeroplanes(self, country: str) -> Dict[str, Any]:
        # 1. Получаем координаты [minlat, maxlat, minlon, maxlon]
        bbox = self.get_country_coordinates(country)

        # 2. Формируем параметры для OpenSky Network
        # (строго по документации: lamin, lamax, lomin, lomax)
        params = {
            "lamin": float(bbox[0]),
            "lamax": float(bbox[1]),
            "lomin": float(bbox[2]),
            "lomax": float(bbox[3]),
        }

        response = requests.get(url=self.opensky_url, params=params, timeout=REQUEST_TIMEOUT)

        # Специальная обработка для лимитов OpenSky (429 Too Many Requests)
        if response.status_code == 429:
            raise RuntimeError(
                "Превышен лимит запросов к OpenSky Network. Подождите немного или используйте аутентификацию."
            )

        response.raise_for_status()

        return response.json()
