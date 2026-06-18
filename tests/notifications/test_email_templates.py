"""Tests for B7 email template service."""

from __future__ import annotations

from pathlib import Path

from app.modules.notifications.domain.email_templates import TemplateService


def _make_service(tmp_path: Path) -> TemplateService:
    (tmp_path / "base_notification.txt").write_text("Fallback: ${msg}")
    (tmp_path / "welcome.txt").write_text("Hello ${name}")
    (tmp_path / "welcome.html").write_text("<h1>Hello ${name}</h1>")
    return TemplateService(template_dir=tmp_path)


def test_render_substitutes_template(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    result = service.render("welcome", {"name": "World"})
    assert result == "Hello World"


def test_render_html_variant(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    result = service.render_html("welcome", {"name": "World"})
    assert result == "<h1>Hello World</h1>"


def test_render_missing_template_falls_back(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    result = service.render("missing", {"msg": "ok"})
    assert result == "Fallback: ok"


def test_list_templates_returns_names(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    templates = service.list_templates()
    assert "welcome" in templates
    assert "base_notification" in templates
