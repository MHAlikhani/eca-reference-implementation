---------------- MODULE ECA_Distributed_Crash_Model ----------------
EXTENDS Naturals, FiniteSets, TLC

(***************************************************************************)
(* ECA crash/restart and distributed enforcement model.                    *)
(* Abstract single-action protocol with multiple PEPs and workers,         *)
(* cumulative revocation-generation watermarks (not delta events),        *)
(* asynchronous delivery, durable replay reservation,                     *)
(* worker fencing, and target-side idempotency.                             *)
(* This is a finite research model, not a production-system proof.          *)
(***************************************************************************)

CONSTANTS Workers, PEPs, Digests, PolicyVersions, Nonces,
          NoDigest, NoPolicy, NoNonce, MaxRevocationSeq

ASSUME /\ Workers # {} /\ PEPs # {} /\ Digests # {}
       /\ PolicyVersions # {} /\ Nonces # {}
       /\ NoDigest \notin Digests /\ NoPolicy \notin PolicyVersions
       /\ NoNonce \notin Nonces /\ MaxRevocationSeq \in Nat

AuthStates == {"NONE", "PERMITTED", "REVOKED", "DENIED"}
Phases == {"IDLE", "RESERVED", "DISPATCH_INTENT", "TARGET_APPLIED", "RECEIPT_STORED", "UNKNOWN", "ABORTED"}

VARIABLES
  requestDigest, requestPolicy, requestNonce,
  authDigest, authPolicy, authState,
  phase, durableNonceSet, durableDigest, durablePolicy,
  durableFence, fencingEpoch, workerOnline, workerEpoch,
  pepSeenSeq, globalRevocationSeq, pendingRevocationMsgs,
  dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence,
  targetAppliedKeys, targetReceiptPresent, targetReceiptDigest,
  targetReceiptNonce, recoveryCount

vars == <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
          authState, phase, durableNonceSet, durableDigest, durablePolicy,
          durableFence, fencingEpoch, workerOnline, workerEpoch, pepSeenSeq,
          globalRevocationSeq, pendingRevocationMsgs, dispatchWorker,
          dispatchPEP, dispatchSeq, dispatchFence, targetAppliedKeys,
          targetReceiptPresent, targetReceiptDigest, targetReceiptNonce,
          recoveryCount>>

IdempotencyKey == <<requestDigest, requestNonce>>
AllPEPsCurrent == \A p \in PEPs : pepSeenSeq[p] = globalRevocationSeq

Init ==
  /\ requestDigest \in Digests
  /\ requestPolicy \in PolicyVersions
  /\ requestNonce \in Nonces
  /\ authDigest = NoDigest /\ authPolicy = NoPolicy /\ authState = "NONE"
  /\ phase = "IDLE"
  /\ durableNonceSet = {}
  /\ durableDigest = NoDigest /\ durablePolicy = NoPolicy
  /\ durableFence = 0 /\ fencingEpoch = 0
  /\ workerOnline = [w \in Workers |-> TRUE]
  /\ workerEpoch = [w \in Workers |-> 0]
  /\ pepSeenSeq = [p \in PEPs |-> 0]
  /\ globalRevocationSeq = 0
  /\ pendingRevocationMsgs = {}
  /\ dispatchWorker = CHOOSE w \in Workers : TRUE
  /\ dispatchPEP = CHOOSE p \in PEPs : TRUE
  /\ dispatchSeq = 0 /\ dispatchFence = 0
  /\ targetAppliedKeys = {}
  /\ targetReceiptPresent = FALSE
  /\ targetReceiptDigest = NoDigest /\ targetReceiptNonce = NoNonce
  /\ recoveryCount = 0

PresentAuthorization(d, pv) ==
  /\ authState = "NONE" /\ authDigest = NoDigest
  /\ d \in Digests /\ pv \in PolicyVersions
  /\ authDigest' = d /\ authPolicy' = pv
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authState, phase,
      durableNonceSet, durableDigest, durablePolicy, durableFence, fencingEpoch,
      workerOnline, workerEpoch, pepSeenSeq, globalRevocationSeq, pendingRevocationMsgs,
      dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence, targetAppliedKeys,
      targetReceiptPresent, targetReceiptDigest, targetReceiptNonce, recoveryCount>>

