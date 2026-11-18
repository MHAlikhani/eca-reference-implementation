# TLA+ execution and verification status

**Model:** `tla/ECA_Lifecycle.tla`  
**Configuration:** `tla/ECA_Lifecycle.cfg`  
**Lineage:** revision 1 (new model line; not historical revision v4)  
**Assessment date:** 18 November 2026

## Official tool selection

The official TLA+ releases page lists v1.8.0 (Clarke) as a pre-release and v1.7.4 (Xenophanes) as the preceding stable release. The project pins the official v1.7.4 `tla2tools.jar` using the upstream-published SHA-1:

```text
bee4a54f3ee3d4afc347c3240ec2d9e93b075104  tla2tools.jar
```

The SHA-1 comparison is an artifact-identity check against the upstream release listing, not a digital signature or independent authenticity proof. The official repository documents Java 11+ and command-line invocations for SANY (`tla2sany.SANY`) and TLC (`tlc2.TLC`). The local environment has OpenJDK 21.0.12.1.

Upstream sources:

- https://github.com/tlaplus/tlaplus/releases
- https://github.com/tlaplus/tlaplus/blob/master/USE.md

## Official execution attempt

The exact command `bash scripts/run_tla.sh` was executed after the lexical audit. It exited with code **2** because `tools/tla2tools.jar` was absent. A filesystem search found no `tla2tools.jar`, SANY, TLC, or Apalache binary. Network access from the container is unavailable (`curl` could not resolve `github.com`); the official binary download endpoint was also inaccessible through the web retrieval path.

| Step | Result | Explanation |
|---|---|---|
| Lexical delimiter/comment/action-frame sanity | PASS | Custom repository check only |
| TLC configuration identifier cross-check | PASS | Static textual cross-check of `Spec` and ten invariant names |
| Official SANY parser | **NOT RUN — BLOCKED** | Pinned official JAR could not be obtained |
| Official TLC model checker | **NOT RUN — BLOCKED** | Runner stops before SANY because pinned JAR is unavailable |

Raw evidence: `reports/tla-official-run.log`, `reports/tla-official-run-exit-code.txt`.

## Alternative finite-state check completed

Because the official tool binary could not be obtained, `scripts/run_explicit_state_check.py` was implemented and executed. It exhaustively explored all 16,384 valuations of the 14 unconstrained Boolean inputs in `Init`, checked 33,668 reachable states and 17,702 transitions, and verified all ten selected safety invariants in an independent Python mirror. It also cross-checked all 13 action names in the TLA+ `Next` operator and the ten configured invariant names.

Result: **PASS for the mirrored finite-state transition system**. See `reports/ALTERNATIVE_MODEL_CHECK_REPORT.md` and raw output `reports/explicit-state-check.log`.

This alternative is not SANY, not TLC, not a TLA+ parser, and not a refinement proof. It does not prove that the Python mirror is semantically equivalent to the TLA+ module. It must not be reported as official TLA+ verification.

## Model scope and abstraction boundaries

The model captures PRE readiness, native permit and exact request binding, reservation and nonce consumption, a second readiness guard before dispatch intent, revocation/cancellation before dispatch, uncertain target outcomes, reconciliation, concurrent-guard closure, POST closure, and accountability closure.

It abstracts cryptographic signatures, real key custody, native PDP/PEP implementations, distributed clocks, network partitions, database internals, target physics, legal/institutional legitimacy, and continuous correctness of runtime guards. The boolean `concurrentGuardClosureEvidenceVerified` is an abstract trusted input; neither TLC nor the Python mirror validates its signature or the physical correctness of the guard. A refinement relation and trace-correspondence study remain necessary before claiming that the Python implementation refines this abstraction.

## CI status

The local CI-equivalent pipeline passed on Python 3.13.5, including 102 tests, 82% total coverage, schema/example checks, wheel build and isolated wheel CLI smoke test, workflow YAML parsing, static TLA checks, and the alternative exhaustive finite-state check. The GitHub Actions workflow is present but has not run on a hosted GitHub runner; the five-version Python matrix has not been exercised locally. See `reports/CI_EXECUTION_REPORT.md`.

## Remaining official gate

To complete the official TLA+ gate, obtain the pinned v1.7.4 JAR in a network-enabled CI runner, verify its checksum, run SANY and TLC against these exact files, and retain their raw output and TLC state statistics. The workflow in `.github/workflows/verification.yml` is configured to do this after push to a connected GitHub repository.
