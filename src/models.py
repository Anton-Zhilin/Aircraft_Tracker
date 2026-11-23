from typing import Any, Dict, List, Optional, Union


class Aeroplane:
    """
    Сущность, представляющая самолет.
    """

    def __init__(
        self,
        icao24: str,
        callsign: str,
        origin_country: str,
        baro_altitude: Optional[float],
        velocity: Optional[float],
        on_ground: bool,
    ) -> None:
        self.icao24 = icao24
        self.callsign = callsign
        self.origin_country = origin_country
        self.baro_altitude = baro_altitude
        self.velocity = velocity
        self.on_ground = on_ground

    # Инкапсуляция и Валидация

    @property
    def icao24(self) -> str:
        return self.__icao24

    @icao24.setter
    def icao24(self, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("ICAO24 должен быть непустой строкой.")
        self.__icao24 = value.strip().lower()

    @property
    def callsign(self) -> str:
        return self.__callsign

    @callsign.setter
    def callsign(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValueError("Позывной должен быть строкой.")
        self.__callsign = value.strip() or "N/A"

    @property
    def origin_country(self) -> str:
        return self.__origin_country

    @origin_country.setter
    def origin_country(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValueError("Страна регистрации должна быть строкой.")
        self.__origin_country = value.strip() or "Unknown"

    @property
    def baro_altitude(self) -> Optional[float]:
        return self.__baro_altitude

    @baro_altitude.setter
    def baro_altitude(self, value: Optional[Union[float, int]]) -> None:  # ← Исправление 1
        if value is None:
            self.__baro_altitude = None
        else:
            if not isinstance(value, (int, float)):
                raise ValueError(f"Некорректный тип высоты: {type(value)}")
            if value < -500:
                raise ValueError(f"Аномально низкая барометрическая высота: {value}")
            self.__baro_altitude = float(value)

    @property
    def velocity(self) -> Optional[float]:
        return self.__velocity

    @velocity.setter
    def velocity(self, value: Optional[Union[float, int]]) -> None:  # ← Исправление 2
        if value is None:
            self.__velocity = None
        else:
            if not isinstance(value, (int, float)):
                raise ValueError(f"Некорректный тип скорости: {type(value)}")
            if value < 0:
                raise ValueError(f"Скорость не может быть отрицательной: {value}")
            self.__velocity = float(value)

    @property
    def on_ground(self) -> bool:
        return self.__on_ground

    @on_ground.setter
    def on_ground(self, value: Any) -> None:
        if not isinstance(value, bool):
            raise ValueError("Статус 'на земле' должен быть булевым значением.")
        self.__on_ground = value

    # Вспомогательные методы для сравнения

    def _get_comparable_altitude(self) -> float:
        return self.baro_altitude if self.baro_altitude is not None else -99999.0

    def _get_comparable_velocity(self) -> float:
        return self.velocity if self.velocity is not None else -1.0

    def _get_comparison_tuple(self) -> tuple:
        return (self._get_comparable_altitude(), self._get_comparable_velocity())

    # Магические методы сравнения

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self._get_comparison_tuple() == other._get_comparison_tuple()

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self._get_comparison_tuple() < other._get_comparison_tuple()

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self._get_comparison_tuple() <= other._get_comparison_tuple()

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self._get_comparison_tuple() > other._get_comparison_tuple()

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self._get_comparison_tuple() >= other._get_comparison_tuple()

    # Явные методы сравнения

    def is_higher_than(self, other: "Aeroplane") -> bool:
        if not isinstance(other, Aeroplane):
            raise TypeError("Сравнение возможно только с другим объектом Aeroplane")
        return self._get_comparable_altitude() > other._get_comparable_altitude()

    def is_faster_than(self, other: "Aeroplane") -> bool:
        if not isinstance(other, Aeroplane):
            raise TypeError("Сравнение возможно только с другим объектом Aeroplane")
        return self._get_comparable_velocity() > other._get_comparable_velocity()

    def __str__(self) -> str:
        alt_str = f"{self.baro_altitude:.1f} м" if self.baro_altitude is not None else "Н/Д"
        vel_str = f"{self.velocity:.1f} м/с" if self.velocity is not None else "Н/Д"
        ground_str = "На земле" if self.on_ground else "В воздухе"
        return f"[{self.callsign}] ({self.origin_country}) | {ground_str} | Высота: {alt_str} | Скорость: {vel_str}"


class AeroplaneParser:
    """
    Класс, отвечающий за преобразование сырых данных API в объекты Aeroplane.
    """

    @staticmethod
    def parse_from_opensky_response(raw_response: Dict[str, Any]) -> List[Aeroplane]:
        planes = []
        states = raw_response.get("states", [])

        for state in states:
            try:
                icao24 = state[0] if state[0] is not None else "unknown"
                callsign = state[1] if state[1] is not None else "N/A"
                origin_country = state[2] if state[2] is not None else "Unknown"

                baro_altitude = state[7]
                velocity = state[9]
                on_ground = bool(state[8]) if state[8] is not None else False

                plane = Aeroplane(
                    icao24=str(icao24),
                    callsign=str(callsign),
                    origin_country=str(origin_country),
                    baro_altitude=float(baro_altitude) if baro_altitude is not None else None,
                    velocity=float(velocity) if velocity is not None else None,
                    on_ground=on_ground,
                )
                planes.append(plane)

            except (ValueError, TypeError, IndexError):
                continue

        return planes