Permit ==
  /\ authState = "NONE" /\ authDigest = requestDigest /\ authPolicy = requestPolicy
  /\ authState' = "PERMITTED"
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy, phase,
      durableNonceSet, durableDigest, durablePolicy, durableFence, fencingEpoch,
      workerOnline, workerEpoch, pepSeenSeq, globalRevocationSeq, pendingRevocationMsgs,
      dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence, targetAppliedKeys,
      targetReceiptPresent, targetReceiptDigest, targetReceiptNonce, recoveryCount>>

Revoke ==
  /\ authState \in {"PERMITTED", "REVOKED"} /\ phase \in {"IDLE", "RESERVED", "DISPATCH_INTENT"}
  /\ globalRevocationSeq < MaxRevocationSeq
  /\ globalRevocationSeq' = globalRevocationSeq + 1
  /\ pendingRevocationMsgs' = pendingRevocationMsgs \cup
       {[pep |-> p, seq |-> globalRevocationSeq + 1] : p \in PEPs}
  /\ authState' = "REVOKED"
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy, phase,
      durableNonceSet, durableDigest, durablePolicy, durableFence, fencingEpoch,
      workerOnline, workerEpoch, pepSeenSeq, dispatchWorker, dispatchPEP, dispatchSeq,
      dispatchFence, targetAppliedKeys, targetReceiptPresent, targetReceiptDigest,
      targetReceiptNonce, recoveryCount>>

(* A higher sequence is a cumulative generation barrier: accepting n means *)
(* every authorization/dispatch from a generation below n is stale.        *)
DeliverRevocation(p) ==
  /\ p \in PEPs
  /\ \E m \in pendingRevocationMsgs : m.pep = p
  /\ LET msg == CHOOSE m \in pendingRevocationMsgs : m.pep = p
     IN /\ pepSeenSeq' = [pepSeenSeq EXCEPT ![p] = IF @ > msg.seq THEN @ ELSE msg.seq]
        /\ pendingRevocationMsgs' = pendingRevocationMsgs \ {msg}
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, phase, durableNonceSet, durableDigest, durablePolicy, durableFence,
      fencingEpoch, workerOnline, workerEpoch, globalRevocationSeq, dispatchWorker,
      dispatchPEP, dispatchSeq, dispatchFence, targetAppliedKeys, targetReceiptPresent,
      targetReceiptDigest, targetReceiptNonce, recoveryCount>>

Reserve(w) ==
  /\ w \in Workers /\ workerOnline[w]
  /\ authState = "PERMITTED" /\ phase = "IDLE"
  /\ authDigest = requestDigest /\ authPolicy = requestPolicy
  /\ pepSeenSeq[dispatchPEP] = globalRevocationSeq
  /\ requestNonce \notin durableNonceSet
  /\ durableNonceSet' = durableNonceSet \cup {requestNonce}
  /\ durableDigest' = requestDigest /\ durablePolicy' = requestPolicy
  /\ durableFence' = fencingEpoch
  /\ phase' = "RESERVED"
  /\ dispatchWorker' = w
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, fencingEpoch, workerOnline, workerEpoch, pepSeenSeq,
      globalRevocationSeq, pendingRevocationMsgs, dispatchPEP, dispatchSeq,
      dispatchFence, targetAppliedKeys, targetReceiptPresent, targetReceiptDigest,
      targetReceiptNonce, recoveryCount>>

PersistDispatchIntent ==
  /\ phase = "RESERVED" /\ authState = "PERMITTED"
  /\ workerOnline[dispatchWorker]
  /\ pepSeenSeq[dispatchPEP] = globalRevocationSeq
  /\ durableDigest = requestDigest /\ durablePolicy = requestPolicy
  /\ durableFence = fencingEpoch
  /\ phase' = "DISPATCH_INTENT"
  /\ dispatchSeq' = globalRevocationSeq
  /\ dispatchFence' = fencingEpoch
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, durableNonceSet, durableDigest, durablePolicy, durableFence,
      fencingEpoch, workerOnline, workerEpoch, pepSeenSeq, globalRevocationSeq,
      pendingRevocationMsgs, dispatchWorker, dispatchPEP, targetAppliedKeys,
      targetReceiptPresent, targetReceiptDigest, targetReceiptNonce, recoveryCount>>

