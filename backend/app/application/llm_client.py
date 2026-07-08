from collections.abc import Mapping
from typing import Protocol


class LLMClient(Protocol):
    def propose_operations(self, *, plan_context: Mapping[str, object], message: str) -> str:
        """Return raw JSON text matching the AiOperationProposal schema."""
