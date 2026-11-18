# ECA lifecycle TLA+ model guide

**Module:** tla/ECA_Lifecycle.tla  
**Configuration:** tla/ECA_Lifecycle.cfg  
**Lineage:** revision 1  
**Verification:** official SANY 2.1 and TLC 2.19 passed in GitHub Actions run #2.

The module is a finite-state abstraction of the ETC lifecycle around one request and one nonce. It covers readiness, durable reservation, dispatch intent, uncertain target outcomes, reconciliation, concurrent-guard closure, POST closure, and accountability closure.

## State transitions

| Action | Guard and effect |
|---|---|
| Reserve | Requires ActionReadyAtReservation; consumes nonce and records readiness. |
| Dispatch | Requires a second ActionReadyAtDispatch check; moves to INTENT. |
| CancelAfterReadinessLoss | Cancels a reservation if readiness is lost before dispatch. |
| Revoke | Changes the abstract revocation predicate to false. |
| TargetCommit / TargetReject | Produce terminal outcome and abstract verified receipt. |
| LoseReceipt | Moves to UNKNOWN without a verified receipt. |
| ConcurrentGuardLost | Moves in-flight action to UNKNOWN if guard is lost. |
| ReconcileCommit / ReconcileReject | Reconcile UNKNOWN from abstract target receipt. |
| RecordConcurrentGuardClosure | Records a separate guard-closure attestation. |
| ClosePost | Requires terminal outcome, readiness, receipt, guard closure, post trace/duties and challenge route. |
| CloseAccountability | Requires POST closure, challenge availability and resolved review. |

## Invariants

Ten safety invariants are configured: TypeOK, NoReserveWithoutActionReady, PostClosureRequiresGuardClosure, NoDispatchWithoutCapturedReadiness, NoEffectWithoutDispatchIntent, NoFalseTerminalReceipt, UnknownHasNoVerifiedReceipt, PostClosureSoundness, AccountabilityClosureSoundness, and NonceIsNotReused.

CHECK_DEADLOCK FALSE is deliberate: terminal or closed states may be quiescent, and deadlock checking is disabled.

## Official hosted execution

Run #2: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960

SANY 2.1 parsed and semantically processed ECA_Lifecycle. TLC 2.19 completed with 16,384 initial, 34,086 generated, 33,668 distinct, zero remaining, depth 9, and no error.

Artifact: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960/artifacts/14469505467

## Proof boundaries

The model abstracts signatures, key custody, native PDP/PEP behavior, distributed clocks, storage internals, target physics and institutional legitimacy. It does not establish deadlock freedom, liveness, fairness, distributed atomicity, exactly-once physical effects, or Python-to-TLA refinement. An external boolean such as concurrentGuardClosureEvidenceVerified is not cryptographically verified by TLC.
