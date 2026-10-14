"""Agent LangGraph : le LLM boucle entre réflexion et outils jusqu'à la réponse."""

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.config import get_llm
from src.tools import get_schema, sql_query

from src.tools import get_schema, search_reviews, sql_query
# Les outils dont dispose l'agent (on ajoutera le RAG au bloc 4)
TOOLS = [sql_query, search_reviews]

# Les instructions permanentes de l'agent : son rôle, ses règles, le schéma
SYSTEM_PROMPT = f"""Tu es un data analyst expert de la base e-commerce brésilienne Olist (2016-2018).
Tu réponds en français à des questions business, en t'appuyant uniquement sur les données.

Règles :
- Questions CHIFFRÉES (combien, moyenne, top, évolution) : utilise sql_query (syntaxe DuckDB).
- Questions QUALITATIVES (pourquoi, de quoi se plaignent les clients, ce qu'ils apprécient) :
  utilise search_reviews. Les avis sont en portugais : résume-les en français et cite 2-3 exemples traduits.
- Tu peux COMBINER les deux outils (ex : trouver les États les plus lents en SQL,
  puis chercher ce que leurs clients disent avec search_reviews).
- Utilise uniquement les tables et colonnes listées ci-dessous.
- Si une requête renvoie une ERREUR, lis le message, corrige la requête et réessaie.
- PÉRIMÈTRE STRICT : tu réponds UNIQUEMENT aux questions sur les données Olist.
  Si une question sort de ce périmètre (culture générale, actualité, code, etc.),
  tu ne donnes JAMAIS la réponse, même si tu la connais. Réponds seulement :
  "Je suis un assistant d'analyse des données e-commerce Olist : cette question sort de mon périmètre."
- Dans ta réponse finale, donne les éléments clés et explique en une phrase comment tu les as obtenus.
Tables disponibles :
{get_schema()}
"""

llm = get_llm().bind_tools(TOOLS)


# --- NŒUD 1 : l'agent réfléchit ----------------------------------------------
def agent_node(state: MessagesState):
    """Le LLM lit toute la conversation et décide : appeler un outil ou répondre."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}  # ajouté à l'état


# --- CONSTRUCTION DU GRAPHE --------------------------------------------------
def build_agent():
    graph = StateGraph(MessagesState)              # l'état = la liste des messages

    graph.add_node("agent", agent_node)            # nœud 1 : réfléchir
    graph.add_node("tools", ToolNode(TOOLS))       # nœud 2 : exécuter les outils

    graph.add_edge(START, "agent")                 # on commence par réfléchir
    graph.add_conditional_edges("agent", tools_condition)  # outil demandé ? -> "tools", sinon -> FIN
    graph.add_edge("tools", "agent")               # après un outil, on retourne réfléchir

    return graph.compile()


agent = build_agent()