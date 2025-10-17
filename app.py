from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import os
import subprocess
import sys
import smtplib
import secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'tic_tac_toe_secret_key_2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuration Email
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'votre.email@gmail.com',
    'sender_password': 'votre_mot_de_passe_application',
    'app_name': 'Tic-Tac-Toe Game'
}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


def check_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users LIMIT 1")
        conn.close()
        return True
    except:
        return False


def init_password_reset_table():
    """Initialise la table password_resets si elle n'existe pas"""
    conn = get_db()
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()


def send_reset_email(email, token):
    """Envoie un email de réinitialisation"""
    try:
        reset_url = url_for('reset_password', token=token, _external=True)

        # Mode développement - afficher le lien dans la console
        print("=" * 60)
        print("📧 EMAIL DE RÉINITIALISATION (MODE DÉVELOPPEMENT)")
        print("=" * 60)
        print(f"Destinataire: {email}")
        print(f"Lien de reset: {reset_url}")
        print("=" * 60)

        # Si la configuration email est valide, essayer d'envoyer
        if (EMAIL_CONFIG['sender_email'] != 'votre.email@gmail.com' and
                EMAIL_CONFIG['sender_password'] != 'votre_mot_de_passe_application'):

            message = MIMEMultipart()
            message['From'] = EMAIL_CONFIG['sender_email']
            message['To'] = email
            message['Subject'] = f"Réinitialisation de votre mot de passe - {EMAIL_CONFIG['app_name']}"

            body = f"""
            <html>
            <body>
                <h2>Réinitialisation de votre mot de passe</h2>
                <p>Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe :</p>
                <p><a href="{reset_url}">Réinitialiser mon mot de passe</a></p>
                <p><strong>Ce lien expirera dans 1 heure.</strong></p>
            </body>
            </html>
            """

            message.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
                server.send_message(message)

            return True
        else:
            return True  # Mode développement

    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return True  # Mode développement


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('❌ Tous les champs sont obligatoires', 'error')
            return render_template('login.html')

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, hash_password(password))
            )
            user = cursor.fetchone()

            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['score'] = user['score']
                flash('✅ Connexion réussie!', 'success')
                return redirect(url_for('game_menu'))
            else:
                flash('❌ Identifiants incorrects', 'error')

        except Exception as e:
            flash(f'❌ Erreur: {str(e)}', 'error')
        finally:
            conn.close()

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation
        errors = []
        if not all([username, email, password, confirm_password]):
            errors.append('Tous les champs sont obligatoires')
        if len(password) < 6:
            errors.append('Le mot de passe doit faire au moins 6 caractères')
        if password != confirm_password:
            errors.append('Les mots de passe ne correspondent pas')

        if errors:
            for error in errors:
                flash(f'❌ {error}', 'error')
            return render_template('signup.html')

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hash_password(password))
            )
            conn.commit()
            flash('✅ Compte créé avec succès! Connectez-vous.', 'success')
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash('❌ Nom d\'utilisateur ou email déjà utilisé', 'error')
        except Exception as e:
            flash(f'❌ Erreur: {str(e)}', 'error')
        finally:
            conn.close()

    return render_template('signup.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('❌ Veuillez entrer votre adresse email', 'error')
            return render_template('forgot_password.html')

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id, username FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if user:
                token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=1)

                cursor.execute(
                    'INSERT INTO password_resets (email, token, expires_at) VALUES (?, ?, ?)',
                    (email, token, expires_at)
                )
                conn.commit()

                if send_reset_email(email, token):
                    flash('✅ Un email de réinitialisation a été envoyé!', 'success')
                else:
                    flash('⚠️ Email non envoyé, mais vous pouvez utiliser le lien manuellement', 'warning')
            else:
                flash('✅ Si cet email existe, un lien de réinitialisation a été envoyé', 'success')

        except Exception as e:
            flash('❌ Erreur lors du traitement', 'error')
            print(f"Erreur forgot_password: {e}")
        finally:
            conn.close()

        return render_template('forgot_password.html')

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT email, expires_at, used FROM password_resets WHERE token = ?',
            (token,)
        )
        reset_request = cursor.fetchone()

        if not reset_request:
            flash('❌ Lien de réinitialisation invalide', 'error')
            return redirect(url_for('forgot_password'))

        email, expires_at, used = reset_request

        if used or datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f'):
            flash('❌ Lien de réinitialisation expiré ou déjà utilisé', 'error')
            return redirect(url_for('forgot_password'))

        if request.method == 'POST':
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not new_password or not confirm_password:
                flash('❌ Tous les champs sont obligatoires', 'error')
                return render_template('reset_password.html', token=token)

            if new_password != confirm_password:
                flash('❌ Les mots de passe ne correspondent pas', 'error')
                return render_template('reset_password.html', token=token)

            if len(new_password) < 6:
                flash('❌ Le mot de passe doit contenir au moins 6 caractères', 'error')
                return render_template('reset_password.html', token=token)

            cursor.execute(
                'UPDATE users SET password = ? WHERE email = ?',
                (hash_password(new_password), email)
            )

            cursor.execute(
                'UPDATE password_resets SET used = 1 WHERE token = ?',
                (token,)
            )

            conn.commit()
            flash('✅ Mot de passe réinitialisé avec succès!', 'success')
            return redirect(url_for('login'))

        return render_template('reset_password.html', token=token)

    except Exception as e:
        flash('❌ Erreur lors de la réinitialisation', 'error')
        print(f"Erreur reset_password: {e}")
        return redirect(url_for('forgot_password'))
    finally:
        conn.close()


@app.route('/game-menu')
def game_menu():
    if 'user_id' not in session:
        flash('🔒 Veuillez vous connecter', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['score'] = user['score']

    return render_template('game.html',
                           username=session['username'],
                           score=session.get('score', 0))


@app.route('/launch-game')
def launch_game():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        subprocess.Popen([sys.executable, 'tic_tac_toe.py'])
        flash('🎮 Jeu lancé!', 'success')
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'error')

    return redirect(url_for('game_menu'))


@app.route('/update-score', methods=['POST'])
def update_score():
    try:
        data = request.get_json()
        username = data.get('username')
        points = data.get('score', 0)

        if not username:
            return jsonify({'success': False, 'error': 'Username manquant'})

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET score = score + ? WHERE username = ?",
            (points, username)
        )
        conn.commit()

        cursor.execute("SELECT score FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return jsonify({'success': True, 'new_score': result['score']})
        else:
            return jsonify({'success': False, 'error': 'Utilisateur non trouvé'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/logout')
def logout():
    session.clear()
    flash('👋 Déconnexion réussie', 'info')
    return redirect(url_for('login'))


@app.route('/debug')
def debug():
    if not check_db():
        return "❌ Base de données corrompue. Exécutez reset_complet.py"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()

    cursor.execute("SELECT id, username, email, score FROM users")
    users = cursor.fetchall()
    conn.close()

    html = "<h1>🔧 Debug</h1>"
    html += "<h2>Structure:</h2><ul>"
    for col in columns:
        html += f"<li>{col[1]} ({col[2]})</li>"
    html += "</ul><h2>Utilisateurs:</h2><ul>"
    for user in users:
        html += f"<li>ID:{user[0]} - {user[1]} - {user[2]} - Score:{user[3]}</li>"
    html += "</ul>"

    return html


if __name__ == '__main__':
    init_password_reset_table()
    if check_db():
        print("🚀 Serveur démarré: http://127.0.0.1:5000")
        print("📱 Accédez à: http://127.0.0.1:5000")
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    else:
        print("❌ ERREUR: Base de données corrompue")
        print("💡 Exécutez: python reset_complet.py")