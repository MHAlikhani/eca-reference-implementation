# Design Decision Log

| ID | Decision | Rationale | Consequence |
|---|---|---|---|
| D-001 | New implementation lineage is 2.0.0. | Avoid representing reconstructed code as missing historical 1.x source. | No equivalence claim with prior implementation. |
| D-002 | ETC schema remains `0.3-proposed`. | Aligns with the current manuscript vocabulary while separating profile maturity from implementation release. | Schema version is provisional, not a standard. |
| D-003 | Canonicalization is custom and named. | Reject floats and define deterministic representation for this profile. | Not RFC 8785/JCS; cross-language vectors needed. |
| D-004 | RRC is diagnostic only. | Coverage must not authorize an action. | Readiness uses conjunctive gates, not a threshold. |
| D-005 | Native PDP and PEP remain external. | ETC maps assurance evidence; it does not supersede enforcement. | Requires trusted integration assessments. |
| D-006 | UNKNOWN is a first-class outcome. | Timeout or lost receipt cannot prove non-execution. | Reconciliation must use target evidence; blind retry is disallowed by adapter. |
| D-007 | HMAC helpers are demo-only. | Keep package runnable without inventing production PKI. | No production cryptographic claim. |
| D-008 | SQLite demo is single-host. | Make tested scope explicit and bounded. | No global revocation or distributed transaction claim. |
| D-009 | TLA+ official verification is a release gate. | Lexical scan cannot substitute for SANY/TLC. | Current model status remains NOT RUN until logs exist. |
| D-010 | No open-source license assigned. | User has not explicitly selected distribution terms. | Package remains private / no license granted. |
