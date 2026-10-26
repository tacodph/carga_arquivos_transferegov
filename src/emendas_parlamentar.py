"""Carga das emendas por ano com o parlamentar normalizado.

Lê siconv_emenda.csv e apoiadores_emendas_programas.csv (fotos completas) e
grava em tabelas com chave natural real:

- tab_autores_emendas / tab_parlamentares / tab_parlamentares_alias
- tab_emendas_beneficiarios_ano
- tab_emendas_apoiadores
- vw_emendas_resumo_ano (materializada)

O parlamentar é identificado pelo código do autor = left(nr_emenda, 4), que é
estável no siconv; o nome vira atributo. Carga incremental e update são o
mesmo passo: INSERT ... ON CONFLICT DO UPDATE só quando o row_hash muda.
Chaves ativas que não vieram na foto são inativadas (fl_ativo = false).

DDL: docs/sql/emendas_parlamentar.sql
"""

import csv
import io
import logging
import re
import unicodedata
from datetime import date
from collections.abc import Iterable
from pathlib import Path

from src.config import EXTRACTED_DIR, get_csv_encoding, get_db_config
from src.db_meta import qualified_table, table_exists
from src.staging import _normalize_decimal_separators

logger = logging.getLogger(__name__)

SICONV_EMENDA_CSV = "siconv_emenda.csv"
APOIADORES_CSV = "apoiadores_emendas_programas.csv"

TABLES = (
    "tab_parlamentares",
    "tab_autores_emendas",
    "tab_parlamentares_alias",
    "tab_emendas_beneficiarios_ano",
    "tab_emendas_apoiadores",
)

ANO_MIN = 2000
ANO_MAX = date.today().year + 2

# Trava (pg_advisory_xact_lock) comum às cargas que gravam parlamentar: esta,
# a das transferências especiais e a do fundo a fundo.
CHAVE_TRAVA_PARLAMENTAR = 7465100

# Só inativa o que sumiu se a foto nova tiver ao menos esta fração das linhas
# ativas — protege contra CSV truncado ou download parcial.
INATIVACAO_MIN_RATIO = 0.8


