from core.settings_manager import DEFAULT_SETTINGS, SettingsManager


def test_set_then_get_round_trip(tmp_path):
    settings_path = tmp_path / "settings.json"
    manager = SettingsManager(settings_path)

    manager.set("volume", 42)

    reloaded = SettingsManager(settings_path)
    assert reloaded.get("volume") == 42


def test_missing_file_returns_defaults(tmp_path):
    settings_path = tmp_path / "does_not_exist.json"

    manager = SettingsManager(settings_path)

    assert manager.get("volume") == DEFAULT_SETTINGS["volume"]


def test_corrupted_file_returns_defaults_without_crash(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{not valid json", encoding="utf-8")

    manager = SettingsManager(settings_path)

    assert manager.get("volume") == DEFAULT_SETTINGS["volume"]


def test_get_unknown_key_returns_provided_default(tmp_path):
    manager = SettingsManager(tmp_path / "settings.json")

    assert manager.get("unknown_key", "fallback") == "fallback"
