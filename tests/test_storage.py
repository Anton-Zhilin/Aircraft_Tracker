import os
import tempfile
import unittest

from aircraft_tracker.models import Aeroplane
from aircraft_tracker.storage import JSONStorage


class TestJSONStorage(unittest.TestCase):
    """Тесты JSONStorage с использованием временных файлов."""

    def setUp(self):
        """Создаём временный файл для каждого теста."""
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        self.temp_file.close()
        self.storage = JSONStorage(self.temp_file.name)

        self.plane1 = Aeroplane("4b1812", "SWR438A", "Switzerland", 4267.2, 189.7, False)
        self.plane2 = Aeroplane("a1b2c3", "UAL1621", "United States", 10203.18, 268.79, False)

    def tearDown(self):
        """Удаляем временный файл после теста."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    # Тесты add_aeroplane

    def test_add_multiple_planes(self):
        """Добавление нескольких самолётов."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.add_aeroplane(self.plane2)
        all_planes = self.storage.get_all_aeroplanes()
        self.assertEqual(len(all_planes), 2)

    # Тесты delete_aeroplane

    def test_delete_plane(self):
        """Удаление самолёта."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.add_aeroplane(self.plane2)
        self.storage.delete_aeroplane(self.plane1)
        all_planes = self.storage.get_all_aeroplanes()
        self.assertEqual(len(all_planes), 1)
        self.assertEqual(all_planes[0].icao24, "a1b2c3")

    # Тесты get_aeroplanes (фильтрация)

    def test_filter_by_country(self):
        """Фильтрация по стране регистрации."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.add_aeroplane(self.plane2)
        result = self.storage.get_aeroplanes({"origin_country": "Switzerland"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].icao24, "4b1812")

    def test_filter_by_altitude_range(self):
        """Фильтрация по диапазону высот."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.add_aeroplane(self.plane2)
        result = self.storage.get_aeroplanes({"min_altitude": 5000, "max_altitude": 15000})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].icao24, "a1b2c3")

    def test_filter_by_velocity(self):
        """Фильтрация по скорости."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.add_aeroplane(self.plane2)
        result = self.storage.get_aeroplanes({"min_velocity": 200})
        self.assertEqual(len(result), 1)

    def test_filter_by_on_ground(self):
        """Фильтрация по статусу 'на земле'."""
        ground_plane = Aeroplane("g1", "GND1", "USA", 0, 0, True)
        self.storage.add_aeroplane(self.plane1)
        self.storage.add_aeroplane(ground_plane)
        result = self.storage.get_aeroplanes({"on_ground": True})
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].on_ground)

    def test_filter_combined(self):
        """Комбинированная фильтрация."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.add_aeroplane(self.plane2)
        result = self.storage.get_aeroplanes(
            {"origin_country": "Switzerland", "min_altitude": 4000, "max_altitude": 5000}
        )
        self.assertEqual(len(result), 1)

    # Тесты save_all_aeroplanes

    def test_save_all_overwrite(self):
        """Массовое сохранение в режиме overwrite."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.save_all_aeroplanes([self.plane2], mode="overwrite")
        all_planes = self.storage.get_all_aeroplanes()
        self.assertEqual(len(all_planes), 1)
        self.assertEqual(all_planes[0].icao24, "a1b2c3")

    def test_save_all_append(self):
        """Массовое сохранение в режиме append."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.save_all_aeroplanes([self.plane2], mode="append")
        all_planes = self.storage.get_all_aeroplanes()
        self.assertEqual(len(all_planes), 2)

    def test_save_all_append_no_duplicates(self):
        """Append не добавляет дубликаты по icao24."""
        self.storage.add_aeroplane(self.plane1)
        self.storage.save_all_aeroplanes([self.plane1], mode="append")
        all_planes = self.storage.get_all_aeroplanes()
        self.assertEqual(len(all_planes), 1)
