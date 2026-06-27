import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4
from types import SimpleNamespace

from app.shared.adapters.azure import AzureAdapter
from app.models.azure_connection import AzureConnection
from app.shared.core.exceptions import AdapterError


def _connection():
    return AzureConnection(
        tenant_id=uuid4(),
        name="Test",
        azure_tenant_id="tenant",
        client_id="client",
        subscription_id="sub",
        client_secret="secret",
    )


@pytest.mark.asyncio
async def test_verify_connection_success():
    adapter = AzureAdapter(_connection())
    adapter.last_error = "stale"
    mock_client = MagicMock()

    async def list_groups():
        if False:
            yield None
        return

    mock_client.resource_groups.list = list_groups

    with patch.object(
        adapter, "_get_resource_client", AsyncMock(return_value=mock_client)
    ):
        assert await adapter.verify_connection() is True
    assert adapter.last_error is None


@pytest.mark.asyncio
async def test_verify_connection_failure():
    adapter = AzureAdapter(_connection())
    with patch.object(
        adapter, "_get_resource_client", AsyncMock(side_effect=RuntimeError("boom"))
    ):
        assert await adapter.verify_connection() is False
    assert adapter.last_error is not None
    assert "Azure credential verification failed" in adapter.last_error


def test_parse_row_invalid_date_raises():
    adapter = AzureAdapter(_connection())
    row = [1.0, "Compute", "eastus", "Usage", "bad-date"]

    with pytest.raises(ValueError, match="Azure usage date must be a valid datetime string"):
        adapter._parse_row(row, "ActualCost")


def test_parse_row_rejects_non_finite_amount():
    adapter = AzureAdapter(_connection())

    with pytest.raises(ValueError, match="Azure cost row amount must be finite"):
        adapter._parse_row([float("nan"), "Compute", "eastus", "Usage", "20240101"], "ActualCost")


@pytest.mark.asyncio
async def test_get_cost_and_usage_success():
    adapter = AzureAdapter(_connection())
    row = [2.5, "Compute", "eastus", "Usage", "20240101"]
    mock_client = MagicMock()
    mock_client.query.usage = AsyncMock(return_value=SimpleNamespace(rows=[row]))

    with patch.object(adapter, "_get_cost_client", AsyncMock(return_value=mock_client)):
        results = await adapter.get_cost_and_usage(
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 2, tzinfo=timezone.utc),
        )

    assert len(results) == 1
    assert results[0]["service"] == "Compute"


@pytest.mark.asyncio
async def test_get_cost_and_usage_error_raises_adapter_error():
    adapter = AzureAdapter(_connection())
    mock_client = MagicMock()
    mock_client.query.usage = AsyncMock(side_effect=RuntimeError("query failed"))

    with patch.object(adapter, "_get_cost_client", AsyncMock(return_value=mock_client)):
        with pytest.raises(AdapterError):
            await adapter.get_cost_and_usage(
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            )


@pytest.mark.asyncio
async def test_get_cost_and_usage_invalid_row_date_bubbles():
    adapter = AzureAdapter(_connection())
    row = [2.5, "Compute", "eastus", "Usage", "bad-date"]
    mock_client = MagicMock()
    mock_client.query.usage = AsyncMock(return_value=SimpleNamespace(rows=[row]))

    with patch.object(adapter, "_get_cost_client", AsyncMock(return_value=mock_client)):
        with pytest.raises(ValueError, match="Azure usage date must be a valid datetime string"):
            await adapter.get_cost_and_usage(
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            )


@pytest.mark.asyncio
async def test_discover_resources_filters_by_type_and_region():
    adapter = AzureAdapter(_connection())
    mock_client = MagicMock()

    res1 = SimpleNamespace(
        id="1",
        name="vm-1",
        location="eastus",
        tags={"env": "prod"},
        hardware_profile=SimpleNamespace(vm_size="Standard_B2s"),
    )
    res2 = SimpleNamespace(
        id="2",
        name="vm-2",
        location="westus",
        tags=None,
        hardware_profile=SimpleNamespace(vm_size="Standard_B1s"),
    )

    async def list_vms():
        yield res1
        yield res2

    mock_client.virtual_machines.list_all = list_vms

    with patch.object(
        adapter, "_get_compute_client", AsyncMock(return_value=mock_client)
    ):
        results = await adapter.discover_resources(
            resource_type="compute", region="eastus"
        )

    assert len(results) == 1
    assert results[0]["name"] == "vm-1"


