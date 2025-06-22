from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.route('/health')
def health():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Web interface is running"}

if __name__ == '__main__':
    print("🌐 Starting Web Interface Server...")
    print("📱 Open your browser to: http://localhost:3000")
    print("🎮 Make sure the Game Engine API is running on port 5001")
    app.run(debug=True, port=3000, host='0.0.0.0') 