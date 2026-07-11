import argparse
import json
import logging
import time

import psycopg2

from src.catalog import load_catalog
from src.cleanup import cleanup_after_successful_load, ensure_stale_files_removed
from src.config import (
    EXCLUDED_CSV_FILES,
    EXCLUDED_TABLES,
    EXTRACTED_DIR,
    DOWNLOADS_DIR,
    get_connection,
)
from src.db_conn import ensure_connection, reconnect, safe_rollback
from src.controle_carga import (
    close_stuck_controle_records,
    finish_pipeline_carga,
    finish_table_carga_error,
    finish_table_carga_skipped,
    finish_table_carga_success,
    list_recent_controle,
    recount_carga_dia_table_stats,
    start_pipeline_carga,
    start_table_carga,
)
from src.controle_carga_dia import (
    finish_carga_dia,
    get_carga_dia_by_id,
    list_carga_dia_hoje,
    start_carga_dia,
)
from src.db_meta import table_exists
from src.download import download_all
from src.extract import extract_csvs
from src.keys import TABLE_KEYS, is_merge_ready, is_truncate_reload
from src.load_order import LOAD_ORDER
import src.logging_config as log_cfg
from src.logging_config import (
    record_error,
    record_table_result,
    save_summary,
    setup_logging,
)
from src.cipi_schema import prepare_cipi_table
from src.emendas import update_emendas_resumo
from src.fornecedores_licitacoes import (
    is_fornecedores_licitacoes_table,
    load_fornecedores_licitacoes_to_staging,
)
from src.merge import merge_table, truncate_reload_table
from src.splitters import (
    get_consorcio_columns,
    get_consorcio_dedupe_columns,
    get_consorcio_required_columns,
    get_cipi_columns,
    get_cipi_csv_sources,
    get_cipi_dedupe_columns,
    get_cipi_required_columns,
    get_dl_columns,
    get_dl_csv_sources,
    get_dl_required_columns,
    get_emenda_columns,
    get_emenda_csv_sources,
    get_emenda_required_columns,
    get_programa_columns,
    is_cipi_table,
    is_consorcio_split_table,
    is_dl_table,
    is_emenda_split_table,
    is_programa_split_table,
)
from src.staging import load_csv_to_staging
from src.validate import check_data_carga, register_data_carga, validate_run

logger = logging.getLogger("carga")

_CONNECTION_ERRORS = (psycopg2.InterfaceError, psycopg2.OperationalError)


def _finish_table_error_safe(conn, controle_id, table: str, error: str) -> None:
    try:
        finish_table_carga_error(conn, controle_id, table, error)
    except _CONNECTION_ERRORS:
        fresh = reconnect(conn)
        try:
            finish_table_carga_error(fresh, controle_id, table, error)
        finally:
            fresh.close()


def build_catalog_index(catalog: list[dict]) -> dict[str, str]:
    index: dict[str, str] = {}
    for entry in catalog:
        for table in entry["tabelas"]:
            index[table] = entry["arquivo"]
    return index


def tables_from(from_table: str) -> list[str]:
    if from_table not in LOAD_ORDER:
        raise ValueError(f"Tabela fora da ordem de carga: {from_table}")
    start = LOAD_ORDER.index(from_table)
    return LOAD_ORDER[start:]


def _run_tables_loop(
    conn,
    tables: list[str],
    index: dict[str, str],
    carga_dia_id: int | None,
) -> tuple[int, int, int, object]:
    processed = 0
    errors = 0
    skipped = 0
    for table in tables:
        if table == "tab_data_carga":
            continue
        table_started = time.time()
        try:
            result = process_table(conn, table, index, carga_dia_id=carga_dia_id)
            if result.get("skipped"):
                skipped += 1
            else:
                processed += 1
            record_table_result(table, result, time.time() - table_started)
            logger.info(
                "tabela=%s updated=%s inserted=%s skipped=%s duracao=%.2fs",
                table,
                result.get("updated"),
                result.get("inserted"),
                result.get("skipped"),
                time.time() - table_started,
            )
        except Exception as exc:
            safe_rollback(conn)
            conn = ensure_connection(conn)
            errors += 1
            record_error(table, str(exc))
            logger.exception("Erro em %s: %s", table, exc)
    return processed, errors, skipped, conn


