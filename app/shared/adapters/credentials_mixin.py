from typing import Any

from pydantic import SecretStr

from app.shared.core.exceptions import ExternalAPIError


class CredentialsResolverMixin:
    """
    Mixin to resolve API keys and secrets from credentials objects,
    handling SecretStr and plain string types.
    """

    _credentials: Any

    def _resolve_api_key(self) -> str:
        token = getattr(self._credentials, "api_key", None)
        if token is None:
            raise ExternalAPIError("Missing API key for connector")
        if isinstance(token, SecretStr):
            resolved = token.get_secret_value()
        elif hasattr(token, "get_secret_value"):
            resolved = token.get_secret_value()
        elif isinstance(token, str):
            resolved = token
        else:
            raise ExternalAPIError("Missing API key for connector")
        if not resolved or not resolved.strip():
            raise ExternalAPIError("Missing API key for connector")
        return resolved.strip()

    def _resolve_api_secret(self) -> str:
        token = getattr(self._credentials, "api_secret", None)
        if token is None:
            raise ExternalAPIError("Missing API secret for connector")
        if isinstance(token, SecretStr):
            resolved = token.get_secret_value()
        elif hasattr(token, "get_secret_value"):
            resolved = token.get_secret_value()
        elif isinstance(token, str):
            resolved = token
        else:
            raise ExternalAPIError("Missing API secret for connector")
        if not resolved or not resolved.strip():
            raise ExternalAPIError("Missing API secret for connector")
        return resolved.strip()