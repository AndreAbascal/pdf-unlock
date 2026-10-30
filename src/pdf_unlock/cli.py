"""Command-line interface for pdf-unlock."""

import argparse
import getpass
import os
import warnings
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn

from . import __version__
from .discovery import discover
from .models import Status
from .passwords import Passwords
from .processor import process


def positive_int(value: str) -> int:
    try:
        number = int(value)
        if number > 0:
            return number
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("must be a positive integer")


def main() -> None:
    raise SystemExit(run())


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Remove PDF encryption locally, replacing originals."
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="PDF file or directory (default: current directory)"
    )
    parser.add_argument(
        "-r", "-R", "--recursive", action="store_true", help="include subdirectories"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="inspect without prompting or writing"
    )
    parser.add_argument("--no-prompt", action="store_true", help="never prompt for passwords")
    parser.add_argument(
        "--password-env", metavar="NAME", help="read a password from an environment variable"
    )
    parser.add_argument("--max-attempts", type=positive_int, default=3)
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-q", "--quiet", action="store_true")
    verbosity.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--version", action="version", version=f"pdf-unlock {__version__}")
    args = parser.parse_args(argv)
    console = Console(highlight=False, markup=False)
    error_console = Console(stderr=True, highlight=False, markup=False)
    path = Path(args.path).expanduser().absolute()
    try:
        files, errors = discover(path, args.recursive)
    except (ValueError, OSError) as exc:
        error_console.print(f"Invalid path: {exc}")
        return 2
    if args.password_env and args.password_env not in os.environ:
        error_console.print(f"Environment variable {args.password_env!r} is not set")
        return 2
    passwords = Passwords()
    if args.password_env:
        passwords.remember(os.environ[args.password_env])
    if not args.quiet:
        console.print(
            f"PDF Unlock\nPath: {path}\nRecursive: {'Yes' if args.recursive else 'No'}\nFound {len(files)} PDF files."
        )
    for error in errors:
        error_console.print(f"Discovery error: {error}")
    counts = {status: 0 for status in Status}

    def ask(file: Path, attempt: int) -> str:
        # Rich's live refresh can erase getpass's prompt while it waits for input.
        progress.stop()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                try:
                    return getpass.getpass(
                        f"Password for {file} (attempt {attempt}/{args.max_attempts}): "
                    )
                except getpass.GetPassWarning as exc:
                    raise OSError("Secure password input unavailable") from exc
        finally:
            progress.start()

    try:
        with Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=args.quiet or not console.is_terminal or len(files) < 2,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing", total=len(files))
            for file in files:
                result = process(
                    file,
                    passwords,
                    dry_run=args.dry_run,
                    prompt=None if args.no_prompt or args.dry_run else ask,
                    max_attempts=args.max_attempts,
                )
                counts[result.status] += 1
                if result.status == Status.FAILED:
                    error_console.print(f"{file}: {result.message}")
                elif not args.quiet:
                    console.print(f"{file}: {result.message}")
                progress.advance(task)
    except KeyboardInterrupt:
        error_console.print("Interrupted")
        return 130
    if not args.quiet:
        console.print(
            f"Summary: Found {len(files)} | Unlocked {counts[Status.UNLOCKED]} | "
            f"Unencrypted {counts[Status.UNENCRYPTED]} | Encrypted {counts[Status.ENCRYPTED]} | "
            f"Failed {counts[Status.FAILED] + len(errors)}"
        )
    return 1 if counts[Status.FAILED] or errors else 0
