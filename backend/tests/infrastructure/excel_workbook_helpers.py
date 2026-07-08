from collections.abc import Iterable
from io import BytesIO
from typing import cast

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet


def workbook_bytes(rows: Iterable[Iterable[object]], *, title: str = "Tasks") -> bytes:
    workbook = Workbook()
    worksheet = cast(Worksheet, workbook.active)
    worksheet.title = title
    for row in rows:
        worksheet.append(list(row))

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
