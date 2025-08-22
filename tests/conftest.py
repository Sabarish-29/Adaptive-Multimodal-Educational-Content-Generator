import sys
import types
import pathlib
import importlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = ROOT / "packages"
SERVICES = ROOT / "services"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
if PKG.exists() and str(PKG) not in sys.path:
    sys.path.append(str(PKG))
if SERVICES.exists() and str(SERVICES) not in sys.path:
    sys.path.append(str(SERVICES))

# Motor stub to avoid real pymongo version issues (must occur before loading service modules)
if "motor.motor_asyncio" not in sys.modules:
    from tests.fakes.inmemory_db import InMemoryMongoClient  # type: ignore

    mm = types.ModuleType("motor.motor_asyncio")
    mm.AsyncIOMotorClient = InMemoryMongoClient  # type: ignore[attr-defined]
    rootpkg = types.ModuleType("motor")
    rootpkg.motor_asyncio = mm
    sys.modules["motor"] = rootpkg
    sys.modules["motor.motor_asyncio"] = mm

# Provide common_utils shortcut package (inner layout) if not present
cu_inner = PKG / "common_utils" / "common_utils"
if cu_inner.exists() and "common_utils" not in sys.modules:
    pkg = types.ModuleType("common_utils")
    pkg.__path__ = [str(cu_inner)]  # type: ignore
    sys.modules["common_utils"] = pkg
    for name in ["request", "encryption", "ratelimit"]:
        mod_path = cu_inner / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(
                f"common_utils.{name}", mod_path
            )
            m = importlib.util.module_from_spec(spec)  # type: ignore
            assert spec and spec.loader
            spec.loader.exec_module(m)  # type: ignore
            sys.modules[f"common_utils.{name}"] = m
            setattr(pkg, name, m)

# Provide top-level service package aliases (contentgen.main etc.) for legacy test imports
for svc in ["adaptation", "contentgen", "profiles", "eval_safety", "rag", "sessions"]:
    svc_path = SERVICES / svc / svc / "main.py"
    if svc_path.exists():
        spec = importlib.util.spec_from_file_location(f"{svc}.main", svc_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(module)  # type: ignore
            pkg = sys.modules.get(svc)
            if not pkg:
                pkg_mod = types.ModuleType(svc)
                pkg_mod.__path__ = [str(svc_path.parent)]  # type: ignore
                sys.modules[svc] = pkg_mod
                pkg = pkg_mod
            sys.modules[f"{svc}.main"] = module

# Make Prometheus metric creation idempotent for tests that reload modules
try:
    import prometheus_client

    def _ensure_metric(name: str, constructor, *args, **kwargs):
        try:
            return constructor(name, *args, **kwargs)
        except ValueError:
            reg = getattr(prometheus_client, "REGISTRY", None)
            if reg and hasattr(reg, "_names_to_collectors"):
                return reg._names_to_collectors.get(name)
            return None

    # Monkeypatch common constructors used in services to be tolerant
    from prometheus_client import (
        Counter as _OrigCounter,
        Histogram as _OrigHistogram,
        Gauge as _OrigGauge,
    )

    class _Counter(_OrigCounter):
        def __init__(self, name, *a, **k):
            inst = _ensure_metric(name, _OrigCounter, *a, **k)
            self.__dict__ = inst.__dict__

    class _Histogram(_OrigHistogram):
        def __init__(self, name, *a, **k):
            inst = _ensure_metric(name, _OrigHistogram, *a, **k)
            self.__dict__ = inst.__dict__

    class _Gauge(_OrigGauge):
        def __init__(self, name, *a, **k):
            inst = _ensure_metric(name, _OrigGauge, *a, **k)
            self.__dict__ = inst.__dict__

    prometheus_client.Counter = _Counter  # type: ignore
    prometheus_client.Histogram = _Histogram  # type: ignore
    prometheus_client.Gauge = _Gauge  # type: ignore
except Exception:
    pass


# Pytest hook to reset encryption singleton when flags change across tests
def pytest_runtest_setup(item):  # type: ignore
    try:
        import common_utils.encryption as enc  # type: ignore

        if hasattr(enc, "_reset_for_test"):
            enc._reset_for_test()  # type: ignore
    except Exception:
        pass