def _skip_table(
    conn,
    table: str,
    carga_dia_id: int | None,
    reason: str,
    log_fn,
) -> dict:
    log_fn(reason)
    if carga_dia_id is not None:
        controle_id = start_table_carga(conn, table, id_controle_carga_dia=carga_dia_id)
        finish_table_carga_skipped(conn, controle_id, table, reason)
    return {"updated": 0, "inserted": 0, "skipped": True}


def process_table(
    conn,
    table: str,
    catalog_index: dict[str, str],
    carga_dia_id: int | None = None,
) -> dict:
    if table == "tab_data_carga":
        return {"updated": 0, "inserted": 0, "skipped": True}

    if table in EXCLUDED_TABLES:
        return _skip_table(
            conn,
            table,
            carga_dia_id,
            "Carga desabilitada temporariamente",
            lambda msg: logger.info("Pulando %s: %s", table, msg),
        )

    if not table_exists(conn, table):
        raise ValueError(f"Tabela destino nÃ£o existe no banco: {table}")

    if not is_merge_ready(table) and not is_truncate_reload(table):
        return _skip_table(
            conn,
            table,
            carga_dia_id,
            "Chave em revisão",
            lambda msg: logger.warning("Pulando %s: chave em revisÃ£o", table),
        )

    if is_fornecedores_licitacoes_table(table):
        controle_id = start_table_carga(conn, table, id_controle_carga_dia=carga_dia_id)
        try:
            load_fornecedores_licitacoes_to_staging(conn)
            result = merge_table(conn, table)
            finish_table_carga_success(conn, controle_id, table, result)
            return result
        except Exception as exc:
            safe_rollback(conn)
            _finish_table_error_safe(conn, controle_id, table, str(exc))
            raise

    csv_name = catalog_index.get(table)
    if not csv_name:
        return _skip_table(
            conn,
            table,
            carga_dia_id,
            "Sem CSV no catálogo",
            lambda msg: logger.warning("Pulando %s: sem CSV no catÃ¡logo", table),
        )

    if csv_name in EXCLUDED_CSV_FILES:
        return _skip_table(
            conn,
            table,
            carga_dia_id,
            f"Arquivo {csv_name} com carga desabilitada temporariamente",
            lambda msg: logger.info(
                "Pulando %s: arquivo %s com carga desabilitada temporariamente",
                table,
                csv_name,
            ),
        )

    csv_path = EXTRACTED_DIR / csv_name
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV nÃ£o encontrado: {csv_path}")

    columns = None
    dedupe_columns = None
    required_columns = None
    csv_column_sources = None
    if is_programa_split_table(table):
        columns = get_programa_columns(table)
    elif is_consorcio_split_table(table):
        columns = get_consorcio_columns(table)
        dedupe_columns = get_consorcio_dedupe_columns(table)
        required_columns = get_consorcio_required_columns(table)
    elif is_emenda_split_table(table):
        columns = get_emenda_columns(table)
        required_columns = get_emenda_required_columns(table)
        csv_column_sources = get_emenda_csv_sources(table)
    elif is_cipi_table(table):
        columns = get_cipi_columns(table)
        dedupe_columns = get_cipi_dedupe_columns(table)
        required_columns = get_cipi_required_columns(table)
        csv_column_sources = get_cipi_csv_sources(table)
    elif is_dl_table(table):
        columns = get_dl_columns(table)
        required_columns = get_dl_required_columns(table)
        csv_column_sources = get_dl_csv_sources(table)

    controle_id = start_table_carga(conn, table, id_controle_carga_dia=carga_dia_id)
    try:
        if is_cipi_table(table):
            prepare_cipi_table(conn, table)
        load_csv_to_staging(
            conn,
            csv_path,
            table,
            columns=columns,
            dedupe_columns=dedupe_columns,
            required_columns=required_columns,
            csv_column_sources=csv_column_sources,
        )
        if is_truncate_reload(table):
            logger.info("Carga completa (TRUNCATE + INSERT) para %s", table)
            result = truncate_reload_table(conn, table)
        else:
            result = merge_table(conn, table)
        if table == "tab_beneficiarios_emendas":
            update_emendas_resumo(conn)
        finish_table_carga_success(conn, controle_id, table, result)
        return result
    except Exception as exc:
        safe_rollback(conn)
        _finish_table_error_safe(conn, controle_id, table, str(exc))
        raise


