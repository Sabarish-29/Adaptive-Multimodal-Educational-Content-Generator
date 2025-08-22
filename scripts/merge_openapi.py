"""Merge per-service OpenAPI specs into one (Phase 0 placeholder).

Currently we maintain a single master spec at docs/api/openapi.yaml.
This script is scaffolded for future multi-file merge.
"""

import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "docs" / "api" / "openapi.yaml"


def main():
    data = yaml.safe_load(MASTER.read_text())
    (ROOT / "docs" / "api" / "openapi.merged.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False)
    )
    print(
        f"Merged spec written: docs/api/openapi.merged.yaml (version {data.get('info', {}).get('version')})"
    )


if __name__ == "__main__":
    main()
