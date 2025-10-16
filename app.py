from flask import Flask, render_template_string, request, redirect, url_for

# --- Configuration ---
app = Flask(__name__)
comments = []
FLAG = "CTF{ceci_est_un_flag}" 

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_comment = request.form.get('comment', '')
        
        # Stockage de l'entrée (VULNÉRABILITÉ)
        if user_comment:
            comments.append(user_comment)
            
        return redirect(url_for('index'))

    # Rendu de la page avec les commentaires stockés
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CTF - XSS Corrigé (Alert 1)</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            .comment-section { margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }
            .comment { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9; word-wrap: break-word; }
            form { margin-top: 20px; }
            textarea { width: 100%; height: 80px; padding: 10px; box-sizing: border-box; }
            input[type="submit"] { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
        </style>

        <script>
            // On stocke la fonction alert native
            const originalAlert = window.alert;
            
            // Surcharge la fonction alert pour intercepter le message '1'
            window.alert = function(message) {
                // On vérifie si le message est '1' (en le convertissant en chaîne)
                if (String(message) === '1') {
                    // Simule la réussite du CTF
                    if (confirm("Payload XSS détecté (alert(1)) ! Cliquez sur OK pour récupérer le FLAG.")) {
                        window.location.href = '{{ url_for("success") }}';
                    }
                }
                // Exécute l'alerte native pour afficher le message à l'utilisateur
                originalAlert(message);
            };
        </script>
    </head>
    <body>
        <h1>Bienvenue au CTF XSS Challenge! ✅</h1>
        <p>L'objectif est d'utiliser le payload **<code>alert(1)</code>** pour déclencher une alerte, puis d'être redirigé vers la **Flag** !</p>

        <h2>Laisser un commentaire</h2>
        <form method="POST">
            <label for="comment">Votre Commentaire (Max 200 chars):</label><br>
            <textarea id="comment" name="comment" maxlength="200" required></textarea><br>
            <input type="submit" value="Post Comment">
        </form>

        <div class="comment-section">
            <h2>Commentaires (Stockés)</h2>
            {% for comment in comments %}
                <div class="comment">{{ comment | safe }}</div>
            {% else %}
                <p>Pas encore de commentaires. Soyez le premier !</p>
            {% endfor %}
        </div>
        
    </body>
    </html>
    """
    # Le filtre '| safe' est la source de la vulnérabilité XSS stockée.
    return render_template_string(html, comments=comments)


@app.route('/success')
def success():
    """
    Page affichant le drapeau (Flag).
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CTF Success</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; text-align: center; }}
            h1 {{ color: #28a745; }}
            .flag {{ border: 2px dashed #007bff; padding: 20px; background-color: #e9f7ff; font-size: 1.2em; font-weight: bold; word-break: break-all; }}
        </style>
    </head>
    <body>
        <h1>🥳 Félicitations! Exploit Réussi!</h1>
        <p>Vous avez trouvé la vulnérabilité XSS stockée.</p>
        <div class="flag">{FLAG}</div>
        <p><a href="/">Retourner au challenge</a></p>
    </body>
    </html>
    """
    return render_template_string(html)


if __name__ == '__main__':
    app.run(debug=True)
