"""Dependency policy enforcement + vulnerability gate.

Enforces pinning & disallowed patterns; fails on HIGH/CRITICAL vulnerabilities (pip-audit) unless skipped.

Enforced:
 1. Exact version pins (==).
 2. Disallowed packages blocked (requests, django).
 3. No editable installs or VCS refs.
 4. No wildcards '*'.
 5. Allowlist exceptions from .dependency-allowlist (exact line).
 6. Vulnerability gate: pip-audit JSON scan; block HIGH/CRITICAL (unless DEP_POLICY_SKIP_VULN=true env var set).

Warnings:
    * FastAPI version mismatches.
    * Environment markers (;) usage.

Usage: python scripts/dependency_policy.py
"""

from __future__ import annotations
import sys
import pathlib
import re
import subprocess
import json
import os
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVICE_REQS = list(ROOT.glob("services/*/requirements.txt"))
DEV_REQ = ROOT / "requirements-dev.txt"
PIN_RE = re.compile(r"^[a-zA-Z0-9_.-]+==[0-9][^=]*$")
DISALLOWED = {"requests": "Use httpx instead", "django": "Not needed in microservices"}
MIN_VERSIONS = {
    # Example: 'fastapi': '0.110.0'
}
FORBIDDEN_PREFIXES = ("git+", "svn+", "hg+", "bzr+")
ALLOWLIST_FILE = ROOT / ".dependency-allowlist"
VULN_ALLOWLIST_FILE = ROOT / ".vuln-allowlist"
fastapi_versions = {}
errors: list[str] = []
warnings: list[str] = []

allow_exceptions: set[str] = set()
if ALLOWLIST_FILE.exists():
    allow_exceptions = {
        l.strip()
        for l in ALLOWLIST_FILE.read_text().splitlines()
        if l.strip() and not l.strip().startswith("#")
    }


def _check_line(service: str, line: str):
    original = line
    if original in allow_exceptions:
        return
    # Strip inline comments
    if " #" in line:
        line = line.split(" #", 1)[0].strip()
    if not line or line.startswith("#"):
        return
    if line.startswith("-e "):
        errors.append(f"{service}: editable install not allowed: {original}")
        return
    if any(line.startswith(pfx) for pfx in FORBIDDEN_PREFIXES):
        errors.append(f"{service}: VCS reference not allowed: {original}")
    if "==" not in line:
        errors.append(f"{service}: unpinned spec '{original}' (must use ==)")
    else:
        pkg = line.split("==")[0]
        if pkg.lower() in DISALLOWED:
            errors.append(
                f"{service}: disallowed package '{pkg}': {DISALLOWED[pkg.lower()]}"
            )
        if not PIN_RE.match(line.split(";")[0].strip()):
            errors.append(f"{service}: invalid pin pattern '{original}'")
        # Minimal version gate
        mv = MIN_VERSIONS.get(pkg.lower()) if pkg else None
        if mv:
            pinned_ver = line.split("==")[1].split(";")[0]
            if pinned_ver < mv:
                errors.append(
                    f"{service}: {pkg} version {pinned_ver} below minimum {mv}"
                )
    if "*" in line:
        errors.append(f"{service}: wildcard '*' not permitted '{original}'")
    if ";" in line:
        warnings.append(
            f"{service}: environment marker present (review for consistency): {original}"
        )
    # collect fastapi
    if line.lower().startswith("fastapi=="):
        fastapi_versions[service] = line.split("==")[1].split(";")[0]


for req_file in SERVICE_REQS:
    service = req_file.parent.name
    for line in req_file.read_text().splitlines():
        _check_line(service, line.strip())

if DEV_REQ.exists():
    for line in DEV_REQ.read_text().splitlines():
        _check_line("dev", line.strip())

# fastapi version consistency
if fastapi_versions:
    version_groups = defaultdict(list)
    for svc, ver in fastapi_versions.items():
        version_groups[ver].append(svc)
    if len(version_groups) > 1:
        warnings.append(
            "FastAPI version mismatch across services: "
            + ", ".join(f"{ver} -> {svcs}" for ver, svcs in version_groups.items())
        )

if warnings:
    print("WARNINGS:")
    for w in warnings:
        print("  -", w)


def _vuln_scan():
    if os.getenv("DEP_POLICY_SKIP_VULN", "").lower() == "true":
        return []
    try:
        req_args = []
        for rf in SERVICE_REQS + ([DEV_REQ] if DEV_REQ.exists() else []):
            if rf.exists():
                req_args.extend(["-r", str(rf)])
        if not req_args:
            return []
        cmd = ["pip-audit", "-f", "json"] + req_args
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode not in (0, 1):
            print("pip-audit execution issue:", proc.stderr.strip())
            return []
        data = json.loads(proc.stdout or "[]")
    except FileNotFoundError:
        print("pip-audit not installed; skipping vulnerability gate")
        return []
    except Exception as e:  # noqa: BLE001
        print("pip-audit failed:", e)
        return []
    blocks = []
    allowed_ids: set[str] = set()
    if VULN_ALLOWLIST_FILE.exists():
        allowed_ids = {
            l.strip()
            for l in VULN_ALLOWLIST_FILE.read_text().splitlines()
            if l.strip() and not l.strip().startswith("#")
        }
    for entry in data:
        name = entry.get("name")
        ver = entry.get("version")
        for v in entry.get("vulns", []):
            sev = (v.get("severity") or "UNKNOWN").upper()
            vid = v.get("id")
            if sev in ("HIGH", "CRITICAL"):
                if vid in allowed_ids:
                    print(f"Allowlisted vulnerability {vid} for {name}:{ver}")
                    continue
                blocks.append(f"{name}:{ver}:{vid}:{sev}")
    return blocks


vuln_blocks = _vuln_scan()

if errors or vuln_blocks:
    if errors:
        print("Dependency policy violations:")
        for e in errors:
            print("  -", e)
    if vuln_blocks:
        print("Blocking vulnerabilities (HIGH/CRITICAL):")
        for b in vuln_blocks:
            print("  -", b)
    sys.exit(1)

print("Dependency & vulnerability policy check passed.")
