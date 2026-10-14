"""Outils que l'agent peut appeler : SQL (chiffres) et recherche dans les avis (texte)."""

import re

import chromadb
import duckdb
from langchain_core.tools import tool

from src.config import CHROMA_DIR, DB_PATH, get_embeddings

MAX_ROWS = 50

# Mots interdits : tout ce qui pourrait modifier ou supprimer des données
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|create|alter|attach|copy|pragma|install|load|export)\b",
    re.IGNORECASE,
)


# =============================================================================
# Schéma de la base (donné au LLM dans ses instructions)
# =============================================================================
def get_schema() -> str:
    """Liste les tables et leurs colonnes, pour que le LLM sache ce qui existe."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    rows = con.execute(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
        """
    ).fetchall()
    con.close()

    schema = {}
    for table, column, dtype in rows:
        schema.setdefault(table, []).append(f"{column} ({dtype})")
    return "\n".join(f"- {t}: {', '.join(cols)}" for t, cols in schema.items())


# =============================================================================
# Outil 1 : requêtes SQL (questions chiffrées)
# =============================================================================
@tool
def sql_query(query: str) -> str:
    """Exécute une requête SQL SELECT (DuckDB) sur la base Olist et renvoie le résultat.
    Utilise cet outil pour toute question chiffrée (montants, nombres, moyennes, délais).
    Seules les requêtes en lecture (SELECT ou WITH) sont autorisées."""
    q = query.strip().rstrip(";")

    # Garde-fou 1 : uniquement de la lecture
    if not q.lower().startswith(("select", "with")):
        return "ERREUR : seules les requêtes SELECT ou WITH sont autorisées."
    if FORBIDDEN.search(q) or ";" in q:
        return "ERREUR : requête refusée (mot-clé interdit ou plusieurs requêtes)."

    try:
        # Garde-fou 2 : connexion en lecture seule
        con = duckdb.connect(str(DB_PATH), read_only=True)
        # Garde-fou 3 : on limite le nombre de lignes renvoyées
        df = con.execute(f"SELECT * FROM ({q}) LIMIT {MAX_ROWS}").fetchdf()
        con.close()
    except Exception as e:
        # On renvoie l'erreur au LLM au lieu de planter : il pourra corriger sa requête
        return f"ERREUR SQL : {e}"

    if df.empty:
        return "La requête n'a renvoyé aucune ligne."
    return df.to_string(index=False)


# =============================================================================
# Outil 2 : recherche sémantique dans les avis clients (questions qualitatives)
# =============================================================================
_embeddings = None  # créé une seule fois, au premier appel


@tool
def search_reviews(query: str, state: str = "", max_score: int = 5) -> str:
    """Recherche sémantique dans les avis clients Olist (textes en portugais).
    Utilise cet outil pour les questions QUALITATIVES : pourquoi les clients sont
    mécontents, de quoi ils se plaignent, ce qu'ils apprécient.
    - query : ce que tu cherches, en langage naturel (ex : "retard de livraison").
    - state : optionnel, code d'un État pour filtrer (ex : "SP", "AM").
    - max_score : optionnel, note maximale des avis (ex : 2 pour les avis négatifs)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = get_embeddings()

    collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection("reviews")

    # Filtres sur les métadonnées (note et/ou État)
    conditions = [{"score": {"$lte": max_score}}]
    if state:
        conditions.append({"state": state.upper()})
    where = conditions[0] if len(conditions) == 1 else {"$and": conditions}

    # 1. La question devient un vecteur  2. ChromaDB trouve les avis les plus proches
    results = collection.query(
        query_embeddings=[_embeddings.embed_query(query)],
        n_results=8,
        where=where,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    if not docs:
        return "Aucun avis trouvé avec ces critères."
    return "\n".join(f"[note {m['score']}/5 | {m['state']}] {d}" for d, m in zip(docs, metas))