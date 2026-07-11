import logging

from src.db_meta import qualified_staging, qualified_table
from src.staging import load_sql_to_staging

logger = logging.getLogger(__name__)

TABLE = "tab_fornecedores_licitacoes"
SOURCE_TABLE = "tab_itens_licitacao"
LOADED_COLUMNS = ["identificacao_fornecedor", "nome_fornecedor"]


def is_fornecedores_licitacoes_table(table_name: str) -> bool:
    return table_name == TABLE


def build_fornecedores_staging_sql() -> str:
    itens = qualified_table(SOURCE_TABLE)
    fornecedores = qualified_table(TABLE)
    staging = qualified_staging(TABLE)
    cols = ", ".join(f'"{c}"' for c in LOADED_COLUMNS)
    return f"""
    INSERT INTO {staging} ({cols})
    SELECT DISTINCT
        bt.identificacao_fornecedor_item_licitacao,
        bt.nome_fornecedor_item_licitacao
    FROM {itens} bt
    LEFT JOIN {fornecedores} tfl
        ON bt.identificacao_fornecedor_item_licitacao = tfl.identificacao_fornecedor
    WHERE bt.identificacao_fornecedor_item_licitacao IS NOT NULL
      AND bt.identificacao_fornecedor_item_licitacao NOT IN ('------------')
    """


def load_fornecedores_licitacoes_to_staging(conn) -> int:
    count = load_sql_to_staging(
        conn,
        TABLE,
        build_fornecedores_staging_sql(),
        LOADED_COLUMNS,
    )
    logger.info(
        "Staging %s: %s fornecedores distintos de %s",
        TABLE,
        count,
        SOURCE_TABLE,
    )
    return count
