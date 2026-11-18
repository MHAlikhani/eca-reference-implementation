# Toolchain currency and execution review

**Review date:** 18 November 2026

| Component | Local baseline | Hosted verification | Result |
|---|---|---|---|
| Python | 3.13.5 | 3.11–3.15 | All five versions passed |
| jsonschema | 4.26.0 | 4.26.0 | Installed in each Python job |
| pytest | 9.0.2 | 9.2.0 | 102 tests passed per version |
| coverage.py | 7.13.3 | 7.16.1 | 82% combined; threshold 80% |
| TLA+ Tools | Not available locally | 1.7.4 stable | Checksum passed; SANY/TLC completed |
| Java | 21.0.12.1 local | Eclipse Temurin 21.0.13 | TLA+ job passed |

GitHub Actions run #2:
https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960

The matrix used pytest 9.2.0, coverage.py 7.16.1 and jsonschema 4.26.0. Each Python version completed 102 tests and passed the 80% coverage gate. The TLA+ job verified the official v1.7.4 SHA-1 and ran SANY 2.1 / TLC 2.19 successfully.

Future toolchain changes require rerunning CI; this review does not guarantee compatibility with releases published later.
