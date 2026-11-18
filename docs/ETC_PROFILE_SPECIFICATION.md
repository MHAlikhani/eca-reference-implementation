# ECA Cross-Layer Traceability Contract
## Profile specification 0.3-proposed — implementation companion 2.0.0

**Status:** Author proposal / proposed engineering profile. This document is not an adopted international standard.

## 1. Scope and design boundary

The ETC is a typed, versioned semantic mapping over native records that already belong to identity, delegation, policy, evidence, build/release, authorization, enforcement, target outcome, review, and remediation systems. It describes the meaning and verification state of cross-layer relations. It does not itself create authority, issue grants, make policy decisions, execute actions, prove legitimacy, or guarantee safety.

The unit of assessment is a declared action and its risk profile in a specified operating context. An organization-wide ECA badge is outside this profile.

## 2. Normative language and epistemic labels

The words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** express requirements within this proposed profile, not legal obligations. An implementation claiming profile conformance must state deviations and residual risks.

Claims are classified as:

- **ESTABLISHED SOURCE:** supported by a cited external source.
- **AUTHOR PROPOSAL:** design proposal advanced by this work.
- **FORMAL DEFINITION:** stipulated predicate or mathematical definition within the profile.
- **WORK IN PROGRESS:** draft, provisional or incomplete external work.
- **UNTESTED HYPOTHESIS:** empirical proposition that has not been established by the reported evidence.

## 3. ETC contract object

A contract contains:

1. Profile identifier and version.
2. Action identity, action class, target and exact canonical request.
3. Request digest and action-validity interval.
4. Risk profile and phase-specific required relation types.
5. Nodes identifying native records or resources.
6. Typed relation instances with issuer, verification, validity, freshness, ownership, privacy and retention metadata.
7. PRE, CONCURRENT, POST and ACCOUNTABILITY obligations and their state. Each obligation ID is unique; `DISCHARGED` requires a discharge-evidence reference; every CONCURRENT obligation also requires a runtime-guard reference.
8. Closure policy, including hard-gate treatment and a challenge/recovery route.

The authoritative JSON structure is `src/eca_reference/schemas/etc-profile-0.3-proposed.schema.json`. The schema is structural validation only. The Python semantic validator adds cross-object checks such as referential integrity, relation endpoint kinds, digest binding, and temporal rules. External issuer and verifier trust roots remain outside the local validator.

## 4. Canonical relation vocabulary

All relation names are case-sensitive. An implementation MUST NOT silently alias or infer another relation type.

| Relation | Required source kind | Required target kind | Meaning |
|---|---|---|---|
| `governed_by_mission` | action | mission | Action is mapped to an approved mission/use record. |
| `delegated_through` | action | delegation | Action is mapped to the native delegation chain or profile reference. |
| `evaluated_under_policy` | action | policy | Action is linked to the policy version evaluated. |
| `supported_by_evidence` | action | evidence | Action claim is linked to supporting or challenging evidence. |
| `implemented_by_artifact` | action | artifact | Action behavior is mapped to an implementation artifact. |
| `built_as_release` | artifact | release | Artifact is mapped to a specific release/build. |
| `authorized_by_native_decision` | action | native_authorization | Action is bound to the owning native authorization decision. |
| `enforced_at_boundary` | action | enforcement_point | Action is mapped to the enforcement boundary that guards its effect. |
| `observed_as_target_effect` | action | target_effect | Action is linked to a target-side effect/outcome observation. |
| `challenged_through_review` | action | review_process | Action is connected to a challenge/review route. |
| `remediated_by_action` | action | remediation_action | Corrective or remedial action is linked to the original action. |
| `supersedes_version` | same kind | same kind | Source is a later version that supersedes target; versions must differ. |

ETC is a directed temporal multigraph. More than one assertion may exist for a relation type where issuers or verifiers differ. An unresolved `DISPUTED` or `CONTRADICTED` parallel assertion blocks phase closure even if another parallel assertion is `VERIFIED`; an implementation MUST NOT hide conflict by choosing the most convenient edge.

## 5. Relation envelope

Each relation MUST carry, at minimum, the fields required by the JSON Schema: stable relation ID, canonical type, source and target node IDs, schema/profile version, asserting issuer, assertion and observation times, validity, native evidence reference, verification method, verifier reference, trust-profile reference, limitations, status, owner, privacy classification, retention rule, and declared change dependencies. The exact required/optional structure is authoritative in the schema file.

The verifier-relative status vocabulary is:

| Status | Meaning | Satisfies a required relation? |
|---|---|---|
| `VERIFIED` | Successfully checked under a named verifier and trust profile, within declared scope and time. | Yes, if all other constraints pass. |
| `PRESENT_UNVERIFIED` | A record/reference exists but has not been verified to support the claimed relation. | No. |
| `STALE` | Evidence or verification is outside a required freshness/validity condition. | No. |
| `UNAVAILABLE` | Required evidence or verifier is unavailable. | No. |
| `DISPUTED` | There is an unresolved challenge or competing assertion. | No; blocks the affected obligation. |
| `CONTRADICTED` | Evidence affirmatively conflicts with the asserted relation. | No; blocks the affected obligation. |
| `NOT_APPLICABLE` | A pre-authorized profile exception applies to this relation in this risk context. | Only for a non-critical obligation, with valid exception and profile allowance; it is excluded from VERIFIED coverage. |

