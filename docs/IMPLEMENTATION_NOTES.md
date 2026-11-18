# Implementation Notes

## Runtime behavior

The public lifecycle adapter evaluates `ACTION_READY` itself; callers do not submit a standalone `action_ready=True` boolean as the runtime's authority. It requires externally supplied native authorization and effect-boundary assessments, checks their declared verification metadata and exact request bindings, enforces their risk-profile maximum age, and checks current revocation/replay fields. It persists a reservation only after PRE closure and required obligations pass. Immediately before persisting dispatch intent, it re-evaluates readiness using the assessments supplied for that dispatch attempt. If readiness fails, the reservation is cancelled and no target call is made.

This second evaluation narrows a stale-assessment window but does not eliminate the check-to-use race between independently operated authorization services, enforcement points, network paths and targets. The caller must obtain fresh assessments from the owning systems; simply re-submitting a cached object is not a live revocation query. For stronger deployments, the native authorization decision, nonce consumption, dispatch intent and enforcement lease should share a transactional or explicitly coordinated authority boundary.

The runtime persists dispatch intent before calling the target simulator. A target call exception, lost receipt or receipt-binding failure after that point yields `UNKNOWN`, not an invented rejection. Reconciliation consults the same idempotency key and requires a verified matching receipt; it does not retry with a new key. A terminal journal outcome requires a target receipt bound to request digest, nonce, target, action and terminal result, plus a separate verifier assessment envelope.

The dispatch-time readiness snapshot stored in the local journal is an audit record of the local evaluation. It is not itself a third-party signed dispatch attestation and cannot be substituted for the externally verified immutable dispatch assessment required by `TRACE_CLOSED_POST`. The caller must obtain that attestation from the appropriate trusted verifier.

The journal's low-level `reserve` and `record_outcome` methods are persistence APIs, not security boundaries. Applications should expose the lifecycle adapter rather than directly exposing journal writes. Production integration requires process isolation, access controls, verifier authentication, and protection of the database and host.

## Concurrent obligations

Each `CONCURRENT` obligation names a `runtime_guard_ref`. The effect-boundary assessment supplied at readiness must list that reference among active guards. The runtime repeats this check immediately before dispatch intent. After a terminal outcome, POST closure requires the obligation to be marked `DISCHARGED` with a discharge evidence reference. The reference implementation does not itself run a continuous guard monitor or validate the guard's physical/software correctness; the assessment and monitoring must come from the deployment's enforcement domain.

## Concurrency and durability scope

SQLite transactions use `BEGIN IMMEDIATE`, WAL mode, `synchronous=FULL`, and a unique nonce constraint to serialize concurrent reservations on one database. The test suite exercises concurrent reservation attempts using threads. This is not a distributed locking protocol, a multi-host fencing service, or an exactly-once physical effect guarantee. Separate hosts or separate database files are not coordinated. Operational durability also depends on the host filesystem, storage device, backup/restore process and platform guarantees.

## Canonicalization

The profile rejects floating-point values to avoid language-dependent binary float formatting. Applications that need decimals must define a canonical decimal string grammar and a new canonicalization profile rather than silently passing floats. This profile is intentionally narrow and is not RFC 8785/JCS.

## Error handling

- `SchemaValidationError`: instance does not satisfy the JSON Schema.
- `SemanticValidationError`: structure exists but violates profile semantics.
- `ReadinessError`: caller attempted reservation or dispatch without an affirmative readiness result.
- `ReplayError`: nonce has already been used for a materially different request or authorization.
- `StateTransitionError`: illegal or unknown journal state transition.
- `CanonicalizationError`: input cannot be represented by the declared canonicalization profile.

## Synthetic example

`examples/municipal-composite-contract.example.json` is a fictional composite used solely to exercise the schema and evaluator. It is not an empirical case study and its timestamps/records are synthetic.
