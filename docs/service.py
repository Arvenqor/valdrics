from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger()


class DemoDataService:
    """
    Provides mock data for unauthenticated or demo users.
    This allows users to explore Valdrics features without connecting a real cloud account.
    """

    def __init__(self) -> None:
        self._tenant_id = UUID("00000000-0000-0000-0000-000000000000")  # A fixed UUID for demo

    def get_demo_tenant_id(self) -> UUID:
        return self._tenant_id

    async def get_demo_cost_and_usage(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Generates mock cost and usage data."""
        mock_data = []
        current_date = start_date
        while current_date <= end_date:
            # Simulate some daily spend
            daily_cost = Decimal(str(100 + (current_date.day % 10) * 5 + (current_date.month % 3) * 10))
            mock_data.append(
                {
                    "recorded_at": current_date.isoformat(),
                    "provider": "aws",
                    "account_id": uuid4(),
                    "account_name": "Demo AWS Account",
                    "service": "AmazonEC2",
                    "region": "us-east-1",
                    "usage_type": "Compute",
                    "resource_id": f"i-{current_date.day:02d}{current_date.month:02d}",
                    "cost_usd": float(daily_cost),
                    "carbon_kg": float(daily_cost * Decimal("0.05")),
                    "cost_status": "FINAL",
                }
            )
            # Add a second service for variety
            mock_data.append(
                {
                    "recorded_at": current_date.isoformat(),
                    "provider": "aws",
                    "account_id": uuid4(),
                    "account_name": "Demo AWS Account",
                    "service": "AmazonS3",
                    "region": "us-east-1",
                    "usage_type": "Storage",
                    "resource_id": f"bucket-{current_date.day:02d}{current_date.month:02d}",
                    "cost_usd": float(daily_cost / Decimal("5")),
                    "carbon_kg": float(daily_cost / Decimal("5") * Decimal("0.01")),
                    "cost_status": "FINAL",
                }
            )
            current_date += timedelta(days=1)
        logger.info("generated_demo_cost_data", num_records=len(mock_data))
        return mock_data

    async def get_demo_carbon_report(self) -> Dict[str, Any]:
        """Generates mock carbon report data."""
        return {
            "total_co2_kg": 42.7,
            "equivalent_miles_driven": 105,
            "trees_needed_offset": 1.9,
            "carbon_efficiency": 89,
            "region_recommendations": [
                {"region": "us-west-2", "reduction_percent": 94},
                {"region": "eu-north-1", "reduction_percent": 80},
            ],
        }

    async def get_demo_zombie_resources(self) -> List[Dict[str, Any]]:
        """Generates mock zombie resource data."""
        return [
            {
                "resource_id": "i-0abcdef1234567890",
                "resource_type": "ec2_instance",
                "provider": "aws",
                "region": "us-east-1",
                "estimated_monthly_cost_usd": 50.0,
                "reason": "Idle EC2 instance (CPU < 5% for 30 days)",
                "recommendation": "Terminate instance or resize to t3.nano",
            },
            {
                "resource_id": "vol-0fedcba9876543210",
                "resource_type": "ebs_volume",
                "provider": "aws",
                "region": "us-east-1",
                "estimated_monthly_cost_usd": 5.0,
                "reason": "Orphaned EBS volume (not attached for 60 days)",
                "recommendation": "Delete volume",
            },
        ]