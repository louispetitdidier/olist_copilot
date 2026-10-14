"""Configuration centrale : chemins et connexion au LLM."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "olist.duckdb"


def get_llm():
    """Renvoie le LLM utilisé partout dans le projet."""
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    return ChatGoogleGenerativeAI(model=model, temperature=0)


def text_of(message) -> str:
    """Extrait le texte d'une réponse du LLM (parfois une liste de morceaux)."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(part.get("text", "") for part in content if isinstance(part, dict))

from langchain_google_genai import GoogleGenerativeAIEmbeddings

CHROMA_DIR = ROOT / "data" / "chroma"


def get_embeddings():
    """Modèle qui transforme un texte en vecteur (embedding)."""
    model = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
    return GoogleGenerativeAIEmbeddings(model=model)