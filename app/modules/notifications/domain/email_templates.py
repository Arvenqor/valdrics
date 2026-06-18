"""Reusable email template service.

Provides safe rendering of .txt and .html templates with stdlib
string.Template substitution. Used by B7 email template modernization.
"""

from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Dict

import structlog

logger = structlog.get_logger()

DEFAULT_TEMPLATE_DIR = Path("app/assets/email_templates")
DEFAULT_FALLBACK = "base_notification"


class TemplateService:
    """Template renderer for notification and billing emails."""

    def __init__(self, template_dir: Path | None = None) -> None:
        self.template_dir = template_dir or DEFAULT_TEMPLATE_DIR
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> list[str]:
        """Return available template base names without extension."""
        names: set[str] = set()
        if not self.template_dir.exists():
            return sorted(names)
        for path in self.template_dir.iterdir():
            if path.is_file():
                stem = path.name.split(".", 1)[0]
                names.add(stem)
        return sorted(names)

    def render(self, name: str, context: Dict[str, str]) -> str:
        """Render a .txt template with safe substitution."""
        return self._render_variant(name, context, ext="txt")

    def render_html(self, name: str, context: Dict[str, str]) -> str:
        """Render an .html template with safe substitution."""
        return self._render_variant(name, context, ext="html")

    def _render_variant(self, name: str, context: Dict[str, str], ext: str) -> str:
        path = self.template_dir / f"{name}.{ext}"
        if not path.exists():
            fallback_name = DEFAULT_FALLBACK
            fallback_path = self.template_dir / f"{fallback_name}.{ext}"
            if fallback_path.exists():
                path = fallback_path
            else:
                raise FileNotFoundError(
                    f"Template not found and no fallback available: {name}.{ext}"
                )
        text = path.read_text(encoding="utf-8")
        template = Template(text)
        try:
            return template.safe_substitute(context)
        except Exception as exc:
            logger.error(
                "email_template_render_failed",
                template=str(path),
                error=str(exc),
            )
            raise RuntimeError(f"Template render failed: {path}") from exc
