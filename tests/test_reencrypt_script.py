import json
import subprocess
import sys
import os
import tempfile
import pathlib

SCRIPT = pathlib.Path("scripts/reencrypt_fields.py")


def run(cmd):
    return subprocess.check_output([sys.executable, str(SCRIPT)] + cmd, text=True)


def test_dry_run_executes():
    out = run(["--dry-run", "--batch", "3"])
    assert "summary" in out
    data = json.loads(out.splitlines()[-1])
    assert data["summary"] is True
    assert data["updated"] == 0  # dry run


def test_execute_and_state_resume():
    with tempfile.TemporaryDirectory() as td:
        state = os.path.join(td, "state.json")
        # First partial run small batch
        out1 = run(["--batch", "4", "--state", state])
        # Second run resumes and completes
        out2 = run(["--batch", "4", "--state", state])
        last_line = json.loads(out2.splitlines()[-1])
        assert last_line["summary"] is True
        assert (
            last_line["updated"] == last_line["processed"]
        )  # all processed updated in execute mode
        assert last_line["errors"] == 0
