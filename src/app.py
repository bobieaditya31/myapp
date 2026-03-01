from flask import Flask
import os
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = socket.gethostname()
    return f"""
    <h1>Hello from Jenkins + ArgoCD + Kind!</h1>
    <p>Pod: {hostname}</p>
    <p>Version: v1.0</p>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "service": "myapp"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)