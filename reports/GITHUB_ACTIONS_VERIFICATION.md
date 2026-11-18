# GitHub Actions verification evidence

Repository: MHAlikhani/eca-reference-implementation  
Workflow: ECA verification  
Successful run #2: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960  
Commit tested: b9c760d280993c760091af5f1ed705038e8cf80d  
Conclusion: all six jobs succeeded.

## Python matrix

| Python | Tests | Coverage | Job ID |
|---|---:|---:|---:|
| 3.11 | 102 passed | 82% | 135108909207 |
| 3.12 | 102 passed | 82% | 135108909307 |
| 3.13 | 102 passed | 82% | 135108909147 |
| 3.14 | 102 passed | 82% | 135108909177 |
| 3.15 | 102 passed | 82% | 135108909143 |

Total: 510 successful executions. Dependencies installed: pytest 9.2.0, coverage.py 7.16.1, jsonschema 4.26.0. Each job built the wheel and passed the configured 80% coverage gate.

## TLA+ job

Job ID: 135108908582  
Artifact: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960/artifacts/14469505467

The official TLA+ Tools v1.7.4 checksum passed. SANY 2.1 parsed and semantically processed ECA_Lifecycle. TLC 2.19 completed with 16,384 initial, 34,086 generated, 33,668 distinct, zero remaining, depth 9, and no error found. Ten safety invariants were configured. CHECK_DEADLOCK FALSE; no deadlock-freedom, liveness, fairness or refinement claim.

Artifact ZIP SHA-256: aceacbca35a41ecdc4b0181a0bb87a4281bb625473832e739bb6a623212c292c.

The first run's timezone-naive datetime test mismatch was corrected by deterministic FormatChecker validation in commit b9c760d; run #2 passed all jobs.
