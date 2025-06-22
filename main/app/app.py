from flask import Flask, render_template, request, jsonify
import sys
import os

# Add the project root to the Python path to allow for imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game_engine.main_game_loop import process_player_action, start_game

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main game page."""
    opening_message = start_game()
    return render_template('index.html', opening_message=opening_message)

@app.route('/play', methods=['POST'])
def play():
    """Handle the player's action."""
    data = request.get_json()
    player_action = data.get('action')

    if not player_action:
        return jsonify({'error': 'No action provided.'}), 400

    narrative = process_player_action(player_action)
    
    return jsonify({'narrative': narrative})

if __name__ == '__main__':
    app.run(debug=True) 