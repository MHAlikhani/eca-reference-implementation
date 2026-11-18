#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="$ROOT/tla/ECA_Lifecycle.tla"
CONFIG="$ROOT/tla/ECA_Lifecycle.cfg"
JAR="${TLA2TOOLS_JAR:-$ROOT/tools/tla2tools.jar}"
# Official stable TLA+ Tools v1.7.4 artifact checksum published upstream.
# SHA-1 is used only to match the upstream release checksum, not as a signature.
EXPECTED_SHA1="bee4a54f3ee3d4afc347c3240ec2d9e93b075104"

python "$ROOT/scripts/audit_tla_lexically.py" "$MODEL"
if [[ ! -f "$JAR" ]]; then
  echo "BLOCKED: tla2tools.jar not found at $JAR" >&2
  echo "Obtain official stable TLA+ Tools v1.7.4 (the upstream page also lists v1.8.0 as a pre-release) and set TLA2TOOLS_JAR." >&2
  exit 2
fi
ACTUAL_SHA1="$(sha1sum "$JAR" | awk '{print $1}')"
if [[ "$ACTUAL_SHA1" != "$EXPECTED_SHA1" ]]; then
  echo "BLOCKED: tla2tools.jar SHA-1 mismatch (expected $EXPECTED_SHA1, got $ACTUAL_SHA1)" >&2
  exit 3
fi
JAVA_MAJOR="$(java -version 2>&1 | awk -F '"' '/version/ {split($2,a,"."); if (a[1]=="1") print a[2]; else print a[1]; exit}')"
if [[ -z "$JAVA_MAJOR" || "$JAVA_MAJOR" -lt 11 ]]; then
  echo "BLOCKED: Java 11 or newer is required (detected ${JAVA_MAJOR:-unknown})" >&2
  exit 4
fi
cd "$ROOT/tla"
echo "SANY parse started: $(date -u +%FT%TZ)"
java -cp "$JAR" tla2sany.SANY "$MODEL"
echo "SANY parse completed: $(date -u +%FT%TZ)"
echo "TLC model check started: $(date -u +%FT%TZ)"
java -XX:+UseParallelGC -cp "$JAR" tlc2.TLC -workers auto -config "$CONFIG" "$MODEL"
echo "TLC model check completed: $(date -u +%FT%TZ)"
