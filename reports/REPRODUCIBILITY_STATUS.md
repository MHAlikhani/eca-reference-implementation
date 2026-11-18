# Reproducibility and verification status

**Release:** ECA Reference Implementation 2.0.0  
**ETC profile:** 0.3-proposed  
**TLA+ lineage:** revision 1  
**Hosted verification:** GitHub Actions run #2, 18 November 2026  
**Designation:** bounded research reference; official CI/TLA+ passed; not production-certified

## 1. Clean-room lineage

This is a clean-room implementation. It is not a byte-for-byte reconstruction of ECA Reference Implementation 1.0.1. Historical source, historical tests/raw outputs, and historical TLA+ revision-v4 files were unavailable for independent reproduction. No equivalence claim is made.

## 2. Hosted CI

Run #2 passed all six jobs on commit b9c760d280993c760091af5f1ed705038e8cf80d:
- Python 3.11, 3.12, 3.13, 3.14 and 3.15: 102/102 tests each; 82% combined coverage; wheel built.
- TLA+ SANY and TLC: checksum, parse and model-check passed.

Total: 510 successful test executions. Each Python job passed the 80% coverage threshold. The workflow used pytest 9.2.0, coverage.py 7.16.1 and jsonschema 4.26.0.

## 3. Official TLA+ result

SANY 2.1 parsed and semantically processed tla/ECA_Lifecycle.tla. TLC 2.19 reported:

| Metric | Result |
|---|---:|
| Initial states | 16,384 |
| Generated | 34,086 |
| Distinct | 33,668 |
| Remaining | 0 |
| Depth | 9 |
| Safety invariants configured | 10 |
| Result | No error found |

The official TLA+ Tools 1.7.4 checksum passed. Artifact:
https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960/artifacts/14469505467

Limits: CHECK_DEADLOCK FALSE; no deadlock-freedom, liveness, fairness, production safety, cryptographic correctness, or Python-to-TLA refinement claim.

## 4. Alternative model check

The independent Python mirror remains supplementary: 16,384 initial valuations, 33,668 reachable states, 17,702 transitions, ten invariants. It is not SANY/TLC.

## 5. Remaining limits

No independent security audit, field deployment, controlled comparative evaluation, proof of legal/institutional legitimacy, distributed atomicity, globally linearizable revocation, exactly-once physical effect, or production certification is claimed. HMAC helpers are demonstrations and SQLite runtime is single-host. No open-source license is granted; repository visibility is Public.

## 6. Reproduction

    python -m pip install -e ".[test]"
    bash scripts/run_local_ci.sh
    bash scripts/run_tla.sh
    sha256sum -c SHA256SUMS.txt

The hosted workflow downloads the pinned official TLA+ JAR and executes SANY/TLC automatically.
