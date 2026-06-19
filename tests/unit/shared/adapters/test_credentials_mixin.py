from typing import Any
import pytest
from pydantic import SecretStr

from app.shared.adapters.credentials_mixin import CredentialsResolverMixin
from app.shared.core.exceptions import ExternalAPIError


class DummyCredentials:
    def __init__(self, api_key: Any = None, api_secret: Any = None):
        if api_key is not None:
            self.api_key = api_key
        if api_secret is not None:
            self.api_secret = api_secret


class SecretLike:
    def __init__(self, val: str):
        self.val = val

    def get_secret_value(self) -> str:
        return self.val


class DummyAdapter(CredentialsResolverMixin):
    def __init__(self, credentials: Any):
        self._credentials = credentials


def test_resolve_api_key_plain_string() -> None:
    adapter = DummyAdapter(DummyCredentials(api_key="my-plain-key"))
    assert adapter._resolve_api_key() == "my-plain-key"


def test_resolve_api_key_secret_str() -> None:
    adapter = DummyAdapter(DummyCredentials(api_key=SecretStr("my-secret-key")))
    assert adapter._resolve_api_key() == "my-secret-key"


def test_resolve_api_key_custom_secret() -> None:
    adapter = DummyAdapter(DummyCredentials(api_key=SecretLike("my-custom-key")))
    assert adapter._resolve_api_key() == "my-custom-key"


def test_resolve_api_key_missing() -> None:
    adapter = DummyAdapter(DummyCredentials(api_key=None))
    with pytest.raises(ExternalAPIError) as exc_info:
        adapter._resolve_api_key()
    assert "Missing API token" in str(exc_info.value)


def test_resolve_api_key_empty() -> None:
    adapter = DummyAdapter(DummyCredentials(api_key="   "))
    with pytest.raises(ExternalAPIError) as exc_info:
        adapter._resolve_api_key()
    assert "Missing API token" in str(exc_info.value)


def test_resolve_api_key_invalid_type() -> None:
    adapter = DummyAdapter(DummyCredentials(api_key=12345))
    with pytest.raises(ExternalAPIError) as exc_info:
        adapter._resolve_api_key()
    assert "Missing API token" in str(exc_info.value)


def test_resolve_api_secret_plain_string() -> None:
    adapter = DummyAdapter(DummyCredentials(api_secret="my-plain-secret"))
    assert adapter._resolve_api_secret() == "my-plain-secret"


def test_resolve_api_secret_secret_str() -> None:
    adapter = DummyAdapter(DummyCredentials(api_secret=SecretStr("my-secret-secret")))
    assert adapter._resolve_api_secret() == "my-secret-secret"


def test_resolve_api_secret_custom_secret() -> None:
    adapter = DummyAdapter(DummyCredentials(api_secret=SecretLike("my-custom-secret")))
    assert adapter._resolve_api_secret() == "my-custom-secret"


def test_resolve_api_secret_missing() -> None:
    adapter = DummyAdapter(DummyCredentials(api_secret=None))
    with pytest.raises(ExternalAPIError) as exc_info:
        adapter._resolve_api_secret()
    assert "Missing API secret for connector" in str(exc_info.value)


def test_resolve_api_secret_empty() -> None:
    adapter = DummyAdapter(DummyCredentials(api_secret="   "))
    with pytest.raises(ExternalAPIError) as exc_info:
        adapter._resolve_api_secret()
    assert "Missing API secret for connector" in str(exc_info.value)


def test_resolve_api_secret_invalid_type() -> None:
    adapter = DummyAdapter(DummyCredentials(api_secret=12345))
    with pytest.raises(ExternalAPIError) as exc_info:
        adapter._resolve_api_secret()
    assert "Missing API secret for connector" in str(exc_info.value)
