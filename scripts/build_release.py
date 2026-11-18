#!/usr/bin/env python3
"""Create a deterministic integrity manifest and source/reproducibility ZIP."""
from __future__ import annotations
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / f"{ROOT.name}.zip"
ZIP_DATE = (2026, 11, 18, 0, 0, 0)
EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", ".venv", "build", "dist",
                  ".mypy_cache", ".ruff_cache", ".tox", "htmlcov"}
EXCLUDED_NAMES = {".coverage", "RELEASE_MANIFEST.json", "SHA256SUMS.txt"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def included_files() -> list[Path]:
    result=[]
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel=path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in rel.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix==".pyc":
            continue
        result.append(path)
    return sorted(result,key=lambda p:p.relative_to(ROOT).as_posix())

def main() -> None:
    paths=included_files()
    records=[{"path":p.relative_to(ROOT).as_posix(),"size_bytes":p.stat().st_size,"sha256":sha256(p)} for p in paths]
    manifest={
      "release":{"name":"ECA Reference Implementation","version":"2.0.0",
        "designation":"official CI and bounded TLA+ checks passed; not production-certified",
        "etc_profile":"0.3-proposed","tla_model_lineage":"revision 1",
        "assessed_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")},
      "verification_summary":{
        "github_actions":{"status":"passed","workflow":"ECA verification","run_id":44391171960,
          "commit":"b9c760d280993c760091af5f1ed705038e8cf80d",
          "python_versions":["3.11","3.12","3.13","3.14","3.15"],"tests_per_version":102,
          "total_test_executions":510,"combined_coverage_percent":82,"coverage_threshold_percent":80},
        "sany":{"status":"passed","version":"2.1","job_id":135108908582},
        "tlc":{"status":"passed","version":"2.19","job_id":135108908582,"initial_states":16384,
          "states_generated":34086,"distinct_states":33668,"states_remaining_in_queue":0,
          "state_graph_depth":9,"configured_safety_invariants":10,"deadlock_check_enabled":False,
          "result":"No error has been found"},
        "tla_tools":{"version":"1.7.4","jar_sha1":"bee4a54f3ee3d4afc347c3240ec2d9e93b075104",
          "artifact_id":14469505467},
        "alternative_finite_state_checker":{"status":"passed_mirrored_transition_system_only",
          "initial_valuations":16384,"reachable_states":33668,"transitions":17702,
          "safety_invariants":10,"transition_operators_cross_checked":13,"not_equivalent_to_sany_or_tlc":True},
        "external_security_audit":"not_performed","field_validation":"not_performed",
        "implementation_refinement_proof":"not_provided","production_certification":"not_claimed"},
      "files":records,
      "manifest_note":"This manifest excludes itself and SHA256SUMS.txt from its files array. Generated build/ and dist/ are excluded."
    }
    manifest_path=ROOT/"RELEASE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    sums=[f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}" for p in paths]
    sums.append(f"{sha256(manifest_path)}  RELEASE_MANIFEST.json")
    (ROOT/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")
    archive= included_files()+[manifest_path,ROOT/"SHA256SUMS.txt"]
    with zipfile.ZipFile(OUT,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
      for p in sorted(archive,key=lambda x:x.relative_to(ROOT).as_posix()):
        rel=p.relative_to(ROOT).as_posix()
        info=zipfile.ZipInfo(f"{ROOT.name}/{rel}",date_time=ZIP_DATE)
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o100644&0xFFFF)<<16
        info.create_system=3
        z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    digest=sha256(OUT)
    OUT.with_suffix(OUT.suffix+".sha256").write_text(f"{digest}  {OUT.name}\n",encoding="ascii")
    print(f"Created: {OUT}")
    print(f"SHA-256: {digest}")
    print(f"Files archived: {len(archive)}")

if __name__=="__main__":
    main()
