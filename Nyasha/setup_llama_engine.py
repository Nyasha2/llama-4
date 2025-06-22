#!/usr/bin/env python3
"""
Setup script for Llama 4 Enhanced Interactive Story Game Engine
This script installs dependencies and helps configure the environment.
"""

import os
import sys
import subprocess
import shutil

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error {description}: {e}")
        print(f"Error output: {e.stderr}")
        return None

def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing required dependencies...")
    
    # Check if we're in a virtual environment
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠️  Warning: You're not in a virtual environment!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Please activate your virtual environment and run this script again.")
            return False
    
    dependencies = [
        "flask",
        "flask-cors", 
        "requests",
        "python-dotenv",
        "spacy",
        "PyPDF2"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    # Install spaCy model
    run_command("python -m spacy download en_core_web_sm", "Installing spaCy English model")
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating necessary directories...")
    
    directories = [
        "uploads",
        "knowledge_base",
        "src/game_engine",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment_file():
    """Help user set up the .env file."""
    print("🔑 Setting up environment configuration...")
    
    env_file = ".env"
    env_example = """# Llama 4 API Configuration for Hackathon
# Your Llama API key provided for the hackathon
Llama_API_KEY=your_hackathon_api_key_here

# Llama API endpoint (default endpoint, modify if different)
Llama_API_ENDPOINT=https://api.llama-api.com/chat/completions

# Optional: Set to true for debug mode
DEBUG=true
"""
    
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} already exists. Backing it up...")
        shutil.copy(env_file, f"{env_file}.backup")
        print(f"✅ Backup created: {env_file}.backup")
    
    with open(env_file, 'w') as f:
        f.write(env_example)
    
    print(f"✅ Created {env_file} file")
    print("🔑 IMPORTANT: Edit the .env file and add your actual Llama API key!")
    print("   Replace 'your_hackathon_api_key_here' with your real API key")

def test_setup():
    """Test if the setup is working."""
    print("🧪 Testing setup...")
    
    try:
        # Test imports
        import flask
        import flask_cors
        import requests
        from dotenv import load_dotenv
        import spacy
        
        print("✅ All required packages imported successfully")
        
        # Test spaCy model
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy English model loaded successfully")
        except OSError:
            print("❌ spaCy English model not found. Run: python -m spacy download en_core_web_sm")
            return False
        
        # Test environment file
        load_dotenv()
        api_key = os.getenv("Llama_API_KEY")
        if api_key and api_key != "your_hackathon_api_key_here":
            print("✅ Environment configuration looks good")
        else:
            print("⚠️  Please update your .env file with your actual API key")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Llama 4 Enhanced Interactive Story Game Engine Setup")
    print("=" * 60)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment_file()
    
    # Test setup
    if test_setup():
        print("\n" + "=" * 60)
        print("🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Edit the .env file and add your Llama API key")
        print("2. Run the enhanced engine: python src/game_engine/llama_enhanced_engine.py")
        print("3. Run the web interface: python app/app.py")
        print("4. Open your browser to http://localhost:3000")
        print("\n🔗 API will be available at: http://localhost:5002")
        print("🌐 Web interface will be at: http://localhost:3000")
    else:
        print("❌ Setup completed with warnings. Please check the issues above.")

if __name__ == "__main__":
    main() 