def cmd_list_tables(_: argparse.Namespace) -> None:
    catalog = load_catalog()
    index = build_catalog_index(catalog)
    for table in LOAD_ORDER:
        csv_name = index.get(table, "-")
        if table in EXCLUDED_TABLES or csv_name in EXCLUDED_CSV_FILES:
            status = "excluido"
        elif is_fornecedores_licitacoes_table(table):
            status = "sql_derivada"
        elif is_truncate_reload(table):
            status = "truncate_reload"
        else:
            status = TABLE_KEYS.get(table, {}).get("status", "ausente")
        print(f"{table:55} {csv_name:45} {status}")


def cmd_download_only(_: argparse.Namespace) -> None:
    catalog = load_catalog()
    logger.info("Baixando ZIPs...")
    download_all(catalog, DOWNLOADS_DIR)
    logger.info("Extraindo CSVs...")
    extracted = extract_csvs(catalog, DOWNLOADS_DIR, EXTRACTED_DIR)
    logger.info("ExtraÃ­dos %s CSVs", len(extracted))


def cmd_run_table(args: argparse.Namespace) -> None:
    catalog = load_catalog()
    index = build_catalog_index(catalog)
    conn = get_connection()
    started = time.time()
    log_arquivo = log_cfg.RUN_SUMMARY.get("log_file")
    own_carga_dia = args.carga_dia_id is None
    if own_carga_dia:
        carga_dia_id = start_carga_dia(conn, qtd_arquivos_extraidos=0, log_arquivo=log_arquivo)
    else:
        carga_dia_id = args.carga_dia_id
        logger.info("run-table vinculado ao controle_carga_dia id=%s", carga_dia_id)
    try:
        result = process_table(conn, args.table, index, carga_dia_id=carga_dia_id)
        record_table_result(args.table, result, time.time() - started)
        logger.info("%s: %s", args.table, result)
        if own_carga_dia:
            carregados = 0 if result.get("skipped") else 1
            finish_carga_dia(
                conn,
                carga_dia_id,
                carregados,
                0,
                1 if result.get("skipped") else 0,
                mensagem=f"run-table {args.table}",
            )
        else:
            carregados, erros, pulados = recount_carga_dia_table_stats(
                conn, carga_dia_id, LOAD_ORDER
            )
            finish_carga_dia(
                conn,
                carga_dia_id,
                carregados,
                erros,
                pulados,
                mensagem=f"run-table {args.table}",
            )
    except Exception as exc:
        safe_rollback(conn)
        record_error(args.table, str(exc))
        conn_ctrl = ensure_connection(conn)
        try:
            finish_carga_dia(
                conn_ctrl,
                carga_dia_id,
                0,
                1,
                0,
                mensagem=str(exc),
            )
        finally:
            if conn_ctrl is not conn:
                conn_ctrl.close()
        logger.exception("Erro em %s: %s", args.table, exc)
        raise
    finally:
        conn.close()
        if log_cfg.LAST_SUMMARY_PATH:
            save_summary(log_cfg.LAST_SUMMARY_PATH)


