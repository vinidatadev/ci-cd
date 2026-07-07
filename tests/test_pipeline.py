import os
import duckdb
import pytest
from src.transform import run_pipeline

PROCESSED_PATH = "data/processed/clean_sales.parquet"


@pytest.fixture(scope="module", autouse=True)
def run_transform():
    """Executa o pipeline antes dos testes."""
    run_pipeline()


def test_arquivo_processado_existe():
    """Valida que o arquivo Parquet foi gerado."""
    assert os.path.exists(PROCESSED_PATH), f"Arquivo não encontrado: {PROCESSED_PATH}"


def test_sem_order_ids_duplicados():
    """Valida que não há order_ids duplicados no resultado."""
    con = duckdb.connect()
    result = con.execute(f"""
        SELECT order_id, COUNT(*) AS cnt
        FROM read_parquet('{PROCESSED_PATH}')
        GROUP BY order_id
        HAVING cnt > 1
    """).fetchall()
    con.close()
    assert result == [], f"Duplicatas encontradas: {result}"


def test_sem_quantity_nula():
    """Valida que a coluna quantity não contém valores nulos."""
    con = duckdb.connect()
    nulls = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{PROCESSED_PATH}')
        WHERE quantity IS NULL
    """).fetchone()[0]
    con.close()
    assert nulls == 0, f"Encontradas {nulls} linhas com quantity nula"


def test_contagem_de_linhas():
    """Valida que o resultado tem o número correto de linhas (6 raw - 1 duplicata = 5)."""
    con = duckdb.connect()
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{PROCESSED_PATH}')").fetchone()[0]
    con.close()
    assert count == 5, f"Esperado 5 linhas, encontrado {count}"
