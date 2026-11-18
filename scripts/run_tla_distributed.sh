#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="$ROOT/tla/ECA_Distributed_Crash_Model.tla"
CONFIG="$ROOT/tla/ECA_Distributed_Crash_Model.cfg"
JAR="${TLA2TOOLS_JAR:-$ROOT/tools/tla2tools.jar}"
EXPECTED_SHA1="bee4a54f3ee3d4afc347c3240ec2d9e93b075104"
if [[ ! -f "$JAR" ]]; then
  echo "BLOCKED: official tla2tools.jar is absent" >&2
  exit 2
fi
ACTUAL_SHA1="$(sha1sum "$JAR" | awk '{print $1}')"
if [[ "$ACTUAL_SHA1" != "$EXPECTED_SHA1" ]]; then
  echo "FAIL: tla2tools.jar SHA-1 mismatch" >&2
  exit 3
fi
JAVA_MAJOR="$(java -version 2>&1 | awk -F '"' '/version/ {split($2,a,"."); if (a[1]=="1") print a[2]; else print a[1]; exit}')"
if [[ -z "$JAVA_MAJOR" || "$JAVA_MAJOR" -lt 11 ]]; then
  echo "FAIL: Java 11+ required" >&2
  exit 4
fi
mkdir -p "$ROOT/reports"
cd "$ROOT/tla"
echo "Distributed v5 SANY parse started: $(date -u +%FT%TZ)"
java -cp "$JAR" tla2sany.SANY "$MODEL"
echo "Distributed v5 SANY parse completed: $(date -u +%FT%TZ)"
echo "Distributed v5 TLC model check started: $(date -u +%FT%TZ)"
java -XX:+UseParallelGC -cp "$JAR" tlc2.TLC -workers auto -config "$CONFIG" "$MODEL"
echo "Distributed v5 TLC model check completed: $(date -u +%FT%TZ)"
