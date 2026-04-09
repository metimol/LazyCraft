import pytest
from unittest.mock import patch, mock_open
from const import JsonManager


def test_json_manager_success():
    fake_json = '{"TEST_KEY": "Test Value"}'

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=fake_json)):
            manager = JsonManager("fake.json")
            assert manager.get_value("TEST_KEY") == "Test Value"


def test_json_manager_missing_key():
    fake_json = '{"TEST_KEY": "Test Value"}'

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=fake_json)):
            manager = JsonManager("fake.json")
            with pytest.raises(ValueError):
                manager.get_value("MISSING_KEY")


def test_json_manager_file_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        manager = JsonManager("nonexistent.json")
        with pytest.raises(ValueError):
            manager.get_value("ANY_KEY")
