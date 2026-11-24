import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from aircraft_tracker.models import Aeroplane


class BaseStorage(ABC):
    """
    Абстрактный базовый класс для работы с хранилищем данных о самолетах.
    """

    @abstractmethod
    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        """Добавить информацию о самолете в хранилище."""
        pass

    @abstractmethod
    def delete_aeroplane(self, aeroplane: Aeroplane) -> None:
        """Удалить информацию о самолете из хранилища."""
        pass

    @abstractmethod
    def get_aeroplanes(self, criteria: Dict[str, Any]) -> List[Aeroplane]:
        """Получить данные из хранилища по указанным критериям."""
        pass

    @abstractmethod
    def get_all_aeroplanes(self) -> List[Aeroplane]:
        """Получить все данные из хранилища."""
        pass

    @abstractmethod
    def save_all_aeroplanes(self, aeroplanes: List[Aeroplane], mode: str = "overwrite") -> None:
        """Массово сохранить список самолетов за одну операцию."""
        pass


class JSONStorage(BaseStorage):
    """
    Реализация хранилища на основе JSON-файла.
    """

    def __init__(self, file_path: str = "aeroplanes.json") -> None:
        self.file_path = file_path
        # Создаем файл, если он не существует
        if not os.path.exists(self.file_path):
            self._save_to_file([])

    # Внутренние методы для работы с файлом

    def _load_from_file(self) -> List[Dict[str, Any]]:
        """Загрузить данные из JSON-файла."""
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_to_file(self, data: List[Dict[str, Any]]) -> None:
        """Сохранить данные в JSON-файл."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _aeroplane_to_dict(self, aeroplane: Aeroplane) -> Dict[str, Any]:
        """Сериализовать объект Aeroplane в словарь для JSON."""
        return {
            "icao24": aeroplane.icao24,
            "callsign": aeroplane.callsign,
            "origin_country": aeroplane.origin_country,
            "baro_altitude": aeroplane.baro_altitude,
            "velocity": aeroplane.velocity,
            "on_ground": aeroplane.on_ground,
        }

    def _dict_to_aeroplane(self, data: Dict[str, Any]) -> Aeroplane:
        """Десериализовать словарь из JSON в объект Aeroplane."""
        return Aeroplane(
            icao24=data["icao24"],
            callsign=data["callsign"],
            origin_country=data["origin_country"],
            baro_altitude=data.get("baro_altitude"),
            velocity=data.get("velocity"),
            on_ground=data.get("on_ground", False),
        )

    # Реализация абстрактных методов

    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        """
        Добавить самолет в JSON-файл.
        Если самолет с таким icao24 уже существует, обновляет его данные.
        """
        data = self._load_from_file()

        # Удаляем старую запись, если она есть (обновление)
        data = [item for item in data if item.get("icao24") != aeroplane.icao24]

        # Добавляем новую запись
        data.append(self._aeroplane_to_dict(aeroplane))
        self._save_to_file(data)

    def delete_aeroplane(self, aeroplane: Aeroplane) -> None:
        """Удалить самолет из JSON-файла по уникальному идентификатору icao24."""
        data = self._load_from_file()

        # Оставляем все записи, кроме удаляемой
        data = [item for item in data if item.get("icao24") != aeroplane.icao24]

        self._save_to_file(data)

    def get_aeroplanes(self, criteria: Dict[str, Any]) -> List[Aeroplane]:
        """
        Получить самолеты по критериям фильтрации.
        """
        data = self._load_from_file()
        planes = [self._dict_to_aeroplane(item) for item in data]

        result = planes

        # Фильтрация по стране регистрации
        if "origin_country" in criteria:
            result = [p for p in result if p.origin_country.lower() == criteria["origin_country"].lower()]

        # Фильтрация по диапазону высот
        if "min_altitude" in criteria:
            result = [p for p in result if p.baro_altitude is not None and p.baro_altitude >= criteria["min_altitude"]]

        if "max_altitude" in criteria:
            result = [p for p in result if p.baro_altitude is not None and p.baro_altitude <= criteria["max_altitude"]]

        # Фильтрация по диапазону скоростей
        if "min_velocity" in criteria:
            result = [p for p in result if p.velocity is not None and p.velocity >= criteria["min_velocity"]]

        if "max_velocity" in criteria:
            result = [p for p in result if p.velocity is not None and p.velocity <= criteria["max_velocity"]]

        # Фильтрация по статусу (в воздухе/на земле)
        if "on_ground" in criteria:
            result = [p for p in result if p.on_ground == criteria["on_ground"]]

        return result

    def get_all_aeroplanes(self) -> List[Aeroplane]:
        """Получить все самолеты из JSON-файла."""
        data = self._load_from_file()
        return [self._dict_to_aeroplane(item) for item in data]

    def save_all_aeroplanes(self, aeroplanes: List[Aeroplane], mode: str = "overwrite") -> None:
        """
        Сохраняет список самолетов в файл за ОДНУ операцию (мгновенно).
        """
        if mode == "overwrite":
            # Конвертируем весь список в словари и сохраняем один раз
            data = [self._aeroplane_to_dict(plane) for plane in aeroplanes]
            self._save_to_file(data)

        elif mode == "append":
            # Читаем файл один раз
            existing_data = self._load_from_file()
            # Создаем множество ID для быстрого поиска O(1)
            existing_icao24s = {item["icao24"] for item in existing_data}

            new_data = []
            for plane in aeroplanes:
                if plane.icao24 not in existing_icao24s:
                    new_data.append(self._aeroplane_to_dict(plane))

            # Сохраняем объединенный результат один раз
            self._save_to_file(existing_data + new_data)
