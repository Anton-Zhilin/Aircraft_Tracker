import unittest

from aircraft_tracker.models import Aeroplane
from main import filter_by_altitude, filter_by_country, get_top_n, sort_by_altitude_desc


class TestFilterByCountry(unittest.TestCase):
    """Тесты фильтрации по стране."""

    def setUp(self):
        self.planes = [
            Aeroplane("a1", "T1", "United States", 1000, 100, False),
            Aeroplane("a2", "T2", "Germany", 2000, 200, False),
            Aeroplane("a3", "T3", "United States", 3000, 300, False),
        ]

    def test_filter_single_country(self):
        """Фильтрация по одной стране."""
        result = filter_by_country(self.planes, ["United States"])
        self.assertEqual(len(result), 2)

    def test_filter_multiple_countries(self):
        """Фильтрация по нескольким странам."""
        result = filter_by_country(self.planes, ["United States", "Germany"])
        self.assertEqual(len(result), 3)

    def test_filter_no_match(self):
        """Фильтрация без совпадений."""
        result = filter_by_country(self.planes, ["France"])
        self.assertEqual(len(result), 0)

    def test_filter_empty_list(self):
        """Пустой список стран — возвращает все самолёты."""
        result = filter_by_country(self.planes, [])
        self.assertEqual(len(result), 3)


class TestFilterByAltitude(unittest.TestCase):
    """Тесты фильтрации по высоте."""

    def setUp(self):
        self.planes = [
            Aeroplane("a1", "T1", "USA", 5000, 100, False),
            Aeroplane("a2", "T2", "USA", 10000, 200, False),
            Aeroplane("a3", "T3", "USA", 15000, 300, False),
            Aeroplane("a4", "T4", "USA", None, 400, False),
        ]

    def test_filter_range(self):
        """Фильтрация по диапазону высот."""
        result = filter_by_altitude(self.planes, 6000, 12000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].baro_altitude, 10000)

    def test_filter_excludes_none(self):
        """Самолёты без высоты исключаются."""
        result = filter_by_altitude(self.planes, 0, 20000)
        self.assertEqual(len(result), 3)


class TestSortByAltitudeDesc(unittest.TestCase):
    """Тесты сортировки по убыванию высоты."""

    def test_sort_descending(self):
        """Сортировка от высокой к низкой."""
        planes = [
            Aeroplane("a1", "T1", "USA", 5000, 100, False),
            Aeroplane("a2", "T2", "USA", 15000, 200, False),
            Aeroplane("a3", "T3", "USA", 10000, 300, False),
        ]
        sorted_planes = sort_by_altitude_desc(planes)
        self.assertEqual(sorted_planes[0].baro_altitude, 15000)
        self.assertEqual(sorted_planes[1].baro_altitude, 10000)
        self.assertEqual(sorted_planes[2].baro_altitude, 5000)

    def test_sort_with_none_altitude(self):
        """Самолёты без высоты — в конце списка."""
        planes = [
            Aeroplane("a1", "T1", "USA", None, 100, False),
            Aeroplane("a2", "T2", "USA", 5000, 200, False),
        ]
        sorted_planes = sort_by_altitude_desc(planes)
        self.assertEqual(sorted_planes[0].baro_altitude, 5000)
        self.assertIsNone(sorted_planes[1].baro_altitude)


class TestGetTopN(unittest.TestCase):
    """Тесты получения топ-N самолётов."""

    def setUp(self):
        self.planes = [
            Aeroplane("a1", "T1", "USA", 1000, 100, False),
            Aeroplane("a2", "T2", "USA", 2000, 200, False),
            Aeroplane("a3", "T3", "USA", 3000, 300, False),
            Aeroplane("a4", "T4", "USA", 4000, 400, False),
        ]

    def test_top_2(self):
        """Топ-2 после сортировки."""
        sorted_planes = sort_by_altitude_desc(self.planes)
        top = get_top_n(sorted_planes, 2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0].baro_altitude, 4000)
        self.assertEqual(top[1].baro_altitude, 3000)

    def test_top_larger_than_list(self):
        """N больше количества самолётов — возвращает весь список."""
        sorted_planes = sort_by_altitude_desc(self.planes)
        top = get_top_n(sorted_planes, 10)
        self.assertEqual(len(top), 4)

    def test_top_zero(self):
        """N=0 — возвращает пустой список."""
        top = get_top_n(self.planes, 0)
        self.assertEqual(len(top), 0)
