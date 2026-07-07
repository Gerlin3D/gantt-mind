from datetime import date

from app.application.plan_service import DEMO_PLAN_ID
from app.domain.entities import Plan, Task, TaskDependency
from app.domain.scheduler import schedule_plan
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository


def build_demo_plan() -> Plan:
    plan = Plan(
        id=DEMO_PLAN_ID,
        name="GanttMind Demo Project",
        start_date=date(2026, 1, 5),
        tasks=(
            Task("discovery", DEMO_PLAN_ID, "Project discovery", 2, 1, assignee="Maya"),
            Task("requirements", DEMO_PLAN_ID, "Requirements analysis", 3, 2, assignee="Alex"),
            Task("ux-research", DEMO_PLAN_ID, "UX research", 2, 3, assignee="Nina"),
            Task("ui-design", DEMO_PLAN_ID, "UI design", 4, 4, assignee="Nina"),
            Task("backend-api", DEMO_PLAN_ID, "Backend API", 5, 5, assignee="Ivan"),
            Task("frontend-dev", DEMO_PLAN_ID, "Frontend development", 5, 6, assignee="Olga"),
            Task("integration", DEMO_PLAN_ID, "Integration", 3, 7, assignee="Ivan"),
            Task("qa-testing", DEMO_PLAN_ID, "QA testing", 3, 8, assignee="Alex"),
            Task("production-release", DEMO_PLAN_ID, "Production release", 1, 9, assignee="Maya"),
        ),
        dependencies=(
            TaskDependency("discovery", "requirements"),
            TaskDependency("discovery", "ux-research"),
            TaskDependency("requirements", "backend-api"),
            TaskDependency("ux-research", "ui-design"),
            TaskDependency("ui-design", "frontend-dev"),
            TaskDependency("backend-api", "integration"),
            TaskDependency("frontend-dev", "integration"),
            TaskDependency("integration", "qa-testing"),
            TaskDependency("qa-testing", "production-release"),
        ),
    )
    return schedule_plan(plan)


def seed_demo_plan() -> bool:
    with SessionLocal() as session:
        repository = SQLAlchemyPlanRepository(session)
        if repository.exists(DEMO_PLAN_ID):
            return False

        repository.save(build_demo_plan())
        session.commit()
        return True


def main() -> None:
    created = seed_demo_plan()
    if created:
        print("Seeded demo plan.")
    else:
        print("Demo plan already exists.")


if __name__ == "__main__":
    main()
