"""Indexe un échantillon d'avis clients dans ChromaDB (à lancer une seule fois).

Usage :
    python scripts/build_index.py
"""

import sys
from pathlib import Path
import time
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb
import duckdb

from src.config import CHROMA_DIR, DB_PATH, get_embeddings

N_REVIEWS = 1000
BATCH = 90

# 1. Récupérer des avis qui ont un commentaire écrit, avec leur note et l'État du client
con = duckdb.connect(str(DB_PATH), read_only=True)
rows = con.execute(
    f"""
    SELECT * FROM (
        SELECT r.review_id, r.review_score, c.customer_state, r.review_comment_message
        FROM order_reviews r
        JOIN orders o    ON r.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE r.review_comment_message IS NOT NULL
          AND length(r.review_comment_message) > 20
    )
    USING SAMPLE {N_REVIEWS} ROWS (reservoir, 42)
    """
).fetchall()
con.close()
print(f"{len(rows)} avis récupérés")

# 2. Créer (ou recréer) la collection ChromaDB, stockée dans data/chroma
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
try:
    client.delete_collection("reviews")
except Exception:
    pass
collection = client.create_collection("reviews", metadata={"hnsw:space": "cosine"})

# 3. Calculer les embeddings par lots de 100 et les ranger dans ChromaDB
embeddings = get_embeddings()
seen = set()
for i in range(0, len(rows), BATCH):
    batch = [r for r in rows[i : i + BATCH] if r[0] not in seen]
    seen.update(r[0] for r in batch)
    if not batch:
        continue
    texts = [r[3] for r in batch]
    vectors = embeddings.embed_documents(texts)
    collection.add(
        ids=[r[0] for r in batch],
        embeddings=vectors,
        documents=texts,
        metadatas=[{"score": int(r[1]), "state": r[2]} for r in batch],
    )
    print(f"  {min(i + BATCH, len(rows))}/{len(rows)} avis indexés")
    if i + BATCH < len(rows):
        time.sleep(62)

print(f"\nIndex créé : {collection.count()} avis dans {CHROMA_DIR}")