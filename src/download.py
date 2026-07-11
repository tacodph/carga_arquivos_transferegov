import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from src.catalog import get_unique_zips
from src.config import DOWNLOADS_DIR


def _is_valid_zip(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with zipfile.ZipFile(path, "r") as zf:
            return zf.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def download_zip(url: str, dest_path: Path) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, dest_path)
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
            downloaded.append(dest)
            continue

        downloaded.append(download_zip(zip_info["link"], dest))

    return downloaded
