"""Pose une question à l'agent et affiche chaque étape de son raisonnement.

Usage :
    python scripts/ask.py "Ta question ici"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage

from src.agent import agent
from src.config import text_of

question = sys.argv[1] if len(sys.argv) > 1 else "Quels sont les 3 États avec le plus de commandes ?"
print(f"QUESTION : {question}\n")

# stream() renvoie le résultat de chaque nœud au fur et à mesure
# recursion_limit : sécurité pour que l'agent ne boucle jamais à l'infini
for step in agent.stream(
    {"messages": [HumanMessage(content=question)]},
    config={"recursion_limit": 15},
    stream_mode="updates",
):
    for node, update in step.items():
        msg = update["messages"][-1]

        if node == "agent" and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"[AGENT] appelle l'outil '{call['name']}' :")
                print(call["args"].get("query", call["args"]), "\n")

        elif node == "tools":
            print("[OUTIL] résultat :")
            print(msg.content[:800], "\n")

        elif node == "agent":
            print("=" * 60)
            print("[REPONSE FINALE]")
            print(text_of(msg))