# Manuscript alignment register — technical release 2.0.0

This register records changes required when synchronizing the book with the clean-room ECA release. It does not claim the manuscript has already been revised.

1. Identify 2.0.0 as a clean-room lineage, separate from historical 1.x artifacts.
2. Do not reuse historical test totals without original source/raw evidence. Current result: 102 tests per Python version across 3.11–3.15 (510 executions).
3. Keep ETC profile 0.3-proposed distinct from implementation 2.0.0.
4. Use PRE, CONCURRENT, POST and ACCOUNTABILITY obligation vocabulary. Explain the bounded runtime-guard check and its continuous-monitoring limitation.
5. Include max-age controls for native authorization and enforcement assessments; authenticity remains with native verifiers.
6. Distinguish local dispatch-readiness snapshot from externally verified immutable dispatch-time assessment required for POST closure.
7. Explain readiness re-evaluation at reservation and immediately before dispatch, while retaining the distributed check-to-use race limitation.
8. Report official SANY 2.1/TLC 2.19 success on revision 1 in run #2: 34,086 generated states, 33,668 distinct, zero remaining, depth 9, no error, ten safety invariants. CHECK_DEADLOCK FALSE; do not claim deadlock freedom, liveness, fairness, or Python-to-TLA refinement.
9. Report 82% combined coverage in each Python job against 80%; coverage is not proof coverage.
10. Retain limits: single-host SQLite, demo HMAC, synthetic example, no production deployment, independent audit, field validation, controlled evaluation, or certification.
11. Do not imply proof of ECA novelty, superiority, safety, legal legitimacy or commercial readiness.

Before publication, revise affected chapters, appendices, tables, captions, abstract, authorial note, implementation summary, reproducibility appendix, version table and references. Then perform a manuscript-wide claim audit. The manuscript may report the bounded SANY/TLC result but must preserve these limits.
