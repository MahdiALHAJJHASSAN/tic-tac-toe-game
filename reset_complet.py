import sqlite3
import os
import time


def reset_database():
    """Réinitialise complètement la base de données"""

    print("🔄 Réinitialisation de la base de données...")

    # Attendre que la base de données soit libérée
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # Supprimer l'ancienne base de données si elle existe
            if os.path.exists('users.db'):
                os.remove('users.db')
                print("🗑️ Ancienne base de données supprimée")
                break
            else:
                print("ℹ️ Aucune base de données existante trouvée")
                break

        except PermissionError:
            if attempt < max_attempts - 1:
                print(f"⏳ Base de données verrouillée, nouvel essai dans 2 secondes... ({attempt + 1}/{max_attempts})")
                time.sleep(2)
            else:
                print(
                    "❌ Impossible de supprimer la base de données - elle est probablement utilisée par un autre processus")
                print("💡 Fermez toutes les instances de l'application et réessayez")
                return False

    # Créer une nouvelle base de données
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Créer la table users
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           username
                           TEXT
                           UNIQUE
                           NOT
                           NULL,
                           email
                           TEXT
                           UNIQUE
                           NOT
                           NULL,
                           password
                           TEXT
                           NOT
                           NULL,
                           score
                           INTEGER
                           DEFAULT
                           0,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # Créer la table password_resets
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS password_resets
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           email
                           TEXT
                           NOT
                           NULL,
                           token
                           TEXT
                           UNIQUE
                           NOT
                           NULL,
                           expires_at
                           TEXT
                           NOT
                           NULL,
                           used
                           INTEGER
                           DEFAULT
                           0,
                           created_at
                           TEXT
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # Vider les tables existantes
        cursor.execute('DELETE FROM users')
        cursor.execute('DELETE FROM password_resets')

        # Insérer des utilisateurs de test
        import hashlib

        def hash_password(password):
            return hashlib.sha256(password.encode()).hexdigest()

        test_users = [
            ("alex", "alex@test.com", hash_password("alex123"), 10),
            ("test", "test@test.com", hash_password("test123"), 5),
            ("admin", "admin@test.com", hash_password("admin123"), 15),
            ("user1", "user1@test.com", hash_password("user123"), 0)
        ]

        for username, email, password, score in test_users:
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password, score) VALUES (?, ?, ?, ?)",
                    (username, email, password, score)
                )
                print(f"✅ Utilisateur créé: {username}")
            except sqlite3.IntegrityError:
                print(f"⚠️ Utilisateur existe déjà: {username}")

        conn.commit()

        # Vérifier la structure
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n📊 STRUCTURE DE LA TABLE users:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")

        # Vérifier le contenu
        cursor.execute("SELECT username, email, score FROM users")
        users = cursor.fetchall()
        print("\n👥 UTILISATEURS CRÉÉS:")
        for user in users:
            print(f"   {user[0]} - {user[1]} - Score: {user[2]}")

        conn.close()

        print("\n🎉 RÉINITIALISATION TERMINÉE!")
        print("\n🔑 COMPTES DE TEST:")
        print("   👤 alex / 🔑 alex123")
        print("   👤 test / 🔑 test123")
        print("   👤 admin / 🔑 admin123")
        print("   👤 user1 / 🔑 user123")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la création de la base de données: {e}")
        return False


if __name__ == "__main__":
    success = reset_database()
    if success:
        print("\n🚀 Vous pouvez maintenant lancer le serveur avec: python app.py")
    else:
        print("\n💡 Conseil: Assurez-vous que:")
        print("   - Le serveur Flask est arrêté (Ctrl+C)")
        print("   - Aucune autre application n'utilise la base de données")
        print("   - Vous avez les permissions d'écriture dans le dossier")