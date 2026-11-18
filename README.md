# ECA Reference Implementation 2.0.0

**Clean-room replacement release · ECA/ETC profile 0.3-proposed · 18 November 2026**

This repository is a new, bounded reference implementation of the proposed **ECA Cross-Layer Traceability Contract (ETC)**. It is not a continuation or byte-for-byte reconstruction of the author-reported ECA Reference Implementation 1.0.1. It does not claim equivalence with unavailable historical source code, tests, or raw results.

ECA is treated here as a **lifecycle integration and assurance-mapping profile** over native records. It does not issue permission, replace a policy decision point (PDP), create a new authorization credential, or independently establish institutional legitimacy, truth, safety, or legality.

## Release scope

The release contains:

- A Draft 2020-12 JSON Schema for ETC profile `0.3-proposed`.
- Strict request canonicalization profile `eca-canonical-json-v1` and SHA-256 request digests.
- Structural and semantic validation of relation vocabulary, node endpoints, temporal status, freshness, and risk-scoped phase obligations.
- PRE, POST, and ACCOUNTABILITY trace-closure reports, plus separate CONCURRENT runtime-guard obligations.
- An `ACTION_READY` evaluator that consumes external native-authorization and effect-boundary assessments.
- A delegation-chain attenuation demonstrator using HMAC **for local testing only**.
- A single-host SQLite journal and idempotent SQLite target simulator for bounded lifecycle experiments.
- An abstract TLA+ lifecycle model and a configuration file, pending official SANY/TLC execution.
- Synthetic examples, automated tests, scripts, and raw run reports.

## Quick start

Requirements: Python 3.11 or newer. The local 102-test run used Python 3.13.5, `jsonschema` 4.26.0, `pytest` 9.0.2, `coverage` 7.13.3, SQLite 3.46.1, and OpenJDK 21.0.12. The fresh-install test extra in `pyproject.toml` targets pytest 9.2.0 and coverage.py 7.16.1, which were the current upstream releases checked on 18 November 2026; those newer versions were not executable in the offline authoring environment. See [`reports/TOOLCHAIN_CURRENCY.md`](reports/TOOLCHAIN_CURRENCY.md).

For a fresh install using the current declared test-tool pins:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

To reproduce the exact local authoring dependency snapshot used for the recorded results instead:

```bash
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
```

Validate the synthetic contract:

```bash
eca-validate examples/municipal-composite-contract.example.json --phase PRE
```

Run the full local CI-equivalent pipeline (compile, tests, coverage, schema/example checks, wheel build and isolated CLI smoke test, workflow syntax, static TLA checks, and exhaustive finite-state alternative):

```bash
bash scripts/run_local_ci.sh
```

Individual test and package commands remain available:

```bash
bash scripts/run_tests.sh
bash scripts/check_package.sh
```

## Core evaluation semantics

- `VERIFIED` means verified relative to the named verifier and trust profile; it is not a claim of universal truth.
- `NOT_APPLICABLE` requires an explicit, approved, time-bounded exception and cannot discharge a critical relation.
- `MISSING` is a diagnostic result, not a relation status.
- PRE closure, action readiness, POST closure, and accountability closure are distinct predicates. CONCURRENT obligations are separate runtime guards checked against declared active guard references at reservation and immediately before dispatch, then discharged with evidence for POST closure.
- The Relation Readiness/Coverage ratio (RRC) is diagnostic only. It never substitutes for a required hard gate.
- `ACTION_READY` requires a closed PRE trace, discharged PRE obligations, registered CONCURRENT obligations bound to active runtime guards, a fresh native PDP `PERMIT` bound to the exact request, required approvals, and a fresh active effect-boundary assessment. The risk profile declares `native_authorization_max_age_seconds` and `enforcement_assessment_max_age_seconds`; future or stale assessments fail readiness.
- An uncertain target outcome remains `UNKNOWN`. Reconciliation requires target-linked evidence; the runtime does not blindly redispatch an uncertain operation.

The complete semantics are in [`docs/ETC_PROFILE_SPECIFICATION.md`](docs/ETC_PROFILE_SPECIFICATION.md). Canonicalization test vectors are in [`vectors/canonicalization-v1.json`](vectors/canonicalization-v1.json).

