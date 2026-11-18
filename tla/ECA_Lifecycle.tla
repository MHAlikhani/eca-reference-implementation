--------------------------- MODULE ECA_Lifecycle ---------------------------
EXTENDS Naturals, FiniteSets, TLC

(***************************************************************************)
(* Finite lifecycle abstraction for the ECA Reference Implementation.      *)
(*                                                                         *)
(* This model captures reservation/readiness gates, dispatch intent,        *)
(* uncertain outcomes, reconciliation, concurrent-guard closure, and       *)
(* phase closure. It abstracts cryptography, distributed clocks, database  *)
(* internals, target physics, institutional legitimacy, and actual guard   *)
(* implementation. The input boolean                                     *)
(* concurrentGuardClosureEvidenceVerified represents an externally        *)
(* authenticated guard-closure attestation; TLC does not verify signatures. *)
(***************************************************************************)

VARIABLES
    requestValid,
    preTraceClosed,
    preObligationsDischarged,
    nativePermit,
    nativeBindingExact,
    requiredApprovalsPresent,
    boundaryActive,
    nativeAuthorizationVerified,
    concurrentGuardsActive,
    revocationClear,
    postTraceClosed,
    postDutiesDischarged,
    challengeRouteAvailable,
    reviewResolved,
    phase,
    nonceConsumed,
    dispatchReadinessCaptured,
    reservationReadinessCaptured,
    receiptVerified,
    concurrentGuardClosureRecorded,
    concurrentGuardClosureEvidenceVerified,
    effectResult,
    postClosed,
    accountabilityClosed

vars == <<
    requestValid,
    preTraceClosed,
    preObligationsDischarged,
    nativePermit,
    nativeBindingExact,
    requiredApprovalsPresent,
    boundaryActive,
    nativeAuthorizationVerified,
    concurrentGuardsActive,
    revocationClear,
    postTraceClosed,
    postDutiesDischarged,
    challengeRouteAvailable,
    reviewResolved,
    phase,
    nonceConsumed,
    dispatchReadinessCaptured,
    reservationReadinessCaptured,
    receiptVerified,
    concurrentGuardClosureRecorded,
    concurrentGuardClosureEvidenceVerified,
    effectResult,
    postClosed,
    accountabilityClosed
>>

Phases == {"IDLE", "RESERVED", "INTENT", "UNKNOWN", "COMMITTED", "REJECTED", "RECONCILED", "CANCELLED"}
TerminalPhases == {"COMMITTED", "REJECTED", "RECONCILED"}
EffectResults == {"NONE", "UNKNOWN", "COMMITTED", "REJECTED"}

BaseReadiness ==
    requestValid
    /\ preTraceClosed
    /\ preObligationsDischarged
    /\ nativePermit
    /\ nativeBindingExact
    /\ requiredApprovalsPresent
    /\ boundaryActive
    /\ nativeAuthorizationVerified
    /\ concurrentGuardsActive
    /\ revocationClear

ActionReadyAtReservation == BaseReadiness /\ ~nonceConsumed
ActionReadyAtDispatch == BaseReadiness /\ nonceConsumed

Init ==
    /\ requestValid \in BOOLEAN
    /\ preTraceClosed \in BOOLEAN
    /\ preObligationsDischarged \in BOOLEAN
    /\ nativePermit \in BOOLEAN
    /\ nativeBindingExact \in BOOLEAN
    /\ requiredApprovalsPresent \in BOOLEAN
    /\ boundaryActive \in BOOLEAN
    /\ nativeAuthorizationVerified \in BOOLEAN
    /\ concurrentGuardsActive \in BOOLEAN
    /\ postTraceClosed \in BOOLEAN
    /\ postDutiesDischarged \in BOOLEAN
    /\ challengeRouteAvailable \in BOOLEAN
    /\ reviewResolved \in BOOLEAN
    /\ concurrentGuardClosureEvidenceVerified \in BOOLEAN
    /\ revocationClear = TRUE
    /\ phase = "IDLE"
    /\ nonceConsumed = FALSE
    /\ dispatchReadinessCaptured = FALSE
    /\ reservationReadinessCaptured = FALSE
    /\ receiptVerified = FALSE
    /\ concurrentGuardClosureRecorded = FALSE
    /\ effectResult = "NONE"
    /\ postClosed = FALSE
    /\ accountabilityClosed = FALSE

