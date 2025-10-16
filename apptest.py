from flask import Flask, request
app = Flask(__name__)

@app.route("/")

def home():
	#request.headers.get('CustomHeader', 'squalala')
	return "Welcome to app1"
	
@app.route("/test")

def test():
	return "squalala"

	
@app.route("/error")

def error():
	return 1 / 0
		
if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5001)
	

