import unittest
from unittest.mock import patch, MagicMock
import json

from aircraft_tracker.api import AeroplanesAPI


class TestAeroplanesAPI(unittest.TestCase):
    """Тесты класса AeroplanesAPI с мокированием HTTP-запросов."""

    def setUp(self):
        """Создаём экземпляр API перед каждым тестом."""
        self.api = AeroplanesAPI()

    # Примеры ответов API

    NOMINATIM_RESPONSE = [
        {
            "place_id": 346277167,
            "name": "Spain",
            "boundingbox": ["36.0", "43.8", "-9.3", "3.3"]
        }
    ]

    OPENSKY_RESPONSE = {
        "time": 1766142246,
        "states": [
            [
                "4b1812", "SWR438A ", "Switzerland",
                1766166618, 1766166618, -0.0168, 51.0888,
                4267.2, False, 189.7, 129.39, 14.63,
                None, 4282.44, "2061", False, 0
            ],
            [
                "a1b2c3", "UAL1621", "United States",
                1766166620, 1766166620, -10.5, 52.1,
                10203.18, False, 268.79, 130.0, 0.0,
                None, 10250.0, "1000", False, 0
            ]
        ]
    }

    # Тесты get_country_coordinates

    @patch("aircraft_tracker.api.requests.get")
    def test_get_country_coordinates_success(self, mock_get):
        """Успешное получение координат страны."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.NOMINATIM_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        bbox = self.api.get_country_coordinates("Spain")

        self.assertEqual(bbox, ["36.0", "43.8", "-9.3", "3.3"])
        mock_get.assert_called_once()

    @patch("aircraft_tracker.api.requests.get")
    def test_get_country_coordinates_not_found(self, mock_get):
        """Страна не найдена — должно быть исключение ValueError."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            self.api.get_country_coordinates("Atlantida")
        self.assertIn("не найдена", str(ctx.exception))

    @patch("aircraft_tracker.api.requests.get")
    def test_get_country_coordinates_no_boundingbox(self, mock_get):
        """Ответ без boundingbox — должно быть исключение."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "Spain"}]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            self.api.get_country_coordinates("Spain")

    # --- Тесты get_aeroplanes ---

    @patch("aircraft_tracker.api.requests.get")
    def test_get_aeroplanes_success(self, mock_get):
        """Успешное получение данных о самолётах."""
        # Мокаем два последовательных вызова requests.get

        nominatim_mock = MagicMock()
        nominatim_mock.json.return_value = self.NOMINATIM_RESPONSE
        nominatim_mock.raise_for_status = MagicMock()

        opensky_mock = MagicMock()
        opensky_mock.json.return_value = self.OPENSKY_RESPONSE
        opensky_mock.raise_for_status = MagicMock()
        opensky_mock.status_code = 200

        mock_get.side_effect = [nominatim_mock, opensky_mock]

        result = self.api.get_aeroplanes("Spain")

        self.assertIn("states", result)
        self.assertEqual(len(result["states"]), 2)
        self.assertEqual(mock_get.call_count, 2)

    @patch("aircraft_tracker.api.requests.get")
    def test_get_aeroplanes_rate_limit(self, mock_get):
        """Превышение лимита запросов OpenSky — RuntimeError."""
        nominatim_mock = MagicMock()
        nominatim_mock.json.return_value = self.NOMINATIM_RESPONSE
        nominatim_mock.raise_for_status = MagicMock()

        opensky_mock = MagicMock()
        opensky_mock.status_code = 429

        mock_get.side_effect = [nominatim_mock, opensky_mock]

        with self.assertRaises(RuntimeError) as ctx:
            self.api.get_aeroplanes("Spain")
        self.assertIn("лимит", str(ctx.exception).lower())

