"""Configuration loading tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_prefixed_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EASY_FASTAPI_APP_NAME", "configured-app")

    settings = Settings(_env_file=None)

    assert settings.app_name == "configured-app"


def test_settings_reject_invalid_port() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, port=70_000)
