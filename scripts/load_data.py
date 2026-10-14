"""
Charge les 9 CSV Olist dans une base DuckDB (data/olist.duckdb).

Usage :
    python scripts/load_data.py

À relancer à chaque fois qu'on veut repartir d'une base propre :
le script supprime et recrée les tables.
"""

from pathlib import Path

import duckdb

# --- 1. Chemins ---------------------------------------------------------------
# On part de l'emplacement de ce fichier pour que le script marche
# quel que soit le dossier depuis lequel on le lance.
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "olist.duckdb"

# --- 2. Correspondance fichier CSV -> nom de table -----------------------------
# Les noms Kaggle sont longs ("olist_orders_dataset.csv") : on les raccourcit
# pour que l'agent écrive du SQL plus simple ("orders").
TABLES = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}


def main() -> None:
    # Vérifie que tous les CSV sont bien là avant de commencer
    missing = [f for f in TABLES if not (RAW_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Fichiers manquants dans {RAW_DIR} :\n  - " + "\n  - ".join(missing)
        )

    # --- 3. Connexion : DuckDB crée le fichier s'il n'existe pas ----------------
    con = duckdb.connect(str(DB_PATH))

    # --- 4. Chargement de chaque CSV ---------------------------------------------
    # read_csv_auto devine tout seul les types de colonnes (entiers, dates...).
    for filename, table in TABLES.items():
        path = (RAW_DIR / filename).as_posix()
        con.execute(f"DROP TABLE IF EXISTS {table}")
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{path}')")
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:<22} {n:>9,} lignes")

    # --- 5. Petit test : une vraie question business -----------------------------
    print("\nTest : chiffre d'affaires par État (top 5)")
    result = con.execute(
        """
        SELECT c.customer_state AS etat,
               ROUND(SUM(oi.price), 0) AS chiffre_affaires
        FROM order_items oi
        JOIN orders o    ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY etat
        ORDER BY chiffre_affaires DESC
        LIMIT 5
        """
    ).fetchdf()
    print(result.to_string(index=False))

    con.close()
    print(f"\nBase créée : {DB_PATH}")


if __name__ == "__main__":
    main()
