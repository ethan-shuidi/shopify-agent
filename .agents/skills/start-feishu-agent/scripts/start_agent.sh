#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_dir/../../../.." && pwd)"
cd "$project_root"

python_bin="$project_root/.venv/bin/python"
env_file="$project_root/.env"

if [[ ! -x "$python_bin" ]]; then
  echo "Missing .venv. Create it with Python 3.11+ and install the project first." >&2
  exit 1
fi

if [[ ! -f "$env_file" ]]; then
  echo "Missing .env. Copy .env.example to .env and fill in the credentials." >&2
  exit 1
fi

duplicate_keys="$($python_bin - <<'PY'
from collections import Counter
from pathlib import Path

keys = []
for raw_line in Path('.env').read_text(encoding='utf-8').splitlines():
    line = raw_line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    key = line.split('=', 1)[0].strip()
    if key:
        keys.append(key)

print(','.join(sorted(key for key, count in Counter(keys).items() if count > 1)))
PY
)"

if [[ -n "$duplicate_keys" ]]; then
  echo "Duplicate .env keys found: $duplicate_keys" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

required_vars=(
  FEISHU_APP_ID
  FEISHU_APP_SECRET
  AGENT_MODEL
  OPENAI_BASE_URL
  OPENAI_API_KEY
)

for variable_name in "${required_vars[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "Missing required setting: $variable_name" >&2
    exit 1
  fi
done

ca_bundle="$($python_bin -m certifi)"
export SSL_CERT_FILE="$ca_bundle"
export REQUESTS_CA_BUNDLE="$ca_bundle"

echo "Starting Feishu Agent from $project_root"
exec "$python_bin" -m app.main
