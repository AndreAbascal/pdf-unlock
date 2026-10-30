# pdf-unlock

A local command-line tool that removes PDF encryption using credentials you provide. It inspects each PDF individually and replaces successfully decrypted files at their original paths. Documents and passwords are never uploaded.

```bash
pdf-unlock document.pdf
pdf-unlock .
pdf-unlock . -r
pdf-unlock ./documents -R
```

**Back up important PDFs first.** Replacement removes the original encryption; decrypted PDFs are no longer protected and should be stored appropriately. The tool cannot recover unknown passwords or crack encryption.

## Install

Python 3.10 or newer is required. On macOS, Linux, and Windows, install [pipx](https://pipx.pypa.io/) or [uv](https://docs.astral.sh/uv/), then run from a checkout:

```bash
pipx install .
# or
uv tool install .
```

Once the package is published to PyPI, use `pipx install pdf-unlock-cli` or `uv tool install pdf-unlock-cli`. Ensure the tool installation directory is on your PATH (for pipx, run `pipx ensurepath`). Then `pdf-unlock` works from any directory.

## Usage

```text
pdf-unlock [PATH] [-r|-R|--recursive] [--dry-run] [--no-prompt]
           [--password-env NAME] [--max-attempts N] [-q|-v] [--version]
```

PATH defaults to the current directory. Directories are **never recursive by default**: only PDFs directly inside are processed. Use `-r`, `-R`, or `--recursive` to include subdirectories. PDF extensions are case insensitive. Symbolic links are excluded, including symlinked input paths and directories. Files are processed sequentially in deterministic order.

Unencrypted files are skipped without changes or a password prompt. Encryption that accepts an empty password is removed without a prompt. Otherwise, enter a password securely when asked; three attempts are allowed by default. Successful passwords are kept only in memory for the current run and tried on later files. The tool does not persist passwords.

For unattended use, set an environment variable and run `pdf-unlock ./documents --password-env PDF_PASSWORD --no-prompt`. Environment variables may be visible to other processes or inherited by children depending on your system. Avoid exposing sensitive values. `--no-prompt` skips files without available valid credentials. `--max-attempts N` changes interactive attempts. `--dry-run` inspects files without writing or requesting credentials; password-protected files are reported as encrypted without validating passwords. `--quiet` limits output to errors; `--verbose` shows normal per-file output.

The program writes to a unique temporary file alongside the original, verifies that the output opens without a password and is unencrypted, preserves permission bits where practical, syncs the output, and atomically replaces the original. Failures leave the original in place and remove the temporary file. This is not a guarantee of durability across power loss. Replacement may change other filesystem metadata, such as ownership, timestamps, extended attributes, or hard-link relationships.

Exit codes: 0 for success (including unencrypted files and a successful dry run), 1 if a file or directory traversal fails, 2 for invalid arguments or input, and 130 for interruption.

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

- If the command is not found, check your pipx or uv tool directory is on PATH and restart the terminal.
- Incorrect or unavailable passwords leave the original untouched. Check your credentials and retry.
- A read-only file, an unwritable directory, a corrupt PDF, or insufficient disk space can prevent replacement. Fix the issue and retry.
- If password entry is unavailable in an automated environment, use `--password-env` with `--no-prompt`.

## License

MIT. See [LICENSE](LICENSE).
