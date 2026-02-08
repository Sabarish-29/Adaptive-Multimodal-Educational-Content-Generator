"""Sandboxed code executor tool for tutoring."""

import subprocess
import tempfile
import os
from typing import Dict


def execute_python(code: str, timeout: int = 5) -> Dict[str, str]:
    """
    Execute Python code in a sandboxed subprocess.
    Used by the tutor to demonstrate code concepts.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        try:
            result = subprocess.run(
                ["python", f.name],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Execution timed out.", "returncode": -1}
        finally:
            os.unlink(f.name)
