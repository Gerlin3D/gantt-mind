class ApplicationError(RuntimeError):
    """Base class for application use case failures."""


class PlanNotFoundError(ApplicationError):
    def __init__(self, plan_id: str) -> None:
        super().__init__(f"Plan was not found: {plan_id}")
        self.plan_id = plan_id


class PlanVersionConflictError(ApplicationError):
    def __init__(self, plan_id: str, expected_version: int, actual_version: int) -> None:
        super().__init__(
            f"Plan {plan_id} version conflict: expected {expected_version}, got {actual_version}."
        )
        self.plan_id = plan_id
        self.expected_version = expected_version
        self.actual_version = actual_version


class InvalidChangeSetError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class LlmProviderError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidAiOutputError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
