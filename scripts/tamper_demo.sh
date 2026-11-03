#!/usr/bin/env bash
# Simulates a swapped/compromised artifact: corrupts boto3's hashes in a copy of
# the lock and shows that a hash-checked install refuses it.
set -euo pipefail
cd "$(dirname "$0")/.."

tmp=$(mktemp -d)
sed -E '/^boto3==/,/# via/ s/(--hash=sha256:)[0-9a-f]{8}/\1deadbeef/' requirements.txt > "$tmp/tampered.txt"

echo "== Tampered boto3 entry =="
sed -n '/^boto3==/,/# via/p' "$tmp/tampered.txt"
echo
echo "== Installing with --require-hashes (expected to FAIL) =="
python -m venv "$tmp/venv"
if "$tmp/venv/bin/pip" install --no-cache-dir --require-hashes -r "$tmp/tampered.txt"; then
  echo "UNEXPECTED: install succeeded"; exit 1
else
  echo; echo "Blocked: pip detected the hash mismatch and installed nothing."
fi
rm -rf "$tmp"
