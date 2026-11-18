# Contribution rules

This repository is maintained as a research reference. Contributions must:

1. preserve the distinction between schema validation, semantic validation, native verification and external trust;
2. include tests for positive, negative, boundary and regression behavior;
3. document any change to relation vocabulary, status semantics, canonicalization, closure predicates or state transitions;
4. avoid describing tests as proofs or local simulations as deployment evidence;
5. include exact tool versions and raw output for claimed verification results;
6. preserve `UNKNOWN` where the target effect cannot be established;
7. state any new trust assumptions and residual risks.

Changes to the canonicalization profile or normative relation vocabulary require a profile-versioning decision and new interoperability vectors; they must not be silently introduced as patch-level changes.
