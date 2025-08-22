"""Site customization to ensure mounted shared packages are importable.

If a container mounts ../../packages/common_utils at /app/common_utils_ext, we
append that path AND its parent to sys.path early so imports like
`from common_utils.request import ...` resolve regardless of working dir.
"""

import sys
import os

candidate = os.path.abspath(os.path.join(os.getcwd(), "common_utils_ext"))
if os.path.isdir(candidate) and candidate not in sys.path:
    sys.path.insert(0, candidate)
    inner = os.path.join(candidate, "common_utils")
    if os.path.isdir(inner) and inner not in sys.path:
        sys.path.insert(0, inner)
