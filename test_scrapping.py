import requests
from bs4 import BeautifulSoup
import json # Juste pour afficher le résultat joliment

# ==============================================================================
# CECI EST VOTRE "TOOL", LA FONCTION QUE VOUS LIVREREZ AU BACKEND
# ==============================================================================
def get_horaires_lieu(url_du_lieu: str) -> dict:
    """
    Scrappe une page de visiterlyon.com pour en extraire les horaires.

    Args:
        url_du_lieu: L'URL complète de la page du lieu à scraper.

    Returns:
        Un dictionnaire contenant les horaires ou un message d'erreur.
    """
    # Étape 1 : Gestion des erreurs de base (input invalide)
    if not url_du_lieu.startswith("https://www.visiterlyon.com" ):
        return {"erreur": "URL invalide. L'URL doit provenir de visiterlyon.com"}

    try:
        # Étape 2 : Télécharger la page (avec un timeout pour la robustesse)
        headers = {'User-Agent': 'Epitech-IA-Agent-Project/1.0'} # Bonne pratique pour s'identifier
        reponse = requests.get(url_du_lieu, headers=headers, timeout=10)
        reponse.raise_for_status() # Lève une exception si le statut est une erreur (404, 500...)

    except requests.Timeout:
        return {"erreur": "Le site a mis trop de temps à répondre."}
    except requests.RequestException as e:
        return {"erreur": f"Impossible de récupérer la page. Statut: {e.response.status_code if e.response else 'N/A'}"}

    # Étape 3 : Parser le HTML
    soup = BeautifulSoup(reponse.content, 'html.parser')

    # Étape 4 : Extraire les données (C'est la partie qui demande de l'analyse)
    # NOTE : Le sélecteur CSS ci-dessous est un EXEMPLE et doit être adapté au vrai site.
    horaires_div = soup.find('div', class_='horaires-pratiques')

    if not horaires_div:
        return {"erreur": "Impossible de trouver la section des horaires sur la page."}

    # Étape 5 : Nettoyer et structurer les données
    lignes_horaires = horaires_div.find_all('p')
    horaires_extraits = [ligne.get_text(strip=True) for ligne in lignes_horaires]

    if not horaires_extraits:
        return {"info": "La section horaires a été trouvée mais elle est vide."}
        
    # Étape 6 : Retourner le résultat propre au format dictionnaire
    return {
        "source_url": url_du_lieu,
        "horaires": horaires_extraits
    }

# ==============================================================================
# CECI EST VOTRE "BANC D'ESSAI" LOCAL
# ==============================================================================
if __name__ == "__main__":
    print("--- Début des tests locaux pour les outils de scrapping ---")

    # Cas 1 : Un test qui devrait fonctionner
    # (URL fictive, à remplacer par une vraie URL de visiterlyon.com)
    print("\n[TEST 1] Cas nominal avec une URL valide...")
    url_musee_confluences = "https://www.visiterlyon.com/lieux-a-visiter/musee-des-confluences"
    resultat1 = get_horaires_lieu(url_musee_confluences )
    print(json.dumps(resultat1, indent=2, ensure_ascii=False))

    # Cas 2 : Un test avec une page qui n'existe pas (erreur 404)
    print("\n[TEST 2] Cas d'erreur avec une URL inexistante...")
    url_invalide = "https://www.visiterlyon.com/ce-lieu-n-existe-pas"
    resultat2 = get_horaires_lieu(url_invalide )
    print(json.dumps(resultat2, indent=2, ensure_ascii=False))

    # Cas 3 : Un test avec une URL d'un autre site
    print("\n[TEST 3] Cas d'erreur avec une URL non autorisée...")
    url_externe = "https://www.google.com"
    resultat3 = get_horaires_lieu(url_externe )
    print(json.dumps(resultat3, indent=2, ensure_ascii=False))

    print("\n--- Fin des tests locaux ---")
