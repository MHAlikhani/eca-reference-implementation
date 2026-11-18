# Threat Model and Assurance Limitations

## 1. Security objective

The limited objective is to prevent the local reference evaluator/runtime from treating a malformed, stale, mismatched, revoked, unverified, or unresolved record as sufficient evidence for action readiness, and to preserve uncertainty after dispatch when target effects cannot be established.

It is not an objective of this release to prove that the institution, policy, data, target, or action is safe or legitimate.

## 2. Assets

- canonical action request and its digest;
- native authorization decision and delegation chain;
- policy, mission, artifact and release references;
- evidence relation assertions and verifier metadata;
- boundary enforcement assessment;
- nonce and idempotency key;
- durable dispatch intent and lifecycle event journal;
- target receipt and reconciliation evidence;
- review, challenge, recovery and remediation references.

## 3. Adversary and fault classes considered

The tests exercise selected cases of request substitution, relation endpoint substitution, unknown relation/status values, duplicate IDs, digest mismatch, stale/expired evidence, future timestamps, disputed/contradicted parallel claims, critical N/A waiver attempts, delegation scope expansion, invalid signatures, revoked ancestor, issuer discontinuity, nonce replay, idempotency-key misuse, receipt tampering/misbinding, missing approval roles, non-PERMIT native verdicts, unknown revocation state, inactive boundary, declared bypass gaps, lost target receipt, illegal state transition and concurrent reservation attempts.

These are finite test cases, not exhaustive adversarial coverage.

## 4. Trust assumptions and out-of-scope threats

| Area | Assumption / limitation |
|---|---|
| Identity and authority | The caller's identity, legitimacy of the root delegator, legal competence and institutional authority are external. |
| Native PDP | Native assessment is already verified by its owning system; the ETC library does not replace that verifier. |
| Signatures and keys | The included HMAC code is for local tests only; secret compromise, distribution, rotation, HSM, separation of duties and production PKI are not solved. |
| Time | Correctness depends on trustworthy clocks and timestamp semantics. Distributed clock skew and offline validity are not modeled in Python runtime. |
| Revocation | The local evaluator consumes a revocation state supplied by native authorization. Global instantaneous revocation is not provided. |
| Data truth | A verified signature or relation does not establish that the underlying observation or statement is true. Sensor compromise and source collusion remain possible. |
| SQLite | Single-host WAL durability is demonstrated; multi-host coordination, Byzantine storage, backup restore, disk-controller guarantees and power-loss behavior require deployment-specific validation. |
| Concurrent obligations | The evaluator checks that declared runtime guard references are active in the supplied enforcement assessment and later discharged; it does not independently monitor an external guard continuously or prove its runtime correctness. |
| Target effect | The SQLite target simulator is not a physical actuator. Exactly-once physical effect is not claimed. |
| Runtime compromise | Malicious host, root/admin compromise, kernel compromise, interpreter compromise and malicious dependencies are outside the runtime proof boundary. |
| Privacy | The profile includes privacy/retention references; this release does not provide a complete privacy-preserving disclosure protocol, data minimization engine or legal compliance analysis. |
| Safety | Hazard analysis, independent safety case, human factors, fallback controller and real-world validation are external. |
| Availability | Fail-closed behavior can cause delay/denial of legitimate action. This release does not measure evidence-induced paralysis or latency. |

## 5. Important failure semantics

After a durable dispatch-intent event, an exception or missing receipt does not prove that the target did nothing. The runtime therefore records `UNKNOWN`. Reconciliation consults the same target idempotency record. This reduces unsafe blind retry in the demonstration, but does not eliminate uncertainty in real distributed systems or physical operations.

An exception before the dispatch call and an exception after a request may have crossed a network boundary are not equivalent. Production adapters must identify the exact point after which outcome becomes uncertain.

## 6. Security claims this release does not make

This package does not claim:

- formal proof of the Python implementation;
- TLC verification of the accompanying TLA+ module;
- linearizable distributed revocation;
- universal forward simulation between implementation and model;
- exactly-once physical-world effects;
- resistance to malicious insiders or compromised trust roots;
- cryptographic agility or post-quantum readiness;
- field-tested safety, legality, fairness or effectiveness;
- independent audit or certification;
- superiority over strong existing authorization/assurance architectures.

## 7. Required next assurance steps

Before high-consequence use, obtain independent review of the specification and code, run official SANY/TLC with archived outputs, test multi-process and multi-host races, test crash/restart and storage faults on the target deployment stack, integrate real native verifiers and target receipt schemes, perform a domain hazard analysis, and run a controlled comparative evaluation with a preregistered protocol. Production deployment requires a separate security/safety case and accountable owner.
