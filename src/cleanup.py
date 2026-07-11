import logging
import re
from datetime import date, datetime
from pathlib import Path

from src.config import DOWNLOADS_DIR, EXTRACTED_DIR, LOGS_DIR

logger = logging.getLogger(__name__)

LOG_FILE_PATTERN = re.compile(r"^(carga|resumo)_(\d{8})_\d{6}\.(log|json)$")


def _should_skip_file(path: Path) -> bool:
    return path.name.startswith(".")


def _log_file_date(path: Path) -> date | None:
    match = LOG_FILE_PATTERN.match(path.name)
    if not match:
        return None
    stamp = match.group(2)
    return datetime.strptime(stamp, "%Y%m%d").date()


def _file_reference_date(path: Path) -> date:
    log_date = _log_file_date(path)
    if log_date is not None:
        return log_date
    return datetime.fromtimestamp(path.stat().st_mtime).date()


def find_stale_files(today: date | None = None) -> list[Path]:
    """Arquivos de downloads, extraídos e logs com data anterior a hoje."""
    today = today or date.today()
    stale: list[Path] = []

    for directory in (DOWNLOADS_DIR, EXTRACTED_DIR):
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if not path.is_file() or _should_skip_file(path):
                continue
            if _file_reference_date(path) < today:
                stale.append(path)

    if LOGS_DIR.exists():
        for path in LOGS_DIR.iterdir():
            if not path.is_file() or _should_skip_file(path):
                continue
            log_date = _log_file_date(path)
            if log_date is not None and log_date < today:
                stale.append(path)

    return sorted(stale)


def delete_stale_files(today: date | None = None) -> dict:
    today = today or date.today()
    stale = find_stale_files(today)
    deleted: list[str] = []
    errors: list[dict] = []

    for path in stale:
        try:
            path.unlink()
            deleted.append(str(path))
        except OSError as exc:
            errors.append({"path": str(path), "error": str(exc)})

    return {
        "deleted": deleted,
        "deleted_count": len(deleted),
        "errors": errors,
    }


def ensure_stale_files_removed(today: date | None = None) -> dict:
    """Verifica no início da carga e remove resíduos de dias anteriores."""
    today = today or date.today()
    stale = find_stale_files(today)
    if not stale:
        logger.info(
            "Verificação inicial: nenhum arquivo de dias anteriores em "
            "downloads, extracted ou logs"
        )
        return {"had_stale": False, "deleted_count": 0, "deleted": [], "errors": []}

    logger.warning(
        "Verificação inicial: %s arquivo(s) de dias anteriores encontrado(s); "
        "removendo...",
        len(stale),
    )
    result = delete_stale_files(today)
    result["had_stale"] = True
    if result["deleted_count"]:
        logger.info(
            "Limpeza inicial concluída: %s arquivo(s) removido(s)",
            result["deleted_count"],
        )
    if result["errors"]:
        logger.error(
            "Falha ao remover %s arquivo(s) na limpeza inicial",
            len(result["errors"]),
        )
    return result


def cleanup_after_successful_load(today: date | None = None) -> dict:
    """Remove downloads, extraídos e logs de dias anteriores após carga completa."""
    today = today or date.today()
    stale = find_stale_files(today)
    if not stale:
        logger.info(
            "Limpeza pós-carga: nenhum arquivo de dias anteriores para remover"
        )
        return {"deleted_count": 0, "deleted": [], "errors": []}

    logger.info(
        "Limpeza pós-carga: removendo %s arquivo(s) de dias anteriores",
        len(stale),
    )
    result = delete_stale_files(today)
    if result["deleted_count"]:
        logger.info(
            "Limpeza pós-carga concluída: %s arquivo(s) removido(s)",
            result["deleted_count"],
        )
    if result["errors"]:
        logger.error(
            "Falha ao remover %s arquivo(s) na limpeza pós-carga",
            len(result["errors"]),
        )
    return result
