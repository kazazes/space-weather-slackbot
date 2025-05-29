import pytest
from unittest.mock import patch, Mock
import main


class TestDataSources:
    """Test suite for NOAA SWPC data source functions"""

    @pytest.fixture
    def mock_kp_data(self):
        """Mock K-index data from NOAA API"""
        return [
            {"k_index": "3", "time_tag": "2024-01-15T10:00:00Z", "kp_index": "3.0"},
            {"k_index": "5", "time_tag": "2024-01-15T11:00:00Z", "kp_index": "5.0"},
            {"k_index": "7", "time_tag": "2024-01-15T12:00:00Z", "kp_index": "7.0"},
        ]

    @pytest.fixture
    def mock_flare_data(self):
        """Mock solar flare data from GOES"""
        return [
            {
                "flux": "8.5e-6",
                "time_tag": "2024-01-15T10:00:00Z",
                "satellite": "GOES-16",
            },
            {
                # M-class flare
                "flux": "1.2e-5",
                "time_tag": "2024-01-15T11:00:00Z",
                "satellite": "GOES-16",
            },
            {
                # X-class flare
                "flux": "2.4e-4",
                "time_tag": "2024-01-15T12:00:00Z",
                "satellite": "GOES-16",
            },
        ]

    @pytest.fixture
    def mock_proton_data(self):
        """Mock proton flux data"""
        return [
            {"flux": "0.8", "time_tag": "2024-01-15T10:00:00Z", "energy": ">=10 MeV"},
            {"flux": "5.2", "time_tag": "2024-01-15T11:00:00Z", "energy": ">=10 MeV"},
            {
                # Above threshold
                "flux": "15.7",
                "time_tag": "2024-01-15T12:00:00Z",
                "energy": ">=10 MeV",
            },
        ]

    @pytest.fixture
    def mock_solar_wind_data(self):
        """Mock solar wind data from DSCOVR"""
        return [
            {"speed": "350.5", "time_tag": "2024-01-15T10:00:00Z", "density": "5.2"},
            {"speed": "450.8", "time_tag": "2024-01-15T11:00:00Z", "density": "7.1"},
            {
                # Above threshold
                "speed": "725.3",
                "time_tag": "2024-01-15T12:00:00Z",
                "density": "12.5",
            },
        ]

    @patch("main.requests.get")
    def test_fetch_json_success(self, mock_get):
        """Test successful JSON fetching"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        result = main.fetch_json("http://test.url")
        assert result == {"data": "test"}
        mock_get.assert_called_once_with("http://test.url")

    @patch("main.requests.get")
    def test_fetch_json_failure(self, mock_get):
        """Test JSON fetching with network error"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            main.fetch_json("http://test.url")

    @patch("main.fetch_json")
    def test_get_latest_kp(self, mock_fetch, mock_kp_data):
        """Test K-index parsing"""
        mock_fetch.return_value = mock_kp_data

        kp, time_tag = main.get_latest_kp()

        assert kp == 7.0
        assert time_tag == "2024-01-15T12:00:00Z"
        mock_fetch.assert_called_once_with(main.K_INDEX_URL)

    @patch("main.fetch_json")
    def test_get_latest_kp_empty_data(self, mock_fetch):
        """Test K-index parsing with empty data"""
        mock_fetch.return_value = []

        with pytest.raises(IndexError):
            main.get_latest_kp()

    def test_check_storm_levels(self):
        """Test storm level detection for different Kp values"""
        test_cases = [
            (3.0, None),  # No storm
            (4.9, None),  # Just below G1
            (5.0, "Minor"),  # G1
            (6.0, "Moderate"),  # G2
            (7.0, "Strong"),  # G3
            (8.0, "Severe"),  # G4
            (9.0, "Extreme"),  # G5
        ]

        for kp, expected_level in test_cases:
            assert main.check_storm(kp) == expected_level

    @patch("main.fetch_json")
    def test_check_flare_m_class(self, mock_fetch, mock_flare_data):
        """Test M-class flare detection"""
        # M-class flare
        mock_fetch.return_value = [mock_flare_data[1]]

        level, flux, time_tag = main.check_flare()

        assert level == "M"
        assert flux == 1.2e-5
        assert time_tag == "2024-01-15T11:00:00Z"

    @patch("main.fetch_json")
    def test_check_flare_x_class(self, mock_fetch, mock_flare_data):
        """Test X-class flare detection"""
        # X-class flare
        mock_fetch.return_value = [mock_flare_data[2]]

        level, flux, time_tag = main.check_flare()

        assert level == "X"
        assert flux == 2.4e-4
        assert time_tag == "2024-01-15T12:00:00Z"

    @patch("main.fetch_json")
    def test_check_flare_below_threshold(self, mock_fetch, mock_flare_data):
        """Test flare detection below M-class threshold"""
        # Below threshold
        mock_fetch.return_value = [mock_flare_data[0]]

        level, flux, time_tag = main.check_flare()

        assert level is None
        assert flux is None
        assert time_tag is None

    @patch("main.fetch_json")
    def test_check_proton_flux_alert(self, mock_fetch, mock_proton_data):
        """Test proton flux alert detection"""
        # Above threshold
        mock_fetch.return_value = [mock_proton_data[2]]

        alert, flux, time_tag = main.check_proton_flux()

        assert alert is True
        assert flux == 15.7
        assert time_tag == "2024-01-15T12:00:00Z"

    @patch("main.fetch_json")
    def test_check_proton_flux_normal(self, mock_fetch, mock_proton_data):
        """Test proton flux below threshold"""
        # Below threshold
        mock_fetch.return_value = [mock_proton_data[0]]

        alert, flux, time_tag = main.check_proton_flux()

        assert alert is False
        assert flux == 0.8
        assert time_tag == "2024-01-15T10:00:00Z"

    @patch("main.fetch_json")
    def test_check_solar_wind_alert(self, mock_fetch, mock_solar_wind_data):
        """Test high solar wind speed detection"""
        # Above threshold
        mock_fetch.return_value = [mock_solar_wind_data[2]]

        alert, speed, time_tag = main.check_solar_wind()

        assert alert is True
        assert speed == 725.3
        assert time_tag == "2024-01-15T12:00:00Z"

    @patch("main.fetch_json")
    def test_check_solar_wind_normal(self, mock_fetch, mock_solar_wind_data):
        """Test normal solar wind speed"""
        # Below threshold
        mock_fetch.return_value = [mock_solar_wind_data[0]]

        alert, speed, time_tag = main.check_solar_wind()

        assert alert is False
        assert speed == 350.5
        assert time_tag == "2024-01-15T10:00:00Z"

    @patch("main.fetch_json")
    def test_data_parsing_with_missing_fields(self, mock_fetch):
        """Test handling of malformed data"""
        # Missing flux field in flare data
        mock_fetch.return_value = [{"time_tag": "2024-01-15T12:00:00Z"}]

        with pytest.raises(KeyError):
            main.check_flare()

    @patch("main.fetch_json")
    def test_data_parsing_with_invalid_numeric_values(self, mock_fetch):
        """Test handling of invalid numeric values"""
        # Invalid flux value
        mock_fetch.return_value = [
            {"flux": "not_a_number", "time_tag": "2024-01-15T12:00:00Z"}
        ]

        with pytest.raises(ValueError):
            main.check_flare()


class TestThresholds:
    """Test threshold configurations"""

    def test_geostorm_thresholds_ordering(self):
        """Ensure geomagnetic storm thresholds are properly ordered"""
        thresholds = main.GEOSTORM_THRESHOLDS

        assert thresholds["Minor"] < thresholds["Moderate"]
        assert thresholds["Moderate"] < thresholds["Strong"]
        assert thresholds["Strong"] < thresholds["Severe"]
        assert thresholds["Severe"] < thresholds["Extreme"]

    def test_flare_thresholds_ordering(self):
        """Ensure flare thresholds are properly ordered"""
        assert main.FLARE_THRESHOLDS["M"] < main.FLARE_THRESHOLDS["X"]
        assert main.FLARE_THRESHOLDS["M"] == 1e-5
        assert main.FLARE_THRESHOLDS["X"] == 1e-4

    def test_threshold_constants(self):
        """Verify threshold constants match expected values"""
        assert main.PROTON_FLUX_THRESHOLD == 10
        assert main.SOLAR_WIND_SPEED_THRESHOLD == 600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
