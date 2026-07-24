#!/usr/bin/env bash
# Group-(a) code-quality gate (JN-47). Runs in CI and locally.
#   - radon: cyclomatic complexity + maintainability index (report only)
#   - xenon: HARD gate — fails if any block/module/average exceeds the threshold
# Single source of truth for the thresholds; CI calls this script.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "== radon cc (report) =="
radon cc -s -a src

echo "== radon mi (report) =="
radon mi -s src

echo "== xenon gate (hard) =="
xenon --max-absolute C --max-modules B --max-average A src

echo "OK: complexity within thresholds"
