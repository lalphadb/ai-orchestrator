#!/usr/bin/env python3
"""
Script de création des utilisateurs dans la base de données correcte
"""

import os
import sys
from datetime import datetime, timezone

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import User, get_db_session
from app.core.security import generate_uuid, get_password_hash


def create_default_users():
    """Crée les utilisateurs par défaut dans la DB"""

    users_to_create = [
        {
            "username": "admin",
            "email": "admin@4lb.ca",
            "password": "admin",
            "is_admin": True,
        },
        {
            "username": "lalpha",
            "email": "lalpha@4lb.ca",
            "password": "lalpha",
            "is_admin": True,
        },
        {
            "username": "root3d",
            "email": "root3d@4lb.ca",
            "password": "root3d",
            "is_admin": True,
        },
        {
            "username": "demo",
            "email": "demo@test.com",
            "password": "demo",
            "is_admin": False,
        },
        {
            "username": "louis",
            "email": "boudreaulouis@gmail.com",
            "password": "louis",
            "is_admin": False,
        },
        {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testuser2",
            "is_admin": False,
        },
    ]

    db = get_db_session()

    try:
        print("🔧 Création/Réparation des utilisateurs...")
        print("=" * 60)

        created_count = 0
        updated_count = 0

        for user_data in users_to_create:
            username = user_data["username"]

            # Check if user already exists
            existing_user = db.query(User).filter(User.username == username).first()

            if existing_user:
                # Update password
                print(f"\n🔄 {username}: Existe déjà, mise à jour du mot de passe...")
                existing_user.hashed_password = get_password_hash(user_data["password"])
                existing_user.email = user_data.get("email", existing_user.email)
                existing_user.is_admin = user_data.get("is_admin", existing_user.is_admin)
                updated_count += 1
            else:
                # Create new user
                print(f"\n✨ {username}: Création...")
                new_user = User(
                    id=generate_uuid(),
                    username=username,
                    email=user_data.get("email"),
                    hashed_password=get_password_hash(user_data["password"]),
                    is_active=True,
                    is_admin=user_data.get("is_admin", False),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(new_user)
                created_count += 1

            print(f"   Email: {user_data.get('email', 'N/A')}")
            print(f"   Admin: {'Oui' if user_data.get('is_admin') else 'Non'}")
            print(f"   Password: {user_data['password']}")

        # Commit changes
        db.commit()

        print("\n" + "=" * 60)
        print(f"✅ {created_count} utilisateurs créés")
        print(f"🔄 {updated_count} utilisateurs mis à jour")

        print("\n📝 Récapitulatif des utilisateurs:")
        for user_data in users_to_create:
            status = "👑 ADMIN" if user_data.get("is_admin") else "👤 USER"
            print(f"   {status} {user_data['username']} = {user_data['password']}")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  AI ORCHESTRATOR - CRÉATION UTILISATEURS                 ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Show which DB is being used
    from app.core.config import settings

    print(f"📁 Base de données: {settings.DATABASE_URL}")
    print(f"📂 Répertoire: {os.getcwd()}")
    print()

    success = create_default_users()

    if success:
        print("\n🎉 Opération terminée ! Vous pouvez maintenant vous connecter.")
        sys.exit(0)
    else:
        print("\n💥 L'opération a échoué. Vérifiez les logs ci-dessus.")
        sys.exit(1)