def cmd_run(args: argparse.Namespace) -> None:
    ensure_stale_files_removed()

    catalog = load_catalog()
    index = build_catalog_index(catalog)

    if not args.skip_download:
        logger.info("Download e extração...")
        download_all(catalog, DOWNLOADS_DIR)
        extracted = extract_csvs(catalog, DOWNLOADS_DIR, EXTRACTED_DIR)
    else:
        logger.info("Execução sem download/extração (--skip-download)")
        extracted = [
            EXTRACTED_DIR / entry["arquivo"]
            for entry in catalog
            if (EXTRACTED_DIR / entry["arquivo"]).exists()
        ]
    qtd_extraidos = len(extracted)

    conn = get_connection()
    processed = 0
    errors = 0
    skipped = 0
    started = time.time()
    log_arquivo = log_cfg.RUN_SUMMARY.get("log_file")
    carga_dia_id = start_carga_dia(conn, qtd_extraidos, log_arquivo=log_arquivo)
    pipeline_id = start_pipeline_carga(conn, id_controle_carga_dia=carga_dia_id)
    try:
        processed, errors, skipped, conn = _run_tables_loop(
            conn, LOAD_ORDER, index, carga_dia_id
        )

        conn = ensure_connection(conn)
        if processed > 0:
            register_data_carga(conn)
            logger.info("tab_data_carga atualizada")

        mensagem = (
            f"extraidos={qtd_extraidos} carregados={processed} "
            f"erros={errors} pulados={skipped}"
        )
        finish_carga_dia(
            conn,
            carga_dia_id,
            processed,
            errors,
            skipped,
            mensagem=mensagem,
        )
        finish_pipeline_carga(
            conn,
            pipeline_id,
            processed,
            errors,
            mensagem=mensagem,
        )
        cleanup_after_successful_load()
    except Exception as exc:
        conn = ensure_connection(conn)
        finish_carga_dia(
            conn,
            carga_dia_id,
            processed,
            errors + 1,
            skipped,
            mensagem=str(exc),
        )
        finish_pipeline_carga(
            conn,
            pipeline_id,
            processed,
            errors + 1,
            mensagem=str(exc),
        )
        raise
    finally:
        conn.close()
        if log_cfg.LAST_SUMMARY_PATH:
            save_summary(log_cfg.LAST_SUMMARY_PATH)
        logger.info(
            "Pipeline finalizado em %.2fs. Tabelas processadas: %s",
            time.time() - started,
            processed,
        )


def cmd_resume(args: argparse.Namespace) -> None:
    ensure_stale_files_removed()

    carga_dia_id = args.carga_dia_id
    from_table = args.from_table

    catalog = load_catalog()
    index = build_catalog_index(catalog)

    if not args.skip_download:
        logger.info("Download e extração...")
        download_all(catalog, DOWNLOADS_DIR)
        extract_csvs(catalog, DOWNLOADS_DIR, EXTRACTED_DIR)
    else:
        logger.info("Retomada sem download (--skip-download)")

    conn = get_connection()
    started = time.time()

    carga_dia = get_carga_dia_by_id(conn, carga_dia_id)
    if not carga_dia:
        conn.close()
        raise ValueError(f"controle_carga_dia id={carga_dia_id} não encontrado")
    if carga_dia["dt_fim"]:
        logger.warning(
            "controle_carga_dia id=%s já finalizado (status=%s); retomando mesmo assim",
            carga_dia_id,
            carga_dia["status"],
        )

    logger.info(
        "Fechando registros abertos e retomando carga_dia=%s a partir de %s",
        carga_dia_id,
        from_table,
    )
    close_stuck_controle_records(
        conn,
        carga_dia_id,
        mensagem=f"Interrompido; retomada a partir de {from_table}",
    )

    pipeline_id = start_pipeline_carga(conn, id_controle_carga_dia=carga_dia_id)
    tables = tables_from(from_table)
    run_processed = 0
    run_errors = 0
    run_skipped = 0

    try:
        run_processed, run_errors, run_skipped, conn = _run_tables_loop(
            conn, tables, index, carga_dia_id
        )

        conn = ensure_connection(conn)
        carregados, erros, pulados = recount_carga_dia_table_stats(
            conn, carga_dia_id, LOAD_ORDER
        )
        if carregados > 0:
            register_data_carga(conn)
            logger.info("tab_data_carga atualizada")

        mensagem = (
            f"retomada={from_table} run_carregados={run_processed} "
            f"run_erros={run_errors} run_pulados={run_skipped} "
            f"total_carregados={carregados} total_erros={erros} "
            f"total_pulados={pulados}"
        )
        finish_carga_dia(
            conn,
            carga_dia_id,
            carregados,
            erros,
            pulados,
            mensagem=mensagem,
        )
        finish_pipeline_carga(
            conn,
            pipeline_id,
            run_processed,
            run_errors,
            mensagem=mensagem,
        )
        cleanup_after_successful_load()
    except Exception as exc:
        conn = ensure_connection(conn)
        carregados, erros, pulados = recount_carga_dia_table_stats(
            conn, carga_dia_id, LOAD_ORDER
        )
        finish_carga_dia(
            conn,
            carga_dia_id,
            carregados,
            erros + 1,
            pulados,
            mensagem=str(exc),
        )
        finish_pipeline_carga(
            conn,
            pipeline_id,
            run_processed,
            run_errors + 1,
            mensagem=str(exc),
        )
        raise
    finally:
        conn.close()
        if log_cfg.LAST_SUMMARY_PATH:
            save_summary(log_cfg.LAST_SUMMARY_PATH)
        logger.info(
            "Retomada finalizada em %.2fs (carga_dia=%s, de %s)",
            time.time() - started,
            carga_dia_id,
            from_table,
        )


