"""Auto path injector for monorepo services.
Ensures `common_utils` and other local packages import without manual PYTHONPATH.
Python automatically imports sitecustomize if present on sys.path (root here).
"""
import os, sys
root = os.path.abspath(os.path.dirname(__file__))
paths = [
    root,
    os.path.join(root, 'packages'),
    os.path.join(root, 'packages', 'common_utils'),
    os.path.join(root, 'packages', 'common_utils', 'common_utils'),
]
for p in paths:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
