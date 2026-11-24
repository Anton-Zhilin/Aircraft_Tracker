from typing import List


from aircraft_tracker.api import AeroplanesAPI
from aircraft_tracker.models import Aeroplane, AeroplaneParser
from aircraft_tracker.storage import JSONStorage


# Вспомогательные функции для обработки данных


def filter_by_country(planes: List[Aeroplane], countries: List[str]) -> List[Aeroplane]:
    """Фильтрует самолеты по списку стран регистрации"""
    if not countries:
        return planes

    countries_lower = [c.strip().lower() for c in countries]
    return [p for p in planes if p.origin_country.lower() in countries_lower]


def filter_by_altitude(planes: List[Aeroplane], min_alt: float, max_alt: float) -> List[Aeroplane]:
    """Фильтрует самолеты по диапазону барометрической высоты."""
    result = []
    for p in planes:
        if p.baro_altitude is not None:
            if min_alt <= p.baro_altitude <= max_alt:
                result.append(p)
    return result


def sort_by_altitude_desc(planes: List[Aeroplane]) -> List[Aeroplane]:
    """
    Сортирует самолеты по высоте по убыванию (от самых высоких к низким).
    """
    return sorted(planes, reverse=True)


def get_top_n(planes: List[Aeroplane], n: int) -> List[Aeroplane]:
    """Возвращает первые N элементов списка."""
    return planes[:n]


def print_aeroplanes(planes: List[Aeroplane]) -> None:
    """Красивый вывод списка самолетов в консоль."""
    if not planes:
        print("\n Самолеты не найдены по заданным критериям.")
        return

    print(f"\n✅ Найдено самолетов: {len(planes)}")
    print("-" * 80)
    print(f"{'Позывной':<12} | {'Страна':<20} | {'Статус':<10} | {'Высота (м)':<12} | {'Скорость (м/с)'}")
    print("-" * 80)

    for p in planes:
        alt_str = f"{p.baro_altitude:.1f}" if p.baro_altitude is not None else "Н/Д"
        vel_str = f"{p.velocity:.1f}" if p.velocity is not None else "Н/Д"
        status = "На земле" if p.on_ground else "В воздухе"

        print(f"{p.callsign:<12} | {p.origin_country:<20} | {status:<10} | {alt_str:<12} | {vel_str}")
    print("-" * 80)


# Основная функция взаимодействия с пользователем


def user_interaction() -> None:
    print("=" * 60)
    print(" 🛩️  Добро пожаловать в Aircraft Tracker!")
    print("=" * 60)

    # 1. Запрос страны
    country = input("\n🌍 Введите название страны для поиска (на английском, например, Spain):\n").strip()
    if not country:
        print("❌ Название страны не может быть пустым. Завершение работы.")
        return

    # 2. Получение данных через API
    try:
        print(f"\n⏳ Запрос данных для страны '{country}'...")
        api = AeroplanesAPI()
        raw_data = api.get_aeroplanes(country)

        # 3. Преобразование сырых данных в объекты
        aeroplanes = AeroplaneParser.parse_from_opensky_response(raw_data)
        print(f"✅ Успешно получены данные о {len(aeroplanes)} самолетах.")

        # 4. Сохранение в JSON
        storage = JSONStorage("aeroplanes_data.json")
        storage.save_all_aeroplanes(aeroplanes, mode="overwrite")
        print("✅ Данные успешно сохранены.")

    except ValueError as ve:
        print(f"❌ Ошибка данных: {ve}")
        return
    except Exception as e:
        print(f"❌ Произошла непредвиденная ошибка при запросе: {e}")
        return

    if not aeroplanes:
        print("⚠️ В данном воздушном пространстве сейчас нет зарегистрированных самолетов.")
        return

    # Топ N
    top_n_str = input("🔝 Введите количество самолетов для вывода в ТОП (по высоте):\n").strip()
    try:
        top_n = int(top_n_str) if top_n_str else 10
        if top_n <= 0:
            top_n = 10
    except ValueError:
        print("⚠️ Неверный формат числа, установлено значение по умолчанию: 10")
        top_n = 10

    # Фильтр по стране регистрации
    filter_countries_str = input(
        "🏳️ Введите страны регистрации для фильтрации (через пробел, или Enter для пропуска):\n").strip()
    filter_countries = filter_countries_str.split() if filter_countries_str else []

    # Фильтр по высоте (дополнительная возможность)
    altitude_range_str = input(
        "☁️ Введите диапазон высот полета (например, '5000 - 10000', или Enter для пропуска):\n").strip()
    min_alt, max_alt = -99999.0, 99999.0
    if altitude_range_str:
        try:
            # Заменяем дефис на пробел и разбиваем, чтобы принять и "5000-10000", и "5000 - 10000"
            parts = altitude_range_str.replace('-', ' ').split()
            if len(parts) == 2:
                min_alt, max_alt = float(parts[0]), float(parts[1])
            else:
                print("⚠️ Неверный формат диапазона, фильтрация по высоте пропущена.")
        except ValueError:
            print("⚠️ Неверный формат чисел, фильтрация по высоте пропущена.")

    # 6. Применение логики обработки
    print("\n⚙️  Обработка данных...")

    # Применяем фильтры
    filtered_aeroplanes = filter_by_country(aeroplanes, filter_countries)
    ranged_aeroplanes = filter_by_altitude(filtered_aeroplanes, min_alt, max_alt)

    # Сортируем и берем топ
    sorted_aeroplanes = sort_by_altitude_desc(ranged_aeroplanes)
    top_aeroplanes = get_top_n(sorted_aeroplanes, top_n)

    # 7. Вывод результата
    print_aeroplanes(top_aeroplanes)


if __name__ == "__main__":
    user_interaction()