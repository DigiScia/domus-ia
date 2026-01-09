from langchain_core.tools import tool
import json
import logging
import sys
import os

# Ajout du chemin racine pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.services.contract_service import generate_lease_contract
from web.services.email_service import send_email
from outils.outils_negociation import get_property_negotiation_details # Pour récupérer les détails (mock)

logger = logging.getLogger(__name__)

@tool
def notify_owner_of_deal(
    property_id: str,
    client_name: str,
    client_phone: str,
    final_price: float,
    summary: str
) -> str:
    """
    Finalise un accord, génère le contrat de bail et notifie le propriétaire par Email.
    À utiliser UNIQUEMENT lorsque le client et l'IA sont tombés d'accord sur le prix.
    
    Args:
        property_id: L'ID du bien immobilier concerné.
        client_name: Le nom du client (locataire potentiel).
        client_phone: Le numéro de téléphone du client.
        final_price: Le prix final négocié.
        summary: Un court résumé de la négociation pour le propriétaire.
    
    Returns:
        Confirmation de l'envoi des notifications.
    """
    
    logger.info(f"🔔 Initialisation notification propriétaire pour bien {property_id}")
    
    # 1. Récupération des données (Mock ou via un service)
    # Dans un vrai cas, on ferait un appel DB. Ici on utilise l'outil existant pour simuler ou on hardcode pour la démo.
    # On va simuler des données propriétaire car get_property_negotiation_details ne retourne pas tout.
    
    # Simulation données propriétaire
    owner_data = {
        "name": "M. Immobilier",
        "email": "owner@example.com", # Email destinataire (simulé)
        "phone": "+212600000000",
        "address": "10 Av. Mohammed V, Casablanca"
    }
    
    # Simulation données bien (récupération partielle via l'ID pour le réalisme)
    # Idéalement on appellerait un property_service.get_by_id(property_id)
    property_data = {
        "id": property_id,
        "title": f"Bien Réf. {property_id}",
        "location": "Casablanca (Simulé)",
        "type": "Appartement",
        "price": final_price,
        "description": "Superbe appartement bien situé."
    }
    
    tenant_data = {
        "name": client_name,
        "phone": client_phone
    }
    
    # 2. Génération du Contrat
    contract_path = generate_lease_contract(owner_data, tenant_data, property_data)
    
    if not contract_path:
        return "Erreur lors de la génération du contrat. Veuillez réessayer."
        
    # 3. Envoi de l'Email
    email_subject = f"✅ Nouvel Accord pour votre bien {property_data['title']}"
    email_body = f"""
    <h2>Félicitations ! Un accord a été trouvé.</h2>
    <p>Notre agent IA a finalisé une négociation pour votre bien.</p>
    
    <h3>Détails de l'accord :</h3>
    <ul>
        <li><strong>Bien :</strong> {property_data['title']} ({property_data['location']})</li>
        <li><strong>Prix Final :</strong> {final_price} MAD</li>
        <li><strong>Client :</strong> {client_name} ({client_phone})</li>
    </ul>
    
    <p><strong>Résumé de la discussion :</strong><br>
    {summary}</p>
    
    <hr>
    <p>📎 <strong>Ci-joint :</strong> Une ébauche de contrat de bail générée automatiquement pour faciliter vos démarches.</p>
    <p>Cordialement,<br><strong>L'équipe DomusIA</strong></p>
    """
    
    email_sent = send_email(owner_data["email"], email_subject, email_body, attachment_path=contract_path)
    
    # 4. Notification WhatsApp (Optionnel / Futur)
    # Pour l'instant on se contente de l'email car Twilio nécessite des templates pour initier la conversation.
    
    if email_sent:
        return f"✅ Propriétaire notifié avec succès ! Le contrat a été généré et envoyé par email à {owner_data['email']}."
    else:
        return "⚠️ Le contrat a été généré mais l'envoi de l'email a échoué (vérifiez les logs)."
