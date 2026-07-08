from typing import Protocol

from app.domain.entities import ChangeSet


class ChangeSetRepository(Protocol):
    def save(self, change_set: ChangeSet) -> ChangeSet:
        """Persist a ChangeSet record and return it."""
