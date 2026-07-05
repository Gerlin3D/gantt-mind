class DomainError(ValueError):
    """Base class for domain rule violations."""


class DuplicateTaskIdError(DomainError):
    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task id is duplicated: {task_id}")
        self.task_id = task_id


class TaskPlanMismatchError(DomainError):
    def __init__(self, task_id: str, plan_id: str) -> None:
        super().__init__(f"Task {task_id} does not belong to plan {plan_id}.")
        self.task_id = task_id
        self.plan_id = plan_id


class InvalidTaskDurationError(DomainError):
    def __init__(self, task_id: str, duration_days: int) -> None:
        super().__init__(f"Task {task_id} duration must be a positive integer.")
        self.task_id = task_id
        self.duration_days = duration_days


class UnsupportedDependencyTypeError(DomainError):
    def __init__(self, dependency_type: str) -> None:
        super().__init__(f"Unsupported dependency type: {dependency_type}")
        self.dependency_type = dependency_type


class SelfDependencyError(DomainError):
    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task {task_id} cannot depend on itself.")
        self.task_id = task_id


class UnknownTaskDependencyError(DomainError):
    def __init__(self, task_id: str) -> None:
        super().__init__(f"Dependency references unknown task: {task_id}")
        self.task_id = task_id


class CyclicDependencyError(DomainError):
    def __init__(self) -> None:
        super().__init__("Task dependencies contain a cycle.")
