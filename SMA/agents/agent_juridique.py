# agents/agent_juridique.py
import os
from langchain_openai import ChatOpenAI # CHANGEMENT ICI
from langchain_core.messages import SystemMessage
from outils.outils_droit import query_droit_immobilier
from state import AgentState

def create_droit_agent(api_key: str):
    """Crée la logique de noeud et les outils de l'Agent Conseiller Juridique."""
    
    llm = ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=0.2) # CHANGEMENT ICI
    tools = [query_droit_immobilier] 
    llm_with_tools = llm.bind_tools(tools)

    prompt = """Tu es "Maître Immo" ⚖️, le conseiller juridique de DomusIA - expert en droit immobilier marocain.

🎯 TA MISSION : Répondre aux questions juridiques sur l'immobilier au Maroc.

📚 MÉTHODE :
1. Utilise TOUJOURS l'outil 'query_droit_immobilier' pour chercher dans les documents
2. Si les documents contiennent l'info → cite-les et réponds précisément
3. Si les documents sont incomplets → complète avec tes connaissances générales du droit marocain

📱 FORMAT WHATSAPP (réponses courtes et claires) :

⚖️ *[Titre de la question]*

[Réponse concise - 2-3 paragraphes max]

⚠️ *À noter :* [Mise en garde si nécessaire]

🔗 Pour plus de détails, consulte un notaire.
"""

    def droit_node(state: AgentState):
        response = llm_with_tools.invoke([SystemMessage(content=prompt)] + state["messages"])
        return {"messages": [response]}
    
    return droit_node, tools