def normalize_nome(value: str | None) -> str:
    """Upper, sem acento, só letras/dígitos e espaço simples."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Z0-9 ]", " ", text.upper())
    return re.sub(r"\s+", " ", text).strip()


def _decimal(value: str | None) -> str:
    value = (value or "").strip()
    return _normalize_decimal_separators(value) if value else ""


def _as_float(value: str) -> float:
    try:
        return float(value) if value else 0.0
    except ValueError:
        return 0.0


def _ano_from_cod_programa(cod_programa: str) -> int | None:
    # cod_programa_emenda = órgão (5) + ano (4) + sequência (4)
    if len(cod_programa) != 13 or not cod_programa.isdigit():
        return None
    ano = int(cod_programa[5:9])
    return ano if ANO_MIN <= ano <= ANO_MAX else None


def _read_csv(csv_path: Path) -> Iterable[dict[str, str]]:
    with csv_path.open(encoding=get_csv_encoding(), newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        header = [c.strip().lower().replace("﻿", "") for c in next(reader)]
        for row in reader:
            yield {col: (row[i].strip() if i < len(row) else "") for i, col in enumerate(header)}


def _copy_rows(cur, table: str, columns: list[str], rows: Iterable[list]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerows(rows)
    buffer.seek(0)
    cols = ", ".join(f'"{c}"' for c in columns)
    cur.copy_expert(
        f'COPY "{table}" ({cols}) FROM STDIN WITH (FORMAT csv, DELIMITER \';\', NULL \'\')',
        buffer,
    )


# ---------------------------------------------------------------------------
# Staging
# ---------------------------------------------------------------------------

STG_BENEF_COLUMNS = [
    "ano",
    "nr_emenda",
    "cod_autor",
    "cod_programa_emenda",
    "beneficiario_emenda",
    "id_proposta",
    "qualif_proponente",
    "ind_impositivo",
    "tipo_parlamentar",
    "nome_parlamentar",
    "nome_normalizado",
    "valor_repasse_proposta_emenda",
    "valor_repasse_emenda",
]

STG_APOIO_COLUMNS = [
    "id_cnpj_programa_emenda",
    "parlamentar_solicitante",
    "solicitante_normalizado",
    "nr_emenda",
    "cod_autor",
    "nome_parlamentar",
    "nome_normalizado",
    "indicacao",
    "id_programa",
    "cnpj_proponente",
    "nome_proponente",
    "valor_repasse_proposta",
]


def _stage_siconv_emenda(cur, csv_path: Path) -> dict:
    cur.execute(
        """
        CREATE TEMP TABLE IF NOT EXISTS stg_emendas_beneficiarios_ano (
            ano smallint, nr_emenda varchar(10), cod_autor char(4),
            cod_programa_emenda varchar(20), beneficiario_emenda varchar(20),
            id_proposta integer, qualif_proponente varchar(100),
            ind_impositivo varchar(5), tipo_parlamentar varchar(30),
            nome_parlamentar varchar(200), nome_normalizado varchar(200),
            valor_repasse_proposta_emenda numeric(19,2),
            valor_repasse_emenda numeric(19,2)
        ) ON COMMIT PRESERVE ROWS
        """
    )
    cur.execute("TRUNCATE stg_emendas_beneficiarios_ano")

    rows: dict[tuple, list] = {}
    stats = {"lidas": 0, "sem_emenda": 0, "ano_invalido": 0, "chave_duplicada": 0}
    for r in _read_csv(csv_path):
        stats["lidas"] += 1
        nr_emenda = r.get("nr_emenda", "")
        if not nr_emenda.isdigit() or len(nr_emenda) < 5:
            stats["sem_emenda"] += 1
            continue
        cod_programa = r.get("cod_programa_emenda", "")
        ano = _ano_from_cod_programa(cod_programa)
        beneficiario = r.get("beneficiario_emenda", "")
        if ano is None or not beneficiario:
            stats["ano_invalido"] += 1
            continue
        id_proposta = r.get("id_proposta", "") or "0"
        nome = r.get("nome_parlamentar", "")
        out = [
            ano,
            nr_emenda,
            nr_emenda[:4],
            cod_programa,
            beneficiario,
            id_proposta,
            r.get("qualif_proponente", ""),
            normalize_nome(r.get("ind_impositivo")),
            r.get("tipo_parlamentar", ""),
            nome,
            normalize_nome(nome),
            _decimal(r.get("valor_repasse_proposta_emenda")),
            _decimal(r.get("valor_repasse_emenda")),
        ]
        key = (ano, nr_emenda, cod_programa, beneficiario, id_proposta)
        current = rows.get(key)
        if current is not None:
            stats["chave_duplicada"] += 1
            # Mesma chave com valores diferentes (só ocorre sem proposta):
            # fica a linha de maior valor, sem somar para não dobrar.
            if _as_float(out[11]) <= _as_float(current[11]):
                continue
        rows[key] = out

    _copy_rows(cur, "stg_emendas_beneficiarios_ano", STG_BENEF_COLUMNS, rows.values())
    stats["staging"] = len(rows)
    return stats


def _stage_apoiadores(cur, csv_path: Path) -> dict:
    cur.execute(
        """
        CREATE TEMP TABLE IF NOT EXISTS stg_emendas_apoiadores (
            id_cnpj_programa_emenda integer, parlamentar_solicitante varchar(200),
            solicitante_normalizado varchar(200), nr_emenda varchar(10),
            cod_autor char(4), nome_parlamentar varchar(200),
            nome_normalizado varchar(200), indicacao varchar(30),
            id_programa integer, cnpj_proponente varchar(20),
            nome_proponente varchar(255), valor_repasse_proposta numeric(19,2)
        ) ON COMMIT PRESERVE ROWS
        """
    )
    cur.execute("TRUNCATE stg_emendas_apoiadores")

    rows: dict[tuple, list] = {}
    stats = {"lidas": 0, "sem_id": 0, "chave_duplicada": 0}
    for r in _read_csv(csv_path):
        stats["lidas"] += 1
        id_registro = r.get("id_cnpj_programa_emenda_apoiadores_emendas", "")
        if not id_registro.isdigit():
            stats["sem_id"] += 1
            continue
        nr_emenda = r.get("numero_emenda_apoiadores_emendas", "")
        if not nr_emenda.isdigit():
            nr_emenda = ""
        nome = r.get("nome_parlamentar_apoiadores_emendas", "")
        solicitante = r.get("parlamentar_solicitante_apoiadores_emendas", "")
        out = [
            id_registro,
            solicitante,
            normalize_nome(solicitante),
            nr_emenda,
            nr_emenda[:4] if len(nr_emenda) >= 5 else "",
            nome,
            normalize_nome(nome),
            r.get("indicacao_apoiadores_emendas", ""),
            r.get("id_programa", ""),
            r.get("cnpj_proponente_apoiadores_emendas", ""),
            r.get("nome_proponente_apoiadores_emendas", ""),
            _decimal(r.get("valor_repasse_proposta_apoiadores_emendas")),
        ]
        key = (id_registro, solicitante)
        if key in rows:
            stats["chave_duplicada"] += 1
        rows[key] = out

    _copy_rows(cur, "stg_emendas_apoiadores", STG_APOIO_COLUMNS, rows.values())
    # COPY grava '' como NULL; a chave usa '' para "sem solicitante"
    cur.execute(
        "UPDATE stg_emendas_apoiadores SET parlamentar_solicitante = '' "
        "WHERE parlamentar_solicitante IS NULL"
    )
    stats["staging"] = len(rows)
    return stats


# ---------------------------------------------------------------------------
# Parlamentar
# ---------------------------------------------------------------------------


def _sync_autores(cur, stg_sql: str, origem: str) -> dict:
    """Grava códigos de autor e liga cada um a um parlamentar.

    stg_sql: SELECT cod_autor, nome_parlamentar, nome_normalizado, tipo_parlamentar
    (uma linha por código). Do siconv o nome sobrescreve; do apoiadores só
    entram códigos que o siconv não conhece.
    """
    autores = qualified_table("tab_autores_emendas")
    parlamentares = qualified_table("tab_parlamentares")
    alias = qualified_table("tab_parlamentares_alias")

    cur.execute("SELECT pg_advisory_xact_lock(%s)", (CHAVE_TRAVA_PARLAMENTAR,))
    cur.execute("DROP TABLE IF EXISTS stg_autores")
    cur.execute(f"CREATE TEMP TABLE stg_autores AS {stg_sql}")

    if origem == "siconv_emenda":
        conflict = """
            DO UPDATE SET
                nome_parlamentar = EXCLUDED.nome_parlamentar,
                nome_normalizado = EXCLUDED.nome_normalizado,
                tipo_parlamentar = EXCLUDED.tipo_parlamentar,
                origem = EXCLUDED.origem,
                dte_carga = now()
            WHERE a.nome_normalizado IS DISTINCT FROM EXCLUDED.nome_normalizado
               OR a.tipo_parlamentar IS DISTINCT FROM EXCLUDED.tipo_parlamentar
               OR a.origem <> EXCLUDED.origem
        """
    else:
        # apoiadores só preenche código que o siconv trouxe sem nome
        conflict = """
            DO UPDATE SET
                nome_parlamentar = EXCLUDED.nome_parlamentar,
                nome_normalizado = EXCLUDED.nome_normalizado,
                origem = EXCLUDED.origem,
                dte_carga = now()
            WHERE COALESCE(a.nome_normalizado, '') = ''
        """
    cur.execute(
        f"""
        INSERT INTO {autores} AS a
            (cod_autor, nome_parlamentar, nome_normalizado, tipo_parlamentar, origem)
        SELECT cod_autor, nome_parlamentar, nome_normalizado, tipo_parlamentar, %s
        FROM stg_autores
        ON CONFLICT (cod_autor) {conflict}
        """,
        (origem,),
    )
    autores_gravados = cur.rowcount

    # 1) Liga pelo alias já conhecido (resolve a mesma pessoa em outro código).
    cur.execute(
        f"""
        UPDATE {autores} AS a
        SET id_parlamentar = al.id_parlamentar, dte_carga = now()
        FROM {alias} AS al
        WHERE a.id_parlamentar IS NULL
          AND a.nome_normalizado <> ''
          AND al.nome_normalizado = a.nome_normalizado
        """
    )
    # 2) Cria parlamentar para os nomes ainda sem dono e liga.
    cur.execute(
        f"""
        INSERT INTO {parlamentares} (nome_parlamentar, nome_normalizado, tipo_parlamentar)
        SELECT DISTINCT ON (a.nome_normalizado)
               a.nome_parlamentar, a.nome_normalizado, a.tipo_parlamentar
        FROM {autores} AS a
        WHERE a.id_parlamentar IS NULL AND a.nome_normalizado <> ''
        ORDER BY a.nome_normalizado, a.cod_autor DESC
        """
    )
    parlamentares_novos = cur.rowcount
    cur.execute(
        f"""
        INSERT INTO {alias} (nome_normalizado, nome_original, id_parlamentar, origem)
        SELECT p.nome_normalizado, p.nome_parlamentar, p.id_parlamentar, %s
        FROM {parlamentares} AS p
        WHERE NOT EXISTS (SELECT 1 FROM {alias} al WHERE al.nome_normalizado = p.nome_normalizado)
        ON CONFLICT (nome_normalizado) DO NOTHING
        """,
        (origem,),
    )
    cur.execute(
        f"""
        UPDATE {autores} AS a
        SET id_parlamentar = al.id_parlamentar, dte_carga = now()
        FROM {alias} AS al
        WHERE a.id_parlamentar IS NULL
          AND a.nome_normalizado <> ''
          AND al.nome_normalizado = a.nome_normalizado
        """
    )
    return {"autores_gravados": autores_gravados, "parlamentares_novos": parlamentares_novos}


def _sync_alias_apoiadores(cur) -> int:
    """Grava as grafias do apoiadores como alias do parlamentar do código.

    Se a grafia já pertence a outro parlamentar, o código fica para revisão
    (ex.: mesmo código com nomes de pessoas diferentes nas duas fontes).
    """
    autores = qualified_table("tab_autores_emendas")
    alias = qualified_table("tab_parlamentares_alias")

    cur.execute(
        f"""
        INSERT INTO {alias} (nome_normalizado, nome_original, id_parlamentar, origem)
        SELECT DISTINCT ON (s.nome_normalizado)
               s.nome_normalizado, s.nome_parlamentar, a.id_parlamentar, 'apoiadores'
        FROM stg_emendas_apoiadores AS s
        JOIN {autores} AS a ON a.cod_autor = s.cod_autor
        WHERE s.nome_normalizado <> '' AND a.id_parlamentar IS NOT NULL
        ORDER BY s.nome_normalizado, s.cod_autor
        ON CONFLICT (nome_normalizado) DO NOTHING
        """
    )
    novos = cur.rowcount
    cur.execute(
        f"""
        UPDATE {autores} AS a
        SET fl_revisar = true, dte_carga = now()
        WHERE NOT a.fl_revisar
          AND EXISTS (
              SELECT 1
              FROM stg_emendas_apoiadores AS s
              JOIN {alias} AS al ON al.nome_normalizado = s.nome_normalizado
              WHERE s.cod_autor = a.cod_autor
                AND al.id_parlamentar <> a.id_parlamentar
          )
        """
    )
    if cur.rowcount:
        logger.warning("%s códigos de autor marcados para revisão (nome conflitante)", cur.rowcount)
    return novos


# ---------------------------------------------------------------------------
# Upsert + inativação
# ---------------------------------------------------------------------------


def _upsert(cur, table: str, key: list[str], columns: list[str], select_sql: str) -> dict:
    """INSERT ... ON CONFLICT DO UPDATE só quando o row_hash muda."""
    dest = qualified_table(table)
    all_cols = columns + ["row_hash"]
    cols_sql = ", ".join(f'"{c}"' for c in all_cols)
    set_sql = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in all_cols if c not in key)
    key_sql = ", ".join(f'"{c}"' for c in key)
    cur.execute(
        f"""
        WITH upserted AS (
            INSERT INTO {dest} AS t ({cols_sql})
            {select_sql}
            ON CONFLICT ({key_sql}) DO UPDATE SET
                {set_sql},
                fl_ativo = true,
                dte_inativacao = NULL,
                dte_carga = now()
            WHERE t.row_hash <> EXCLUDED.row_hash OR NOT t.fl_ativo
            RETURNING (xmax = 0) AS inserido
        )
        SELECT COUNT(*) FILTER (WHERE inserido), COUNT(*) FILTER (WHERE NOT inserido)
        FROM upserted
        """
    )
    inserted, updated = cur.fetchone()
    return {"inserted": inserted, "updated": updated}


def _inativar_ausentes(cur, table: str, staging: str, key: list[str]) -> int:
    dest = qualified_table(table)
    cur.execute(f"SELECT COUNT(*) FROM {staging}")
    stg_count = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {dest} WHERE fl_ativo")
    ativos = cur.fetchone()[0]
    if ativos and stg_count < ativos * INATIVACAO_MIN_RATIO:
        logger.warning(
            "%s: foto com %s linhas para %s ativas; inativação pulada (possível CSV parcial)",
            table,
            stg_count,
            ativos,
        )
        return 0
    match = " AND ".join(f's."{c}" = t."{c}"' for c in key)
    cur.execute(
        f"""
        UPDATE {dest} AS t
        SET fl_ativo = false, dte_inativacao = now(), dte_carga = now()
        WHERE t.fl_ativo
          AND NOT EXISTS (SELECT 1 FROM {staging} AS s WHERE {match})
        """
    )
    return cur.rowcount


BENEF_KEY = ["ano", "nr_emenda", "cod_programa_emenda", "beneficiario_emenda", "id_proposta"]
BENEF_COLUMNS = BENEF_KEY + [
    "cod_autor",
    "qualif_proponente",
    "ind_impositivo",
    "tipo_parlamentar",
    "valor_repasse_proposta_emenda",
    "valor_repasse_emenda",
]

APOIO_KEY = ["id_cnpj_programa_emenda", "parlamentar_solicitante"]
APOIO_COLUMNS = APOIO_KEY + [
    "nr_emenda",
    "cod_autor",
    "ano",
    "nome_parlamentar",
    "indicacao",
    "id_parlamentar_solicitante",
    "id_programa",
    "cnpj_proponente",
    "nome_proponente",
    "valor_repasse_proposta",
]


def _row_hash(alias: str, columns: list[str]) -> str:
    parts = ", ".join(f"{alias}.{c}::text" for c in columns)
    return f"md5(concat_ws('|', {parts}))"


def carga_siconv_emenda(conn, csv_path: Path | None = None) -> dict:
    csv_path = csv_path or EXTRACTED_DIR / SICONV_EMENDA_CSV
    with conn.cursor() as cur:
        stats = _stage_siconv_emenda(cur, csv_path)
        stats.update(
            _sync_autores(
                cur,
                """
                SELECT DISTINCT ON (cod_autor)
                       cod_autor, nome_parlamentar, nome_normalizado, tipo_parlamentar
                FROM stg_emendas_beneficiarios_ano
                WHERE nome_normalizado <> ''
                ORDER BY cod_autor, ano DESC
                """,
                "siconv_emenda",
            )
        )
        # Autores sem nome no siconv ainda precisam existir (FK lógica).
        cur.execute(
            f"""
            INSERT INTO {qualified_table("tab_autores_emendas")} (cod_autor, origem)
            SELECT DISTINCT cod_autor, 'siconv_emenda' FROM stg_emendas_beneficiarios_ano
            ON CONFLICT (cod_autor) DO NOTHING
            """
        )
        data_cols = [c for c in BENEF_COLUMNS if c not in BENEF_KEY]
        select_cols = ", ".join(f"s.{c}" for c in BENEF_COLUMNS)
        result = _upsert(
            cur,
            "tab_emendas_beneficiarios_ano",
            BENEF_KEY,
            BENEF_COLUMNS,
            f"SELECT {select_cols}, {_row_hash('s', data_cols)} FROM stg_emendas_beneficiarios_ano AS s",
        )
        result["inativados"] = _inativar_ausentes(
            cur, "tab_emendas_beneficiarios_ano", "stg_emendas_beneficiarios_ano", BENEF_KEY
        )
    conn.commit()
    result["stats"] = stats
    logger.info("tab_emendas_beneficiarios_ano: %s", result)
    return result


def carga_apoiadores(conn, csv_path: Path | None = None) -> dict:
    csv_path = csv_path or EXTRACTED_DIR / APOIADORES_CSV
    autores = qualified_table("tab_autores_emendas")
    alias = qualified_table("tab_parlamentares_alias")
    programas = qualified_table("tab_programas")
    with conn.cursor() as cur:
        stats = _stage_apoiadores(cur, csv_path)
        stats.update(
            _sync_autores(
                cur,
                """
                SELECT DISTINCT ON (cod_autor)
                       cod_autor, nome_parlamentar, nome_normalizado, NULL::varchar AS tipo_parlamentar
                FROM stg_emendas_apoiadores
                WHERE cod_autor <> '' AND nome_normalizado <> ''
                ORDER BY cod_autor, id_cnpj_programa_emenda DESC
                """,
                "apoiadores",
            )
        )
        stats["alias_novos"] = _sync_alias_apoiadores(cur)

        # ano vem do cod_programa (dígitos 6–9) via tab_programas, quando carregada
        ano_sql = "NULL::smallint"
        join_sql = ""
        if table_exists(conn, "tab_programas"):
            ano_sql = (
                "CASE WHEN pr.cod_programa::text ~ '^[0-9]{13}$' "
                "THEN substring(pr.cod_programa::text, 6, 4)::smallint END"
            )
            join_sql = (
                f"LEFT JOIN (SELECT DISTINCT ON (id_programa) id_programa, cod_programa "
                f"FROM {programas}) AS pr ON pr.id_programa = s.id_programa"
            )
        data_cols = [c for c in APOIO_COLUMNS if c not in APOIO_KEY]
        result = _upsert(
            cur,
            "tab_emendas_apoiadores",
            APOIO_KEY,
            APOIO_COLUMNS,
            f"""
            SELECT x.*, {_row_hash('x', data_cols)}
            FROM (
                SELECT
                    s.id_cnpj_programa_emenda,
                    s.parlamentar_solicitante,
                    NULLIF(s.nr_emenda, '') AS nr_emenda,
                    NULLIF(s.cod_autor, '') AS cod_autor,
                    {ano_sql} AS ano,
                    COALESCE(NULLIF(s.nome_parlamentar, ''), a.nome_parlamentar) AS nome_parlamentar,
                    NULLIF(s.indicacao, '') AS indicacao,
                    al.id_parlamentar AS id_parlamentar_solicitante,
                    s.id_programa,
                    s.cnpj_proponente,
                    s.nome_proponente,
                    s.valor_repasse_proposta
                FROM stg_emendas_apoiadores AS s
                LEFT JOIN {autores} AS a ON a.cod_autor = s.cod_autor
                LEFT JOIN {alias} AS al
                       ON al.nome_normalizado = s.solicitante_normalizado
                      AND s.solicitante_normalizado <> ''
                {join_sql}
            ) AS x
            """,
        )
        result["inativados"] = _inativar_ausentes(
            cur, "tab_emendas_apoiadores", "stg_emendas_apoiadores", APOIO_KEY
        )
        cur.execute(
            """
            SELECT COUNT(*) FILTER (WHERE solicitante_normalizado <> ''),
                   COUNT(*) FILTER (WHERE solicitante_normalizado <> '' AND NOT EXISTS (
                       SELECT 1 FROM {alias} al WHERE al.nome_normalizado = s.solicitante_normalizado))
            FROM stg_emendas_apoiadores AS s
            """.format(alias=alias)
        )
        com_solicitante, sem_match = cur.fetchone()
        stats["solicitantes"] = com_solicitante
        stats["solicitantes_sem_parlamentar"] = sem_match
    conn.commit()
    result["stats"] = stats
    logger.info("tab_emendas_apoiadores: %s", result)
    return result


def refresh_resumo(conn) -> None:
    view = qualified_table("vw_emendas_resumo_ano")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ispopulated FROM pg_matviews WHERE schemaname = %s AND matviewname = %s",
            (get_db_config().schema, "vw_emendas_resumo_ano"),
        )
        row = cur.fetchone()
    old_autocommit = conn.autocommit
    conn.commit()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            concurrently = "CONCURRENTLY " if row and row[0] else ""
            cur.execute(f"REFRESH MATERIALIZED VIEW {concurrently}{view}")
    finally:
        conn.autocommit = old_autocommit


def tabelas_prontas(conn) -> bool:
    missing = [t for t in TABLES if not table_exists(conn, t)]
    if missing:
        logger.warning(
            "Carga emendas/parlamentar pulada: faltam tabelas %s (rodar docs/sql/emendas_parlamentar.sql)",
            ", ".join(missing),
        )
        return False
    return True


def carga_emendas_parlamentar(conn) -> dict:
    """Siconv primeiro (define códigos e nomes), depois apoiadores, depois o resumo."""
    benef = carga_siconv_emenda(conn)
    apoio = carga_apoiadores(conn)
    refresh_resumo(conn)
    return {
        "tab_emendas_beneficiarios_ano": benef,
        "tab_emendas_apoiadores": apoio,
    }
