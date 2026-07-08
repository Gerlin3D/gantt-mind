from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.domain.entities import Plan
from app.infrastructure.excel.parser import parse_import_workbook
from app.infrastructure.repositories.sqlalchemy_plan_repository import SQLAlchemyPlanRepository
from app.seed import build_demo_plan
from tests.infrastructure.excel_workbook_helpers import workbook_bytes


def test_get_demo_plan_returns_contract(client: TestClient, db_session: Session) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(build_demo_plan())
    db_session.commit()

    response = client.get("/api/plans/demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "demo-plan"
    assert payload["name"] == "GanttMind Demo Project"
    assert payload["start_date"] == "2026-01-05"
    assert payload["version"] == 1
    assert len(payload["tasks"]) == 9
    assert len(payload["dependencies"]) == 9
    assert set(payload["tasks"][0]) == {
        "id",
        "name",
        "description",
        "assignee",
        "duration_days",
        "start_date",
        "end_date",
        "position",
    }
    assert set(payload["dependencies"][0]) == {
        "predecessor_task_id",
        "successor_task_id",
        "dependency_type",
    }


def test_get_plan_by_id_returns_snapshot(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    response = client.get("/api/plans/plan-1")

    assert response.status_code == 200
    assert response.json()["id"] == "plan-1"


def test_get_missing_plan_returns_404(client: TestClient) -> None:
    response = client.get("/api/plans/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan was not found: missing"


def test_import_plan_returns_created_snapshot(client: TestClient) -> None:
    content = workbook_bytes(
        [
            ["task", "description", "assignee", "duration", "predecessors"],
            ["Discovery", "Scope", "Maya", 2, ""],
            ["Build", "Build it", "Ivan", 3, "Discovery"],
        ]
    )

    response = client.post(
        "/api/plans/import",
        data={"plan_name": "Imported API Plan", "start_date": "2026-04-06"},
        files={
            "file": (
                "plan.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Imported API Plan"
    assert len(payload["tasks"]) == 2
    assert payload["tasks"][0]["start_date"] == "2026-04-06"
    assert payload["tasks"][1]["start_date"] == "2026-04-08"

    get_response = client.get(f"/api/plans/{payload['id']}")
    assert get_response.status_code == 200


def test_get_import_sample_workbook_returns_xlsx(client: TestClient) -> None:
    response = client.get("/api/plans/import/sample")

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert parse_import_workbook(response.content)


def test_import_plan_returns_validation_report(client: TestClient) -> None:
    response = client.post(
        "/api/plans/import",
        data={"plan_name": "Broken", "start_date": "2026-04-06"},
        files={
            "file": (
                "plan.xlsx",
                workbook_bytes([["task", "duration"], ["Discovery", 0]]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "excel_validation_failed"
    assert payload["errors"][0]["row"] == 2
    assert payload["errors"][0]["column"] == "duration"
    assert payload["errors"][0]["code"] == "invalid_duration"


def test_import_plan_rejects_oversized_file(client: TestClient) -> None:
    response = client.post(
        "/api/plans/import",
        data={"plan_name": "Too Large", "start_date": "2026-04-06"},
        files={
            "file": (
                "plan.xlsx",
                b"0" * (5 * 1024 * 1024 + 1),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["errors"][0]["code"] == "file_too_large"


def test_export_plan_returns_xlsx(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    response = client.get("/api/plans/plan-1/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "repository-test-plan.xlsx" in response.headers["content-disposition"]

    workbook = load_workbook(BytesIO(response.content))
    assert workbook["Tasks"]["B2"].value == "Discovery"
    assert workbook["Tasks"]["F3"].value == "Discovery"


def test_export_missing_plan_returns_404(client: TestClient) -> None:
    response = client.get("/api/plans/missing/export")

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan was not found: missing"


def test_export_import_round_trip_preserves_structure(
    client: TestClient,
    db_session: Session,
    sample_plan: Plan,
) -> None:
    repository = SQLAlchemyPlanRepository(db_session)
    repository.save(sample_plan)
    db_session.commit()

    export_response = client.get("/api/plans/plan-1/export")
    parsed_rows = parse_import_workbook(export_response.content)

    assert [row.task for row in parsed_rows] == ["Discovery", "Implementation"]

    import_response = client.post(
        "/api/plans/import",
        data={"plan_name": "Round Trip", "start_date": "2026-02-02"},
        files={
            "file": (
                "round-trip.xlsx",
                export_response.content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert import_response.status_code == 201
    payload = import_response.json()
    assert [task["name"] for task in payload["tasks"]] == ["Discovery", "Implementation"]
    assert len(payload["dependencies"]) == 1
