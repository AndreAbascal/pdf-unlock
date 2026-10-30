# PDF Unlock

**A simple, local CLI for removing PDF encryption when you have the password.**

[![CI](https://github.com/AndreAbascal/pdf-unlock/actions/workflows/ci.yml/badge.svg)](https://github.com/AndreAbascal/pdf-unlock/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

PDF Unlock processes one file or a whole directory, reuses passwords during the current run, and replaces each successfully decrypted PDF at its original path. Documents and passwords stay on your computer.

```bash
pdf-unlock document.pdf
pdf-unlock .
pdf-unlock . -r
pdf-unlock ./documents -R
```

> **Back up important files first.** Successfully unlocked PDFs replace their originals and are no longer protected by encryption. Store the decrypted files appropriately. This tool does not recover or crack unknown passwords.

## Highlights

- **Local by design:** no document uploads or network access during execution.
- **Simple defaults:** process the current directory, or pass a PDF file or directory.
- **Recursion is opt-in:** use `-r`, `-R`, or `--recursive` to include subdirectories.
- **Fewer prompts:** successful passwords are reused in memory for later files in the same run.
- **Safe replacement:** output is written to a temporary file and verified before replacing the original.
- **Automation friendly:** inspect with `--dry-run` or use an environment variable with `--no-prompt`.

## Installation

Python 3.10 or newer is required. On macOS, Linux, or Windows, install [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/), clone this repository, and run from the checkout:

```bash
uv tool install .
# or
pipx install .
```

Ensure the tool installation directory is on your `PATH` (for pipx, run `pipx ensurepath`). The `pdf-unlock` command then works from any directory.

Once the package is published to PyPI, it can also be installed with `uv tool install pdf-unlock-cli` or `pipx install pdf-unlock-cli`.

## Usage

```text
pdf-unlock [PATH] [-r|-R|--recursive] [--dry-run] [--no-prompt]
           [--password-env NAME] [--max-attempts N] [-q|-v] [--version]
```

| Option | Description |
| --- | --- |
| `PATH` | PDF file or directory; defaults to the current directory. |
| `-r`, `-R`, `--recursive` | Include subdirectories. |
| `--dry-run` | Inspect encryption status without prompting or modifying files. |
| `--no-prompt` | Never request interactive input. |
| `--password-env NAME` | Read a password from an environment variable. |
| `--max-attempts N` | Set the number of interactive attempts per file (default: 3). |
| `-q`, `--quiet` | Show errors only. |
| `-v`, `--verbose` | Show per-file output. |
| `--version` | Show the installed version. |

Directories are **never recursive by default**: only PDFs directly inside are processed. PDF extensions are case insensitive. Symbolic links are excluded, including symlinked input paths and directories. Files are processed sequentially in deterministic order.

### Passwords and unattended use

Unencrypted files are skipped without changes or a password prompt. Encryption that accepts an empty password is removed without a prompt. Otherwise, enter the password securely when asked. Successful passwords are kept only in memory for the current run and tried on later files; they are not persisted.

For unattended use, set an environment variable and run:

```bash
pdf-unlock ./documents --password-env PDF_PASSWORD --no-prompt
```

Environment variables may be visible to other processes or inherited by child processes depending on your system. `--no-prompt` skips files without available valid credentials. A dry run reports password-protected files as encrypted without validating passwords.

### How replacement works

The program writes to a unique temporary file alongside the original, verifies that the output opens without a password and is unencrypted, preserves permission bits where practical, syncs the output, and atomically replaces the original. Failures leave the original in place and remove the temporary file. This is not a guarantee of durability across power loss. Replacement may change other filesystem metadata, such as ownership, timestamps, extended attributes, or hard-link relationships.

| Exit code | Meaning |
| --- | --- |
| `0` | Success, including unencrypted files and a successful dry run. |
| `1` | A file or directory traversal failed. |
| `2` | Invalid arguments or input. |
| `130` | Interrupted. |

## Development

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python -m build
uv run twine check dist/*
```

## Troubleshooting

- **Command not found:** check that your pipx or uv tool directory is on `PATH` and restart the terminal.
- **Incorrect or unavailable password:** the original stays untouched; check your credentials and retry.
- **Cannot replace a file:** check file and directory permissions, disk space, and whether the PDF is corrupt.
- **Password entry unavailable:** for automated use, provide `--password-env` together with `--no-prompt`.

## License

[MIT](LICENSE).
