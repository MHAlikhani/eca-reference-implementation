# Optional external TLA+ tools

This repository does not bundle `tla2tools.jar`. The model runner expects the official stable TLA+ Tools v1.7.4 JAR with the upstream-published SHA-1 checksum pinned in `scripts/run_tla.sh`. The SHA-1 comparison is for matching the published artifact identity; it is not a cryptographic signature or an independent authenticity proof.

As checked on 18 November 2026, the upstream releases page lists v1.8.0 as a pre-release and v1.7.4 as the preceding stable release. The upstream use guide states that Java 11 or newer is required and documents SANY and TLC command-line invocations. Use the command-line tools or the maintained TLA+ editor extension; the TLA+ Toolbox is no longer actively maintained.

To run with an already downloaded/pinned JAR:

```bash
TLA2TOOLS_JAR=/absolute/path/to/tla2tools.jar bash scripts/run_tla.sh
```

The script verifies the pinned checksum, runs SANY, then TLC using `tla/ECA_Lifecycle.cfg`. Raw stdout/stderr should be archived in `reports/`. Do not mark formal parsing or model checking complete unless both tool runs exit successfully and the resulting logs are retained.
