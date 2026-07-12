import csv
import io
import logging
from collections.abc import Iterator
from pathlib import Path

from src.cipi_schema import CIPI_TEXT_COLUMNS
from src.config import get_copy_chunk_rows, get_csv_encoding
from src.db_meta import (
    INTEGER_TYPES,
    NUMERIC_TYPES,
    get_table_column_char_max_lengths,
    get_table_column_types,
    get_table_columns,
    normalize_column,
    qualified_staging,
    qualified_table,
    staging_table_name,
    table_exists,
)

logger = logging.getLogger(__name__)

STAGING_LOADED_COLUMNS: dict[str, list[str]] = {}


def create_staging_table(conn, target_table: str) -> None:
    if not table_exists(conn, target_table):
        raise ValueError(f"Tabela destino não existe: {target_table}")

    stg = staging_table_name(target_table)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TEMP TABLE IF NOT EXISTS {qualified_staging(target_table)}
            (LIKE {qualified_table(target_table)} INCLUDING ALL)
            ON COMMIT PRESERVE ROWS
            """
        )
        cur.execute(f"TRUNCATE {qualified_staging(target_table)}")


def truncate_staging(conn, target_table: str) -> None:
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {qualified_staging(target_table)}")


def _read_csv_header(csv_path: Path, delimiter: str, encoding: str) -> list[str]:
    with csv_path.open(encoding=encoding, newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        return [normalize_column(col) for col in next(reader)]


def _resolve_columns(
    conn,
    target_table: str,
    csv_path: Path,
    columns: list[str] | None,
    delimiter: str,
    encoding: str,
) -> list[str]:
    db_columns = set(get_table_columns(conn, target_table))
    if columns:
        selected = [normalize_column(c) for c in columns]
    else:
        csv_header = _read_csv_header(csv_path, delimiter, encoding)
        selected = [c for c in csv_header if c in db_columns]

    missing = [c for c in selected if c not in db_columns]
    if missing:
        raise ValueError(
            f"Colunas não encontradas em {target_table}: {', '.join(missing)}"
        )
    if not selected:
        raise ValueError(f"Nenhuma coluna compatível entre CSV e {target_table}")
    return selected


def _normalize_decimal_separators(value: str) -> str:
    if "," in value and "." not in value:
        return value.replace(".", "").replace(",", ".")
    if "," in value:
        return value.replace(",", ".")
    return value


def _normalize_date_value(value: str) -> str:
    parts = value.split("/")
    if len(parts) == 3 and len(parts[0]) <= 2 and len(parts[1]) <= 2 and len(parts[2]) == 4:
        day, month, year = parts
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return value


def _normalize_value(
    value: str,
    data_type: str | None,
    column_name: str | None = None,
    char_max_length: int | None = None,
) -> str:
    if value is None:
        return ""
    value = value.strip()
    if value == "":
        return ""
    if column_name and "cep" in column_name.lower():
        value = value.replace(".", "")
    if data_type in NUMERIC_TYPES:
        value = _normalize_decimal_separators(value)
    if (
        data_type in INTEGER_TYPES
        and value
        and not (column_name and column_name in CIPI_TEXT_COLUMNS)
    ):
        try:
            if "." in value:
                return str(int(round(float(value))))
            int(value)
            return value
        except ValueError:
            return ""
    if data_type == "date" and value and "/" in value:
        value = _normalize_date_value(value)
    if char_max_length is not None and len(value) > char_max_length:
        value = value[:char_max_length]
    return value


def _normalize_row(
    row: list[str],
    indexes: list[int],
    selected_columns: list[str],
    column_types: dict[str, str],
    char_max_lengths: dict[str, int],
) -> list[str]:
    out = []
    for idx, col in zip(indexes, selected_columns):
        value = row[idx] if idx < len(row) else ""
        out.append(
            _normalize_value(
                value,
                column_types.get(col),
                column_name=col,
                char_max_length=char_max_lengths.get(col),
            )
        )
    return out


def _row_passes_required(out: list[str], required_indexes: list[int] | None) -> bool:
    if required_indexes is None:
        return True
    return all(out[i] for i in required_indexes)


def _csv_column_indexes(
    header: list[str],
    selected_columns: list[str],
    csv_column_sources: dict[str, str] | None = None,
) -> list[int]:
    indexes = []
    for col in selected_columns:
        source = (csv_column_sources or {}).get(col, col)
        if source not in header:
            raise ValueError(
                f"Coluna CSV '{source}' não encontrada (destino: {col})"
            )
        indexes.append(header.index(source))
    return indexes


def _iter_staging_rows(
    csv_path: Path,
    selected_columns: list[str],
    column_types: dict[str, str],
    char_max_lengths: dict[str, int],
    delimiter: str,
    encoding: str,
    dedupe_columns: list[str] | None = None,
    required_columns: list[str] | None = None,
    csv_column_sources: dict[str, str] | None = None,
) -> Iterator[list[str]]:
    dedupe_indexes = None
    if dedupe_columns:
        dedupe_indexes = [selected_columns.index(c) for c in dedupe_columns]
    required_indexes = None
    if required_columns:
        required_indexes = [selected_columns.index(c) for c in required_columns]

    with csv_path.open(encoding=encoding, newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = [normalize_column(col) for col in next(reader)]
        indexes = _csv_column_indexes(header, selected_columns, csv_column_sources)

        if dedupe_indexes is not None:
            seen_keys: dict[tuple[str, ...], list[str]] = {}
            for row in reader:
                out = _normalize_row(
                    row, indexes, selected_columns, column_types, char_max_lengths
                )
                if not _row_passes_required(out, required_indexes):
                    continue
                key = tuple(out[i] for i in dedupe_indexes)
                if not all(key):
                    continue
                seen_keys[key] = out
            yield from seen_keys.values()
            return

        for row in reader:
            out = _normalize_row(
                row, indexes, selected_columns, column_types, char_max_lengths
            )
            if not _row_passes_required(out, required_indexes):
                continue
            yield out


def _copy_buffer(
    rows: list[list[str]],
    selected_columns: list[str],
    delimiter: str,
    include_header: bool,
) -> io.StringIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    if include_header:
        writer.writerow(selected_columns)
    writer.writerows(rows)
    buffer.seek(0)
    return buffer


def _iter_copy_chunk_buffers(
    rows: Iterator[list[str]],
    selected_columns: list[str],
    delimiter: str,
    chunk_rows: int,
) -> Iterator[tuple[io.StringIO, int, bool]]:
    chunk: list[list[str]] = []
    include_header = True
    for row in rows:
        chunk.append(row)
        if len(chunk) >= chunk_rows:
            yield _copy_buffer(chunk, selected_columns, delimiter, include_header), len(
                chunk
            ), include_header
            chunk = []
            include_header = False
    if chunk:
        yield _copy_buffer(chunk, selected_columns, delimiter, include_header), len(
            chunk
        ), include_header


def _copy_rows_to_staging(
    conn,
    target_table: str,
    selected_columns: list[str],
    rows: Iterator[list[str]],
    delimiter: str,
    chunk_rows: int,
) -> int:
    col_list = ", ".join(f'"{c}"' for c in selected_columns)
    chunks = 0
    rows_copied = 0

    with conn.cursor() as cur:
        for buffer, row_count, include_header in _iter_copy_chunk_buffers(
            rows, selected_columns, delimiter, chunk_rows
        ):
            header = "true" if include_header else "false"
            copy_sql = (
                f"COPY {qualified_staging(target_table)} ({col_list}) "
                f"FROM STDIN WITH (FORMAT csv, HEADER {header}, "
                f"DELIMITER '{delimiter}', NULL '')"
            )
            cur.execute("SET datestyle = 'ISO, DMY'")
            cur.copy_expert(copy_sql, buffer)
            chunks += 1
            rows_copied += row_count

        cur.execute(f"SELECT COUNT(*) FROM {qualified_staging(target_table)}")
        count = cur.fetchone()[0]

    if chunks > 1:
        logger.info(
            "COPY em %s chunks (%s linhas enviadas) para %s; staging=%s",
            chunks,
            rows_copied,
            target_table,
            count,
        )
    return count


def load_csv_to_staging(
    conn,
    csv_path: str | Path,
    target_table: str,
    delimiter: str = ";",
    encoding: str | None = None,
    columns: list[str] | None = None,
    dedupe_columns: list[str] | None = None,
    required_columns: list[str] | None = None,
    chunk_rows: int | None = None,
    csv_column_sources: dict[str, str] | None = None,
) -> int:
    csv_path = Path(csv_path)
    csv_encoding = encoding or get_csv_encoding()
    create_staging_table(conn, target_table)
    selected_columns = _resolve_columns(
        conn, target_table, csv_path, columns, delimiter, csv_encoding
    )
    column_types = get_table_column_types(conn, target_table)
    char_max_lengths = get_table_column_char_max_lengths(conn, target_table)
    batch_size = chunk_rows if chunk_rows is not None else get_copy_chunk_rows()

    rows = _iter_staging_rows(
        csv_path,
        selected_columns,
        column_types,
        char_max_lengths,
        delimiter,
        csv_encoding,
        dedupe_columns=dedupe_columns,
        required_columns=required_columns,
        csv_column_sources=csv_column_sources,
    )
    count = _copy_rows_to_staging(
        conn,
        target_table,
        selected_columns,
        rows,
        delimiter,
        batch_size,
    )

    STAGING_LOADED_COLUMNS[target_table] = selected_columns
    return count


def load_sql_to_staging(
    conn,
    target_table: str,
    insert_sql: str,
    loaded_columns: list[str],
) -> int:
    create_staging_table(conn, target_table)
    with conn.cursor() as cur:
        cur.execute(insert_sql)
        cur.execute(f"SELECT COUNT(*) FROM {qualified_staging(target_table)}")
        count = cur.fetchone()[0]

    STAGING_LOADED_COLUMNS[target_table] = loaded_columns
    return count