Reserve ==
    /\ phase = "IDLE"
    /\ ActionReadyAtReservation
    /\ phase' = "RESERVED"
    /\ nonceConsumed' = TRUE
    /\ reservationReadinessCaptured' = TRUE
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, dispatchReadinessCaptured,
                   receiptVerified, concurrentGuardClosureRecorded,
                   concurrentGuardClosureEvidenceVerified, effectResult,
                   postClosed, accountabilityClosed>>

Dispatch ==
    /\ phase = "RESERVED"
    /\ ActionReadyAtDispatch
    /\ phase' = "INTENT"
    /\ dispatchReadinessCaptured' = TRUE
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, nonceConsumed,
                   reservationReadinessCaptured, receiptVerified,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   effectResult, postClosed, accountabilityClosed>>

CancelAfterReadinessLoss ==
    /\ phase = "RESERVED"
    /\ ~BaseReadiness
    /\ phase' = "CANCELLED"
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured,
                   receiptVerified, concurrentGuardClosureRecorded,
                   concurrentGuardClosureEvidenceVerified, effectResult,
                   postClosed, accountabilityClosed>>

Revoke ==
    /\ revocationClear
    /\ revocationClear' = FALSE
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   postTraceClosed, postDutiesDischarged, challengeRouteAvailable,
                   reviewResolved, phase, nonceConsumed, dispatchReadinessCaptured,
                   reservationReadinessCaptured, receiptVerified,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   effectResult, postClosed, accountabilityClosed>>

TargetCommit ==
    /\ phase = "INTENT"
    /\ phase' = "COMMITTED"
    /\ receiptVerified' = TRUE
    /\ effectResult' = "COMMITTED"
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   postClosed, accountabilityClosed>>

TargetReject ==
    /\ phase = "INTENT"
    /\ phase' = "REJECTED"
    /\ receiptVerified' = TRUE
    /\ effectResult' = "REJECTED"
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   postClosed, accountabilityClosed>>

LoseReceipt ==
    /\ phase = "INTENT"
    /\ phase' = "UNKNOWN"
    /\ receiptVerified' = FALSE
    /\ effectResult' = "UNKNOWN"
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   postClosed, accountabilityClosed>>

ConcurrentGuardLost ==
    /\ phase = "INTENT"
    /\ concurrentGuardsActive
    /\ concurrentGuardsActive' = FALSE
    /\ phase' = "UNKNOWN"
    /\ receiptVerified' = FALSE
    /\ effectResult' = "UNKNOWN"
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, revocationClear,
                   postTraceClosed, postDutiesDischarged, challengeRouteAvailable,
                   reviewResolved, nonceConsumed, dispatchReadinessCaptured,
                   reservationReadinessCaptured, concurrentGuardClosureRecorded,
                   concurrentGuardClosureEvidenceVerified, postClosed, accountabilityClosed>>

ReconcileCommit ==
    /\ phase = "UNKNOWN"
    /\ phase' = "RECONCILED"
    /\ receiptVerified' = TRUE
    /\ effectResult' = "COMMITTED"
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   postClosed, accountabilityClosed>>

ReconcileReject ==
    /\ phase = "UNKNOWN"
    /\ phase' = "RECONCILED"
    /\ receiptVerified' = TRUE
    /\ effectResult' = "REJECTED"
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   postClosed, accountabilityClosed>>

RecordConcurrentGuardClosure ==
    /\ phase \in TerminalPhases
    /\ concurrentGuardClosureEvidenceVerified
    /\ ~concurrentGuardClosureRecorded
    /\ concurrentGuardClosureRecorded' = TRUE
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, phase, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured, receiptVerified,
                   concurrentGuardClosureEvidenceVerified, effectResult,
                   postClosed, accountabilityClosed>>

