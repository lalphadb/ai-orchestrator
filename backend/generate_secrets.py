#!/usr/bin/env python3
"""
Script pour générer de nouveaux secrets sécurisés pour .env

Usage:
    python3 generate_secrets.py
"""

import secrets
import string


def generate_jwt_secret(length=64):
    """Génère une clé secrète JWT aléatoire."""
    return secrets.token_urlsafe(length)


def generate_admin_password(length=24):
    """Génère un mot de passe admin sécurisé."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


if __name__ == "__main__":
    print("=" * 70)
    print("GÉNÉRATION DE SECRETS SÉCURISÉS POUR AI ORCHESTRATOR")
    print("=" * 70)
    print()

    jwt_secret = generate_jwt_secret()
    admin_password = generate_admin_password()

    print("🔑 JWT_SECRET_KEY:")
    print(f"   {jwt_secret}")
    print()

    print("🔒 ADMIN_PASSWORD:")
    print(f"   {admin_password}")
    print()

    print("=" * 70)
    print("INSTRUCTIONS:")
    print("=" * 70)
    print("1. Copiez ces valeurs dans votre fichier backend/.env")
    print("2. Remplacez les anciennes valeurs de JWT_SECRET_KEY et ADMIN_PASSWORD")
    print("3. Redémarrez le serveur: sudo systemctl restart ai-orchestrator")
    print()
    print("⚠️  IMPORTANT: Ne commitez JAMAIS le fichier .env dans Git!")
    print("=" * 70)
