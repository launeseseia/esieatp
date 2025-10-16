# ctf_app.py
# Mini CTF Flask (délibérément vulnérable) – usage LOCAL uniquement.
# Endpoints:
#   /sqli   : Injection SQL simple (flag si contournement admin)
#   /upload : Upload de fichier (flag si condition atteinte)
#   /rce    : Command Injection (flag si preuve d'exécution)
#
# Flags via variables d'environnement (avec valeurs par défaut) :
#   FLAG_SQLI, FLAG_UPLOAD, FLAG_RCE
#
# DANGER : Ne jamais exposer en production.

import os
import sqlite3
import subprocess
from flask import Flask, request, redirect, url_for, send_from_directory, Response

app = Flask(__name__)

# Dossier d'uploads (servi publiquement par l'app)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Flags (modifiable via ENV)
FLAG_SQLI = os.getenv("FLAG_SQLI", "FLAG{SQLI_DEMO}")
FLAG_UPLOAD = os.getenv("FLAG_UPLOAD", "FLAG{UPLOAD_DEMO}")
FLAG_RCE = os.getenv("FLAG_RCE", "FLAG{RCE_DEMO}")

DB_PATH = os.path.join(os.path.dirname(__file__), "ctf.db")

BANNER = """
<h1>Mini CTF (LOCAL)</h1>
<p><b>⚠️ Appli volontairement vulnérable — usage pédagogique local uniquement.</b></p>
<ul>
  <li><a href="/sqli">SQL Injection</a></li>
  <li><a href="/upload">File Upload</a></li>
  <li><a href="/rce">Command Injection</a></li>
</ul>
<hr/>
"""

def init_db():
    # DB simple SQLite avec un compte admin
    create = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if create:
        c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
        c.execute("INSERT INTO users (username, password) VALUES ('admin','admin123')")
        c.execute("INSERT INTO users (username, password) VALUES ('user','password')")
        conn.commit()
    conn.close()

@app.route("/")
def index():
    return Response(BANNER, mimetype="text/html")

# ---------------------------
# 1) SQL Injection (simple)
# ---------------------------
@app.route("/sqli", methods=["GET", "POST"])
def sqli():
    html_form = f"""
    {BANNER}
    <h2>SQL Injection</h2>
    <p>Objectif : contourner l'authentification et obtenir le flag si vous êtes reconnu comme admin.</p>
    <form method="POST">
      <label>Username:</label> <input name="username" value="admin"><br/>
      <label>Password:</label> <input name="password" value=""><br/>
      <button type="submit">Login</button>
    </form>
    <p><i>Indice pédagogique :</i> Certaines concaténations SQL sont dangereuses si non paramétrées.</p>
    """
    if request.method == "GET":
        return Response(html_form, mimetype="text/html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # VULNÉRABLE : requête non paramétrée (concaténation directe)
    # Démo uniquement — SAST/CTF.
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = f"SELECT username FROM users WHERE username = '{username}' AND password = '{password}'"
    try:
        c.execute(query)
        row = c.fetchone()
    except Exception as e:
        row = None
    conn.close()

    if row and row[0] == "admin":
        return Response(BANNER + f"<h3>Authentifié comme admin ✅</h3><pre>{FLAG_SQLI}</pre>", mimetype="text/html")
    else:
        return Response(BANNER + "<h3>Échec d'authentification ❌</h3><p>Astuce : observez la requête et la manière dont elle est construite.</p>", mimetype="text/html")

# ---------------------------
# 2) File Upload (basique)
# ---------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    html_form = f"""
    {BANNER}
    <h2>File Upload</h2>
    <p>Objectif : déposer un fichier et satisfaire la condition pour révéler le flag.</p>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="file">
      <button type="submit">Upload</button>
    </form>
    <p><i>Indice pédagogique :</i> Valider côté serveur (extension/MIME), stocker hors webroot, et éviter toute exécution.</p>
    """

    if request.method == "GET":
        files = os.listdir(UPLOAD_DIR)
        listing = "<ul>" + "".join([f'<li><a href="/uploads/{f}">{f}</a></li>' for f in files]) + "</ul>"
        return Response(html_form + "<h3>Fichiers déjà présents :</h3>" + listing, mimetype="text/html")

    f = request.files.get("file")
    if not f or f.filename == "":
        return Response(BANNER + "<p>Aucun fichier reçu.</p>", mimetype="text/html")

    # VULNÉRABLE : aucune validation d'extension/MIME/nom
    save_path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(save_path)

    # CONDITION DÉMO POUR FLAG :
    # Si l'utilisateur parvient à téléverser un fichier nommé "proof.txt" contenant la chaîne "OWNED",
    # on révèle le flag (simulation d'un mauvais contrôle côté serveur).
    flag_html = ""
    try:
        if f.filename.lower() == "proof.txt":
            with open(save_path, "r", errors="ignore") as fp:
                content = fp.read()
                if "OWNED" in content:
                    flag_html = f"<pre>{FLAG_UPLOAD}</pre>"
    except Exception:
        pass

    return Response(BANNER + f"<p>Fichier <b>{f.filename}</b> uploadé.</p>{flag_html}<p>Accès : <a href='/uploads/{f.filename}'>/uploads/{f.filename}</a></p>", mimetype="text/html")

@app.route("/uploads/<path:fname>")
def serve_upload(fname):
    # Sert les fichiers uploadés (autre mauvaise pratique en réel si mal configuré)
    return send_from_directory(UPLOAD_DIR, fname)

# ---------------------------
# 3) Command Injection
# ---------------------------
@app.route("/rce", methods=["GET", "POST"])
def rce():
    html_form = f"""
    {BANNER}
    <h2>Command Injection</h2>
    <p>Objectif : influencer la commande exécutée côté serveur et prouver la capacité d'exécution.</p>
    <form method="POST">
      <label>Host à "tester":</label>
      <input name="host" value="127.0.0.1">
      <button type="submit">Run</button>
    </form>
    <p><i>Indice pédagogique :</i> L'usage direct du shell avec une entrée non contrôlée est dangereux.</p>
    """
    if request.method == "GET":
        return Response(html_form, mimetype="text/html")

    host = request.form.get("host", "")
    # VULNÉRABLE : passage direct au shell
    cmd = f"ping -c 1 {host}"
    try:
        output = subprocess.getoutput(cmd)  # utilise le shell
    except Exception as e:
        output = str(e)

    # CONDITION DÉMO POUR FLAG :
    # Si la sortie contient "RCE_OK", on affiche le flag (ex: via une injection qui émet cette chaîne).
    flag_html = ""
    if "RCE_OK" in output:
        flag_html = f"<h3>Preuve RCE détectée ✅</h3><pre>{FLAG_RCE}</pre>"

    safe_out = output.replace("<", "&lt;").replace(">", "&gt;")
    return Response(BANNER + f"<p>Commande exécutée : <code>{cmd}</code></p><pre>{safe_out}</pre>{flag_html}", mimetype="text/html")


if __name__ == "__main__":
    init_db()
    # Liaison sur localhost uniquement (ne pas exposer)
    app.run(host="127.0.0.1", port=5000, debug=False)
