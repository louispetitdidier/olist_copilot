"""Évalue l'agent sur le golden dataset, avec un LLM juge.

Usage :
    python scripts/evaluate.py

Résultat : un score dans le terminal + un rapport dans eval/results.md
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from eval.golden_set import GOLDEN_SET
from src.agent import agent
from src.config import DB_PATH, ROOT, get_llm, text_of

PAUSE = 3  # secondes entre deux questions (marge de sécurité sur les limites de débit)


# --- Le format de réponse imposé au juge -------------------------------------
class Verdict(BaseModel):
    correct: bool = Field(description="True si la réponse de l'agent est correcte")
    reason: str = Field(description="Explication courte du verdict, en français")


judge = get_llm().with_structured_output(Verdict)

JUDGE_PROMPT = """Tu es un évaluateur strict d'un agent d'analyse de données.

Question posée : {question}

Bonne réponse (calculée directement sur les données) :
{reference}

Réponse de l'agent :
{answer}

La réponse de l'agent est CORRECTE si elle contient la ou les valeurs principales de la bonne
réponse (une différence d'arrondi est acceptée). Elle est INCORRECTE si une valeur clé est
fausse ou absente. Les explications en plus ne pénalisent pas."""


def reference_answer(item) -> str:
    """Calcule la bonne réponse avec la requête de référence."""
    if item["reference_sql"] is None:
        return item["expected_behavior"]
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(item["reference_sql"]).fetchdf()
    con.close()
    return df.to_string(index=False)


def ask_agent(question: str) -> str:
    """Pose la question à l'agent et renvoie sa réponse finale."""
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=question)]},
            config={"recursion_limit": 15},
        )
        return text_of(result["messages"][-1])
    except Exception as e:
        return f"[ERREUR DE L'AGENT] {e}"


def main():
    results = []
    for i, item in enumerate(GOLDEN_SET, 1):
        print(f"[{i}/{len(GOLDEN_SET)}] {item['question']}")

        reference = reference_answer(item)
        answer = ask_agent(item["question"])
        verdict = judge.invoke(
            JUDGE_PROMPT.format(question=item["question"], reference=reference, answer=answer)
        )

        print(f"    {'CORRECT' if verdict.correct else 'INCORRECT'} : {verdict.reason}\n")
        results.append({**item, "reference": reference, "answer": answer, "verdict": verdict})

        if i < len(GOLDEN_SET):
            time.sleep(PAUSE)

    # --- Score et rapport ------------------------------------------------------
    n_ok = sum(r["verdict"].correct for r in results)
    score = f"{n_ok}/{len(results)} ({100 * n_ok / len(results):.0f} %)"
    print("=" * 60)
    print(f"SCORE : {score}")

    lines = [
        "# Résultats de l'évaluation",
        "",
        f"**Score : {score}**",
        "",
        "| Question | Verdict | Explication du juge |",
        "| --- | --- | --- |",
    ]
    for r in results:
        mark = "✅" if r["verdict"].correct else "❌"
        lines.append(f"| {r['question']} | {mark} | {r['verdict'].reason.replace('|', '/')} |")

    out = ROOT / "eval" / "results.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rapport détaillé : {out}")


if __name__ == "__main__":
    main()