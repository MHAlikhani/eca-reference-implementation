# Manuscript alignment register — technical release 2.0.0

This register records the changes required when the manuscript is synchronised with the clean-room ECA technical release. It is not a claim that the manuscript has already been revised.

## Mandatory alignment items

1. Replace any description of the old implementation as the current reproducible reference with `ECA Reference Implementation 2.0.0`, clearly described as a separate clean-room lineage.
2. Remove or qualify any historical 1.x test count unless the original source, environment, test suite and raw execution outputs are supplied and independently reproduced. The present 102-test result belongs only to 2.0.0.
3. Identify the current ETC schema as `0.3-proposed`; keep this separate from the Python implementation version `2.0.0`.
4. Update the obligation vocabulary to PRE, CONCURRENT, POST and ACCOUNTABILITY. Explain that CONCURRENT is a runtime guard obligation checked at readiness and dispatch in this bounded prototype; the local reference does not continuously monitor or prove the guard implementation.
5. Include the risk-profile maximum-age controls for native authorization and enforcement assessments. State that authenticity remains the responsibility of the external native verifier.
6. Distinguish the local dispatch-readiness journal snapshot from the externally verified immutable dispatch-time assessment required for POST closure.
7. Update the runtime description: readiness is re-evaluated at reservation and immediately before dispatch intent, but this does not eliminate a distributed check-to-use race.
8. Update the TLA+ section to the new revision-1 model. Do not identify it as the unavailable historical revision-v4 source. State that lexical and configuration-name checks passed but SANY/TLC remain unrun until the official tools are available.
9. Replace all package test/coverage statements with the current exact outputs: 102 automated tests passed; 82% aggregate coverage. Do not imply coverage is proof coverage or security assurance.
10. Keep all limitations: single-host SQLite, demo-only HMAC helpers, synthetic example, no production deployment, no external audit, no field validation, no independent controlled evaluation, and no production certification.
11. Do not imply this code release validates ECA's novelty, superiority, safety, legal legitimacy or commercial readiness. The incremental value remains an empirical hypothesis.

## Editorial release gate

Before publication, revise every affected chapter, appendix, table, figure caption, abstract, authorial note, implementation summary, reproducibility appendix, version table and bibliography statement. Then run a manuscript-wide string/claim audit and a source-to-manuscript consistency check against this repository. The manuscript should not describe the formal model as verified until retained official SANY and TLC output supports that claim.
