import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
example = ROOT / ".env.example"
user = ROOT / ".env"
out_file = ROOT / "configs" / "aggregated.env"

if not example.exists():
    print("[sync-env] .env.example missing", file=sys.stderr)
    sys.exit(1)

line_re = re.compile(r"^(?!#)([A-Z0-9_]+)=(.*)$")


def parse(p: pathlib.Path):
    data = {}
    if not p.exists():
        return data
    for line in p.read_text().splitlines():
        m = line_re.match(line.strip())
        if m:
            data[m.group(1)] = m.group(2)
    return data


ex_data = parse(example)
user_data = parse(user)
keys = sorted(set(ex_data) | set(user_data))

lines = []
missing = []
for k in keys:
    if k in user_data:
        lines.append(f"{k}={user_data[k]}")
    else:
        # fallback to example value commented to highlight
        val = ex_data.get(k, "")
        lines.append(f"# MISSING set value -> {k}={val}")
        missing.append(k)

out_file.write_text("\n".join(lines) + "\n")
print(f"[sync-env] wrote {out_file} ({len(lines)} vars, missing {len(missing)})")
if missing:
    print("[sync-env] Missing keys:", ", ".join(missing))
else:
    print("[sync-env] No missing keys")
