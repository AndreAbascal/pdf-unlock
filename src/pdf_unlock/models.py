"""Results returned by the processor."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    UNLOCKED = "unlocked"
    UNENCRYPTED = "unencrypted"
    ENCRYPTED = "encrypted"
    FAILED = "failed"


@dataclass(frozen=True)
class Result:
    path: Path
    status: Status
    message: str
