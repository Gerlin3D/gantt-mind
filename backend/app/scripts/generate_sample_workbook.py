from pathlib import Path

from app.infrastructure.excel.exporter import export_plan_to_xlsx
from app.seed import build_demo_plan

SAMPLE_WORKBOOK_PATH = Path(__file__).resolve().parents[3] / "examples" / "gantt-mind-sample.xlsx"


def main() -> None:
    SAMPLE_WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_WORKBOOK_PATH.write_bytes(export_plan_to_xlsx(build_demo_plan()))
    print(f"Wrote {SAMPLE_WORKBOOK_PATH}")


if __name__ == "__main__":
    main()
