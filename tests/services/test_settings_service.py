from zprompt_helper.secrets.secret_store import InMemorySecretStore
from zprompt_helper.services.settings_service import SettingsService
from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.storage.settings_store import SettingsStore


def test_settings_service_persists_api_key_outside_settings_json(tmp_path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    settings_store = SettingsStore(paths)
    secret_store = InMemorySecretStore()
    service = SettingsService(settings_store, secret_store)

    service.save(
        model="openrouter/auto",
        temperature=0.4,
        top_p=0.8,
        max_tokens=900,
        api_key="sk-demo",
        base_url="https://api.example.test/v1",
    )

    raw_json = (tmp_path / "data" / "settings.json").read_text(encoding="utf-8")
    assert "sk-demo" not in raw_json
    assert "https://api.example.test/v1" in raw_json
    assert service.load().api_key == "sk-demo"
    assert service.load().base_url == "https://api.example.test/v1"


def test_settings_service_loads_defaults_when_settings_file_is_absent(tmp_path) -> None:
    service = SettingsService(
        SettingsStore(ProjectPaths.from_root(tmp_path)),
        InMemorySecretStore(api_key="sk-existing"),
    )

    settings = service.load()

    assert settings.model == ""
    assert settings.temperature == 0.2
    assert settings.top_p == 0.9
    assert settings.max_tokens == 700
    assert settings.api_key == "sk-existing"
    assert settings.base_url == "https://openrouter.ai/api/v1"
    assert settings.theme_mode == "light"


def test_settings_service_blank_api_key_does_not_overwrite_existing_secret(tmp_path) -> None:
    secret_store = InMemorySecretStore(api_key="sk-existing")
    service = SettingsService(SettingsStore(ProjectPaths.from_root(tmp_path)), secret_store)

    service.save(
        model="openrouter/auto",
        temperature=0.3,
        top_p=0.7,
        max_tokens=800,
        api_key="",
        base_url="https://api.example.test/v1",
    )

    assert service.load().api_key == "sk-existing"


def test_settings_service_persists_theme_mode_in_settings_json(tmp_path) -> None:
    service = SettingsService(
        SettingsStore(ProjectPaths.from_root(tmp_path)),
        InMemorySecretStore(),
    )

    service.save(
        model="openrouter/auto",
        temperature=0.3,
        top_p=0.7,
        max_tokens=800,
        api_key="",
        theme_mode="dark",
        base_url="https://api.example.test/v1",
    )

    assert service.load().theme_mode == "dark"
    assert service.load().base_url == "https://api.example.test/v1"


def test_save_theme_mode_preserves_custom_base_url(tmp_path) -> None:
    service = SettingsService(
        SettingsStore(ProjectPaths.from_root(tmp_path)),
        InMemorySecretStore(),
    )
    service.save(
        model="alpha-model",
        temperature=0.3,
        top_p=0.7,
        max_tokens=800,
        api_key="",
        base_url="https://api.example.test/v1",
    )

    service.save_theme_mode("dark")

    settings = service.load()
    assert settings.theme_mode == "dark"
    assert settings.base_url == "https://api.example.test/v1"
