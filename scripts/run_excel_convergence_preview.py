from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.database import get_session
from backend.services import excel_import


def _resolve_default_file_paths(repo_root: Path) -> list[tuple[str, Path]]:
    settings = get_settings()
    configured_paths = [
        ("gestion", settings.test_import_gestion_2024_path),
        ("gestion", settings.test_import_gestion_2025_path),
        ("comptabilite", settings.test_import_comptabilite_2024_path),
        ("comptabilite", settings.test_import_comptabilite_2025_path),
    ]
    resolved: list[tuple[str, Path]] = []
    resolved.extend(
        (import_type, Path(configured_path))
        for import_type, configured_path in configured_paths
        if configured_path
    )

    if resolved:
        return resolved

    data_dir = repo_root / "data"
    patterns = [
        ("gestion", "Gestion 2024.xlsx"),
        ("gestion", "Gestion 2025.xlsx"),
        ("comptabilite", "Comptabilit* 2024.xlsx"),
        ("comptabilite", "Comptabilit* 2025.xlsx"),
    ]
    for import_type, pattern in patterns:
        match = next(iter(sorted(data_dir.glob(pattern))), None)
        if match is not None:
            resolved.append((import_type, match))
    return resolved


def _summarize_preview(
    *,
    repo_root: Path,
    import_type: str,
    file_path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    comparison = payload.get("comparison") or {}
    warnings = list(payload.get("warnings", []))
    errors = list(payload.get("errors", []))
    return {
        "import_type": import_type,
        "file": file_path.relative_to(repo_root).as_posix(),
        "can_import": payload.get("can_import", False),
        "estimated": {
            "contacts": payload.get("estimated_contacts", 0),
            "invoices": payload.get("estimated_invoices", 0),
            "payments": payload.get("estimated_payments", 0),
            "salaries": payload.get("estimated_salaries", 0),
            "entries": payload.get("estimated_entries", 0),
        },
        "warnings": len(warnings),
        "warning_samples": warnings[:3],
        "errors": len(errors),
        "error_samples": errors[:3],
        "comparison": {
            "mode": comparison.get("mode"),
            "totals": comparison.get("totals"),
            "domains": comparison.get("domains", []),
        },
    }


async def _run(repo_root: Path) -> dict[str, Any]:
    previews: list[dict[str, Any]] = []
    async with get_session() as session:
        for import_type, file_path in _resolve_default_file_paths(repo_root):
            if not file_path.is_file():
                previews.append(
                    {
                        "import_type": import_type,
                        "file": str(file_path),
                        "missing": True,
                    }
                )
                continue

            content = file_path.read_bytes()
            if import_type == "gestion":
                preview = await excel_import.preview_gestion_file(session, content)
            else:
                preview = await excel_import.preview_comptabilite_file(session, content)
            previews.append(
                _summarize_preview(
                    repo_root=repo_root,
                    import_type=import_type,
                    file_path=file_path,
                    payload=preview.to_dict(),
                )
            )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "database_url": get_settings().database_url,
        "previews": previews,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run BL-008 convergence previews on the local historical Excel files.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root used to resolve data/ files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path where the JSON summary should be written.",
    )
    args = parser.parse_args()

    report = asyncio.run(_run(args.repo_root.resolve()))
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
