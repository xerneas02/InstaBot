#!/usr/bin/env python3
import os
import sys
import traceback
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired, LoginRequired

SESSION_FILE = "insta_session.json"

def generate_session():
    username = os.getenv("LOGIN_INSTAGRAM")
    password = os.getenv("PASSWORD_INSTAGRAM")
    if not username or not password:
        print("❌ Merci de définir les variables d'environnement LOGIN_INSTAGRAM et PASSWORD_INSTAGRAM.", file=sys.stderr)
        sys.exit(1)

    client = Client()
    try:
        print("🔄 Tentative de connexion à Instagram…")
        client.login(username, password)
        print("✅ Connecté avec succès en tant que", username)
    except TwoFactorRequired:
        print("❌ La 2FA est activée sur ce compte. Veuillez la désactiver ou gérer le code 2FA.", file=sys.stderr)
        sys.exit(2)
    except ChallengeRequired:
        print("❌ Un challenge est requis (challenge_required). Assurez-vous que l’IP/device est déjà validé.", file=sys.stderr)
        sys.exit(3)
    except LoginRequired:
        print("❌ Session invalide ou expirée, réessayez de nouveau.", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print("❌ Erreur inattendue lors du login :", e, file=sys.stderr)
        traceback.print_exc()
        sys.exit(5)

    # Dump des cookies + device settings dans un fichier JSON
    try:
        client.dump_settings(SESSION_FILE)
        print(f"💾 Session sauvegardée dans `{SESSION_FILE}`")
    except Exception as e:
        print("❌ Impossible de sauvegarder la session :", e, file=sys.stderr)
        traceback.print_exc()
        sys.exit(6)

if __name__ == "__main__":
    generate_session()