`MISSING` is a diagnostic condition for an absent required relation, not a stored relation status.

A `NOT_APPLICABLE` exception MUST include a reason, approving owner, approval time, and expiry. Approval time MUST NOT be in the future; expiry MUST be later than approval time and later than the evaluation time. Critical relations MUST NOT be waived through `NOT_APPLICABLE`.

## 6. Canonical request and digest binding

The canonical request profile is `eca-canonical-json-v1`. Its byte encoding is intentionally narrow and is **not** claimed to implement RFC 8785/JCS.

The current implementation rules are: Published positive and negative vectors are maintained in `vectors/canonicalization-v1.json`; independent implementations should pass those vectors before claiming interoperability:

1. Input is one JSON object.
2. Object keys and string values are normalized to Unicode NFC.
3. A collision between keys after NFC normalization is rejected.
4. Object keys are serialized in ascending Unicode code-point order.
5. Arrays retain their input order.
6. Only null, booleans, strings, arrays, objects and signed 64-bit integers are accepted. Binary floating point, NaN, Infinity, non-string keys, out-of-range integers, unpaired surrogates and nesting deeper than 64 levels are rejected.
7. The reserved field `canonicalization_profile` is inserted with value `eca-canonical-json-v1`; a conflicting supplied value is rejected.
8. JSON is UTF-8, non-ASCII characters remain unescaped, separators are compact (`,` and `:` without spaces), keys are sorted, and non-finite numbers are prohibited.
9. The digest is `sha256:` followed by lowercase hexadecimal SHA-256 over those bytes.

Formally:

\[
cd(q) = \texttt{"sha256:"} \; || \; \operatorname{hex}(\operatorname{SHA256}(C_{\kappa}(q)))
\]

The digest binds the canonical request representation. It does not prove truthfulness, legitimacy, policy correctness, or target-side execution. Native protocol binding projection must remain separate: an adapter MUST declare which native fields and effect-bearing parameters it binds, and MUST reject any mismatch between that projection and the ETC request.

## 7. Delegation attenuation

A delegation chain is ordered root-to-leaf. Each child MUST identify the immediately preceding parent, and its issuer MUST equal the parent's subject. For each link:

- child action scope is a subset of parent action scope;
- child resource scope is a subset of parent resource scope;
- child risk ceiling is no greater than parent risk ceiling;
- child's validity interval is contained within parent's interval;
- every link's signature is verified by a key belonging to the declared issuer under the deployment's trust policy;
- any revoked ancestor invalidates descendants according to the selected revocation semantics.

The local HMAC demonstration is not a production trust architecture. Real deployments must use their native credential/signature scheme, key rotation, issuer authorization, revocation, and audit controls. A mathematically attenuated chain does not establish that the root delegator was legally or institutionally legitimate.

## 8. Native authorization and effect-boundary enforcement

The native PDP verdict domain is `PERMIT`, `DENY`, `REQUIRE_HUMAN`, or `DEFER`. Only `PERMIT` can satisfy the native decision gate for `ACTION_READY`. ETC does not issue or override that verdict.

A native authorization assessment used for readiness MUST be affirmatively verified by its native verifier and be bound to the exact request digest, principal, action, target, and policy reference. It MUST have a valid time interval, active revocation state, acceptable replay state, required approval roles, verifier identity, and trust-profile reference.

The effect-boundary assessment MUST be active and bound to the same digest, action, target and policy version. Each native authorization assessment MUST include `verified_at`; each effect-boundary assessment MUST include `assessed_at`. The risk profile MUST declare `native_authorization_max_age_seconds` and `enforcement_assessment_max_age_seconds`. An assessment timestamp in the future or older than its declared maximum age MUST fail readiness. It MUST identify its enforcement point and adapter version and declare how bypass/direct paths are controlled. An adapter version existing in a record does not prove that it is correctly deployed; deployment evidence is external.

## 9. Obligations and lifecycle predicates

Obligations are phase-indexed:

- `PRE`: MUST be discharged with evidence before readiness.
- `CONCURRENT`: MUST be enforced as a runtime guard for the relevant execution interval. The reference evaluator requires each such obligation to name a `runtime_guard_ref`, requires the reference to appear in the supplied active-guard assessment at reservation and again immediately before dispatch, and requires a discharge evidence reference before POST closure. The local prototype does not independently monitor the external guard continuously or prove the guard's implementation; deployments must supply a trustworthy enforcement assessment and guard-monitoring mechanism.
- `ACCOUNTABILITY`: MAY be registered until due; a due obligation MUST be discharged with evidence before accountability closure.
- `POST`: MUST be registered and discharged when due; an overdue undischarged obligation blocks POST closure.

