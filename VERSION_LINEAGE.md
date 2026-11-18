# ECA technical version lineage

| Asset | Version | Status | Lineage note |
|---|---|---|---|
| Python reference package | 2.0.0 | Clean-room bounded research implementation; GitHub CI verified | Not equivalent to historical 1.x source |
| ETC profile/schema | 0.3-proposed | Author proposal | Separate from package version |
| TLA+ lifecycle model | Revision 1 | Official SANY and TLC passed in GitHub Actions run #2 | Not the unavailable historical revision-v4 artifact |
| Test evidence | 102 tests per Python version; 510 executions total | Python 3.11–3.15 passed in run #2 | Applies only to 2.0.0 |
| Coverage | 82% combined | Each job passed the 80% threshold | Not proof coverage |

## Formal verification record

- Run #2: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960
- Tested source commit: b9c760d280993c760091af5f1ed705038e8cf80d
- SANY 2.1 parsed and semantically processed ECA_Lifecycle.
- TLC 2.19: 34,086 generated, 33,668 distinct, zero remaining, depth 9, no error found.
- Ten safety invariants configured. Deadlock checking was disabled; no liveness, fairness, or implementation-refinement proof is claimed.
- TLA+ artifact: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960/artifacts/14469505467

This result applies only to the new 2.0.0 / revision-1 lineage.
