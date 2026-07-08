from typing import cast

from sqlalchemy.orm import Session

from app.domain.entities import ChangeSet, ChangeSetStatus
from app.infrastructure.database.models import ChangeSetModel


class SQLAlchemyChangeSetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, change_set: ChangeSet) -> ChangeSet:
        model = ChangeSetModel(
            id=change_set.id,
            plan_id=change_set.plan_id,
            source=change_set.source,
            user_request=change_set.user_request,
            operations=[dict(operation) for operation in change_set.operations],
            status=change_set.status,
        )
        self._session.add(model)
        self._session.flush()
        return ChangeSet(
            id=model.id,
            plan_id=model.plan_id,
            source=model.source,
            user_request=model.user_request,
            operations=tuple(dict(operation) for operation in model.operations),
            status=cast(ChangeSetStatus, model.status),
            created_at=model.created_at,
        )
