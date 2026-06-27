from pydantic import Field


class ReportingSettings:
    RECON_ALERT_THRESHOLD_PCT: float = Field(
        default=1.0,
        description="Reconciliation delta percent that triggers an alert. 1.0 = 1%.",
    )
    INVOICE_RECONCILIATION_DEFAULT_THRESHOLD_PCT: float = Field(
        default=1.0,
        description="Default allowed drift between ledger and invoice before flagging.",
    )
    RECON_CONFIDENCE_VOLUME_DENOMINATOR: float = Field(
        default=1000.0,
        description="Denominator used to cap confidence weighting by record volume.",
    )
    BATCH_PROCESSING_CHUNK_SIZE: int = Field(
        default=1000,
        description="Chunk size for batch database operations such as bulk deletes "
        "and inserts in attribution and ledger pipelines.",
    )
    CLOSE_PACKAGE_HMAC_SECRET: str = Field(
        default="",
        description="HMAC-SHA256 secret used to sign close-package evidence bundles. "
        "Must be >= 32 chars in production.",
    )
