import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Lit le fichier .env : place GOOGLE_API_KEY et GEMINI_MODEL
# dans les variables d'environnement
load_dotenv()

model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
print(f"Modèle utilisé : {model}")

# LangChain lit automatiquement GOOGLE_API_KEY
llm = ChatGoogleGenerativeAI(model=model, temperature=0)

reponse = llm.invoke("Réponds en une phrase : qu'est-ce qu'un panier moyen en e-commerce ?")
print("\nRéponse du LLM :")
print(reponse.content)