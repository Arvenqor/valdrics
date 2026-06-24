from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
import time
import aioboto3
import structlog
from app.modules.optimization.domain.ports import BaseZombieDetector
from app.modules.optimization.domain.plugin import ZombiePlugin
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.optimization.domain.registry import registry

# Import plugins to trigger registration
import app.modules.optimization.adapters.aws.plugins  # noqa

logger = structlog.get_logger()


class AWSZombieDetector(BaseZombieDetector):
    """
    Concrete implementation of ZombieDetector for AWS.
    Manages aioboto3 session and AWS-specific plugin execution with
    application-level circuit breaking for connection-level failures.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        credentials: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
        connection: Any = None,
    ) -> None:
        super().__init__(region, credentials, db, connection)
        self.session = aioboto3.Session()
        self._adapter = None
        if connection:
            from app.shared.adapters.aws_multitenant import MultiTenantAWSAdapter

            self._adapter = MultiTenantAWSAdapter(connection)

        self._initialize_plugins()
        self._circuit_failures: int = 0
        self._circuit_opened_at: float | None = None

    @property
    def provider_name(self) -> str:
        return "aws"

    def _initialize_plugins(self) -> None:
        """Register every available AWS detection plugin from the registry."""
        self.plugins = registry.get_plugins_for_provider("aws")

    def _circuit_should_skip(self) -> bool:
        from app.shared.core.config import get_settings

        threshold = int(
            getattr(
                get_settings(),
                "ZOMBIE_SCAN_FAILURE_CIRCUIT_THRESHOLD",
                3,
            )
        )
        if self._circuit_failures < threshold:
            return False
        if self._circuit_opened_at is None:
            self._circuit_opened_at = time.monotonic()
            logger.warning(
                "aws_detector_circuit_opened",
                connection_id=str(getattr(self.connection, "id", "unknown")),
                region=self.region,
                failure_count=self._circuit_failures,
            )
        return True

    def _circuit_record_success(self) -> None:
        self._circuit_failures = 0
        self._circuit_opened_at = None

    def _circuit_record_failure(self) -> None:
        self._circuit_failures += 1
        from app.shared.core.config import get_settings

        threshold = int(
            getattr(
                get_settings(),
                "ZOMBIE_SCAN_FAILURE_CIRCUIT_THRESHOLD",
                3,
            )
        )
        if self._circuit_failures >= threshold:
            logger.warning(
                "aws_detector_circuit_failure_threshold_reached",
                connection_id=str(getattr(self.connection, "id", "unknown")),
                region=self.region,
                failure_count=self._circuit_failures,
                threshold=threshold,
            )

    @staticmethod
    def _inventory_scan_metadata(inventory: Any) -> dict[str, Any]:
        method = str(getattr(inventory, "discovery_method", "") or "").strip()
        degraded_methods = {
            "native-api-fallback-partial",
            "native-api-fallback-degraded",
        }
        status = "ok"
        if method == "native-api-fallback-partial":
            status = "partial"
        elif method == "native-api-fallback-degraded":
            status = "degraded"
        return {
            "status": status,
            "method": method or "unknown",
            "resource_count": int(getattr(inventory, "total_count", 0) or 0),
            "coverage_limitations": (
                "Inventory was derived from native fallback discovery and may not "
                "cover the full AWS account resource surface."
                if method in degraded_methods
                else None
            ),
        }

    @classmethod
    def _apply_inventory_completeness(
        cls, results: Dict[str, Any], inventory: Any | None
    ) -> Dict[str, Any]:
        if inventory is None:
            return results

        metadata = cls._inventory_scan_metadata(inventory)
        completeness = results.get("scan_completeness")
        if not isinstance(completeness, dict):
            return results

        completeness["inventory_discovery"] = metadata
        if metadata["status"] == "ok":
            return results

        completeness["degraded"] = True
        completeness["error_count"] = int(completeness.get("error_count", 0) or 0) + 1
        results["partial_results"] = True
        results["inventory_discovery"] = metadata
        return results

    async def scan_all(
        self, on_category_complete: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Overrides the base scan_all to include global discovery via Resource Explorer 2.
        Includes application-level circuit breaking for repeated connection failures.
        """
        if self._circuit_should_skip():
            logger.warning(
                "aws_detector_scan_skipped_circuit_open",
                connection_id=str(getattr(self.connection, "id", "unknown")),
                region=self.region,
                failure_count=self._circuit_failures,
            )
            return {
                "provider": self.provider_name,
                "region": self.region,
                "scanned_at": datetime.now(timezone.utc).isoformat(),
                "total_monthly_waste": Decimal("0"),
                "scan_completeness": {
                    "provider": self.provider_name,
                    "region": self.region,
                    "degraded": True,
                    "error_count": 1,
                    "plugins": {},
                    "overall_error": "circuit_open",
                },
                "partial_results": True,
            }

        from app.modules.optimization.domain.unified_discovery import (
            UnifiedDiscoveryService,
        )

        inventory = None
        if self.connection:
            discovery_service = UnifiedDiscoveryService(str(self.connection.tenant_id))
            inventory = await discovery_service.discover_aws_inventory(self.connection)
            logger.info(
                "aws_detector_global_inventory_loaded",
                count=inventory.total_count,
                method=inventory.discovery_method,
            )

        self._inventory = inventory

        try:
            results = await super().scan_all(on_category_complete=on_category_complete)
            self._circuit_record_success()
            return self._apply_inventory_completeness(results, inventory)
        except Exception:
            self._circuit_record_failure()
            raise

    async def _execute_plugin_scan(self, plugin: ZombiePlugin) -> List[Dict[str, Any]]:
        """
        Execute AWS plugin scan, passing the aioboto3 session and standard config.
        Injects the discovered inventory if available.
        """
        from botocore.config import Config
        from app.shared.core.config import get_settings

        settings = get_settings()
        boto_config = Config(
            connect_timeout=settings.ZOMBIE_PLUGIN_TIMEOUT_SECONDS,
            read_timeout=settings.ZOMBIE_PLUGIN_TIMEOUT_SECONDS,
            retries={"max_attempts": 2},
        )

        creds = self.credentials
        if self._adapter:
            creds = await self._adapter.get_credentials()

        return await plugin.scan(
            session=self.session,
            region=self.region,
            credentials=creds,
            config=boto_config,
            inventory=getattr(self, "_inventory", None),  # Inject inventory
        )