TargetApply ==
  /\ phase = "DISPATCH_INTENT"
  /\ dispatchFence = fencingEpoch
  /\ workerOnline[dispatchWorker]
  /\ workerEpoch[dispatchWorker] = dispatchFence
  /\ dispatchSeq = pepSeenSeq[dispatchPEP]
  /\ dispatchSeq = globalRevocationSeq
  /\ IdempotencyKey \notin targetAppliedKeys
  /\ targetAppliedKeys' = targetAppliedKeys \cup {IdempotencyKey}
  /\ phase' = "TARGET_APPLIED"
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, durableNonceSet, durableDigest, durablePolicy, durableFence,
      fencingEpoch, workerOnline, workerEpoch, pepSeenSeq, globalRevocationSeq,
      pendingRevocationMsgs, dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence,
      targetReceiptPresent, targetReceiptDigest, targetReceiptNonce, recoveryCount>>

PersistReceipt ==
  /\ phase = "TARGET_APPLIED"
  /\ targetReceiptPresent' = TRUE
  /\ targetReceiptDigest' = requestDigest
  /\ targetReceiptNonce' = requestNonce
  /\ phase' = "RECEIPT_STORED"
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, durableNonceSet, durableDigest, durablePolicy, durableFence,
      fencingEpoch, workerOnline, workerEpoch, pepSeenSeq, globalRevocationSeq,
      pendingRevocationMsgs, dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence,
      targetAppliedKeys, recoveryCount>>

Crash(w) ==
  /\ w \in Workers /\ workerOnline[w]
  /\ workerOnline' = [workerOnline EXCEPT ![w] = FALSE]
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, phase, durableNonceSet, durableDigest, durablePolicy, durableFence,
      fencingEpoch, workerEpoch, pepSeenSeq, globalRevocationSeq, pendingRevocationMsgs,
      dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence, targetAppliedKeys,
      targetReceiptPresent, targetReceiptDigest, targetReceiptNonce, recoveryCount>>

Restart(w) ==
  /\ w \in Workers /\ ~workerOnline[w]
  /\ fencingEpoch' = fencingEpoch + 1
  /\ workerOnline' = [workerOnline EXCEPT ![w] = TRUE]
  /\ workerEpoch' = [workerEpoch EXCEPT ![w] = fencingEpoch + 1]
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, phase, durableNonceSet, durableDigest, durablePolicy, durableFence,
      pepSeenSeq, globalRevocationSeq, pendingRevocationMsgs, dispatchWorker,
      dispatchPEP, dispatchSeq, dispatchFence, targetAppliedKeys, targetReceiptPresent,
      targetReceiptDigest, targetReceiptNonce, recoveryCount>>

Recover ==
  /\ phase \in {"RESERVED", "DISPATCH_INTENT", "TARGET_APPLIED"}
  /\ recoveryCount' = recoveryCount + 1
  /\ IF IdempotencyKey \in targetAppliedKeys
        THEN /\ phase' = "UNKNOWN"
             /\ targetReceiptPresent' = FALSE
        ELSE /\ phase' = "ABORTED"
             /\ targetReceiptPresent' = FALSE
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, durableNonceSet, durableDigest, durablePolicy, durableFence,
      fencingEpoch, workerOnline, workerEpoch, pepSeenSeq, globalRevocationSeq,
      pendingRevocationMsgs, dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence,
      targetAppliedKeys, targetReceiptDigest, targetReceiptNonce>>

Reconcile ==
  /\ phase = "UNKNOWN" /\ IdempotencyKey \in targetAppliedKeys
  /\ targetReceiptPresent' = TRUE
  /\ targetReceiptDigest' = requestDigest
  /\ targetReceiptNonce' = requestNonce
  /\ phase' = "RECEIPT_STORED"
  /\ UNCHANGED <<requestDigest, requestPolicy, requestNonce, authDigest, authPolicy,
      authState, durableNonceSet, durableDigest, durablePolicy, durableFence,
      fencingEpoch, workerOnline, workerEpoch, pepSeenSeq, globalRevocationSeq,
      pendingRevocationMsgs, dispatchWorker, dispatchPEP, dispatchSeq, dispatchFence,
      targetAppliedKeys, recoveryCount>>

Next ==
  \/ \E d \in Digests, pv \in PolicyVersions : PresentAuthorization(d, pv)
  \/ Permit \/ Revoke
  \/ \E p \in PEPs : DeliverRevocation(p)
  \/ \E w \in Workers : Reserve(w)
  \/ PersistDispatchIntent \/ TargetApply \/ PersistReceipt
  \/ \E w \in Workers : Crash(w)
  \/ \E w \in Workers : Restart(w)
  \/ Recover \/ Reconcile

