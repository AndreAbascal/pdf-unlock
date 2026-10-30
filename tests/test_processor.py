from unittest.mock import patch

import pikepdf
import pytest

from pdf_unlock.models import Status
from pdf_unlock.passwords import Passwords
from pdf_unlock.processor import process


def test_unencrypted_is_not_modified_or_prompted(tmp_path, make_pdf):
    path = make_pdf(tmp_path / "plain.pdf")
    before = path.read_bytes()
    result = process(path, Passwords(), prompt=lambda *_: pytest.fail("unexpected prompt"))
    assert result.status == Status.UNENCRYPTED
    assert path.read_bytes() == before


@pytest.mark.parametrize("password", ["secret", ""])
def test_unlocks_in_place(tmp_path, make_pdf, password):
    path = make_pdf(tmp_path / "Olá document.PDF", password)
    result = process(path, Passwords(), prompt=lambda *_: password)
    assert result.status == Status.UNLOCKED
    with pikepdf.open(path) as pdf:
        assert not pdf.is_encrypted
    assert list(tmp_path.iterdir()) == [path]


def test_wrong_password_and_max_attempts(tmp_path, make_pdf):
    path = make_pdf(tmp_path / "locked.pdf", "secret")
    before = path.read_bytes()
    calls = []
    result = process(path, Passwords(), prompt=lambda _, n: calls.append(n) or "wrong")
    assert result.status == Status.FAILED
    assert calls == [1, 2, 3]
    assert path.read_bytes() == before


def test_reuse_and_different_passwords(tmp_path, make_pdf):
    cache = Passwords()
    for i, password in enumerate(["first", "first", "second"]):
        path = make_pdf(tmp_path / f"{i}.pdf", password)
        calls = []
        assert (
            process(
                path,
                cache,
                prompt=lambda *_, calls=calls, password=password: calls.append(1) or password,
            ).status
            == Status.UNLOCKED
        )
        assert len(calls) == (0 if i == 1 else 1)
    assert cache.values == ["first", "second"]


@pytest.mark.parametrize("failure", ["save", "verify", "replace"])
def test_failures_preserve_original_and_clean_temp(tmp_path, make_pdf, failure):
    path = make_pdf(tmp_path / "locked.pdf", "secret")
    before = path.read_bytes()
    if failure == "save":
        target = "pikepdf.Pdf.save"
    elif failure == "verify":
        target = "pdf_unlock.processor.os.chmod"
    else:
        target = "pdf_unlock.processor.os.replace"
    with patch(target, side_effect=OSError("failure")):
        result = process(path, Passwords(["secret"]))
    assert result.status == Status.FAILED
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_interruption_cleans_temp(tmp_path, make_pdf):
    path = make_pdf(tmp_path / "locked.pdf", "secret")
    before = path.read_bytes()
    with (
        patch("pdf_unlock.processor.os.replace", side_effect=KeyboardInterrupt),
        pytest.raises(KeyboardInterrupt),
    ):
        process(path, Passwords(["secret"]))
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_dry_run_and_corrupt(tmp_path, make_pdf):
    locked = make_pdf(tmp_path / "locked.pdf", "secret")
    empty = make_pdf(tmp_path / "empty.pdf", "")
    before = locked.read_bytes()
    assert process(locked, Passwords(), dry_run=True).status == Status.ENCRYPTED
    assert process(empty, Passwords(), dry_run=True).status == Status.ENCRYPTED
    assert locked.read_bytes() == before
    corrupt = tmp_path / "bad.pdf"
    corrupt.write_text("not a pdf")
    assert process(corrupt, Passwords()).status == Status.FAILED


def test_validation_failure_preserves_original(tmp_path, make_pdf):
    path = make_pdf(tmp_path / "locked.pdf", "secret")
    before = path.read_bytes()
    real_open = pikepdf.open

    def fail_validation(filename, *args, **kwargs):
        if str(filename).endswith(".tmp"):
            raise pikepdf.PdfError("verification failed")
        return real_open(filename, *args, **kwargs)

    with patch("pdf_unlock.processor.pikepdf.open", side_effect=fail_validation):
        result = process(path, Passwords(["secret"]))
    assert result.status == Status.FAILED
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]
