from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Welcome to app_para"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

@app.after_request
def add_custom_header(resp):
    resp.headers['CustomHeader'] = 'demo-app_para'  # valeur arbitraire
    return resp
