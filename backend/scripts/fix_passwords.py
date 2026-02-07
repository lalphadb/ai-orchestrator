#!/usr/bin/env python3
"""
Script de réparation des mots de passe utilisateurs
Réinitialise tous les mots de passe à leur valeur par défaut (username = password)
"""

import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import User, get_db_session
from app.core.security import get_password_hash


def fix_all_passwords():
    """Réinitialise tous les mots de passe utilisateurs"""

    # Mapping username -> default password
    default_passwords = {
        "admin": "admin",
        "lalpha": "lalpha",
        "demo": "demo",
        "testuser2": "testuser2",
        "louis": "louis",
        "root3d": "root3d",
    }

    db = get_db_session()

    try:
        print("🔧 Réparation des mots de passe utilisateurs...")
        print("=" * 60)

        # Get all users
        users = db.query(User).all()

        fixed_count = 0
        for user in users:
            if user.username in default_passwords:
                new_password = default_passwords[user.username]
                new_hash = get_password_hash(new_password)

                print(f"\n👤 {user.username}:")
                print(f"   - Ancien hash: {user.hashed_password[:40]}...")
                print(f"   - Nouveau hash: {new_hash[:40]}...")

                user.hashed_password = new_hash
                fixed_count += 1
            else:
                print(f"\n⚠️  {user.username}: Pas de mot de passe par défaut défini (ignoré)")

        # Commit changes
        db.commit()

        print("\n" + "=" * 60)
        print(f"✅ {fixed_count} mots de passe réinitialisés avec succès!")
        print("\n📝 Mots de passe par défaut:")
        for username, password in sorted(default_passwords.items()):
            print(f"   {username} = {password}")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur lors de la réparation: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  AI ORCHESTRATOR - RÉPARATION MOTS DE PASSE              ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    success = fix_all_passwords()

    if success:
        print("\n🎉 Réparation terminée ! Vous pouvez maintenant vous connecter.")
        sys.exit(0)
    else:
        print("\n💥 La réparation a échoué. Vérifiez les logs ci-dessus.")
        sys.exit(1)
