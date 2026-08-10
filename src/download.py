import logging
import shutil
import time
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.catalog import get_unique_zips
from src.config import DOWNLOADS_DIR

logger = logging.getLogger(__name__)

_DOWNLOAD_CHUNK_SIZE = 16 * 1024 * 1024  # buffer de escrita em disco (não particiona o ZIP)
_DOWNLOAD_RETRIES = 5
_DOWNLOAD_RETRY_DELAY_S = 5.0
_DOWNLOAD_TIMEOUT_S = 300
_USER_AGENT = "transferegov-carga/1.0"


def _is_valid_zip(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with zipfile.ZipFile(path, "r") as zf:
            return zf.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def download_zip(url: str, dest_path: Path) -> Path:
    """Baixa o ZIP inteiro de uma vez; reinicia do zero a cada tentativa."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
    last_exc: Exception | None = None

    for attempt in range(1, _DOWNLOAD_RETRIES + 1):
        try:
            temp_path.unlink(missing_ok=True)
            req = Request(url, headers={"User-Agent": _USER_AGENT})
            with urlopen(req, timeout=_DOWNLOAD_TIMEOUT_S) as resp, temp_path.open(
                "wb"
            ) as dst:
                shutil.copyfileobj(resp, dst, length=_DOWNLOAD_CHUNK_SIZE)
            temp_path.replace(dest_path)
            break
        except (
            ConnectionResetError,
            ConnectionError,
            TimeoutError,
            URLError,
            OSError,
        ) as exc:
            last_exc = exc
            temp_path.unlink(missing_ok=True)
            dest_path.unlink(missing_ok=True)
            if attempt < _DOWNLOAD_RETRIES:
                delay = _DOWNLOAD_RETRY_DELAY_S * attempt
                logger.warning(
                    "Falha no download de %s (tentativa %s/%s): %s; "
                    "aguardando %.0fs...",
                    dest_path.name,
                    attempt,
                    _DOWNLOAD_RETRIES,
                    exc,
                    delay,
                )
                time.sleep(delay)
            else:
                raise
    else:
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"Falha no download de {url}")

    if not _is_valid_zip(dest_path):
        dest_path.unlink(missing_ok=True)
        raise ValueError(f"Download inválido ou ZIP corrompido: {url}")
    return dest_path


def download_all(catalog: list[dict], downloads_dir: Path | None = None) -> list[Path]:
    downloads_dir = downloads_dir or DOWNLOADS_DIR
    downloads_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []
    for zip_info in get_unique_zips(catalog):
        dest = downloads_dir / zip_info["zip_name"]
        if _is_valid_zip(dest):
            logger.info("Download ignorado (ZIP válido): %s", dest.name)
            downloaded.append(dest)
            continue

        logger.info("Baixando %s...", dest.name)
        downloaded.append(download_zip(zip_info["link"], dest))

    return downloaded
