# agents/agent_negociation.py
import os
from langchain_openai import ChatOpenAI # CHANGEMENT ICI
from langchain_core.messages import SystemMessage, AIMessage
from outils.outils_negociation import get_property_negotiation_details
from outils.outils_notification import notify_owner_of_deal
from state import AgentState

def create_negotiation_agent(api_key: str):
    """
    Crée la logique de noeud et les outils de l'Agent Négociation (Le Closer).
    Utilise GPT-4o.
    """
    
    llm = ChatOpenAI(
        model="gpt-4o", # CHANGEMENT ICI
        api_key=api_key,
        temperature=0.4
    ) 
    
    tools = [get_property_negotiation_details, notify_owner_of_deal]
    llm_with_tools = llm.bind_tools(tools)

    prompt_template = """Tu es un négociateur immobilier expert représentant le PROPRIÉTAIRE (l'annonceur).
    
    TA MISSION : Vendre le bien au meilleur prix possible.
    
    RÈGLES STRICTES DE NÉGOCIATION :
    - NE JAMAIS révéler le 'floor_price' au client. C'est ton secret.
    - Si l'offre du client est < floor_price : Refuse poliment et justifie le prix (atouts, marché).
    - Si l'offre est entre floor_price et listing_price : Propose une contre-offre (couper la poire en deux).
    - Si l'offre est >= listing_price : Accepte avec enthousiasme.
    
    {context_instruction}
    """
    
    def negotiation_node(state: AgentState):
        messages = state["messages"]
        active_id = state.get("active_property_id")
        
        context_instruction = ""
        
        if active_id:
            context_instruction = (
                f"IMPORTANT : L'utilisateur est intéressé par le bien ID: {active_id}. "
                f"ACTION IMMÉDIATE : Appelle TOUT DE SUITE l'outil 'get_property_negotiation_details' avec l'ID {active_id} "
                f"pour obtenir le prix plancher et les arguments de vente."
            )
        else:
            context_instruction = "L'utilisateur veut négocier mais tu ne sais pas quel bien. Demande-lui poliment l'ID du bien ou de coller la référence."

        full_prompt = prompt_template.format(context_instruction=context_instruction)
        
        response = llm_with_tools.invoke([SystemMessage(content=full_prompt)] + messages)
        
        return {"messages": [response]}
    
    return negotiation_node, tools