# Root-level conftest to apply path stubs & aliases for all tests (including service-local tests)
import runpy
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CENTRAL = ROOT / "tests" / "conftest.py"
if CENTRAL.exists():
    # Execute the central test bootstrap script in its own namespace
    runpy.run_path(str(CENTRAL), run_name="central_test_bootstrap")
