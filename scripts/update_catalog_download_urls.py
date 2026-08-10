"""Atualiza zip_name e link no XLSX para a API pública (ZIPs individuais)."""
from pathlib import Path

import openpyxl

from src.catalog import CATALOG_PATH, csv_to_zip_name, zip_download_url
from src.config import get_download_base_url


def main() -> None:
    path = CATALOG_PATH
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    base_url = get_download_base_url()
    updated = 0

    for row in ws.iter_rows(min_row=2):
        arquivo_cell, _tabela_cell, _grupo_cell, zip_cell, link_cell = row[:5]
        if not arquivo_cell.value:
            continue
        arquivo = str(arquivo_cell.value).strip()
        zip_name = csv_to_zip_name(arquivo)
        link = zip_download_url(zip_name, base_url)
        if zip_cell.value != zip_name or link_cell.value != link:
            zip_cell.value = zip_name
            link_cell.value = link
            updated += 1

    wb.save(path)
    print(f"Atualizados {updated} linhas em {path}")
    print(f"Base URL: {base_url}")


if __name__ == "__main__":
    main()
