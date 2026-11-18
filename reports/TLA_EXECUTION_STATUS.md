# TLA+ execution and verification status

**Model:** tla/ECA_Lifecycle.tla  
**Configuration:** tla/ECA_Lifecycle.cfg  
**Lineage:** revision 1 (new model line; not historical revision v4)  
**Official status:** **SANY PASS · TLC PASS**  
**Execution date:** 18 November 2026

## Hosted execution record

- GitHub Actions run #2: https://github.com/MHAlikhani/eca-reference-implementation/actions/runs/44391171960
- Source commit: b9c760d280993c760091af5f1ed705038e8cf80d
- Job ID: 135108908582
- Artifact ID: 14469505467
- Artifact ZIP SHA-256: aceacbca35a41ecdc4b0181a0bb87a4281bb625473832e739bb6a623212c292c

The runner downloaded official TLA+ Tools v1.7.4; the pinned checksum passed:
    bee4a54f3ee3d4afc347c3240ec2d9e93b075104  tools/tla2tools.jar
    tools/tla2tools.jar: OK

Java: OpenJDK 21.0.13. SANY 2.1. TLC 2.19 (08 August 2024, revision 5a47802).

## SANY

**PASS.** SANY parsed tla/ECA_Lifecycle.tla and completed semantic processing of ECA_Lifecycle.

## TLC

**PASS.** TLC completed breadth-first model checking with four workers:

| Metric | Result |
|---|---:|
| Initial states | 16,384 |
| Generated states | 34,086 |
| Distinct states | 33,668 |
| States remaining in queue | 0 |
| State graph depth | 9 |
| Configured safety invariants | 10 |
| Result | No error found |

The ten configured invariants are TypeOK, NoReserveWithoutActionReady, PostClosureRequiresGuardClosure, NoDispatchWithoutCapturedReadiness, NoEffectWithoutDispatchIntent, NoFalseTerminalReceipt, UnknownHasNoVerifiedReceipt, PostClosureSoundness, AccountabilityClosureSoundness, and NonceIsNotReused.

## Scope and limits

- CHECK_DEADLOCK FALSE is set; this run does not establish absence of deadlocks.
- The run does not establish liveness, fairness, availability, or progress under fairness assumptions.
- The model abstracts signatures, key custody, native PDP/PEP implementations, distributed clocks, database internals, target physics, and institutional legitimacy.
- concurrentGuardClosureEvidenceVerified is an abstract input; TLC does not validate its signature or prove continuous operation of a real guard.
- No Python-to-TLA refinement relation or trace-correspondence proof is claimed.
- This is a bounded model-check result for revision 1, not proof of production safety or of historical revision v4.

The independent Python mirror check is supplementary only. The local author's container lacked tla2tools.jar; its historical blocked logs are retained under reports/tla-local-*.
