# ECA Reference Implementation 2.0.0

**Clean-room replacement release · ECA/ETC profile 0.3-proposed · 18 November 2026**

This is a bounded reference implementation of the proposed ECA Cross-Layer Traceability Contract. It is not a byte-for-byte reconstruction of the previously reported ECA Reference Implementation 1.0.1 and makes no equivalence claim with unavailable historical source, tests, or raw outputs.

ECA is a lifecycle integration and assurance-mapping profile over native records. It does not issue permission, replace a policy decision point, create a new authorization credential, or independently establish institutional legitimacy, truth, safety, or legality.

## Release scope

- Draft 2020-12 JSON Schema for ETC profile 0.3-proposed.
- Canonical request serialization profile eca-canonical-json-v1 and SHA-256 digest binding.
- Structural and semantic validation of relation vocabulary, node endpoints, temporal status, freshness, and risk-scoped obligations.
- PRE, POST and ACCOUNTABILITY trace-closure reports, plus separate CONCURRENT runtime-guard obligations.
- ACTION_READY evaluation using external native-authorization and effect-boundary assessments.
- HMAC delegation and target-receipt helpers for local demonstration only.
- Single-host SQLite journal and idempotent target simulator for bounded lifecycle experiments.
- TLA+ lifecycle model and TLC configuration, successfully parsed by official SANY and checked by TLC in GitHub Actions run #2.

## Quick start

Requirements: Python 3.11 or newer.

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -e ".[test]"

Validate the synthetic contract:

    eca-validate examples/municipal-composite-contract.example.json --phase PRE

Run the local CI-equivalent pipeline:

    bash scripts/run_local_ci.sh

Verify tracked source checksums:

    sha256sum -c SHA256SUMS.txt

## Hosted verification

GitHub Actions run #2 completed successfully on commit b9c760d280993c760091af5f1ed705038e8cf80d:
https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960

All six jobs passed:
- Python 3.11: 102 tests passed, 82% combined coverage.
- Python 3.12: 102 tests passed, 82% combined coverage.
- Python 3.13: 102 tests passed, 82% combined coverage.
- Python 3.14: 102 tests passed, 82% combined coverage.
- Python 3.15: 102 tests passed, 82% combined coverage.
- TLA+ SANY and TLC: official JAR checksum passed; SANY 2.1 parsed ECA_Lifecycle; TLC 2.19 completed with no error found.

Total: 510 successful test executions (102 in each interpreter). Each Python job passed the 80% coverage threshold.

TLA+ artifact:
https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960/artifacts/14469505467

TLC recorded 34,086 generated states, 33,668 distinct states, zero remaining queue, and graph depth 9. Ten safety invariants were configured. CHECK_DEADLOCK FALSE is set; this run does not establish deadlock freedom, liveness, fairness, or Python-to-TLA refinement.

## Security and assurance limits

This is a bounded research reference, not a production authorization service.

1. The canonicalization profile is intentionally narrow and is not RFC 8785/JCS.
2. HMAC helpers are demonstrations, not a production key-management architecture.
3. SQLite runtime is single-host; no distributed atomicity, global linearizable revocation, or exactly-once physical effects are claimed.
4. Native authorization, enforcement, dispatch-attestation, and receipt authenticity remain responsibilities of their owning trust domains.
5. A signed or immutable record can still contain a false statement.
6. The example is synthetic and fictional, not a deployment or field observation.
7. The TLA+ model is bounded. Deadlock checking is disabled; no liveness, fairness, or Python-to-TLA refinement proof is claimed.
8. No independent security audit, field trial, controlled evaluation, or production-readiness assessment is claimed.

## Version lineage

- Python reference implementation: 2.0.0, clean-room replacement.
- ETC schema/profile: 0.3-proposed, separate from package version.
- TLA+ lifecycle model: revision 1, not the unavailable historical revision-v4 artifact.
- Historical 1.x test totals and verification statements are not carried forward as verified results.

## License

No open-source license is granted. The repository was confirmed Public on 18 November 2026; public visibility does not grant reuse or redistribution rights. See LICENSE_STATUS.md.
