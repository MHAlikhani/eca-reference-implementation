# ECA lifecycle TLA+ model guide

**Module:** `tla/ECA_Lifecycle.tla`  
**TLC configuration:** `tla/ECA_Lifecycle.cfg`  
**Lineage:** revision 1  
**Verification status:** official SANY/TLC pending; independent exhaustive Python mirror check passed for the stated finite abstraction (not equivalent to SANY/TLC)

## 1. Model purpose

The module is a finite state abstraction of the ETC lifecycle around one request and one nonce. It concentrates on the safety boundary between a request that appears ready, a durable reservation, dispatch intent, uncertain target outcomes, reconciliation, closure of concurrent guards, POST trace closure, and accountability closure.

It is not a model of a complete deployment, a distributed protocol, cryptographic algorithms, human institutions, or a physical actuator. Its booleans are abstract state/input predicates standing for claims that would be produced by real subsystems.

## 2. Abstract state

The model state includes:

- request and PRE predicates: `requestValid`, `preTraceClosed`, `preObligationsDischarged`;
- native permission predicates: `nativePermit`, `nativeBindingExact`, `requiredApprovalsPresent`, `nativeAuthorizationVerified`, `revocationClear`;
- effect-boundary predicates: `boundaryActive`, `concurrentGuardsActive`;
- post and accountability predicates: `postTraceClosed`, `postDutiesDischarged`, `challengeRouteAvailable`, `reviewResolved`;
- lifecycle memory: `phase`, `nonceConsumed`, `reservationReadinessCaptured`, `dispatchReadinessCaptured`, `receiptVerified`, `effectResult`;
- concurrent-guard closure: `concurrentGuardClosureEvidenceVerified`, `concurrentGuardClosureRecorded`;
- closure flags: `postClosed`, `accountabilityClosed`.

The initial state leaves selected evidence/readiness predicates nondeterministic over BOOLEAN. This allows TLC, once run, to explore both satisfied and unsatisfied initial conditions. `revocationClear` starts TRUE and can transition to FALSE through `Revoke`.

## 3. State transitions

| Action | Guard and effect |
|---|---|
| `Reserve` | Requires `ActionReadyAtReservation`; consumes the nonce and records a reservation readiness snapshot. |
| `Dispatch` | Requires a second `ActionReadyAtDispatch` check from the reserved state; records dispatch readiness and moves to `INTENT`. |
| `CancelAfterReadinessLoss` | Cancels a reservation when a readiness predicate no longer holds before dispatch. |
| `Revoke` | Changes the abstract revocation predicate to false. |
| `TargetCommit`, `TargetReject` | Produce a terminal outcome and an abstract verified receipt after dispatch intent. |
| `LoseReceipt` | Moves to `UNKNOWN` without a verified receipt; the physical target outcome remains uncertain. |
| `ConcurrentGuardLost` | Moves an in-flight action to `UNKNOWN` if an active guard is lost. |
| `ReconcileCommit`, `ReconcileReject` | Reconcile `UNKNOWN` using an abstract verified target receipt. |
| `RecordConcurrentGuardClosure` | Records separately supplied, abstractly verified concurrent-guard closure evidence. |
| `ClosePost` | Requires terminal outcome, dispatch readiness, verified receipt, guard closure, post trace and due-duty closure, and a challenge route. |
| `CloseAccountability` | Requires POST closure, an accessible challenge route, and resolved review. |

The model intentionally does not treat a target receipt as proof that a concurrent guard remained active throughout the action. That is a separate evidence obligation represented by `RecordConcurrentGuardClosure`.

## 4. Invariants selected in the TLC configuration

| Invariant | Intended property |
|---|---|
| `TypeOK` | Every state variable stays within its declared finite type. |
| `NoReserveWithoutActionReady` | A non-idle reservation lifecycle state must carry the readiness-capture and nonce-consumption markers; the transition guard enforces readiness at reservation. |
| `NoDispatchWithoutCapturedReadiness` | Intent, uncertain, and terminal states require the dispatch-readiness marker. |
| `NoEffectWithoutDispatchIntent` | Both terminal and `UNKNOWN` outcomes must be downstream of captured dispatch readiness and consumed nonce. |
| `NoFalseTerminalReceipt` | A terminal outcome cannot exist without an abstract verified receipt. |
| `PostClosureRequiresGuardClosure` | POST closure cannot precede concurrent-guard closure evidence. |
| `UnknownHasNoVerifiedReceipt` | An `UNKNOWN` state cannot simultaneously claim a verified receipt. |
| `PostClosureSoundness` | POST closure implies all modeled terminal/dispatch/receipt/guard/trace/duty/challenge predicates. |
| `AccountabilityClosureSoundness` | Accountability closure implies POST closure, challenge availability and review resolution. |
| `NonceIsNotReused` | A consumed nonce cannot return to the initial idle phase in this one-request abstraction. |

`CHECK_DEADLOCK FALSE` is deliberate. A terminal, post-closed or accountability-closed state may be quiescent and is not necessarily a defect. This choice means the configuration does not report quiescence as a deadlock; the listed invariants remain the selected safety checks.

## 5. Abstraction and proof boundaries

The boolean `concurrentGuardClosureEvidenceVerified` is an externally supplied abstract predicate. TLC would explore whether the model gates POST closure on that predicate, but it would not validate signatures, verifier keys, guard monitoring, or physical guard correctness. `receiptVerified` and `nativeAuthorizationVerified` are likewise abstractions, not cryptographic computations.

The model does not establish liveness, fairness, availability, a global revocation bound, a distributed atomic transaction, exactly-once physical effects, legal legitimacy, or Python-to-TLA refinement. A refinement relation and trace correspondence study would be needed before claiming that the implementation refines this abstraction.

## 6. Independent fallback result

The independent checker in `scripts/run_explicit_state_check.py` explores all 16,384 allowed initial Boolean valuations, 33,668 reachable states and 17,702 transitions; it checks the ten configured safety invariants and cross-checks the 13 action names in `Next`. It passes for the mirrored transition system only. It is not a TLA+ parser, SANY, TLC, or an implementation-refinement proof. See `reports/ALTERNATIVE_MODEL_CHECK_REPORT.md`.

## 7. Official execution gate

Run `bash scripts/run_tla.sh` with the official stable TLA+ Tools JAR pinned in `tools/README.md`. The script verifies the published artifact checksum, then invokes SANY and TLC. The current repository status is blocked because the JAR was unavailable in the authoring environment. See `reports/TLA_EXECUTION_STATUS.md`; no official parser or model-checker result is asserted.
