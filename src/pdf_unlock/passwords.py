"""In-memory credentials for one invocation."""

from dataclasses import dataclass, field


@dataclass
class Passwords:
    values: list[str] = field(default_factory=list)

    def remember(self, password: str) -> None:
        if password and password not in self.values:
            self.values.append(password)