## Important security and assurance limits

This is a **bounded research reference**, not a production authorization service.

1. The canonicalization profile is intentionally narrow and is **not** RFC 8785/JCS. Cross-language consumers must implement the exact profile and pass shared test vectors before interoperating.
2. HMAC delegation and target-receipt helpers are test/demo mechanisms. They do not define an organizational key hierarchy, multi-party trust distribution, HSM integration, or production cryptographic policy.
3. The runtime and journals are single-host SQLite demonstrations. They do not provide a distributed transaction, globally linearizable revocation, multi-host fencing, or exactly-once physical effects.
4. A dispatch assessment and native authorization assessment are inputs from their owning trust domains. This library checks their declared fields and bindings; it does not replace the native cryptographic or institutional verifier.
5. `VERIFIED` relation status remains verifier-relative. A signed or immutable record can still contain a false statement.
6. The example is synthetic and fictional. It is not a deployment, case study, interview, or field observation.
7. Official SANY parsing and TLC model checking have **not** been run because the pinned official `tla2tools.jar` could not be obtained in this offline authoring environment. An independent Python finite-state checker exhaustively explored the mirrored transition system (16,384 initial valuations, 33,668 reachable states, 17,702 transitions, ten safety invariants); this is a bounded alternative check, **not** a TLA+ parser, TLC run, or refinement proof. See [`reports/ALTERNATIVE_MODEL_CHECK_REPORT.md`](reports/ALTERNATIVE_MODEL_CHECK_REPORT.md) and [`reports/TLA_EXECUTION_STATUS.md`](reports/TLA_EXECUTION_STATUS.md).
8. No independent security audit, field trial, controlled comparative evaluation, or production-readiness assessment is claimed.

See [`reports/TOOLCHAIN_CURRENCY.md`](reports/TOOLCHAIN_CURRENCY.md) for the dated toolchain review and unrun compatibility gates. Also see [`docs/THREAT_MODEL_AND_LIMITATIONS.md`](docs/THREAT_MODEL_AND_LIMITATIONS.md), [`docs/MANUSCRIPT_ALIGNMENT.md`](docs/MANUSCRIPT_ALIGNMENT.md), and [`reports/REPRODUCIBILITY_STATUS.md`](reports/REPRODUCIBILITY_STATUS.md).

## Version lineage

- Historical manuscript descriptions refer to author-reported implementation/test artifacts from an earlier 1.x line. The source tree and raw outputs required for independent reproduction were not present in the materials inspected for this clean-room replacement.
- This repository starts a separate `2.0.0` implementation lineage.
- The ETC vocabulary remains labeled `0.3-proposed`; implementation release version and profile version are distinct.
- TLA+ model lineage begins at `revision 1`. It does not claim to be the unavailable or unaudited historical `revision v4` source.
- The GitHub Actions workflow is configured for Python 3.11–3.15 and official SANY/TLC. A local CI-equivalent run passed on Python 3.13.5; the hosted workflow and full interpreter matrix have not yet run. See [`reports/CI_EXECUTION_REPORT.md`](reports/CI_EXECUTION_REPORT.md).

## Repository map

```text
src/eca_reference/       Python reference implementation
src/eca_reference/schemas/  ETC JSON Schema
examples/                Synthetic sample contract
vectors/                 Canonicalization interoperability vectors
 tests/                   Automated test suite
 docs/                    Normative profile and assurance notes
 tla/                     TLA+ module and TLC configuration
 docs/TLA_MODEL_GUIDE.md  TLA+ model scope, transitions and invariant rationale
 scripts/                 Reproducibility and audit scripts
.github/workflows/       CI matrix and official TLA+ verification job
 reports/                 Machine-generated and status reports
 tools/                   Optional locally supplied TLA+ tools (not bundled)
```

## License and public distribution

No open-source license is granted in this release. See [`LICENSE_STATUS.md`](LICENSE_STATUS.md). Keep the package private until the author selects the license, an independent reviewer examines the core semantics, and the outstanding TLA+ verification gate is completed.

## Citation

See [`CITATION.cff`](CITATION.cff). No DOI is asserted or fabricated.
