# dep-pinning-demo

A small, runnable repo that shows **what goes wrong when Python dependencies are
unpinned** and what a hash-locked setup looks like instead. The app is a small
S3 key/value store (`boto3` + `python-dotenv`) tested with `moto` and `pytest`.

```
.
├── app/s3_store.py              # the "application"
├── tests/test_s3_store.py       # moto-backed tests
├── unpinned/requirements.txt    # ❌ the original: 5 bare names
├── requirements.in              # ✅ runtime intent (ranges, human-edited)
├── requirements.txt             # ✅ generated lock: every package + sha256 hashes
├── requirements-dev.in          # ✅ dev/test intent, constrained to runtime lock
├── requirements-dev.txt         # ✅ generated dev lock
├── scripts/show_drift.py        # resolves the unpinned file "as of" two dates
├── scripts/tamper_demo.sh       # proves --require-hashes blocks a swapped artifact
├── .github/workflows/ci.yml     # locked job, lock-freshness gate, unpinned demo
├── .github/dependabot.yml       # reviewed upgrades with a 7-day cooldown
└── Makefile
```

## Prerequisites

Python 3.12+, and [uv](https://docs.astral.sh/uv/) for locking and the drift demo:
`pip install uv` (or `pipx install uv`).

## Experiments

### 1. Five lines, ~30 packages
```bash
make unpinned
```
You wrote 5 lines, but pip installs around 30 packages. Everything you didn't
name (botocore, urllib3, s3transfer, cryptography, requests, werkzeug…) floats freely.

### 2. Drift over time (transitive deps)
```bash
make drift                                   # mid-2024 vs today
python scripts/show_drift.py 2025-01-01 2025-12-31
```
This resolves the **same unchanged file** as if `pip install` had run on each
date. Sample output (Nov 2026):

```
Resolved on 2024-06-01: 31 packages | on 2026-11-03: 32 packages
package                   kind        2024-06-01      2026-11-03
botocore                  TRANSITIVE  1.34.117        1.43.123
cryptography              TRANSITIVE  42.0.7          50.0.2
urllib3                   TRANSITIVE  2.2.1           2.8.0
s3transfer                TRANSITIVE  0.10.1          0.19.3
xmltodict                 TRANSITIVE  0.13.0          1.0.4
...
32 of 33 packages differ; 27 of those are transitive (never named in your file).
New transitive packages that appeared: pygments, pytokens
```
New packages joined the tree (and `jinja2` left it) without any commit to this repo.

### 3. Lock the full tree and install with hashes
```bash
python -m venv .venv && . .venv/bin/activate
make install        # pip install --require-hashes --no-deps -r ...
make test           # 2 passed
make tree           # see the transitive tree, every node pinned
```

### 4. Audit the real attack surface
```bash
make audit
```
`pip-audit` scans every package in the lock, not just the five names. While
this repo was being built, it flagged **PYSEC-2026-1845 in pytest 8.4.2**
(fixed in 9.0.3). The fix was a deliberate, reviewable change: bump the range
in `requirements-dev.in`, then run `make lock`. Try it yourself by setting
`pytest>=8,<9`, running `make lock && make audit`, and watching it fail.

### 5. A swapped or compromised artifact
```bash
make tamper
```
This corrupts boto3's hashes in a copy of the lock. pip refuses with
`THESE PACKAGES DO NOT MATCH THE HASHES` and installs nothing. Without hashes,
pip would trust whatever the index served.

### 6. Stale-lock gate
Edit `requirements.in` (e.g. add `requests`), commit **without** running
`make lock`, and push. The `lock-is-fresh` CI job fails with
"Lock files are stale". The lock can't silently diverge from declared intent.

## CI jobs (`.github/workflows/ci.yml`)

| Job | What it proves |
|---|---|
| `locked` | Hash-verified install, tests, `pip-audit` of the full tree, dep tree printout |
| `lock-is-fresh` | `*.in` and the lock files agree; otherwise the build fails |
| `unpinned-demo` | Installs the floating file, uploads `pip freeze` as an artifact, prints the drift report. Run it on different days and compare artifacts. |

A weekly `schedule` re-runs the audit so **new advisories against already-locked
versions** surface even when nobody pushes.

## Day-to-day workflow

| Task | Command |
|---|---|
| Add or change a dependency | edit `requirements*.in` → `make lock` → commit both |
| Deliberately upgrade everything | `make upgrade` → review the diff → test → commit |
| Routine upgrades | Dependabot PRs (grouped, 7-day cooldown) |

## Hardening ideas to try next
- Pin GitHub Actions to full commit SHAs (`actions/checkout@<sha>`) and let
  Dependabot's `github-actions` ecosystem maintain them. Workflows are supply chain too.
- Point pip at an internal mirror or proxy (`PIP_INDEX_URL`) and use only one index
  to rule out dependency confusion.
- Generate an SBOM from the lock (`cyclonedx-py requirements requirements.txt`)
  and compare it with one generated from `unpinned/requirements.txt`.
- Add a branch-protection rule requiring `locked` and `lock-is-fresh` to pass.