Let `Req_PRE(q, t, κ)` be the set of PRE relation obligations declared by the risk profile. Each relation must pass relation-specific semantic, verifier, temporal, freshness and conflict checks. Then:

\[
TRACE\_CLOSED\_PRE(q,t,\kappa) \iff \forall r \in Req_{PRE}(q,t,\kappa): Satisfied(r,t,\kappa)
\]

`ACTION_READY(q,t,κ)` requires all of the following:

- `TRACE_CLOSED_PRE`;
- all PRE obligations are discharged and have discharge evidence;
- native PDP returns `PERMIT` and the native authorization is valid, non-revoked, replay-safe and bound to the exact request;
- all required approval roles are verified;
- the effect-boundary assessment is active, request-pinned, versioned, its declared bypass paths are controlled, and every `CONCURRENT` obligation is bound to an active runtime guard.

`TRACE_CLOSED_POST` requires an immutable, externally verified dispatch-time assessment that `ACTION_READY` held for the same digest/action/target; a target-linked terminal receipt or reconciled outcome; satisfied POST relations; closure of each CONCURRENT guard obligation with discharge evidence; registered post duties; and discharge of each POST duty when due. The current native authorization is not re-evaluated as though a later expiry rewrote a historical dispatch event. Before reservation and again before dispatch intent, the local runtime requires native authorization and enforcement assessments whose timestamps fall within the maximum ages declared by the risk profile.

`ACCOUNTABILITY_CLOSED` adds the accountability relation obligations, discharge of any due ACCOUNTABILITY obligations, a tested/accessibly demonstrated challenge route, and required review-case dispositions with accountable owners. A referral without an owner is not a resolved disposition.

The local evaluator validates the dispatch assessment envelope, fields and bindings but does not authenticate its signature or trust root. Native authorization and effect-boundary assessment timestamps are checked against the risk profile maximum-age limits, but their authenticity still depends on the external verifier. The native attestation verifier must perform that authentication and supply the `VERIFIED` assessment. The same boundary applies to target-receipt verification.

## 10. Relation readiness/coverage ratio

For a phase with `n` required relation types:

\[
RRC = \frac{\#\text{ required relation types satisfied by VERIFIED evidence}}{n}
\]

A valid non-critical `NOT_APPLICABLE` exception can satisfy a phase obligation only where the profile allows it; it is reported separately and excluded from the numerator. RRC is descriptive. It MUST NOT be used as a substitute for `TRACE_CLOSED_PRE`, `ACTION_READY`, `TRACE_CLOSED_POST`, or `ACCOUNTABILITY_CLOSED`.

## 11. Target outcomes and uncertainty

Allowed lifecycle outcome states are `COMMITTED`, `REJECTED`, `UNKNOWN`, and `RECONCILED`. A terminal state requires a target-linked receipt bound to request digest and target, together with a declared receipt verifier, method and trust profile. `RECONCILED` must state whether the target outcome was `COMMITTED` or `REJECTED`.

When dispatch may have occurred but the target result cannot be established, the system MUST retain `UNKNOWN`. It MUST NOT infer rejection from a timeout or retry with a fresh idempotency key without an explicit reconciliation policy. The local runtime persists dispatch intent before calling the target simulator and exposes a reconcile operation that looks up the same idempotency key.

## 12. Change impact and supersession

A relevant change to policy, mission/use profile, delegation, artifact, release, key, adapter, enforcement point, target configuration, trust profile, or verifier can invalidate dependent relations. Implementations SHOULD express dependency edges explicitly and MUST preserve supersession history. Revalidation must occur before dependent actions are again considered ready. A generic graph validator cannot infer every domain-specific dependency; the risk profile and integration adapter must define the relevant change events.

## 13. Validation layers

The reference implementation separates:

1. JSON Schema structural validation;
2. local semantic validation (vocabulary, IDs, endpoints, time and graph constraints);
3. relation-specific status/freshness evaluation;
4. phase closure and RRC calculation;
5. action readiness based on external native authorization and enforcement assessments;
6. post-action closure based on external dispatch and target-receipt assessments;
7. accountability closure based on review disposition evidence.

Passing one layer MUST NOT be described as passing a later layer.

## 14. Conformance statement

Any implementation claiming conformance to ETC profile 0.3-proposed must identify:

- profile and schema version;
- canonicalization profile and interoperable test vectors;
- supported relation types and statuses;
- risk-profile and phase obligations;
- native authorization, enforcement, dispatch-attestation and receipt verifiers, including assessment-age limits;
- cryptographic and institutional trust roots;
- clock, freshness, revocation, offline and replay assumptions;
- privacy, retention, access, redaction and appeal process;
- unsupported capabilities, exceptions and residual risks;
- test, formal analysis and independent review evidence.

This Python implementation is a bounded local reference for structural/semantic evaluation and a single-host lifecycle demonstration. It is not a certified or production conformance implementation.