@pytest.mark.asyncio
async def test_discover_resources_exception_returns_empty():
    adapter = AzureAdapter(_connection())
    adapter.last_error = "stale"
    with patch.object(
        adapter, "_get_compute_client", AsyncMock(side_effect=RuntimeError("boom"))
    ):
        results = await adapter.discover_resources(resource_type="compute")
    assert results == []
    assert adapter.last_error is not None
    assert "Azure resource discovery failed" in adapter.last_error


@pytest.mark.asyncio
async def test_discover_resources_broken_contract_bubbles():
    adapter = AzureAdapter(_connection())
    mock_client = MagicMock()
    broken_vm = SimpleNamespace(
        id="1",
        name="vm-1",
        location=None,
        tags={},
        hardware_profile=SimpleNamespace(vm_size="Standard_B2s"),
    )

    async def list_vms():
        yield broken_vm

    mock_client.virtual_machines.list_all = list_vms

    with patch.object(
        adapter, "_get_compute_client", AsyncMock(return_value=mock_client)
    ):
        with pytest.raises(AttributeError):
            await adapter.discover_resources(resource_type="compute", region="eastus")


@pytest.mark.asyncio
async def test_discover_resources_clears_last_error_on_success():
    adapter = AzureAdapter(_connection())
    adapter.last_error = "stale"

    resource_client = MagicMock()
    res = SimpleNamespace(
        id="res-1",
        name="res-1",
        type="Microsoft.Storage/storageAccounts",
        location="eastus",
        tags={"env": "prod"},
    )

    async def list_resources():
        yield res

    resource_client.resources.list = list_resources

    with patch.object(
        adapter, "_get_resource_client", AsyncMock(return_value=resource_client)
    ):
        results = await adapter.discover_resources(resource_type="storage")

    assert len(results) == 1
    assert adapter.last_error is None


@pytest.mark.asyncio
async def test_get_resource_usage_clears_last_error_on_success():
    adapter = AzureAdapter(_connection())
    adapter.last_error = "stale"
    with patch.object(
        adapter,
        "get_cost_and_usage",
        AsyncMock(
            return_value=[
                {
                    "timestamp": datetime(2026, 1, 10, tzinfo=timezone.utc),
                    "service": "Virtual Machines",
                    "resource_id": "vm-1",
                    "usage_type": "compute_hour",
                    "usage_amount": 2,
                    "cost_usd": 4.2,
                    "currency": "USD",
                    "region": "eastus",
                }
            ]
        ),
    ):
        usage = await adapter.get_resource_usage("virtual machines")

    assert len(usage) == 1
    assert adapter.last_error is None


@pytest.mark.asyncio
async def test_get_resource_usage_invalid_cost_row_bubbles():
    adapter = AzureAdapter(_connection())
    with patch.object(
        adapter,
        "get_cost_and_usage",
        AsyncMock(side_effect=ValueError("Azure usage date must be a valid datetime string")),
    ):
        with pytest.raises(ValueError, match="Azure usage date must be a valid datetime string"):
            await adapter.get_resource_usage("virtual machines")


@pytest.mark.asyncio
async def test_stream_cost_and_usage():
    """Test the stream_cost_and_usage async generator yields all records."""
    adapter = AzureAdapter(_connection())
    mock_records = [{"cost_usd": 5.0, "service": "Virtual Machines"}]
    with patch.object(adapter, "get_cost_and_usage", AsyncMock(return_value=mock_records)):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 2, tzinfo=timezone.utc)

        results = []
        async for r in adapter.stream_cost_and_usage(start, end):
            results.append(r)

        assert len(results) == 1
        assert results[0]["cost_usd"] == 5.0


def test_parse_row_multiple_date_formats():
    """Test that _parse_row handles all Azure date format variants."""
    adapter = AzureAdapter(_connection())
    formats = ["20260101", "2026-01-01", "2026-01-01T00:00:00Z"]
    for fmt in formats:
        row = [10.0, "Svc", "Loc", "Type", fmt]
        parsed = adapter._parse_row(row, "ActualCost")
        assert parsed["timestamp"].year == 2026
        assert parsed["timestamp"].month == 1
        assert parsed["timestamp"].day == 1

