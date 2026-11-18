# Reference Architecture

```text
                       ECA / ETC evaluation layer
      +----------------------------------------------------------+
      | JSON Schema -> semantic validator -> phase closure       |
      |                          |                               |
      |                          +-> RRC (diagnostic only)        |
      |                          +-> ACTION_READY evaluator      |
      |                          +-> POST / accountability       |
      +--------------------------|-------------------------------+
                                 |
            External trust inputs; evaluated, not replaced
      +--------------------------v-------------------------------+
      | Native identity/delegation | Native PDP | Trust verifier |
      | Evidence/provenance        | PEP/AEB     | Review system  |
      +--------------------------|-------------------------------+
                                 |
                  Local reference lifecycle demonstration
      +--------------------------v-------------------------------+
      | SQLite journal: RESERVED -> DISPATCH_INTENT              |
      |             -> COMMITTED / REJECTED / UNKNOWN            |
      |                         -> RECONCILED                    |
      +--------------------------|-------------------------------+
                                 |
                     SQLite target simulator
      +--------------------------v-------------------------------+
      | Idempotency key -> simulated effect -> signed test receipt|
      +----------------------------------------------------------+
```

## Module responsibilities

- `canonical.py`: strict canonical request byte representation and SHA-256 digest.
- `schema.py`: Draft 2020-12 schema checks; format strings are checked by the configured `FormatChecker`.
- `semantics.py`: relation vocabulary, node identity, endpoint kinds, time intervals, freshness, phase obligations, and outcome semantics.
- `contract.py`: public ETC validation, trace-closure, readiness, post-action and accountability evaluation.
- `delegation.py`: local HMAC demonstration of issuer continuity and attenuation.
- `journal.py`: single-host SQLite state transitions, nonce uniqueness and append-only event rows.
- `target.py` / `receipts.py`: local idempotent target simulator and test receipt verification.
- `runtime.py`: synchronous integration demonstration; no network or actuator.
- `cli.py`: command-line structural and semantic contract evaluation.

## Trust boundaries

The implementation deliberately keeps native authorization, enforcement, dispatch-attestation and target-receipt verification in their owning trust domains. The ECA layer validates declared verifier results and exact request/action/target bindings but does not invent a universal key registry. Adapters must prevent direct calls that bypass the effect boundary; this repository cannot enforce the access controls of an external deployment.