def cmd_status(_: argparse.Namespace) -> None:
    conn = get_connection()
    try:
        last = check_data_carga(conn)
        print(f"Ãšltima data_carga: {last or 'nenhuma'}")
        recent = list_recent_controle(conn, limit=10)
        if recent:
            print("\nControle de carga (Ãºltimos registros):")
            for row in recent:
                ref = (
                    f" ref={row['id_controle_carga_refatorado']}"
                    if row.get("id_controle_carga_refatorado")
                    else ""
                )
                dia = (
                    f" dia={row['id_controle_carga_dia']}"
                    if row.get("id_controle_carga_dia")
                    else ""
                )
                print(
                    f"  [{row['id']}] {row['endpoint']:40} {row['status']:20} "
                    f"ins={row.get('qtd_registros_inseridos')} "
                    f"upd={row.get('qtd_registros_atualizados')}"
                    f"{dia}{ref} {row['dt_inicio']}"
                )
                if row["mensagem"]:
                    print(f"       {row['mensagem'][:120]}")

        carga_hoje = list_carga_dia_hoje(conn)
        if carga_hoje:
            print("\nControle de carga do dia (hoje):")
            for row in carga_hoje:
                print(
                    f"  [{row['id']}] seq={row['seq_execucao_dia']} "
                    f"{row['status']:18} "
                    f"extraidos={row['qtd_arquivos_extraidos']} "
                    f"carregados={row['qtd_arquivos_carregados']} "
                    f"erros={row['qtd_arquivos_erro']} "
                    f"pulados={row['qtd_arquivos_pulados']} "
                    f"{row['dt_inicio']}"
                )
                if row["mensagem"]:
                    print(f"       {row['mensagem'][:120]}")
    finally:
        conn.close()


def cmd_validate(_: argparse.Namespace) -> None:
    catalog = load_catalog()
    index = build_catalog_index(catalog)
    conn = get_connection()
    try:
        report = validate_run(conn, index)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline SICONV")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-tables", help="Listar tabelas do catÃ¡logo").set_defaults(
        func=cmd_list_tables
    )
    sub.add_parser("download-only", help="Baixar e extrair CSVs").set_defaults(
        func=cmd_download_only
    )
    p_run = sub.add_parser("run", help="Pipeline completo")
    p_run.add_argument(
        "--skip-download",
        action="store_true",
        help="Não baixar/extrair ZIPs (usar CSVs já em data/extracted/)",
    )
    p_run.set_defaults(func=cmd_run)
    p_table = sub.add_parser("run-table", help="Processar uma tabela")
    p_table.add_argument("table")
    p_table.add_argument(
        "--carga-dia-id",
        type=int,
        default=None,
        help="Vincular ao controle_carga_dia existente (ex.: execução do pipeline)",
    )
    p_table.set_defaults(func=cmd_run_table)
    p_resume = sub.add_parser(
        "resume",
        help="Retomar execução do dia a partir de uma tabela",
    )
    p_resume.add_argument(
        "--carga-dia-id",
        type=int,
        required=True,
        help="id em controle_carga_dia",
    )
    p_resume.add_argument(
        "--from-table",
        required=True,
        help="Primeira tabela a processar (ex.: tab_pagamentos)",
    )
    p_resume.add_argument(
        "--skip-download",
        action="store_true",
        help="Não baixar/extrair ZIPs (usar CSVs já em data/extracted/)",
    )
    p_resume.set_defaults(func=cmd_resume)
    sub.add_parser("status", help="Última carga").set_defaults(func=cmd_status)
    sub.add_parser("validate", help="Validar carga").set_defaults(func=cmd_validate)

    args = parser.parse_args()
    if args.command == "list-tables":
        args.func(args)
        return
    setup_logging()
    args.func(args)


if __name__ == "__main__":
    main()

