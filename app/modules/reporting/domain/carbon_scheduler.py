"""
Carbon-Aware Scheduling

Implements GreenOps automation by:
1. Scheduling non-urgent workloads during renewable energy peaks
2. Preferring low-carbon regions for flexible operations
3. Tracking and reporting carbon impact of scheduling decisions

Data Sources:
- WattTime API (real-time grid carbon intensity)
- Electricity Maps API (alternative)
- AWS Sustainability Pillar data

References:
- Green Software Foundation: Carbon Aware SDK
- AWS Well-Architected: Sustainability Pillar
"""

from datetime import datetime, timezone
import asyncio
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.shared.core.exceptions import ExternalAPIError
from app.shared.core.runtime_paths import get_data_path

logger = structlog.get_logger()
CARBON_FORECAST_RECOVERABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ImportError,
    ExternalAPIError,
    httpx.HTTPError,
    RuntimeError,
    TypeError,
    ValueError,
    KeyError,
)

CARBON_HTTP_RETRY_EXCEPTIONS: tuple[type[Exception], ...] = (
    httpx.TimeoutException,
    httpx.NetworkError,
    httpx.HTTPStatusError,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(CARBON_HTTP_RETRY_EXCEPTIONS),
    reraise=True,
)
async def _http_get_with_retry(client: httpx.AsyncClient, url: str, **kwargs: Any) -> httpx.Response:
    return await client.get(url, **kwargs)


class CarbonIntensity(str, Enum):
    """Carbon intensity levels."""

    VERY_LOW = "very_low"  # < 100 gCO2/kWh
    LOW = "low"  # 100-200 gCO2/kWh
    MEDIUM = "medium"  # 200-400 gCO2/kWh
    HIGH = "high"  # 400-600 gCO2/kWh
    VERY_HIGH = "very_high"  # > 600 gCO2/kWh


@dataclass
class RegionCarbonProfile:
    """Carbon profile for an AWS region."""

    region: str
    renewable_percentage: float
    carbon_intensity_low: float  # Typical low in gCO2/kWh
    carbon_intensity_high: float  # Typical high in gCO2/kWh
    best_hours_utc: List[int]  # Hours when carbon is typically lowest
    peak_solar_hour_utc: Optional[int] = None
    peak_wind_hour_utc: Optional[int] = None