ClosePost ==
    /\ phase \in TerminalPhases
    /\ dispatchReadinessCaptured
    /\ receiptVerified
    /\ concurrentGuardClosureRecorded
    /\ postTraceClosed
    /\ postDutiesDischarged
    /\ challengeRouteAvailable
    /\ postClosed' = TRUE
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, phase, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured, receiptVerified,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   effectResult, accountabilityClosed>>

CloseAccountability ==
    /\ postClosed
    /\ challengeRouteAvailable
    /\ reviewResolved
    /\ accountabilityClosed' = TRUE
    /\ UNCHANGED <<requestValid, preTraceClosed, preObligationsDischarged,
                   nativePermit, nativeBindingExact, requiredApprovalsPresent,
                   boundaryActive, nativeAuthorizationVerified, concurrentGuardsActive,
                   revocationClear, postTraceClosed, postDutiesDischarged,
                   challengeRouteAvailable, reviewResolved, phase, nonceConsumed,
                   dispatchReadinessCaptured, reservationReadinessCaptured, receiptVerified,
                   concurrentGuardClosureRecorded, concurrentGuardClosureEvidenceVerified,
                   effectResult, postClosed>>

Next ==
    \/ Reserve
    \/ Dispatch
    \/ CancelAfterReadinessLoss
    \/ Revoke
    \/ TargetCommit
    \/ TargetReject
    \/ LoseReceipt
    \/ ConcurrentGuardLost
    \/ ReconcileCommit
    \/ ReconcileReject
    \/ RecordConcurrentGuardClosure
    \/ ClosePost
    \/ CloseAccountability

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ requestValid \in BOOLEAN
    /\ preTraceClosed \in BOOLEAN
    /\ preObligationsDischarged \in BOOLEAN
    /\ nativePermit \in BOOLEAN
    /\ nativeBindingExact \in BOOLEAN
    /\ requiredApprovalsPresent \in BOOLEAN
    /\ boundaryActive \in BOOLEAN
    /\ nativeAuthorizationVerified \in BOOLEAN
    /\ concurrentGuardsActive \in BOOLEAN
    /\ revocationClear \in BOOLEAN
    /\ postTraceClosed \in BOOLEAN
    /\ postDutiesDischarged \in BOOLEAN
    /\ challengeRouteAvailable \in BOOLEAN
    /\ reviewResolved \in BOOLEAN
    /\ phase \in Phases
    /\ nonceConsumed \in BOOLEAN
    /\ dispatchReadinessCaptured \in BOOLEAN
    /\ reservationReadinessCaptured \in BOOLEAN
    /\ receiptVerified \in BOOLEAN
    /\ concurrentGuardClosureRecorded \in BOOLEAN
    /\ concurrentGuardClosureEvidenceVerified \in BOOLEAN
    /\ effectResult \in EffectResults
    /\ postClosed \in BOOLEAN
    /\ accountabilityClosed \in BOOLEAN

NoReserveWithoutActionReady ==
    phase = "IDLE" \/ (phase # "IDLE" => reservationReadinessCaptured /\ nonceConsumed)

NoDispatchWithoutCapturedReadiness ==
    phase \in (TerminalPhases \cup {"INTENT", "UNKNOWN"}) => dispatchReadinessCaptured

NoEffectWithoutDispatchIntent ==
    phase \in (TerminalPhases \cup {"UNKNOWN"}) => dispatchReadinessCaptured /\ nonceConsumed

NoFalseTerminalReceipt ==
    phase \in TerminalPhases => receiptVerified

UnknownHasNoVerifiedReceipt ==
    phase = "UNKNOWN" => ~receiptVerified

PostClosureRequiresGuardClosure ==
    postClosed => concurrentGuardClosureRecorded

PostClosureSoundness ==
    postClosed => phase \in TerminalPhases
                 /\ dispatchReadinessCaptured
                 /\ receiptVerified
                 /\ concurrentGuardClosureRecorded
                 /\ postTraceClosed
                 /\ postDutiesDischarged
                 /\ challengeRouteAvailable

AccountabilityClosureSoundness ==
    accountabilityClosed => postClosed /\ challengeRouteAvailable /\ reviewResolved

NonceIsNotReused ==
    nonceConsumed => phase # "IDLE"

=============================================================================
