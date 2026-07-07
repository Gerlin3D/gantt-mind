class ApplicationError(RuntimeError):
    """Base class for application use case failures."""


class PlanNotFoundError(ApplicationError):
    def __init__(self, plan_id: str) -> None:
        super().__init__(f"Plan was not found: {plan_id}")
        self.plan_id = plan_id
