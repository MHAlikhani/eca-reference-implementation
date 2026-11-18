# Reproducibility and verification status

**Release line:** ECA Reference Implementation 2.0.0  
**ETC profile:** 0.3-proposed  
**TLA+ lineage:** ECA lifecycle model, revision 1  
**Assessment date:** 18 November 2026  
**Release designation:** `verification-gated` — not a production or independently certified release

## 1. What was rebuilt

This is a clean-room implementation lineage. It was not reconstructed byte-for-byte from the previously reported ECA Reference Implementation 1.0.1. The historical source files, historical test suite, raw historical test output, and the cited historical TLA+ revision-v4 files were not available for independent reproduction during this work. No equivalence claim is made between this release and those unavailable artifacts.

The release contains:

- ETC schema and Python structural/semantic validator;
- canonical request serialization and digest binding under `eca-canonical-json-v1`;
- relation- and phase-specific trace-closure and action-readiness evaluation;
- attenuable delegation demonstration helpers (HMAC demo profile only);
- single-host SQLite execution journal and lifecycle runtime demonstration;
- target-receipt demonstration helpers (HMAC demo profile only);
- synthetic example contract, automated test suite, CLI, documentation, and a fresh TLA+ abstraction/configuration.

## 2. Executed checks

| Check | Result | Evidence | Scope |
|---|---:|---|---|
| Python automated tests | **102 passed** | `test-run.log`, `junit-results.xml` | Tests for the implementation in this repository only |
| Combined statement/branch coverage report | **82.10% (rounded to 82%)** | `coverage-report.txt`, `coverage.json` | coverage.py combined metric; not proof coverage or security assurance |
| Coverage threshold | **Passed** | `pyproject.toml` (`fail_under = 80`) | Repository-configured threshold |
| Python bytecode compilation | **Passed** | Executed by `scripts/run_tests.sh` | Syntax compilation of Python modules, tests, examples and scripts |
| JSON Schema meta-schema check | **Passed** | `package-check.log` | Draft 2020-12 structural schema validation |
| Synthetic example validation | **Passed** | `package-check.log`, `cli-smoke-output.json` | Synthetic fixture only; not a deployment or empirical case study |
| Wheel build | **Passed** | `package-check.log` | Built `eca_reference-2.0.0-py3-none-any.whl` |
| Wheel target-install/import/CLI smoke test | **Passed** | `wheel-install.log`, `wheel-smoke-status.txt`, `cli-smoke-output.json` | Installed with `pip --no-deps` into a separate target directory, using the authoring environment's dependencies |
| TLA+ lexical/frame sanity audit | **Passed** | `tla-lexical-audit.log` | Custom lexical and action-frame check only; not a TLA+ parser |
| TLC configuration/name cross-check | **Passed** | `tla-config-name-check.log` | Checks that selected config identifiers resolve textually; not a parser or model checker |
| Official SANY parse | **NOT RUN — BLOCKED** | `tla-run.log`, `tla-run-exit-code.txt` | Official `tla2tools.jar` unavailable in the authoring environment |
| Official TLC model checking | **NOT RUN — BLOCKED** | `tla-run.log`, `tla-run-exit-code.txt` | No model-checking result, state count, invariant pass, deadlock result or TLC trace is claimed |

Coverage details: 997 statements, 860 covered lines (86.26% line coverage), 472 branches with 346 covered (73.31% branch coverage), 124 partially covered branches, and a combined coverage.py result of 82.10% (displayed as 82%). Some individual modules are below the aggregate figure. The project’s 80% `fail_under` threshold applies to the combined coverage.py score; it is a quality gate, not a claim of completeness.

## 3. TLA+ verification gate

The new model is in a separate revision-1 lineage; it is not represented as the former revision-v4 artifact. The current model captures a finite abstraction of reservation, readiness, dispatch intent, revocation, uncertain outcomes, reconciliation, concurrent-guard closure, post-action closure, and accountability closure.

The repository includes `.tla` and `.cfg` files and two limited static checks. The official runner is pinned to stable TLA+ Tools v1.7.4 and checks the upstream-published SHA-1 before invoking SANY and TLC. The runner was attempted on the current model and exited with code 2 because the JAR was not present. Consequently, the TLA+ model's grammar and semantics are **not yet verified by SANY**, and its invariants are **not yet model-checked by TLC**. Static lexical checks must not be substituted for either result.

See `TLA_EXECUTION_STATUS.md` for the exact gate, tool pin and commands.

## 4. Trust and implementation limits

