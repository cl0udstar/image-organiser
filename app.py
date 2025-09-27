#!/usr/bin/env python3
"""
Image Organizer - Flask Backend
Modern web-based image organization tool
"""

import sys
import os
from flask import Flask
from flask_cors import CORS

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # Enable CORS for development
    CORS(app)
    
    # Import and setup routes after Flask app is created
    try:
        from backend.api_routes import setup_routes
        setup_routes(app)
        print("✅ Routes loaded successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Please check your file structure and __init__.py files")
        return None
    
    return app

if __name__ == '__main__':
    print("🖼️  Image Organizer Server Starting...")
    
    app = create_app()
    if app is None:
        print("❌ Failed to create app. Exiting.")
        sys.exit(1)
    
    print("🌐 Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