class CarbonData:
    """Loads and holds static carbon profile data."""

    _instance: Optional["CarbonData"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self.REGION_CARBON_PROFILES: Dict[str, RegionCarbonProfile] = {}
        self.REGION_COORDS: Dict[str, tuple[float, float]] = {}
        self.LAST_UPDATED: datetime = datetime.min.replace(tzinfo=timezone.utc)
        self.MAX_AGE_DAYS: int = 30
        self._load_data()

    def _load_data(self) -> None:
        data_path = get_data_path() / "carbon_profiles.json"
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.LAST_UPDATED = datetime.fromisoformat(
                data.get("last_updated", datetime.min.isoformat())
            ).replace(tzinfo=timezone.utc)
            self.MAX_AGE_DAYS = data.get("max_age_days", 30)

            for region_name, profile_data in data.get("region_carbon_profiles", {}).items():
                self.REGION_CARBON_PROFILES[region_name] = RegionCarbonProfile(
                    region=profile_data["region"],
                    renewable_percentage=profile_data["renewable_percentage"],
                    carbon_intensity_low=profile_data["carbon_intensity_low"],
                    carbon_intensity_high=profile_data["carbon_intensity_high"],
                    best_hours_utc=profile_data["best_hours_utc"],
                    peak_solar_hour_utc=profile_data["peak_solar_hour_utc"],
                    peak_wind_hour_utc=profile_data["peak_wind_hour_utc"],
                )
            for region_name, coords in data.get("region_coordinates", {}).items():
                self.REGION_COORDS[region_name] = tuple(coords)

            logger.info("carbon_profiles_loaded", path=str(data_path))
        except Exception as e:
            logger.error("failed_to_load_carbon_profiles", path=str(data_path), error=str(e))
            # Fallback to empty data if loading fails
            self.REGION_CARBON_PROFILES = {}
            self.REGION_COORDS = {}

    @classmethod
    async def get_instance(cls) -> "CarbonData":
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance


WATTTIME_REGION_COORDS: Dict[str, tuple[float, float]] = {} # Will be populated from CarbonData

# Backwards compatibility for tests and other modules
_carbon_data_instance = CarbonData()
CarbonData._instance = _carbon_data_instance
REGION_CARBON_PROFILES = _carbon_data_instance.REGION_CARBON_PROFILES


def validate_carbon_data_freshness(*, strict: bool = True) -> bool:
    """
    BE-CARBON-1: Validate that carbon intensity data is fresh.
    Raises CarbonDataStaleError if data is outdated.
    Returns True if data is current.
    """
    carbon_data = _carbon_data_instance
    now = datetime.now(timezone.utc)
    age = (now - carbon_data.LAST_UPDATED).days

    if age > carbon_data.MAX_AGE_DAYS:
        error_msg = f"Carbon intensity data is {age} days old (max: {carbon_data.MAX_AGE_DAYS}). Update carbon_profiles.json."
        log_kwargs = {
            "last_updated": carbon_data.LAST_UPDATED.isoformat(),
            "age_days": age,
            "max_age_days": carbon_data.MAX_AGE_DAYS,
        }
        if strict:
            logger.error("carbon_data_stale", **log_kwargs)
            raise ValueError(error_msg)
        logger.warning(
            "carbon_data_stale",
            fallback_mode="static_profile_degraded_read",
            **log_kwargs,
        )
        return False

    return True


class CarbonAwareScheduler:
    """
    Schedules workloads based on carbon intensity.

    Usage:
        scheduler = CarbonAwareScheduler()

        # Find best time for backup job
        optimal_time = scheduler.get_optimal_execution_time(
            regions=["us-east-1", "eu-west-1"],
            workload_type="backup"
        )

        # Find lowest carbon region for new workload
        best_region = scheduler.get_lowest_carbon_region(
            candidate_regions=["us-east-1", "us-west-2", "eu-north-1"]
        )
    """

    def __init__(
        self,
        wattime_key: Optional[str] = None,
        electricitymaps_key: Optional[str] = None,
    ):
        self.wattime_key = wattime_key
        self.electricitymaps_key = electricitymaps_key
        self._use_static_data = not (wattime_key or electricitymaps_key)

    async def get_region_intensity(self, region: str) -> CarbonIntensity:
        intensity, _source = await self.get_region_intensity_with_source(region)
        return intensity
    
    async def get_region_intensity_with_source(
        self, region: str
    ) -> tuple[CarbonIntensity, str]:
        """Get current carbon intensity for a region."""
        carbon_data = await CarbonData.get_instance()
        profile = carbon_data.REGION_CARBON_PROFILES.get(region)
        if not profile:
            return CarbonIntensity.MEDIUM, "simulation"  # Unknown = medium

        # BE-CARBON-1: Ensure data is fresh
        validate_carbon_data_freshness(strict=False)

        if self.wattime_key:
            provider_intensity = await self._fetch_wattime_current_intensity(region)
            if provider_intensity is not None:
                return self._classify_intensity(provider_intensity), "api"

        if self.electricitymaps_key:
            provider_intensity = await self._fetch_emap_current_intensity(region)
            if provider_intensity is not None:
                return self._classify_intensity(provider_intensity), "api"

        now_hour = datetime.now(timezone.utc).hour
        intensity = self._simulate_intensity(profile, now_hour)
        return self._classify_intensity(intensity), "simulation"

    async def get_intensity_forecast_with_source(
        self, region: str, hours: int = 24
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Generates a carbon intensity forecast and returns the data provenance.
        """
        # BE-CARBON-1: Ensure data is fresh
        validate_carbon_data_freshness(strict=False)
        carbon_data = await CarbonData.get_instance()
        profile = carbon_data.REGION_CARBON_PROFILES.get(region)
        if not profile:
            return [], "simulation"

        if self.wattime_key:
            forecast = await self._fetch_wattime_forecast(region, hours)
            if forecast:
                return forecast, "api"

        if self.electricitymaps_key:
            forecast = await self._fetch_emap_forecast(region, hours)
            if forecast:
                return forecast, "api"

        return self._build_simulated_forecast(profile, hours), "simulation"

    def _classify_intensity(self, intensity: float) -> CarbonIntensity:
        if intensity < 100:
            return CarbonIntensity.VERY_LOW
        if intensity < 200:
            return CarbonIntensity.LOW
        if intensity < 400:
            return CarbonIntensity.MEDIUM
        if intensity < 600:
            return CarbonIntensity.HIGH
        return CarbonIntensity.VERY_HIGH

    def _simulate_intensity(self, profile: RegionCarbonProfile, hour_utc: int) -> float:
        """Simulates carbon intensity for a specific hour using a sine wave for solar/wind."""
        import math

        # Baseline is halfway between low and high
        base = (profile.carbon_intensity_low + profile.carbon_intensity_high) / 2
        amplitude = (profile.carbon_intensity_high - profile.carbon_intensity_low) / 2

        # Solar effect (lowest at peak solar hour)
        solar_factor = 0.0
        if profile.peak_solar_hour_utc is not None:
            # Lowest intensity at peak solar
            solar_factor = math.cos(
                math.pi * (hour_utc - profile.peak_solar_hour_utc) / 12
            )

        # Wind effect (simulated as another wave if applicable)
        wind_factor = 0.0
        if profile.peak_wind_hour_utc is not None:
            wind_factor = math.cos(
                math.pi * (hour_utc - profile.peak_wind_hour_utc) / 6
            )

        # Combined simulated intensity
        # We subtract the factors because higher renewable = lower carbon intensity
        adjustment = (solar_factor * 0.7 + wind_factor * 0.3) * amplitude
        return max(
            profile.carbon_intensity_low,
            min(profile.carbon_intensity_high, base - adjustment),
        )

    async def get_intensity_forecast(
        self, region: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Generates a carbon intensity forecast.
        Simulation: Provides Average Carbon Intensity (gCO2eq/kWh).
        Production-ready: Will call WattTime (MOER) or Electricity Maps (Average) if API keys are available.
        Fallback: High-fidelity diurnal simulation.
        """
        forecast, _source = await self.get_intensity_forecast_with_source(region, hours)
        return forecast

    def _build_simulated_forecast(
        self, profile: RegionCarbonProfile, hours: int
    ) -> List[Dict[str, Any]]:
        forecast = []
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        base_time = now.replace(minute=0, second=0, microsecond=0)

        for i in range(hours):
            target_time = base_time + timedelta(hours=i)
            target_hour = target_time.hour
            intensity = self._simulate_intensity(profile, target_hour)

            forecast.append(
                {
                    "hour_utc": target_hour,
                    "timestamp": target_time.isoformat(),
                    "intensity_gco2_kwh": round(intensity, 1),
                    "level": self._intensity_to_level(intensity),
                }
            )
        return forecast

    def _intensity_to_level(self, intensity: float) -> str:
        if intensity < 100:
            return "very_low"
        if intensity < 200:
            return "low"
        if intensity < 400:
            return "medium"
        if intensity < 600:
            return "high"
        return "very_high"

    def _get_avg_intensity(self, profile: RegionCarbonProfile) -> float:
        """Returns the average intensity for a profile."""

        return (profile.carbon_intensity_low + profile.carbon_intensity_high) / 2

    def _resolve_region_coordinates(self, region: str) -> tuple[float, float] | None:
        coords = _carbon_data_instance.REGION_COORDS.get(region)
        if coords is None:
            logger.warning("carbon_region_unmapped", region=region)
        return coords

    def get_lowest_carbon_region(self, candidate_regions: List[str]) -> str:
        """
        Find the lowest carbon region from candidates.

        Use for:
        - Disaster recovery failover decisions
        - New workload placement
        """
        if not candidate_regions:
            raise ValueError("No candidate regions provided")

        ranked = sorted(
            candidate_regions,
            key=lambda r: self._get_avg_intensity(
                REGION_CARBON_PROFILES.get(r, RegionCarbonProfile(r, 20, 400, 600, []))
            ),
        )

        best = ranked[0]
        logger.info(
            "lowest_carbon_region_selected", region=best, candidates=candidate_regions
        )

        return best

    async def get_optimal_execution_time(
        self, region: str, max_delay_hours: int = 24
    ) -> Optional[datetime]:
        """
        Find optimal time to execute workload for lowest carbon.

        Returns:
            Best datetime to execute (within delay window)
        """
        # Ensure profile is loaded from CarbonData instance
        # profile = REGION_CARBON_PROFILES.get(region) # Removed global static data
        carbon_data = await CarbonData.get_instance()
        profile = carbon_data.REGION_CARBON_PROFILES.get(region)
        if not profile or not profile.best_hours_utc:
            return None  # Execute now

        now = datetime.now(timezone.utc)

        # Find next best hour within window
        from datetime import timedelta

        # Start looking from current hour
        for hour_offset in range(max_delay_hours):
            target_time = now + timedelta(hours=hour_offset)
            candidate_hour = target_time.hour

            if candidate_hour in profile.best_hours_utc:
                # Normalize to the beginning of that hour
                optimal = target_time.replace(minute=0, second=0, microsecond=0)

                # Ensure we don't return a time in the past
                if optimal < now:
                    continue

                logger.info(
                    "carbon_optimal_time",
                    region=region,
                    optimal_hour=candidate_hour,
                    delay_hours=hour_offset,
                )
                return optimal

        return None  # No optimal time in window

    async def should_defer_workload(
        self, region: str, workload_type: str = "batch"
    ) -> bool:
        """
        Check if workload should be deferred to lower-carbon time.

        Workload types:
        - "critical": Never defer
        - "standard": Defer if high carbon
        - "batch": Always defer to optimal time if possible
        """
        if workload_type == "critical":
            return False

        intensity = await self.get_region_intensity(region)

        if workload_type == "batch":
            return intensity not in [CarbonIntensity.VERY_LOW, CarbonIntensity.LOW]

        # Standard: defer only if very high
        return intensity == CarbonIntensity.VERY_HIGH

    def estimate_carbon_savings(
        self, region_from: str, region_to: str, compute_hours: float
    ) -> Dict[str, float]:
        """
        Estimate carbon savings from region migration.

        Returns:
            Dict with gCO2 saved and percentage reduction

        """
        from_profile = _carbon_data_instance.REGION_CARBON_PROFILES.get(
            region_from, RegionCarbonProfile(region_from, 20, 400, 600, [])
        )
        to_profile = _carbon_data_instance.REGION_CARBON_PROFILES.get(
            region_to, RegionCarbonProfile(region_to, 20, 400, 600, [])
        )

        # Assuming 0.5 kWh per compute hour (rough estimate)
        kwh = compute_hours * 0.5

        from_carbon = self._get_avg_intensity(from_profile) * kwh
        to_carbon = self._get_avg_intensity(to_profile) * kwh
        saved = from_carbon - to_carbon

        return {
            "from_gco2": round(from_carbon, 2),
            "to_gco2": round(to_carbon, 2),
            "saved_gco2": round(saved, 2),
            "reduction_percent": round((saved / from_carbon) * 100, 1)
            if from_carbon > 0
            else 0,
        }

    async def _fetch_wattime_forecast(
        self, region: str, hours: int
    ) -> List[Dict[str, Any]]:
        """Fetch real-time MOER data from WattTime."""

        try:
            from app.shared.core.http import get_http_client


            client = get_http_client()
            # WattTime uses a login endpoint for a token, then GET /v2/forecast
            coords = self._resolve_region_coordinates(region)
            if not coords:
                return []

            payload = {
                "latitude": coords[0],
                "longitude": coords[1],
                "horizon": hours,
            }

            response = await _http_get_with_retry(
                client,
                "https://api2.watttime.org/v2/forecast",
                params=payload,
                headers={"Authorization": f"Bearer {self.wattime_key}"},
            )
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "timestamp": d["point_time"],
                    "intensity_gco2_kwh": d["value"],
                    "level": self._intensity_to_level(d["value"]),
                }
                for d in data.get("data", [])
            ]
        except CARBON_FORECAST_RECOVERABLE_EXCEPTIONS as e:
            logger.error("wattime_api_failed", error=str(e), region=region)
            return []

    async def _fetch_wattime_current_intensity(self, region: str) -> float | None:
        """
        Derive a current provider-backed reading from the first available WattTime forecast point.
        """
        forecast = await self._fetch_wattime_forecast(region, hours=1)
        if not forecast:
            return None
        first_point = forecast[0]
        raw_intensity = first_point.get("intensity_gco2_kwh")
        if not isinstance(raw_intensity, (int, float, str)):
            logger.warning(
                "wattime_current_intensity_invalid_payload",
                region=region,
                value=raw_intensity,
            )
            return None
        try:
            return float(raw_intensity)
        except (TypeError, ValueError):
            logger.warning(
                "wattime_current_intensity_invalid_payload",
                region=region,
                value=raw_intensity,
            )
            return None

    async def _fetch_emap_forecast(
        self, region: str, hours: int
    ) -> List[Dict[str, Any]]:
        """Fetch average intensity from Electricity Maps."""

        try:
            from app.shared.core.http import get_http_client


            client = get_http_client()
            coords = self._resolve_region_coordinates(region)
            if coords is None:
                return []

            headers = (
                {"auth-token": self.electricitymaps_key}
                if self.electricitymaps_key
                else {}
            )
            response = await _http_get_with_retry(
                client,
                "https://api.electricitymap.org/v3/carbon-intensity/forecast",
                params={"lat": coords[0], "lon": coords[1], "horizon": hours},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "timestamp": d["datetime"],
                    "intensity_gco2_kwh": d["carbonIntensity"],
                    "level": self._intensity_to_level(d["carbonIntensity"]),
                }
                for d in data.get("forecast", [])
            ]
        except CARBON_FORECAST_RECOVERABLE_EXCEPTIONS as e:
            logger.error("emap_api_failed", error=str(e), region=region)
            return []

    async def _fetch_emap_current_intensity(self, region: str) -> float | None:
        """Fetch the latest Electricity Maps carbon intensity using geolocation lookup."""
        try:
            from app.shared.core.http import get_http_client


            client = get_http_client()
            coords = self._resolve_region_coordinates(region)
            if coords is None:
                return None

            headers = (
                {"auth-token": self.electricitymaps_key}
                if self.electricitymaps_key
                else {}
            )
            response = await _http_get_with_retry(
                client,
                "https://api.electricitymap.org/v3/carbon-intensity/latest",
                params={"lat": coords[0], "lon": coords[1]},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            raw_intensity = data.get("carbonIntensity")
            if raw_intensity is None:
                logger.warning("emap_latest_missing_intensity", region=region)
                return None
            if not isinstance(raw_intensity, (int, float, str)):
                logger.warning(
                    "emap_latest_invalid_intensity_type",
                    region=region,
                    value_type=type(raw_intensity).__name__,
                )
                return None
            return float(raw_intensity)
        except CARBON_FORECAST_RECOVERABLE_EXCEPTIONS as e:
            logger.error("emap_current_intensity_failed", error=str(e), region=region)
            return None
