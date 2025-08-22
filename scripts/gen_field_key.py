#!/usr/bin/env python
"""Generate a base64 field encryption key (16/24/32 bytes raw -> AES-128/192/256).
Usage: python scripts/gen_field_key.py [length]
Default length: 32 (AES-256)
"""

import os
import sys
import base64

length = 32
if len(sys.argv) > 1:
    try:
        length = int(sys.argv[1])
    except ValueError:
        print("Length must be integer (16,24,32)", file=sys.stderr)
        sys.exit(1)
if length not in (16, 24, 32):
    print("Length must be one of 16,24,32", file=sys.stderr)
    sys.exit(2)
raw = os.urandom(length)
print(base64.b64encode(raw).decode())
