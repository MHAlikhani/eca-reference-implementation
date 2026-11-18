# CI execution report

**Date:** 18 November 2026  
**Environment:** Python 3.13.5; OpenJDK 21.0.12.1; Linux authoring container  
**Run command:** `bash scripts/run_local_ci.sh`  
**Result:** local CI-equivalent pipeline PASS, with official TLA+ gate blocked and alternative exhaustive finite-state check PASS.

## Executed locally

| Gate | Result | Evidence |
|---|---|---|
| Python runtime minimum (>=3.11) | PASS | `reports/local-ci.log` |
| GitHub Actions workflow YAML parse and job presence | PASS | `reports/local-ci.log` |
| Python compileall | PASS | `reports/local-ci.log` |
| Pytest | 102 passed | `reports/test-run.log`, `reports/junit-results.xml` |
| Branch coverage threshold | PASS, 82% total | `reports/coverage-report.txt`, `reports/coverage.json` |
| Draft 2020-12 schema self-check | PASS | `reports/package-check.log` |
| Synthetic contract validation | PASS | `reports/package-check.log` |
| Wheel build | PASS | `reports/package-check.log` |
| Wheel installation to isolated target and CLI invocation | PASS | `reports/local-ci-wheel-smoke.json`, `reports/local-ci.log` |
| TLA+ config-name check | PASS (static only) | `reports/tla-config-name-check.log` |
| TLA+ lexical/action-frame check | PASS (static only) | `reports/tla-lexical-audit.log` |
| Independent exhaustive finite-state check | PASS | `reports/explicit-state-check.log`, `reports/ALTERNATIVE_MODEL_CHECK_REPORT.md` |
| Official SANY/TLC | BLOCKED | `reports/tla-official-run.log`, `reports/tla-official-run-exit-code.txt` |

## Scope limitations

This is a local CI-equivalent execution, not a GitHub-hosted Actions run. No GitHub repository remote or authenticated GitHub Actions session was available, and only Python 3.13.5 is installed locally. Therefore the workflow's Python 3.11–3.15 matrix has not been executed across all five interpreters. The workflow YAML was parsed locally and its `python` and `tla` jobs were confirmed present.

The hosted workflow is retained at `.github/workflows/verification.yml`. When pushed to a connected GitHub repository, it will run the matrix and fetch the official pinned TLA+ artifact in a network-enabled runner. No claim is made that this remote workflow has already run.
