import sys
import os
from web.services.contract_service import generate_lease_contract
from web.services.email_service import send_email

# Ajout du chemin racine
sys.path.append(os.getcwd())

# Mock logger
import logging
logging.basicConfig(level=logging.INFO)

print("🚀 Démarrage du test de notification (Test Logique Direct)...")

from web.services.contract_service import generate_lease_contract
from web.services.email_service import send_email

# Données de test
property_id = "TEST_PROP_123"
client_name = "Jean Dupont"
client_phone = "+212612345678"
final_price = 5000.0
summary = "Le client a accepté le prix après une petite négociation."

print("1. Test génération contrat...")
owner_data = {
    "name": "M. Immobilier",
    "email": "owner@example.com",
    "phone": "+212600000000",
    "address": "10 Av. Mohammed V, Casablanca"
}

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

contract_path = generate_lease_contract(owner_data, tenant_data, property_data)

if contract_path and os.path.exists(contract_path):
    print(f"✅ Contrat généré : {contract_path}")
else:
    print("❌ Echec génération contrat")
    sys.exit(1)

print("\n2. Test envoi email (simulation)...")
email_subject = f"✅ Nouvel Accord pour votre bien {property_data['title']}"
email_body = f"<h2>Test Email</h2><p>Contrat joint.</p>"

# On suppose que send_email va logger/simuler si pas de SMTP
email_sent = send_email(owner_data["email"], email_subject, email_body, attachment_path=contract_path)

if email_sent:
    print("✅ Email traité avec succès (envoyé ou simulé)")
else:
    print("❌ Echec envoi email")

print("\n🏁 Test terminé.")
