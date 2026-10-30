import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pikepdf
import pytest

from pdf_unlock.cli import run


@pytest.mark.parametrize(
    "args,recursive",
    [([], False), (["."], False), (["./"], False), ([".", "-r"], True), (["./", "-R"], True)],
)
def test_current_directory_variants(tmp_path, make_pdf, monkeypatch, args, recursive):
    top = make_pdf(tmp_path / "top.pdf", "secret")
    nested = make_pdf(tmp_path / "nested" / "nested.pdf", "secret")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_PDF_PASSWORD", "secret")
    assert run(args + ["--password-env", "TEST_PDF_PASSWORD", "--no-prompt"]) == 0
    with pikepdf.open(top) as pdf:
        assert not pdf.is_encrypted
    with pikepdf.open(nested, password="secret") as pdf:
        assert pdf.is_encrypted is not recursive


def test_failures_dry_run_and_invalid_inputs(tmp_path, make_pdf, monkeypatch):
    path = make_pdf(tmp_path / "a.pdf", "secret")
    before = path.read_bytes()
    assert run([str(path), "--dry-run"]) == 0
    assert run([str(path), "--no-prompt"]) == 1
    assert path.read_bytes() == before
    assert run([str(tmp_path / "missing")]) == 2
    assert run([str(path), "--password-env", "NOT_SET_PDF_UNLOCK"]) == 2
    with pytest.raises(SystemExit) as exc:
        run(["--max-attempts", "0"])
    assert exc.value.code == 2
    with patch("pdf_unlock.cli.process", side_effect=KeyboardInterrupt):
        assert run([str(path)]) == 130


def test_installed_command(tmp_path, make_pdf):
    executable = Path(sys.executable).parent / (
        "pdf-unlock.exe" if os.name == "nt" else "pdf-unlock"
    )
    assert executable.exists()
    path = make_pdf(tmp_path / "a.pdf", "secret")
    env = dict(os.environ, TEST_PDF_PASSWORD="secret")
    result = subprocess.run(
        [str(executable), str(path), "--password-env", "TEST_PDF_PASSWORD", "--no-prompt"],
        cwd=tmp_path,
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    with pikepdf.open(path) as pdf:
        assert not pdf.is_encrypted


def test_progress_is_paused_during_password_prompt(tmp_path, make_pdf, monkeypatch):
    make_pdf(tmp_path / "a.pdf", "secret")
    make_pdf(tmp_path / "b.pdf")
    events = []
    from rich.progress import Progress

    stop = Progress.stop
    start = Progress.start

    def record_stop(progress):
        events.append("stop")
        return stop(progress)

    def record_start(progress):
        events.append("start")
        return start(progress)

    def prompt(_):
        assert events[-1] == "stop"
        events.append("prompt")
        return "secret"

    monkeypatch.setattr(Progress, "stop", record_stop)
    monkeypatch.setattr(Progress, "start", record_start)
    monkeypatch.setattr("pdf_unlock.cli.getpass.getpass", prompt)
    assert run([str(tmp_path)]) == 0
    assert events[1:4] == ["stop", "prompt", "start"]