TypeOK ==
  /\ requestDigest \in Digests /\ requestPolicy \in PolicyVersions /\ requestNonce \in Nonces
  /\ authDigest \in Digests \cup {NoDigest}
  /\ authPolicy \in PolicyVersions \cup {NoPolicy}
  /\ authState \in AuthStates /\ phase \in Phases
  /\ durableNonceSet \subseteq Nonces
  /\ durableDigest \in Digests \cup {NoDigest}
  /\ durablePolicy \in PolicyVersions \cup {NoPolicy}
  /\ durableFence \in Nat /\ fencingEpoch \in Nat
  /\ workerOnline \in [Workers -> BOOLEAN]
  /\ workerEpoch \in [Workers -> Nat]
  /\ pepSeenSeq \in [PEPs -> Nat]
  /\ globalRevocationSeq \in Nat
  /\ pendingRevocationMsgs \subseteq [pep : PEPs, seq : Nat]
  /\ dispatchWorker \in Workers /\ dispatchPEP \in PEPs
  /\ dispatchSeq \in Nat /\ dispatchFence \in Nat
  /\ targetAppliedKeys \subseteq {IdempotencyKey}
  /\ targetReceiptPresent \in BOOLEAN
  /\ targetReceiptDigest \in Digests \cup {NoDigest}
  /\ targetReceiptNonce \in Nonces \cup {NoNonce}
  /\ recoveryCount \in Nat

NoEffectWithoutDurableIntent ==
  targetAppliedKeys # {} => phase \in {"TARGET_APPLIED", "RECEIPT_STORED", "UNKNOWN"}

AtMostOneTargetEffect == Cardinality(targetAppliedKeys) <= 1

NoTargetEffectWithoutReservation ==
  targetAppliedKeys # {} => requestNonce \in durableNonceSet

NoReceiptWithoutTargetEffect ==
  targetReceiptPresent => /\ IdempotencyKey \in targetAppliedKeys
                           /\ targetReceiptDigest = requestDigest
                           /\ targetReceiptNonce = requestNonce

DispatchFenceNeverFromFuture == dispatchFence <= fencingEpoch

NoPermitWithoutExactBinding ==
  authState = "PERMITTED" => /\ authDigest = requestDigest
                              /\ authPolicy = requestPolicy

DispatchSequenceNeverFromFuture == dispatchSeq <= globalRevocationSeq

PEPWatermarksNeverFromFuture == \A p \in PEPs : pepSeenSeq[p] <= globalRevocationSeq

NonceDurablyReserved == phase \in {"RESERVED", "DISPATCH_INTENT", "TARGET_APPLIED", "UNKNOWN", "RECEIPT_STORED"}
                         => requestNonce \in durableNonceSet


(***************************************************************************)
(* Stage 6 strengthening candidates. These are state invariants, not        *)
(* claims that SANY/TLC has executed. They are deliberately conservative.   *)
(***************************************************************************)
DurableBindingMatchesRequest ==
  phase \in {"RESERVED", "DISPATCH_INTENT", "TARGET_APPLIED", "UNKNOWN", "RECEIPT_STORED"}
    => /\ durableDigest = requestDigest
       /\ durablePolicy = requestPolicy

TargetEffectHasDurableBinding ==
  targetAppliedKeys # {}
    => /\ requestNonce \in durableNonceSet
       /\ durableDigest = requestDigest
       /\ durablePolicy = requestPolicy
       /\ phase \in {"TARGET_APPLIED", "UNKNOWN", "RECEIPT_STORED"}

ReceiptPhaseConsistency ==
  targetReceiptPresent => phase = "RECEIPT_STORED"

ReceiptStoredHasTargetReceipt ==
  phase = "RECEIPT_STORED" => targetReceiptPresent

WorkerEpochsBoundedByFence ==
  \A w \in Workers : workerEpoch[w] <= fencingEpoch

DispatchIntentMatchesDurableFence ==
  phase \in {"DISPATCH_INTENT", "TARGET_APPLIED", "UNKNOWN", "RECEIPT_STORED"}
    => dispatchFence = durableFence

AuthorizationBindingStable ==
  authState \in {"PERMITTED", "REVOKED"}
    => /\ authDigest = requestDigest
       /\ authPolicy = requestPolicy

Spec == Init /\ [][Next]_vars

===========================================================