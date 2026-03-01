from flask import Flask
import socket
import os

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = socket.gethostname()
    return f"""
    <h1>Hello from DevOps Home Lab!</h1>
    <p>Pod: {hostname}</p>
    <p>Version: 1.0</p>
    """

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    port = os.environ.get('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port))