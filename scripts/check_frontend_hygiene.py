#!/usr/bin/env python3
"""Frontend hygiene checks for production safety and consistency.

Checks:
- The legacy `dashboard/` app root must not contain deployable frontend source.
- `PUBLIC_API_URL` usage is restricted to approved proxy/config files.
- Every `<button>` explicitly declares `type=...`.
- Every `target="_blank"` anchor includes `rel="noopener noreferrer"`.
- `{@html ...}` usage requires DOMPurify sanitization in the same file.
- `frontend/svelte.config.js` must not allow CSP `unsafe-inline`.
- `frontend/src/app.html` must not use manual inline style attributes.
- `frontend/src/app.html` must not include manual inline `<script>` or `<style>` blocks.
- `frontend/src/app.html` must not load Google-hosted fonts or stylesheet fonts.
- Svelte transition directives are disallowed because they require inline `<style>` tags under strict CSP.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from scripts.env_generation_common import (
    repo_root_for as _repo_root_for,
    resolve_cli_path_from_root,
)


ALLOWED_PUBLIC_API_URL_FILES = {
    Path("frontend/src/lib/edgeProxy.ts"),
    Path("frontend/src/lib/server/backend-origin.ts"),
    Path("frontend/src/routes/api/edge/[...path]/+server.ts"),
    Path("frontend/src/lib/components/IdentitySettingsCard.svelte"),
    Path("frontend/src/lib/components/IdentitySettingsCardContent.svelte"),
}

SOURCE_EXTENSIONS = {".svelte", ".ts"}
TEST_SUFFIXES = (".test.ts", ".spec.ts", ".test.setup.ts")

TARGET_BLANK_ANCHOR_PATTERN = re.compile(
    r"<a\b[^>]*\btarget\s*=\s*([\"'])_blank\1[^>]*>", flags=re.IGNORECASE | re.DOTALL
)
BUTTON_WITHOUT_TYPE_PATTERN = re.compile(
    r"<button(?![^>]*\btype\s*=)[^>]*>", flags=re.IGNORECASE | re.DOTALL
)
HTML_INJECTION_PATTERN = re.compile(r"\{@html\b")
STYLE_BLOCK_PATTERN = re.compile(r"<style\b[^>]*>.*?</style>", flags=re.IGNORECASE | re.DOTALL)
SVELTE_TRANSITION_DIRECTIVE_PATTERN = re.compile(
    r"<[^>]*\b(?:transition:|in:|out:|animate:)[^>]*>",
    flags=re.IGNORECASE | re.DOTALL,
)
INLINE_STYLE_ATTRIBUTE_PATTERN = re.compile(r"\bstyle\s*=", flags=re.IGNORECASE)
INLINE_SCRIPT_BLOCK_PATTERN = re.compile(r"<script\b[^>]*>.*?</script>", flags=re.IGNORECASE | re.DOTALL)
INLINE_STYLE_BLOCK_PATTERN = re.compile(r"<style\b[^>]*>.*?</style>", flags=re.IGNORECASE | re.DOTALL)
GOOGLE_FONT_HOST_PATTERN = re.compile(r"https://fonts\.(?:googleapis|gstatic)\.com", flags=re.IGNORECASE)
STYLESHEET_FONT_HOST_PATTERN = re.compile(
    r"<link\b[^>]*\brel\s*=\s*([\"'])stylesheet\1[^>]*\bhref\s*=\s*([\"'])https?://",
    flags=re.IGNORECASE | re.DOTALL,
)
UNSAFE_INLINE_PATTERN = re.compile(r"['\"]unsafe-inline['\"]")

LEGACY_DASHBOARD_DEPLOYABLE_PATHS = (
    Path("package.json"),
    Path("pnpm-lock.yaml"),
    Path("svelte.config.js"),
    Path("vite.config.ts"),
    Path("playwright.config.ts"),
    Path("server.node.mjs"),
    Path("wrangler.toml"),
    Path("src"),
    Path("static"),
    Path("e2e"),
    Path("tests"),
)


@dataclass(frozen=True)
class Issue:
    file_path: Path
    message: str
    snippet: str


def _repo_root() -> Path:
    return _repo_root_for(__file__)


def _resolve_repo_root(path: Path) -> Path:
    return resolve_cli_path_from_root(_repo_root(), path, field_name="repo_root")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _iter_source_files(repo_root: Path) -> list[Path]:
    src_root = repo_root / "frontend" / "src"
    files: list[Path] = []
    for path in src_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in SOURCE_EXTENSIONS:
            continue
        if path.name.endswith(TEST_SUFFIXES):
            continue
        files.append(path)
    return files


def _has_rel_noopener_noreferrer(anchor_tag: str) -> bool:
    rel_match = re.search(r"\brel\s*=\s*([\"'])(.*?)\1", anchor_tag, flags=re.IGNORECASE | re.DOTALL)
    if not rel_match:
        return False
    rel_tokens = {token.strip().lower() for token in rel_match.group(2).split() if token.strip()}
    return "noopener" in rel_tokens and "noreferrer" in rel_tokens


def _strip_style_blocks(source: str) -> str:
    return STYLE_BLOCK_PATTERN.sub("", source)


def _allows_safe_json_ld_html_injection(source: str) -> bool:
    # Svelte head JSON-LD needs raw script markup injection; require explicit
    # JSON serialization plus script-breakout escaping before allowing it.
    required_fragments = (
        '{@html',
        'type="application/ld+json"',
        "JSON.stringify(",
        "replaceAll('<', '\\\\u003c')",
        "replaceAll('</script', '<\\\\/script')",
    )
    return all(fragment in source for fragment in required_fragments)


def _find_legacy_dashboard_sources(repo_root: Path) -> list[Path]:
    dashboard_root = repo_root / "dashboard"
    if not dashboard_root.exists():
        return []

    matches: list[Path] = []
    for relative_path in LEGACY_DASHBOARD_DEPLOYABLE_PATHS:
        path = dashboard_root / relative_path
        if path.exists():
            matches.append(path.relative_to(repo_root))
    return sorted(matches)


def run(repo_root: Path) -> int:
    issues: list[Issue] = []
    svelte_config = repo_root / "frontend" / "svelte.config.js"
    app_html = repo_root / "frontend" / "src" / "app.html"

    for legacy_source in _find_legacy_dashboard_sources(repo_root):
        issues.append(
            Issue(
                file_path=legacy_source,
                message=(
                    "legacy dashboard deployable source is not allowed; "
                    "migrate production frontend code to frontend/."
                ),
                snippet=legacy_source.as_posix(),
            )
        )

    if svelte_config.exists():
        config_source = _read_text(svelte_config)
        if UNSAFE_INLINE_PATTERN.search(config_source):
            issues.append(
                Issue(
                    file_path=svelte_config.relative_to(repo_root),
                    message="frontend CSP must not allow unsafe-inline.",
                    snippet="unsafe-inline",
                )
            )

    if app_html.exists():
        app_html_source = _read_text(app_html)
        if INLINE_STYLE_ATTRIBUTE_PATTERN.search(app_html_source):
            issues.append(
                Issue(
                    file_path=app_html.relative_to(repo_root),
                    message="frontend app.html must not include manual inline styles.",
                    snippet='style="..."',
                )
            )
        if INLINE_SCRIPT_BLOCK_PATTERN.search(app_html_source):
            issues.append(
                Issue(
                    file_path=app_html.relative_to(repo_root),
                    message=(
                        "frontend app.html must not include manual inline script blocks; "
                        "use SvelteKit-managed scripts and CSP nonces instead."
                    ),
                    snippet="<script>...</script>",
                )
            )
        if INLINE_STYLE_BLOCK_PATTERN.search(app_html_source):
            issues.append(
                Issue(
                    file_path=app_html.relative_to(repo_root),
                    message=(
                        "frontend app.html must not include manual inline style blocks; "
                        "keep critical styling in versioned CSS assets."
                    ),
                    snippet="<style>...</style>",
                )
            )
        if GOOGLE_FONT_HOST_PATTERN.search(app_html_source):
            issues.append(
                Issue(
                    file_path=app_html.relative_to(repo_root),
                    message=(
                        "frontend app.html must not load Google-hosted fonts; "
                        "use self-hosted fonts/assets that fit the production CSP."
                    ),
                    snippet="fonts.googleapis.com / fonts.gstatic.com",
                )
            )
        if STYLESHEET_FONT_HOST_PATTERN.search(app_html_source):
            issues.append(
                Issue(
                    file_path=app_html.relative_to(repo_root),
                    message=(
                        "frontend app.html must not load external stylesheet font resources; "
                        "ship fonts as controlled first-party assets."
                    ),
                    snippet='<link rel="stylesheet" href="https://...">',
                )
            )

    for source_file in _iter_source_files(repo_root):
        rel_path = source_file.relative_to(repo_root)
        source = _read_text(source_file)
        source_without_style_blocks = _strip_style_blocks(source)

        if "PUBLIC_API_URL" in source and rel_path not in ALLOWED_PUBLIC_API_URL_FILES:
            issues.append(
                Issue(
                    file_path=rel_path,
                    message="PUBLIC_API_URL is only allowed in edge proxy/config files.",
                    snippet="PUBLIC_API_URL",
                )
            )

        for anchor_match in TARGET_BLANK_ANCHOR_PATTERN.finditer(source):
            anchor_tag = anchor_match.group(0).replace("\n", " ")
            if not _has_rel_noopener_noreferrer(anchor_tag):
                issues.append(
                    Issue(
                        file_path=rel_path,
                        message='target="_blank" anchor must include rel="noopener noreferrer".',
                        snippet=anchor_tag,
                    )
                )

        for button_match in BUTTON_WITHOUT_TYPE_PATTERN.finditer(source):
            button_tag = button_match.group(0).replace("\n", " ")
            issues.append(
                Issue(
                    file_path=rel_path,
                    message="<button> must declare an explicit type attribute.",
                    snippet=button_tag,
                )
            )

        if HTML_INJECTION_PATTERN.search(source) and not (
            "DOMPurify.sanitize(" in source or _allows_safe_json_ld_html_injection(source)
        ):
            issues.append(
                Issue(
                    file_path=rel_path,
                    message="`{@html ...}` requires DOMPurify.sanitize(...) in the same file.",
                    snippet="{@html ...}",
                )
            )

        if source_file.suffix == ".svelte":
            for directive_match in SVELTE_TRANSITION_DIRECTIVE_PATTERN.finditer(
                source_without_style_blocks
            ):
                directive = directive_match.group(0).replace("\n", " ")
                issues.append(
                    Issue(
                        file_path=rel_path,
                        message=(
                            "Svelte transition directives are disallowed under strict CSP; "
                            "use CSS animations instead."
                        ),
                        snippet=directive,
                    )
                )

    if issues:
        print(f"[frontend-hygiene] FAIL: {len(issues)} issue(s) found")
        for issue in issues:
            print(f"  - {issue.file_path}: {issue.message} :: {issue.snippet}")
        return 1

    print("[frontend-hygiene] OK: no hygiene violations found")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=str(_repo_root()),
        help="Repository root path",
    )
    args = parser.parse_args(argv)
    try:
        return run(_resolve_repo_root(Path(str(args.repo_root))))
    except ValueError as exc:
        print(f"[frontend-hygiene] failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
