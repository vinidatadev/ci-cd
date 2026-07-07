import duckdb
import os

RAW_PATH = "data/raw_sales.csv"
PROCESSED_DIR = "data/processed"
PROCESSED_PATH = os.path.join(PROCESSED_DIR, "clean_sales.parquet")


def run_pipeline(raw_path: str = RAW_PATH, output_path: str = PROCESSED_PATH) -> int:
    """
    Lê o CSV bruto, aplica regras de limpeza e salva como Parquet.
    Retorna o número de linhas no resultado final.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    con = duckdb.connect()

    # 1. Carrega o CSV
    con.execute(f"CREATE TABLE raw AS SELECT * FROM read_csv_auto('{raw_path}')")

    # 2. Remove duplicatas (mantém a primeira ocorrência de cada order_id)
    con.execute("""
        CREATE TABLE deduped AS
        SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) AS rn
            FROM raw
        ) t WHERE rn = 1
    """)

    # 3. Preenche nulos em 'quantity' com 1 (pedido unitário assumido)
    con.execute("""
        CREATE TABLE clean AS
        SELECT
            order_id,
            customer_id,
            product,
            COALESCE(quantity, 1) AS quantity,
            unit_price,
            order_date
        FROM deduped
    """)

    # 4. Salva como Parquet
    con.execute(f"COPY clean TO '{output_path}' (FORMAT PARQUET)")

    row_count = con.execute("SELECT COUNT(*) FROM clean").fetchone()[0]
    con.close()

    print(f"[OK] Pipeline concluído. {row_count} linhas salvas em: {output_path}")
    return row_count


if __name__ == "__main__":
    run_pipeline()
