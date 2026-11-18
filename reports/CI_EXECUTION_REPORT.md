# CI execution report

**Workflow:** ECA verification  
**Successful run #2:** https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960  
**Source commit tested:** b9c760d280993c760091af5f1ed705038e8cf80d  
**Result:** **6/6 jobs successful** on 18 November 2026.

## Python matrix

| Python | Tests | Combined coverage | Build/package | Job ID |
|---|---:|---:|---|---:|
| 3.11 | 102 passed | 82% | Passed | 135108909207 |
| 3.12 | 102 passed | 82% | Passed | 135108909307 |
| 3.13 | 102 passed | 82% | Passed | 135108909147 |
| 3.14 | 102 passed | 82% | Passed | 135108909177 |
| 3.15 | 102 passed | 82% | Passed | 135108909143 |

Total: 510 successful test executions. Each job passed the configured 80% threshold. Dependencies: pytest 9.2.0, coverage.py 7.16.1, jsonschema 4.26.0. Each job built the wheel.

## Official TLA+ job

The sixth job passed: SANY 2.1 parsed and semantically processed ECA_Lifecycle; TLC 2.19 reported no error with 34,086 generated states, 33,668 distinct, zero remaining, depth 9.

- Job ID: 135108908582
- Artifact: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960/artifacts/14469505467

CHECK_DEADLOCK FALSE is configured. No deadlock, liveness, fairness or Python-to-TLA refinement claim is made.

## First-run correction

The first run exposed a schema/test-layer mismatch for a timezone-naive RFC3339 date-time: the test expected SchemaValidationError, but semantic validation raised SemanticValidationError. Commit b9c760d280993c760091af5f1ed705038e8cf80d introduced a deterministic FormatChecker rejecting date-times without an explicit UTC offset. The corrected suite passed across all five Python jobs in run #2.

The hosted result does not establish production readiness, independent security audit, field validation, legal legitimacy, or correctness of external trust roots.