1. **No production authorization claim.** Native authorization, issuer, effect-boundary and external dispatch assessment authenticity depend on the owning trust domains and verifiers. This package validates local fields, bindings and declared freshness; it does not replace those verifiers.
2. **No production cryptography claim.** HMAC helpers exist for a local reproducible demonstration. They do not define organizational PKI, key custody, HSM use, signer/verifier separation, certificate lifecycle or production cryptographic policy.
3. **No distributed-systems claim.** The runtime and journal are single-host SQLite demonstrations. They do not establish globally linearizable revocation, multi-host fencing, distributed atomicity, or exactly-once physical effects.
4. **No continuous concurrent-guard proof.** The local reference checks declared active guard references during readiness and requires closure evidence for post-action closure. It does not continuously monitor or prove the implementation of an external guard.
5. **No field evidence.** The municipal composite is fictional and synthetic. There has been no field deployment, production integration, independent external security audit, controlled comparative evaluation, or independent replication.
6. **No universal correctness/security proof.** Passing tests and static checks support only the bounded behaviors actually exercised.
7. **No license grant.** No open-source license was selected in this release. Distribution should remain private pending an explicit licensing decision and review.

## 5. Environment and dependency notes

The authoring environment used Python 3.13.5, `jsonschema` 4.26.0, `pytest` 9.0.2, `coverage` 7.13.3, SQLite 3.46.1 and OpenJDK 21.0.12. The dependency lock in the repository is a platform-specific tested snapshot, not a universal cross-platform lockfile.

A global `pip check` in the shared authoring environment reports an unrelated pre-existing conflict: installed `moviepy` 2.2.1 requires `pillow<12`, while the shared environment contains Pillow 12.3.0. Neither `moviepy` nor Pillow is a dependency of this package. This environment-level conflict is not presented as a package test pass.

## 6. Reproduction commands

From the repository root:

```bash
python -m pip install -r requirements-lock.txt
python -m pip install -e '.[test]'
bash scripts/run_tests.sh
bash scripts/check_package.sh
python -m pip install --no-deps --target /tmp/eca-wheel-target dist/eca_reference-2.0.0-py3-none-any.whl
PYTHONPATH=/tmp/eca-wheel-target python -m eca_reference.cli examples/municipal-composite-contract.example.json --phase PRE --now 2026-11-18T12:00:00Z
```

For official TLA+ parsing and model checking, obtain the pinned official `tla2tools.jar` artifact, verify its checksum using the script, then run:

```bash
TLA2TOOLS_JAR=/absolute/path/to/tla2tools.jar bash scripts/run_tla.sh
```

The official runner writes SANY/TLC stdout and stderr to the caller's shell; archive those raw logs under `reports/` before changing this report's status. Do not change the TLA+ verification status to passed unless both tools complete successfully on this exact model and configuration.

## 7. Release disposition

This release is a reproducible Python reference package within the bounded authoring environment, with 102 passing automated tests and an 82% aggregate coverage report. It is **not yet a formally model-checked release**, because the official SANY/TLC gate remains blocked. It is also not externally audited, field-validated, production-certified, or licensed for open-source redistribution.

### Toolchain currency gate

A dated upstream review found Python 3.15.2 as the current feature release, pytest 9.2.0 as the current test-runner release, and coverage.py 7.16.1 as the current coverage release. The actual local test run used Python 3.13.5, pytest 9.0.2, and coverage 7.13.3. The current test-extra pins are updated in `pyproject.toml`, and a CI matrix for Python 3.11–3.15 plus an official TLA+ job has been added. Neither that CI workflow nor the newer local dependency combination has executed in this authoring environment. Package-index DNS access failed during the final review, so this compatibility gate remains open. See `TOOLCHAIN_CURRENCY.md`.

## 8. Subsequent CI-equivalent and alternative model-check update

A local CI-equivalent pipeline was subsequently executed with `bash scripts/run_local_ci.sh` on Python 3.13.5 and OpenJDK 21.0.12.1. It passed workflow YAML parsing, source compilation, all 102 tests, the 80% coverage threshold (82.10% combined), schema/example checks, wheel build, isolated target installation and CLI smoke test, static TLA checks, and the independent exhaustive finite-state checker. The exact run is retained in `reports/local-ci.log`; summary is in `reports/CI_EXECUTION_REPORT.md`.

The alternative checker explored all 16,384 permitted initial valuations, 33,668 reachable states and 17,702 transitions, checking ten safety invariants and cross-checking 13 transition operator names. This is a Python mirror of the finite transition system. It is useful bounded evidence but is **not** SANY, TLC, a TLA+ parser, or an implementation-refinement proof. Official SANY/TLC remain blocked because the official JAR could not be obtained in the offline authoring runtime. The GitHub Actions workflow is configured, but no hosted GitHub Actions run or full Python 3.11–3.15 matrix execution has yet occurred.
