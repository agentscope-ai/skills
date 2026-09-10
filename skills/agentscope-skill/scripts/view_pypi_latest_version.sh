#!/usr/bin/env bash
# Report PyPI release metadata, independently of the installed SDK version.
set -euo pipefail

curl --fail --silent --show-error --location --max-time 30 \
  https://pypi.org/pypi/agentscope/json |
  python3 -c 'import json, sys; print(json.load(sys.stdin)["info"]["version"])'
