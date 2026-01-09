# superviseur_fluent.py
import os
import re
from typing import Literal, Optional
from dotenv import load_dotenv

# LangChain / LangGraph
from langchain_openai import ChatOpenAI  
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field

# Imports des modules modularisés
from state import AgentState 
from agents.agent_recherche import create_search_agent 
from agents.agent_negociation import create_negotiation_agent
from agents.agent_juridique import create_droit_agent

# Imports Outils
from outils.outils_immobilier import search_properties, get_property_statistics
from outils.outils_negociation import get_property_negotiation_details
from outils.outils_droit import query_droit_immobilier

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 

# ==================== 1. ROUTEUR / SUPERVISEUR  ====================

class RouteResponse(BaseModel):
    """Choisit le prochain agent à activer."""
    next: Literal["SEARCH_AGENT", "NEGOTIATION_AGENT", "GENERAL_CHAT", "JURIDIQUE_ADVISOR"] = Field(
        description="L'agent vers lequel router la demande."
    )

def detect_property_id(text: str) -> Optional[str]:
    """Fonction utilitaire pour repérer un ID MongoDB (24 chars hex)"""
    match = re.search(r'\b[a-f0-9]{24}\b', text, re.IGNORECASE)
    return match.group(0) if match else None

def supervisor_node(state: AgentState):
    
    # 1. Utilisation de GPT-4o pour le routage
    llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0) 

    last_msg = state["messages"][-1].content
    
    # --- 1. INTELLIGENCE RÉFLEXE (Détection d'ID) ---
    detected_id = detect_property_id(str(last_msg))
    if detected_id:
        return {
            "next_agent": "NEGOTIATION_AGENT", 
            "active_property_id": detected_id
        }
    
    # --- 2. GESTION DE LA DÉLÉGATION ---
    if state.get("delegation_query"):
        if any(w in state["delegation_query"].lower() for w in ["loi", "taxe", "contrat", "notaire", "légal", "bail", "procédure"]):
            return {"next_agent": "JURIDIQUE_ADVISOR", "messages": [HumanMessage(content=state["delegation_query"])]}
        else:
            return {"next_agent": "GENERAL_CHAT", "messages": [HumanMessage(content=state["delegation_query"])]}
            
    # --- 3. INTELLIGENCE SÉMANTIQUE (Routage LLM Classique) ---
    system_prompt = """Tu es le routeur d'une agence immobilière IA. Ton rôle est UNIQUEMENT de diriger le client.

    RÈGLES DE ROUTAGE :
    1. Demande de recherche, critères, prix, ville -> 'SEARCH_AGENT'.
    2. Discussion sur un bien précis, négociation, offre, "celui-ci m'intéresse" -> 'NEGOTIATION_AGENT'.
    3. Question sur des lois, contrats, taxes, procédures légales, baux -> 'JURIDIQUE_ADVISOR'.
    4. Salutations simples, blabla -> 'GENERAL_CHAT'.
    """
    
    router = llm.with_structured_output(RouteResponse)
    decision = router.invoke([SystemMessage(content=system_prompt)] + state["messages"])
    
    return {"next_agent": decision.next}

# ==================== 2. CONSTRUCTION DU GRAPHE FINAL ====================

def build_fluent_graph():
    workflow = StateGraph(AgentState)

    # Récupération des agents (On passe la clé OpenAI)
    search_node, search_tools = create_search_agent(OPENAI_API_KEY)
    negot_node, negot_tools = create_negotiation_agent(OPENAI_API_KEY)
    droit_node, droit_tools = create_droit_agent(OPENAI_API_KEY)

    # Ajout des noeuds
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("search_agent", search_node)
    workflow.add_node("negotiation_agent", negot_node)
    workflow.add_node("droit_agent", droit_node)
    
    # NOUVEAU: Agent Chat Général avec personnalité DomusIA
    def general_chat_node(state: AgentState):
        # Utilisation de GPT-4o
        llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0.5) 
        
        system_prompt = """Tu es DomusIA 🏠, l'assistant immobilier IA le plus cool du Maroc !
        
🎯 TES TALENTS :
- Recherche de biens immobiliers
- Négociation
- Expertise juridique

💬 TON STYLE :
- Sympa, chaleureux, tutoiement
- Concis (style WhatsApp)
- Emojis avec parcimonie

Exemple : "Hey ! 👋 Je suis DomusIA. Je peux t'aider à trouver, négocier ou comprendre les lois immobilières. Que veux-tu faire ?"
"""
        response = llm.invoke([SystemMessage(content=system_prompt)] + state["messages"])
        return {"messages": [response]}
        
    workflow.add_node("general_chat", general_chat_node)
    
    # Outils
    workflow.add_node("search_tools", ToolNode(search_tools))
    workflow.add_node("negotiation_tools", ToolNode(negot_tools))
    workflow.add_node("droit_tools", ToolNode(droit_tools)) 

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_agent"],
        {
            "SEARCH_AGENT": "search_agent",
            "NEGOTIATION_AGENT": "negotiation_agent",
            "JURIDIQUE_ADVISOR": "droit_agent",
            "GENERAL_CHAT": "general_chat"
        }
    )

    def should_continue_tools(state: AgentState):
        last_msg = state["messages"][-1]
        return "tools" if hasattr(last_msg, "tool_calls") and last_msg.tool_calls else END

    workflow.add_conditional_edges("search_agent", should_continue_tools, {"tools": "search_tools", END: END})
    workflow.add_edge("search_tools", "search_agent")
    
    workflow.add_conditional_edges("negotiation_agent", should_continue_tools, {"tools": "negotiation_tools", END: END})
    workflow.add_edge("negotiation_tools", "negotiation_agent")
    
    workflow.add_conditional_edges("droit_agent", should_continue_tools, {"tools": "droit_tools", END: END})
    workflow.add_edge("droit_tools", "droit_agent")
    
    workflow.add_edge("general_chat", END)
    
    return workflow.compile()