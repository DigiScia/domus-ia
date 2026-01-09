import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Contrat de Bail - {property_title}</title>
    <style>
        body {{ font-family: 'Times', serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
        h1 {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .section {{ margin-bottom: 20px; }}
        .section-title {{ font-weight: bold; text-transform: uppercase; margin-bottom: 5px; background: #f0f0f0; padding: 5px; }}
        .info {{ margin-left: 20px; }}
        .signatures {{ margin-top: 50px; display: flex; justify-content: space-between; }}
        .signature-box {{ width: 45%; border-top: 1px solid #333; padding-top: 10px; text-align: center; height: 100px; }}
        .footer {{ margin-top: 50px; font-size: 0.8em; text-align: center; color: #777; }}
    </style>
</head>
<body>

    <h1>CONTRAT DE BAIL À USAGE D'HABITATION</h1>

    <p><strong>Date :</strong> {date}</p>

    <div class="section">
        <div class="section-title">ENTRE LES SOUSSIGNÉS</div>
        <div class="info">
            <p><strong>LE BAILLEUR (Propriétaire) :</strong><br>
            Nom : {owner_name}<br>
            Adresse : {owner_address}<br>
            Téléphone : {owner_phone}<br>
            Email : {owner_email}</p>
        </div>
    </div>

    <div class="section">
        <div class="section-title">ET</div>
        <div class="info">
            <p><strong>LE PRENEUR (Locataire) :</strong><br>
            Nom : {tenant_name}<br>
            Téléphone : {tenant_phone}</p>
        </div>
    </div>

    <div class="section">
        <div class="section-title">IL A ÉTÉ CONVENU CE QUI SUIT</div>
        <p>Le Bailleur donne en location au Preneur les locaux ci-après désignés.</p>
        
        <div class="info">
            <p><strong>DESIGNATION DU BIEN :</strong><br>
            Adresse : {property_address}<br>
            Type : {property_type}<br>
            Description sommaire : {property_description}</p>
        </div>
    </div>

    <div class="section">
        <div class="section-title">DURÉE DU BAIL</div>
        <p>Le présent bail est consenti pour une durée de <strong>12 mois</strong>, commençant le <strong>{start_date}</strong>.</p>
    </div>

    <div class="section">
        <div class="section-title">LOYER ET CHARGES</div>
        <p>Le présent bail est consenti et accepté moyennant un loyer mensuel de :</p>
        <p style="text-align: center; font-size: 1.2em; font-weight: bold;">{rent_amount} Dirhams (MAD)</p>
        <p>Le loyer est payable d'avance le <strong>{payment_day}</strong> de chaque mois.</p>
    </div>

    <div class="section">
        <div class="section-title">OBLIGATIONS DES PARTIES</div>
        <p><strong>Le Preneur s'engage à :</strong></p>
        <ul>
            <li>Payer le loyer aux termes convenus.</li>
            <li>User paisiblement de la chose louée.</li>
            <li>Ne pas sous-louer sans accord écrit du bailleur.</li>
            <li>Entretenir le logement en bon état.</li>
        </ul>
        <p><strong>Le Bailleur s'engage à :</strong></p>
        <ul>
            <li>Délivrer le logement en bon état d'usage.</li>
            <li>Assurer au locataire la jouissance paisible du logement.</li>
        </ul>
    </div>

    <div class="signatures">
        <div class="signature-box">
            <strong>LE BAILLEUR</strong><br>
            (Lu et approuvé)
        </div>
        <div class="signature-box">
            <strong>LE PRENEUR</strong><br>
            (Lu et approuvé)
        </div>
    </div>

    <div class="footer">
        Document généré automatiquement par DomusIA le {date}.<br>
        Ceci est une ébauche de contrat. Veuillez consulter un notaire pour validation finale.
    </div>

</body>
</html>
"""

def generate_lease_contract(owner_data: dict, tenant_data: dict, property_data: dict) -> str:
    """
    Génère un contrat de bail au format HTML.
    Sauvegarde le fichier dans un dossier temporaire et retourne le chemin absolu.
    """
    try:
        # Création du dossier de sortie si inexistant
        output_dir = os.path.join(os.getcwd(), "generated_contracts")
        os.makedirs(output_dir, exist_ok=True)

        # Nom de fichier unique
        filename = f"bail_{property_data.get('id', 'temp')}_{tenant_data.get('phone', 'unknown')}.html"
        filepath = os.path.join(output_dir, filename)

        # Remplissage du template
        html_content = TEMPLATE_HTML.format(
            date=datetime.now().strftime("%d/%m/%Y"),
            owner_name=owner_data.get("name", "[NOM DU PROPRIÉTAIRE]"),
            owner_address=owner_data.get("address", "[ADRESSE DU PROPRIÉTAIRE]"),
            owner_phone=owner_data.get("phone", "[TÉLÉPHONE]"),
            owner_email=owner_data.get("email", "[EMAIL]"),
            
            tenant_name=tenant_data.get("name", "[NOM DU LOCATAIRE]"),
            tenant_phone=tenant_data.get("phone", "[TÉLÉPHONE]"),
            
            property_title=property_data.get("title", "Bien Immobilier"),
            property_address=property_data.get("location", "[ADRESSE DU BIEN]"),
            property_type=property_data.get("type", "Appartement/Villa"),
            property_description=property_data.get("description", "Description standard"),
            
            start_date=datetime.now().strftime("%d/%m/%Y"), # Date par défaut = aujourd'hui
            rent_amount=property_data.get("price", "----"),
            payment_day="1er"
        )

        # Écriture du fichier
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"✅ Contrat généré : {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"❌ Erreur génération contrat: {e}")
        return None
