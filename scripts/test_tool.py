"""Bloc 2 : le LLM appelle l'outil SQL, étape par étape (sans LangGraph)."""

import sys
from pathlib import Path

# Permet d'importer "src" quand on lance le script depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.config import get_llm, text_of
from src.tools import get_schema, sql_query

question = "Quels sont les 3 États avec le plus de commandes ?"

# 1. On donne l'outil au LLM
llm = get_llm().bind_tools([sql_query])

messages = [
    SystemMessage(content=(
        "Tu es un data analyst expert. Réponds aux questions sur la base e-commerce Olist "
        "en utilisant l'outil sql_query.\n\nTables disponibles :\n" + get_schema()
    )),
    HumanMessage(content=question),
]

# 2. Le LLM réfléchit et DEMANDE un outil (il ne l'exécute pas lui-même)
ai_message = llm.invoke(messages)
print("=== Étape 1 : le LLM demande un outil ===")
for call in ai_message.tool_calls:
    print(f"Outil : {call['name']}")
    print(f"Requête SQL :\n{call['args']['query']}\n")
messages.append(ai_message)

# 3. NOTRE code exécute l'outil et renvoie le résultat au LLM
print("=== Étape 2 : notre code exécute la requête ===")
for call in ai_message.tool_calls:
    result = sql_query.invoke(call["args"])
    print(result, "\n")
    messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

# 4. Le LLM lit le résultat et rédige la réponse finale
final = llm.invoke(messages)
print("=== Étape 3 : réponse finale du LLM ===")
print(text_of(final))