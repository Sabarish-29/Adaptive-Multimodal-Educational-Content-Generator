import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
example = ROOT / ".env.example"
user = ROOT / ".env"
missing_required = []
comments_optional = {
    "SENTRY_DSN",
    "KMS_ENDPOINT",
    "OIDC_DISCOVERY_URL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "FIELD_ENCRYPTION_KEY",
    "FIELD_ENCRYPTION_KEY_ID",
}
pat = re.compile(r"^(?!#)([A-Z0-9_]+)=(.*)$")


def parse(p):
    data = {}
    if not p.exists():
        return data
    for line in p.read_text().splitlines():
        m = pat.match(line.strip())
        if m:
            data[m.group(1)] = m.group(2)
    return data


ex = parse(example)
userd = parse(user)
for k in ex:
    if k not in userd and k not in comments_optional:
        missing_required.append(k)

if missing_required:
    print("[verify-env] Missing required keys:", ", ".join(missing_required))
    sys.exit(1)
print("[verify-env] OK - all required keys present")
