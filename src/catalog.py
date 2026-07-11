from pathlib import Path

import openpyxl

from src.config import DATA_DIR

CATALOG_PATH = DATA_DIR / "lista_arquivo_tabela.xlsx"


def load_catalog(path: Path | None = None) -> list[dict]:
    xlsx_path = path or CATALOG_PATH
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb.active

    entries = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        arquivo, tabela, grupo, zip_name, link = row
        if not arquivo:
            continue

        tabelas = [t.strip() for t in str(tabela).split(",") if t.strip()]
        entries.append(
            {
                "arquivo": str(arquivo).strip(),
                "tabelas": tabelas,
                "grupo": str(grupo).strip() if grupo else "",
                "zip_name": str(zip_name).strip(),
                "link": str(link).strip(),
            }
        )

    wb.close()
    return entries


def get_unique_zips(catalog: list[dict] | None = None) -> list[dict]:
    catalog = catalog or load_catalog()
    seen: set[str] = set()
    zips: list[dict] = []

    for entry in catalog:
        zip_name = entry["zip_name"]
        if zip_name in seen:
            continue
        seen.add(zip_name)
        zips.append({"zip_name": zip_name, "link": entry["link"]})

    return zips
