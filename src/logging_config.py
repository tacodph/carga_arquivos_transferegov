import json
import logging
from datetime import datetime
from pathlib import Path

from src.config import LOGS_DIR

RUN_SUMMARY: dict = {}
LAST_SUMMARY_PATH: Path | None = None


def setup_logging() -> tuple[logging.Logger, Path, Path]:
    global LAST_SUMMARY_PATH
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"carga_{timestamp}.log"
    summary_path = LOGS_DIR / f"resumo_{timestamp}.json"
    LAST_SUMMARY_PATH = summary_path

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    logger = logging.getLogger("carga")
    RUN_SUMMARY.clear()
    RUN_SUMMARY.update(
        {
            "started_at": datetime.now().isoformat(),
            "tables": [],
            "errors": [],
            "log_file": str(log_path),
            "summary_file": str(summary_path),
        }
    )
    return logger, log_path, summary_path


def record_table_result(table: str, result: dict, duration_sec: float) -> None:
    RUN_SUMMARY.setdefault("tables", []).append(
        {
            "table": table,
            "updated": result.get("updated", 0),
            "inserted": result.get("inserted", 0),
            "skipped": result.get("skipped", False),
            "duration_sec": round(duration_sec, 2),
        }
    )


def record_error(table: str, error: str) -> None:
    RUN_SUMMARY.setdefault("errors", []).append({"table": table, "error": error})


def save_summary(summary_path: Path) -> None:
    RUN_SUMMARY["finished_at"] = datetime.now().isoformat()
    summary_path.write_text(
        json.dumps(RUN_SUMMARY, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
