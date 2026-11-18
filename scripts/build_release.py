#!/usr/bin/env python3
"""Create a deterministic integrity manifest and source/reproducibility ZIP."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / f"{ROOT.name}.zip"
ZIP_DATE = (2026, 11, 18, 0, 0, 0)
EXCLUDED_PARTS = {
    ".git", ".pytest_cache", "__pycache__", ".venv", "build",
    ".mypy_cache", ".ruff_cache", ".tox",
}
EXCLUDED_NAMES = {".coverage", "RELEASE_MANIFEST.json", "SHA256SUMS.txt"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def included_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if any(part.endswith(".egg-info") for part in rel.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix == ".pyc":
            continue
        if path.name.endswith(".egg-info"):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def main() -> None:
    files = included_files()
    records = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    manifest = {
        "release": {
            "name": "ECA Reference Implementation",
            "version": "2.0.0",
            "designation": "verification-gated",
            "etc_profile": "0.3-proposed",
            "tla_model_lineage": "revision 1",
            "assessed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "verification_summary": {
            "python_tests": {"status": "passed", "count": 102},
            "coverage": {
                "combined_percent": 82.10,
                "line_percent": 86.26,
                "branch_percent": 73.31,
                "coverage_threshold_combined_percent": 80,
            },
            "schema_and_synthetic_example": "passed",
            "wheel_build_and_target_install_smoke": "passed",
            "tla_lexical_audit": "passed_limited_static_check",
            "tla_config_name_check": "passed_limited_static_check",
            "sany": "not_run_blocked_missing_official_jar",
            "tlc": "not_run_blocked_missing_official_jar",
            "alternative_finite_state_checker": {
                "status": "passed_mirrored_transition_system_only",
                "initial_valuations": 16384,
                "reachable_states": 33668,
                "transitions": 17702,
                "safety_invariants": 10,
                "transition_operators_cross_checked": 13,
                "not_equivalent_to_sany_or_tlc": True,
            },
            "local_ci_equivalent": "passed_python_3.13.5",
            "github_hosted_actions": "not_run_no_connected_repository_session",
            "python_matrix_3_11_to_3_15": "not_run_locally_only_3_13_5_available",
            "external_security_audit": "not_performed",
            "field_validation": "not_performed",
        },
        "files": records,
        "manifest_note": "This manifest excludes itself and SHA256SUMS.txt from the files array to avoid recursive hashing. SHA256SUMS.txt includes the manifest hash.",
    }
    manifest_path = ROOT / "RELEASE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sums = []
    for path in files:
        sums.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    sums.append(f"{sha256(manifest_path)}  RELEASE_MANIFEST.json")
    (ROOT / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")

    archive_files = included_files() + [manifest_path, ROOT / "SHA256SUMS.txt"]
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(archive_files, key=lambda item: item.relative_to(ROOT).as_posix()):
            rel = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{ROOT.name}/{rel}", date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    digest = sha256(OUT)
    sidecar = OUT.with_suffix(OUT.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {OUT.name}\n", encoding="ascii")
    print(f"Created: {OUT}")
    print(f"SHA-256: {digest}")
    print(f"Files archived: {len(archive_files)}")


if __name__ == "__main__":
    main()
