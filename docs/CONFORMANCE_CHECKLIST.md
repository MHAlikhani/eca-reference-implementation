# ETC Profile 0.3-proposed — Conformance Checklist

An implementation should not claim overall conformance merely because the JSON Schema validates.

- [ ] Exact profile version and canonicalization profile declared.
- [ ] Canonicalization test vectors pass across all supported languages.
- [ ] Every relation type is explicitly supported or declared unsupported.
- [ ] Relation status is verifier-relative and includes method/verifier/trust-profile metadata.
- [ ] Node references and relation endpoint kinds are validated.
- [ ] Freshness, validity intervals, clock assumptions and staleness policy are explicit.
- [ ] Required relation sets and critical hard gates are risk-profile-specific.
- [ ] `NOT_APPLICABLE` exceptions are approved, reasoned, scoped, time-bounded and prohibited for critical relations.
- [ ] PRE obligations block readiness unless discharged with evidence.
- [ ] Native PDP decision is independently verified and bound to the exact request/action/target/policy.
- [ ] Delegation attenuation and revocation semantics are checked by the native trust system.
- [ ] The PEP/effect boundary is active, versioned and bypass-controlled.
- [ ] Dispatch-time readiness assessment is immutable, externally verified and request-bound.
- [ ] Target outcome receipt is authenticated and action/target/request-bound.
- [ ] Unknown outcomes remain unknown until target-linked reconciliation.
- [ ] POST duties are registered and discharged when due.
- [ ] Challenge, review, recovery and remedy routes are accessible and have accountable owners.
- [ ] Change-impact dependencies invalidate or reopen affected relations.
- [ ] Privacy class, retention, access and redaction controls are implemented.
- [ ] Test results, formal verification status and independent review are separately reported.
- [ ] Residual risks and unsupported capabilities are published.

Current implementation status is documented in `reports/REPRODUCIBILITY_STATUS.md`. Items requiring an external trust verifier or real deployment adapter are not satisfied by this local Python package alone.
