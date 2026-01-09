# cli_test.py
import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# Import du constructeur de graphe
from superviseur_fluent import build_fluent_graph
from state import AgentState

# Chargement des variables d'environnement
load_dotenv()

def main():
    print("⏳ Chargement du graphe et des outils (RAG, MongoDB)...")
    
    try:
        app = build_fluent_graph()
        print("✅ Système DomusIA initialisé avec succès !")
    except Exception as e:
        print(f"❌ Erreur critique lors du chargement : {e}")
        return

    # État initial
    current_state = {
        "messages": [],
        "next_agent": None,
        "active_property_id": None,
        "delegation_query": None,
        "last_search_results": None
    }

    print("\n" + "="*50)
    print("🤖 INTERFACE DE TEST CLI - DOMUS IA")
    print("Tapez 'q', 'quit' ou 'exit' pour quitter.")
    print("="*50 + "\n")

    while True:
        try:
            user_input = input("\033[94mVous : \033[0m") # En bleu si le terminal supporte les couleurs
            if user_input.lower() in ["q", "quit", "exit"]:
                print("Au revoir ! 👋")
                break
            
            if not user_input.strip():
                continue

            # Ajout du message utilisateur à l'état
            current_state["messages"].append(HumanMessage(content=user_input))

            print("Thinking...", end="\r")

            # Exécution du graphe
            # recursion_limit empêche les boucles infinies entre agents
            result = app.invoke(current_state, config={"recursion_limit": 20})

            # Mise à jour de l'état pour le prochain tour (mémoire)
            current_state = result
            
            # Récupération de la dernière réponse pertinente
            # On parcourt à l'envers pour trouver le dernier message de l'IA qui contient du texte
            last_response = "..."
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    # On ignore les messages qui sont juste des appels d'outils vides
                    if not (hasattr(msg, 'tool_calls') and msg.tool_calls and not msg.content):
                        last_response = msg.content
                        break
            
            print(f"\033[92mIA   : {last_response}\033[0m\n") # En vert

        except KeyboardInterrupt:
            print("\nArrêt forcé.")
            break
        except Exception as e:
            print(f"\n❌ Erreur : {e}")

if __name__ == "__main__":
    main()