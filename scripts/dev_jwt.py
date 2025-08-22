"""Generate a development JWT token (HS256) for manual API calls.

Example (PowerShell):
python scripts/dev_jwt.py --sub learner_demo --roles learner --secret mock-public-key | Set-Clipboard
"""

import argparse
import time
import jwt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sub", required=True, help="Subject / user id placed into sub claim"
    )
    parser.add_argument("--roles", default="learner", help="Comma separated roles list")
    parser.add_argument("--tenant", default="tenant_demo", help="Tenant identifier")
    parser.add_argument(
        "--exp", type=int, default=3600, help="Lifetime in seconds (default 1h)"
    )
    parser.add_argument(
        "--secret", default="mock-public-key", help="Shared dev secret (HS256)"
    )
    args = parser.parse_args()

    payload = {
        "sub": args.sub,
        "roles": [r.strip() for r in args.roles.split(",") if r.strip()],
        "tenant_id": args.tenant,
        "iss": "adaptive-edu-dev",
        "exp": int(time.time()) + args.exp,
        "iat": int(time.time()),
        "env": "dev",
    }
    token = jwt.encode(payload, args.secret, algorithm="HS256")
    print(token)


if __name__ == "__main__":
    main()
