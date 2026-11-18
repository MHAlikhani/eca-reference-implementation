# Alternative exhaustive finite-state model-check report

**Model source:** `tla/ECA_Lifecycle.tla`  
**TLC configuration:** `tla/ECA_Lifecycle.cfg`  
**Independent checker:** `scripts/run_explicit_state_check.py`  
**Run date:** 18 November 2026  
**Status:** PASS for the mirrored finite-state transition system; official SANY/TLC remain blocked.

## Why this alternative was used

The authoring runtime has Java 21 but no local `tla2tools.jar`. DNS/network access to GitHub is unavailable (`curl` returned `Could not resolve host: github.com`). No local `tla2tools.jar`, Apalache, TLC, SANY, Docker, Podman, or `act` executable was found. The official v1.7.4 artifact URL was opened through the web research interface, but the binary download endpoint was restricted; the container download also could not obtain it. The official upstream repository documents the CLI use of `tla2sany.SANY` and `tlc2.TLC`, and the release page publishes the v1.7.4 JAR checksum. See the upstream links in `TLA_EXECUTION_STATUS.md`.

Rather than leave the lifecycle safety properties entirely untested, an independent Python checker was implemented. It enumerates every valuation of the 14 unconstrained Boolean inputs in `Init`, explores all reachable successors of the finite lifecycle transition system, and checks the ten safety invariants named in the TLC configuration. It also cross-checks the 13 action names in the Python transition mirror against the action names in the TLA+ `Next` operator, and checks invariant names against TLA+ definitions.

## Exact results

| Check | Result |
|---|---:|
| Initial Boolean valuations | 16,384 |
| Reachable states exhaustively checked | 33,668 |
| Transitions explored | 17,702 |
| Safety invariants checked | 10 / 10 |
| TLA+ `Next` actions cross-checked | 13 / 13 |
| Counterexample found in the mirrored transition system | No |

The checker exited with code 0. Raw output is retained in `reports/explicit-state-check.log`.

## What this establishes

For the independently encoded finite transition system, all reachable states from all 16,384 allowed initial Boolean valuations satisfy the ten selected safety invariants. The checker also confirms that the set of 13 transition operator names matches the current TLA+ `Next` action list and that the ten configured invariant names have corresponding definitions in the module.

## What this does not establish

This is **not** an execution of TLA+ semantics. It does not parse TLA+ grammar, type-check the TLA+ module, validate operator precedence or substitution semantics, prove that the Python mirror is semantically equivalent to the TLA+ module, establish refinement from the Python implementation, or provide liveness/fairness results. The mirror could share a modeling mistake with the source or diverge in an expression-level detail that action-name matching cannot detect. The alternative check must not be described as SANY success, TLC success, or formal verification of the TLA+ module.

## Completion gate

The alternative finite-state safety check is complete for its stated scope. The official TLA+ gate remains open until the pinned official `tla2tools.jar` can be obtained and both SANY and TLC are run successfully on the exact `.tla` and `.cfg` files. This environment has no route to retrieve that binary. The GitHub Actions workflow retains the official SANY/TLC job so it can run in a network-enabled GitHub-hosted runner after the repository is connected and pushed.
