"""
Typed Credential Classes
Standardizes cloud provider credentials into O(1) Pydantic models.
This decouples adapters from SQLAlchemy models and ensures strict type safety.
"""

from typing import Any

from pydantic import BaseModel, Field, SecretStr


class CloudCredentials(BaseModel):
    """Base class for all cloud credentials - intentionally empty for type safety."""


class AWSCredentials(CloudCredentials):
    """AWS STS AssumeRole Credentials."""

    account_id: str = Field(..., min_length=12, max_length=12)
    role_arn: str
    external_id: str
    region: str = "us-east-1"
    tenant_id: Any | None = None

    @property
    def aws_account_id(self) -> str:
        return self.account_id

    cur_bucket_name: str | None = None
    cur_report_name: str | None = None
    cur_prefix: str | None = None


class AzureCredentials(CloudCredentials):
    """Azure Service Principal Credentials."""

    tenant_id: str
    client_id: str
    subscription_id: str
    client_secret: SecretStr | None = None
    auth_method: str = "secret"


class GCPCredentials(CloudCredentials):
    """GCP Service Account or Workload Identity."""

    project_id: str
    service_account_json: SecretStr | None = None
    auth_method: str = "secret"

    billing_project_id: str | None = None
    billing_dataset: str | None = None
    billing_table: str | None = None


class SaaSCredentials(CloudCredentials):
    """Generic SaaS API Credentials."""

    platform: str
    api_key: SecretStr | None = None
    auth_method: str = "manual"
    connector_config: dict[str, Any] = Field(default_factory=dict)
    spend_feed: list[dict[str, Any]] = Field(default_factory=list)
    base_url: str | None = None
    extra_config: dict[str, Any] = Field(default_factory=dict)


class LicenseCredentials(CloudCredentials):
    """ITAM/License vendor credentials."""

    vendor: str
    auth_method: str = "manual"
    api_key: SecretStr | None = None
    connector_config: dict[str, Any] = Field(default_factory=dict)
    license_feed: list[dict[str, Any]] = Field(default_factory=list)


class PlatformCredentials(CloudCredentials):
    """Internal Platform/Shared Services credentials."""

    vendor: str
    auth_method: str = "manual"
    api_key: SecretStr | None = None
    api_secret: SecretStr | None = None
    connector_config: dict[str, Any] = Field(default_factory=dict)
    spend_feed: list[dict[str, Any]] = Field(default_factory=list)


class HybridCredentials(CloudCredentials):
    """Hybrid/Private cloud credentials."""

    vendor: str
    auth_method: str = "manual"
    api_key: SecretStr | None = None
    api_secret: SecretStr | None = None
    connector_config: dict[str, Any] = Field(default_factory=dict)
    spend_feed: list[dict[str, Any]] = Field(default_factory=list)
