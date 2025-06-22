import json
from src.llm_interface.llama_api import call_llama_api

KNOWLEDGE_GRAPH_PATH = 'knowledge_base/world_knowledge_graph.json'
GAME_STATE_PATH = 'knowledge_base/game_state.json'

def load_json_data(file_path: str) -> dict:
    """Loads data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def save_json_data(data: dict, file_path: str):
    """Saves data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def process_player_action(action: str) -> str:
    """
    Processes the player's action, updates the game state, and returns the new narrative.
    """
    # 1. Load current knowledge and state
    knowledge_graph = load_json_data(KNOWLEDGE_GRAPH_PATH)
    game_state = load_json_data(GAME_STATE_PATH)

    # 2. Add player action to conversation history
    game_state['conversation_history'].append(f"Player: {action}")

    # 3. Construct the prompt for the LLM
    prompt = f"The player's action is: '{action}'. Describe what happens next. Be creative but stay consistent with the world's rules and character personalities. End with a new choice or challenge for the player."

    # 4. Call the LLM to get the next part of the story
    context = {
        "world_knowledge": knowledge_graph,
        "current_game_state": game_state
    }
    narrative_update = call_llama_api(prompt, context)

    # 5. Update the game state with the new narrative
    game_state['conversation_history'].append(f"Narrator: {narrative_update}")

    # 6. Save the updated game state
    save_json_data(game_state, GAME_STATE_PATH)

    return narrative_update

def start_game() -> str:
    """Initializes the game and returns the opening message."""
    # This could be a static or LLM-generated intro
    initial_state = load_json_data(GAME_STATE_PATH)
    return initial_state['conversation_history'][0] if initial_state['conversation_history'] else "The adventure begins..." 