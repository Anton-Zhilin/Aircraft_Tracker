import unittest

from aircraft_tracker.models import Aeroplane, AeroplaneParser


class TestAeroplane(unittest.TestCase):
    """Тесты класса Aeroplane: валидация, инкапсуляция, сравнение."""

    def setUp(self):
        """Создаём два тестовых самолёта."""
        self.plane1 = Aeroplane(
            icao24="4b1812",
            callsign="SWR438A",
            origin_country="Switzerland",
            baro_altitude=4267.2,
            velocity=189.7,
            on_ground=False,
        )
        self.plane2 = Aeroplane(
            icao24="a1b2c3",
            callsign="UAL1621",
            origin_country="United States",
            baro_altitude=10203.18,
            velocity=268.79,
            on_ground=False,
        )

    # Тесты валидации

    def test_valid_creation(self):
        """Корректное создание объекта."""
        self.assertEqual(self.plane1.icao24, "4b1812")
        self.assertEqual(self.plane1.callsign, "SWR438A")
        self.assertEqual(self.plane1.baro_altitude, 4267.2)

    def test_icao24_empty_raises(self):
        """Пустой ICAO24 должен вызывать ValueError."""
        with self.assertRaises(ValueError):
            Aeroplane("", "TEST", "USA", 1000, 100, False)

    def test_icao24_auto_lowercase(self):
        """ICAO24 автоматически приводится к нижнему регистру."""
        p = Aeroplane("ABC123", "TEST", "USA", 1000, 100, False)
        self.assertEqual(p.icao24, "abc123")

    def test_callsign_empty_becomes_na(self):
        """Пустой позывной заменяется на 'N/A'."""
        p = Aeroplane("abc123", "", "USA", 1000, 100, False)
        self.assertEqual(p.callsign, "N/A")

    def test_country_empty_becomes_unknown(self):
        """Пустая страна заменяется на 'Unknown'."""
        p = Aeroplane("abc123", "TEST", "", 1000, 100, False)
        self.assertEqual(p.origin_country, "Unknown")

    def test_negative_velocity_raises(self):
        """Отрицательная скорость должна вызывать ValueError."""
        with self.assertRaises(ValueError):
            Aeroplane("abc123", "TEST", "USA", 1000, -10, False)

    def test_altitude_none_allowed(self):
        """None для высоты допустим."""
        p = Aeroplane("abc123", "TEST", "USA", None, 100, False)
        self.assertIsNone(p.baro_altitude)

    def test_velocity_none_allowed(self):
        """None для скорости допустим."""
        p = Aeroplane("abc123", "TEST", "USA", 1000, None, False)
        self.assertIsNone(p.velocity)

    # Тесты инкапсуляции (сеттеры)

    def test_setter_velocity_validation(self):
        """Сеттер velocity тоже валидирует данные."""
        with self.assertRaises(ValueError):
            self.plane1.velocity = -50

    def test_setter_altitude_validation(self):
        """Сеттер baro_altitude валидирует аномальные значения."""
        with self.assertRaises(ValueError):
            self.plane1.baro_altitude = -1000

    # Тесты сравнения

    def test_comparison_by_altitude(self):
        """Самолёт с большей высотой 'больше'."""
        self.assertGreater(self.plane2, self.plane1)
        self.assertLess(self.plane1, self.plane2)

    def test_comparison_equal_altitude(self):
        """При равной высоте сравниваются по скорости."""
        p1 = Aeroplane("a1", "T1", "USA", 5000, 100, False)
        p2 = Aeroplane("a2", "T2", "USA", 5000, 200, False)
        self.assertLess(p1, p2)

    def test_equality(self):
        """Одинаковые самолёты равны."""
        p1 = Aeroplane("a1", "T1", "USA", 5000, 100, False)
        p2 = Aeroplane("a2", "T2", "USA", 5000, 100, False)
        self.assertEqual(p1, p2)

    def test_is_higher_than(self):
        """Явный метод is_higher_than."""
        self.assertTrue(self.plane2.is_higher_than(self.plane1))
        self.assertFalse(self.plane1.is_higher_than(self.plane2))

    def test_is_faster_than(self):
        """Явный метод is_faster_than."""
        self.assertTrue(self.plane2.is_faster_than(self.plane1))
        self.assertFalse(self.plane1.is_faster_than(self.plane2))

    def test_comparison_with_none_altitude(self):
        """Самолёт без высоты считается 'ниже всех'."""
        p_no_alt = Aeroplane("a1", "T1", "USA", None, 100, False)
        self.assertLess(p_no_alt, self.plane1)

    def test_comparison_with_none_velocity(self):
        """Самолёт без скорости считается 'медленнее всех'."""
        p_no_vel = Aeroplane("a1", "T1", "USA", 5000, None, False)
        p_with_vel = Aeroplane("a2", "T2", "USA", 5000, 100, False)
        self.assertLess(p_no_vel, p_with_vel)

    def test_eq_with_non_aeroplane(self):
        """Сравнение с объектом другого типа возвращает NotImplemented."""
        self.assertEqual(self.plane1.__eq__("not a plane"), NotImplemented)


class TestAeroplaneParser(unittest.TestCase):
    """Тесты парсера сырых данных OpenSky."""

    RAW_RESPONSE = {
        "time": 1766142246,
        "states": [
            [
                "4b1812",
                "SWR438A",
                "Switzerland",
                1766166618,
                1766166618,
                -0.0168,
                51.0888,
                4267.2,
                False,
                189.7,
                129.39,
                14.63,
                None,
                4282.44,
                "2061",
                False,
                0,
            ],
            ["a1b2c3", None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ],
    }

    def test_parse_success(self):
        """Парсинг корректного ответа."""
        planes = AeroplaneParser.parse_from_opensky_response(self.RAW_RESPONSE)
        self.assertEqual(len(planes), 2)
        self.assertEqual(planes[0].icao24, "4b1812")
        self.assertEqual(planes[0].callsign, "SWR438A")

    def test_parse_null_fields(self):
        """Поля со значением null должны стать None или дефолтными."""
        planes = AeroplaneParser.parse_from_opensky_response(self.RAW_RESPONSE)
        plane2 = planes[1]
        self.assertEqual(plane2.callsign, "N/A")
        self.assertEqual(plane2.origin_country, "Unknown")
        self.assertIsNone(plane2.baro_altitude)
        self.assertIsNone(plane2.velocity)

    def test_parse_empty_states(self):
        """Пустой список states — возвращается пустой список."""
        result = AeroplaneParser.parse_from_opensky_response({"states": []})
        self.assertEqual(result, [])

    def test_parse_no_states_key(self):
        """Отсутствие ключа 'states' — возвращается пустой список."""
        result = AeroplaneParser.parse_from_opensky_response({"time": 123})
        self.assertEqual(result, [])
