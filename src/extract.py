import logging
import time
import zipfile
from pathlib import Path

from src.config import DOWNLOADS_DIR, EXTRACTED_DIR

logger = logging.getLogger(__name__)

_REPLACE_RETRIES = 8
_REPLACE_RETRY_DELAY_S = 2.0


def _replace_with_retries(temp_path: Path, dest_path: Path) -> None:
    """Substitui dest_path pelo conteúdo de temp_path, com retry no Windows."""
    last_exc: PermissionError | None = None
    for attempt in range(1, _REPLACE_RETRIES + 1):
        try:
            if dest_path.exists():
                dest_path.unlink()
            temp_path.replace(dest_path)
            return
        except PermissionError as exc:
            last_exc = exc
            if attempt < _REPLACE_RETRIES:
                logger.warning(
                    "Arquivo em uso ao gravar '%s' (tentativa %s/%s); "
                    "aguardando %.1fs...",
                    dest_path,
                    attempt,
                    _REPLACE_RETRIES,
                    _REPLACE_RETRY_DELAY_S,
                )
                time.sleep(_REPLACE_RETRY_DELAY_S)

    if (
        last_exc is not None
        and dest_path.exists()
        and temp_path.exists()
        and dest_path.stat().st_size == temp_path.stat().st_size
    ):
        temp_path.unlink(missing_ok=True)
        logger.warning(
            "Não foi possível substituir '%s'; mantendo arquivo existente "
            "(mesmo tamanho do ZIP)",
            dest_path,
        )
        return

    temp_path.unlink(missing_ok=True)
    raise PermissionError(
        f"Sem permissão para gravar '{dest_path}'. "
        "Causas comuns no Windows: antivírus/Defender escaneando o arquivo, "
        "outra execução do pipeline (python) em andamento, ou indexação do disco. "
        "Aguarde alguns segundos e rode novamente; se os CSVs já estão em "
        "data/extracted/, use --skip-download."
    ) from last_exc


def _find_csv_in_zip(zf: zipfile.ZipFile, csv_name: str) -> str | None:
    for name in zf.namelist():
        if Path(name).name == csv_name:
            return name
    return None


def extract_csvs(
    catalog: list[dict],
    downloads_dir: Path | None = None,
    extracted_dir: Path | None = None,
) -> list[Path]:
    downloads_dir = downloads_dir or DOWNLOADS_DIR
    extracted_dir = extracted_dir or EXTRACTED_DIR
    extracted_dir.mkdir(parents=True, exist_ok=True)

    zip_cache: dict[str, zipfile.ZipFile] = {}
    extracted: list[Path] = []

    try:
        for entry in catalog:
            csv_name = entry["arquivo"]
            zip_path = downloads_dir / entry["zip_name"]
            dest_path = extracted_dir / csv_name

            if not zip_path.exists():
                raise FileNotFoundError(f"ZIP não encontrado: {zip_path}")

            if entry["zip_name"] not in zip_cache:
                zip_cache[entry["zip_name"]] = zipfile.ZipFile(zip_path, "r")

            zf = zip_cache[entry["zip_name"]]
            member = _find_csv_in_zip(zf, csv_name)
            if member is None:
                raise FileNotFoundError(
                    f"CSV '{csv_name}' não encontrado em {entry['zip_name']}"
                )

            zip_info = zf.getinfo(member)
            if (
                dest_path.exists()
                and dest_path.stat().st_size == zip_info.file_size
            ):
                logger.info(
                    "Extração ignorada (já extraído): %s (%s bytes)",
                    csv_name,
                    zip_info.file_size,
                )
                extracted.append(dest_path)
                continue

            data = zf.read(member)
            temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
            temp_path.write_bytes(data)
            _replace_with_retries(temp_path, dest_path)

            extracted.append(dest_path)
    finally:
        for zf in zip_cache.values():
            zf.close()

    return extracted
