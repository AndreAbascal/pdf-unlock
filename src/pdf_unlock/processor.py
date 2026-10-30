"""PDF inspection and verified same-directory atomic replacement."""

import os
import stat
import tempfile
from collections.abc import Callable
from pathlib import Path

import pikepdf

from .models import Result, Status
from .passwords import Passwords


def process(
    path: Path,
    passwords: Passwords,
    *,
    dry_run: bool = False,
    prompt: Callable[[Path, int], str] | None = None,
    max_attempts: int = 3,
) -> Result:
    """Inspect or unlock one PDF. An unsuccessful operation preserves its original."""
    try:
        try:
            pdf = pikepdf.open(path, password="")
        except pikepdf.PasswordError:
            if dry_run:
                return Result(path, Status.ENCRYPTED, "Encrypted (password required)")
            pdf = None
            for password in passwords.values:
                try:
                    pdf = pikepdf.open(path, password=password)
                    break
                except pikepdf.PasswordError:
                    continue
            if pdf is None and prompt is not None:
                for attempt in range(1, max_attempts + 1):
                    try:
                        password = prompt(path, attempt)
                    except (EOFError, OSError):
                        break
                    try:
                        pdf = pikepdf.open(path, password=password)
                        passwords.remember(password)
                        break
                    except pikepdf.PasswordError:
                        continue
            if pdf is None:
                return Result(path, Status.FAILED, "Password unavailable or incorrect")
        with pdf:
            if not pdf.is_encrypted:
                return Result(path, Status.UNENCRYPTED, "Already unencrypted")
            if dry_run:
                return Result(path, Status.ENCRYPTED, "Encrypted (empty password works)")
            # Refuse to replace a read-only original even where directory permissions allow it.
            original_stat = path.stat()
            if not stat.S_IMODE(original_stat.st_mode) & 0o222:
                raise PermissionError("Original file is read-only")
            temporary: str | None = None
            try:
                fd, temporary = tempfile.mkstemp(
                    prefix=".pdf-unlock-", suffix=".tmp", dir=path.parent
                )
                os.close(fd)
                pdf.save(temporary, encryption=False)
                # Release the original before replacement, especially on Windows.
                pdf.close()
                with pikepdf.open(temporary, password="") as verified:
                    if verified.is_encrypted:
                        raise ValueError("Output is still encrypted")
                os.chmod(temporary, stat.S_IMODE(original_stat.st_mode))
                with open(temporary, "rb") as output:
                    os.fsync(output.fileno())
                # Do not replace a file changed or substituted during processing.
                current = path.stat()
                if path.is_symlink() or (
                    current.st_dev,
                    current.st_ino,
                    current.st_size,
                    current.st_mtime_ns,
                ) != (
                    original_stat.st_dev,
                    original_stat.st_ino,
                    original_stat.st_size,
                    original_stat.st_mtime_ns,
                ):
                    raise OSError("Original file changed during processing")
                os.replace(temporary, path)
                temporary = None
            finally:
                if temporary is not None:
                    try:
                        os.unlink(temporary)
                    except FileNotFoundError:
                        pass
        return Result(path, Status.UNLOCKED, "Unlocked successfully")
    except (OSError, pikepdf.PdfError, ValueError, RuntimeError) as exc:
        return Result(path, Status.FAILED, f"Could not process PDF: {exc}")
