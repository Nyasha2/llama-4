import json
import logging
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from flask import Flask, jsonify, request
from flask_cors import CORS
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

from prompts import (
    CHARACTER_SYSTEM_PROMPT,
    RELATIONSHIP_SYSTEM_PROMPT,
    EVENT_EXTRACTION_SYSTEM_PROMPT,
    STORY_ADAPTATION_SYSTEM_PROMPT,
    CHARACTER_DIALOGUE_SYSTEM_PROMPT,
    WORLD_STATE_SYSTEM_PROMPT,
    PLAYER_CHOICE_SYSTEM_PROMPT,
    JSON_SYSTEM_PROMPT
)

# Flask setup
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameState(Enum):
    INITIALIZING = "initializing"
    BOOK_LOADED = "book_loaded"
    KNOWLEDGE_EXTRACTED = "knowledge_extracted"
    GAME_SETUP = "game_setup"
    PLAYING = "playing"
    PAUSED = "paused"

@dataclass
class GameSettings:
    book_title: str
    selected_character: str
    starting_point: int  # Event index to start from
    custom_setting: Optional[str] = None  # e.g., "New York modern setting"
    language: str = "English"
    difficulty: str = "normal"

@dataclass
class WorldState:
    current_event_index: int
    character_states: Dict
    location_states: Dict
    plot_elements: Dict
    relationships: Dict
    modified_events: List[Dict]

class InteractiveStoryEngine:
    def __init__(self, model_name: str = None):
        # Use a publicly available model by default, or allow custom model
        if model_name is None:
            # Try Llama 4 first, fall back to a public model if not accessible
            try:
                self.model_name = "Llama-4-Maverick-17B-128E-Instruct-FP8"
                # Test if we can access the model
                from transformers import AutoTokenizer
                AutoTokenizer.from_pretrained(self.model_name)
            except Exception:
                logger.warning("Llama 4 model not accessible, falling back to Llama 3.2")
                self.model_name = "Llama-3.2-3B-Instruct"
        else:
            self.model_name = model_name
            
        logger.info(f"Initializing with model: {self.model_name}")
        
        try:
            self.llm = LLM(
                model=self.model_name,
                enforce_eager=False,
                tensor_parallel_size=1,  # Reduced for compatibility
                max_model_len=32000,     # Reduced for smaller models
                override_generation_config={
                    "attn_temperature_tuning": True,
                },
            )
        except Exception as e:
            logger.error(f"Failed to initialize model {self.model_name}: {e}")
            logger.info("Trying with a smaller, public model...")
            self.model_name = "microsoft/DialoGPT-medium"
            self.llm = LLM(
                model=self.model_name,
                enforce_eager=False,
                tensor_parallel_size=1,
                max_model_len=1024,
            )
            
        self.sampling_params = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=4000)
        
        # Game state
        self.game_state = GameState.INITIALIZING
        self.book_content = ""
        self.book_title = ""
        self.characters = {}
        self.relationships = {}
        self.events_timeline = []
        self.world_state = None
        self.game_settings = None
        
        # Knowledge base storage
        self.knowledge_base_path = "knowledge_base/"
        os.makedirs(self.knowledge_base_path, exist_ok=True)

    def load_book(self, file_path: str) -> bool:
        """Load book from PDF or TXT file."""
        try:
            if file_path.endswith('.pdf'):
                self.book_content = self._extract_pdf_text(file_path)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.book_content = f.read()
            else:
                raise ValueError("Unsupported file format. Use PDF or TXT.")
            
            # Extract book title from content or filename
            self.book_title = self._extract_book_title()
            self.game_state = GameState.BOOK_LOADED
            logger.info(f"Book loaded successfully: {self.book_title}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading book: {e}")
            return False

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            raise
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise

    def _extract_book_title(self) -> str:
        """Extract book title from content."""
        lines = self.book_content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) < 100:  # Likely a title
                return line
        return "Unknown Title"

    def extract_knowledge_graphs(self) -> bool:
        """Extract characters, relationships, and events from the book."""
        try:
            logger.info("Starting knowledge extraction...")
            
            # Step 1: Extract characters and relationships
            self._extract_characters_and_relationships()
            
            # Step 2: Extract events timeline
            self._extract_events_timeline()
            
            # Step 3: Save knowledge base
            self._save_knowledge_base()
            
            self.game_state = GameState.KNOWLEDGE_EXTRACTED
            logger.info("Knowledge extraction completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during knowledge extraction: {e}")
            return False

    def _extract_characters_and_relationships(self):
        """Extract character relationships using LLM."""
        logger.info("Extracting characters and relationships...")
        
        # Step 1: Character analysis
        messages = [
            {"role": "system", "content": CHARACTER_SYSTEM_PROMPT},
            {"role": "user", "content": self.book_content},
        ]
        
        character_outputs = self.llm.chat(messages, self.sampling_params)
        character_analysis = character_outputs[0].outputs[0].text
        
        # Step 2: Relationship graph generation
        messages = [
            {"role": "system", "content": RELATIONSHIP_SYSTEM_PROMPT},
            {"role": "user", "content": f"Book Title: {self.book_title}\n\nCharacter Analysis:\n{character_analysis}"},
        ]
        
        relationship_outputs = self.llm.chat(messages, self.sampling_params)
        relationship_response = relationship_outputs[0].outputs[0].text
        
        # Extract JSON from response
        try:
            graph_data = self._extract_json_from_response(relationship_response)
            self.characters = {node['id']: node for node in graph_data['nodes']}
            self.relationships = graph_data
            logger.info(f"Extracted {len(self.characters)} characters and {len(graph_data['links'])} relationships")
        except Exception as e:
            logger.error(f"Error parsing relationship data: {e}")
            raise

    def _extract_events_timeline(self):
        """Extract chronological events from the book."""
        logger.info("Extracting events timeline...")
        
        messages = [
            {"role": "system", "content": EVENT_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": self.book_content},
        ]
        
        events_outputs = self.llm.chat(messages, self.sampling_params)
        events_response = events_outputs[0].outputs[0].text
        
        # Parse events from response
        self.events_timeline = self._parse_events_from_response(events_response)
        logger.info(f"Extracted {len(self.events_timeline)} events from timeline")

    def _parse_events_from_response(self, response: str) -> List[Dict]:
        """Parse events from LLM response."""
        events = []
        lines = response.split('\n')
        current_event = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('**Event Sequence'):
                if current_event:
                    events.append(current_event)
                current_event = {}
            elif line.startswith('* **Event ID:**'):
                current_event['id'] = line.split(':', 1)[1].strip()
            elif line.startswith('* **Type:**'):
                current_event['type'] = line.split(':', 1)[1].strip()
            elif line.startswith('* **Primary Characters:**'):
                current_event['primary_characters'] = [c.strip() for c in line.split(':', 1)[1].split(',')]
            elif line.startswith('* **Location:**'):
                current_event['location'] = line.split(':', 1)[1].strip()
            elif line.startswith('* **Description:**'):
                current_event['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('* **Interactive Potential:**'):
                current_event['interactive_potential'] = line.split(':', 1)[1].strip()
        
        if current_event:
            events.append(current_event)
        
        return events

    def setup_game(self, settings: GameSettings) -> bool:
        """Setup game with user preferences."""
        try:
            self.game_settings = settings
            
            # Initialize world state
            self.world_state = WorldState(
                current_event_index=settings.starting_point,
                character_states={},
                location_states={},
                plot_elements={},
                relationships=self.relationships,
                modified_events=[]
            )
            
            # Generate story summary up to starting point
            summary = self._generate_story_summary(settings.starting_point, settings)
            
            self.game_state = GameState.GAME_SETUP
            logger.info(f"Game setup completed. Starting at event {settings.starting_point}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up game: {e}")
            return False

    def _generate_story_summary(self, starting_point: int, settings: GameSettings) -> str:
        """Generate story summary up to the starting point with custom settings."""
        events_so_far = self.events_timeline[:starting_point]
        
        prompt = f"""
        Generate a story summary for the book "{self.book_title}" up to event {starting_point}.
        
        Custom Settings:
        - Setting: {settings.custom_setting or 'Original setting'}
        - Language: {settings.language}
        - Selected Character: {settings.selected_character}
        
        Events covered: {len(events_so_far)}
        
        Adapt the summary to the custom settings while maintaining the core story elements.
        End with the current situation for {settings.selected_character} and prompt for their next action.
        """
        
        messages = [
            {"role": "system", "content": "You are a master storyteller creating engaging story summaries."},
            {"role": "user", "content": prompt}
        ]
        
        outputs = self.llm.chat(messages, self.sampling_params)
        return outputs[0].outputs[0].text

    def start_game(self) -> Dict:
        """Start the interactive game."""
        if self.game_state != GameState.GAME_SETUP:
            raise ValueError("Game not properly set up")
        
        self.game_state = GameState.PLAYING
        
        # Generate initial summary and choices
        summary = self._generate_story_summary(self.game_settings.starting_point, self.game_settings)
        choices = self._generate_player_choices()
        
        return {
            "status": "game_started",
            "summary": summary,
            "current_character": self.game_settings.selected_character,
            "current_location": self._get_current_location(),
            "choices": choices
        }

    def _generate_player_choices(self) -> List[Dict]:
        """Generate meaningful choices for the player."""
        current_event = self.events_timeline[self.world_state.current_event_index]
        
        context = f"""
        Current Event: {current_event.get('description', '')}
        Character: {self.game_settings.selected_character}
        Location: {current_event.get('location', '')}
        Interactive Potential: {current_event.get('interactive_potential', '')}
        """
        
        messages = [
            {"role": "system", "content": PLAYER_CHOICE_SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ]
        
        outputs = self.llm.chat(messages, self.sampling_params)
        choice_response = outputs[0].outputs[0].text
        
        # Parse choices from response
        return self._parse_choices_from_response(choice_response)

    def _parse_choices_from_response(self, response: str) -> List[Dict]:
        """Parse player choices from LLM response."""
        choices = []
        lines = response.split('\n')
        current_choice = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('**Option'):
                if current_choice:
                    choices.append(current_choice)
                title = line.split(':', 1)[1].strip() if ':' in line else f"Choice {len(choices) + 1}"
                current_choice = {"title": title}
            elif line.startswith('* **Action:**'):
                current_choice['action'] = line.split(':', 1)[1].strip()
            elif line.startswith('* **Risk Level:**'):
                current_choice['risk_level'] = line.split(':', 1)[1].strip()
            elif line.startswith('* **Likely Immediate Outcome:**'):
                current_choice['outcome'] = line.split(':', 1)[1].strip()
        
        if current_choice:
            choices.append(current_choice)
        
        return choices

    def process_player_choice(self, choice_index: int, custom_action: str = None) -> Dict:
        """Process player's choice and adapt the story."""
        try:
            # Get current choices
            choices = self._generate_player_choices()
            
            if choice_index >= len(choices):
                raise ValueError("Invalid choice index")
            
            selected_choice = choices[choice_index]
            action = custom_action or selected_choice.get('action', '')
            
            # Adapt story based on choice
            adapted_story = self._adapt_story(action)
            
            # Update world state
            self._update_world_state(action, adapted_story)
            
            # Generate next choices
            next_choices = self._generate_player_choices()
            
            return {
                "status": "choice_processed",
                "action_taken": action,
                "story_continuation": adapted_story,
                "next_choices": next_choices,
                "world_state": self._get_world_state_summary()
            }
            
        except Exception as e:
            logger.error(f"Error processing player choice: {e}")
            return {"status": "error", "message": str(e)}

    def _adapt_story(self, player_action: str) -> str:
        """Adapt the story based on player action."""
        current_event = self.events_timeline[self.world_state.current_event_index]
        
        context = f"""
        Original Event: {current_event}
        Player Action: {player_action}
        Character: {self.game_settings.selected_character}
        World State: {self.world_state.__dict__}
        """
        
        messages = [
            {"role": "system", "content": STORY_ADAPTATION_SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ]
        
        outputs = self.llm.chat(messages, self.sampling_params)
        return outputs[0].outputs[0].text

    def _update_world_state(self, action: str, story_result: str):
        """Update the world state based on action and results."""
        # Move to next event
        self.world_state.current_event_index += 1
        
        # Record the modification
        modification = {
            "event_index": self.world_state.current_event_index - 1,
            "original_event": self.events_timeline[self.world_state.current_event_index - 1],
            "player_action": action,
            "result": story_result
        }
        self.world_state.modified_events.append(modification)

    def _get_current_location(self) -> str:
        """Get current location from world state."""
        if self.world_state.current_event_index < len(self.events_timeline):
            return self.events_timeline[self.world_state.current_event_index].get('location', 'Unknown')
        return 'Unknown'

    def _get_world_state_summary(self) -> Dict:
        """Get a summary of the current world state."""
        return {
            "current_event": self.world_state.current_event_index,
            "total_events": len(self.events_timeline),
            "modifications_made": len(self.world_state.modified_events),
            "current_location": self._get_current_location()
        }

    def _save_knowledge_base(self):
        """Save extracted knowledge to files."""
        # Save character relationships
        with open(os.path.join(self.knowledge_base_path, "world_knowledge_graph.json"), 'w') as f:
            json.dump(self.relationships, f, indent=2)
        
        # Save events timeline
        with open(os.path.join(self.knowledge_base_path, "events_timeline.json"), 'w') as f:
            json.dump(self.events_timeline, f, indent=2)
        
        # Save game state
        game_state_data = {
            "book_title": self.book_title,
            "total_characters": len(self.characters),
            "total_events": len(self.events_timeline),
            "extraction_complete": True
        }
        
        with open(os.path.join(self.knowledge_base_path, "game_state.json"), 'w') as f:
            json.dump(game_state_data, f, indent=2)

    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from LLM response."""
        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            
            if start_idx == -1 or end_idx == -1:
                # Try using JSON extraction prompt
                messages = [
                    {"role": "system", "content": JSON_SYSTEM_PROMPT},
                    {"role": "user", "content": response}
                ]
                
                outputs = self.llm.chat(messages, self.sampling_params)
                json_response = outputs[0].outputs[0].text
                return json.loads(json_response)
            
            json_str = response[start_idx:end_idx + 1]
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            raise

# Flask API endpoints
game_engine = InteractiveStoryEngine()

@app.route("/load_book", methods=["POST"])
def load_book():
    """Load a book file and extract knowledge."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        # Save uploaded file
        file_path = os.path.join("book_data", file.filename)
        os.makedirs("book_data", exist_ok=True)
        file.save(file_path)
        
        # Load and process book
        if not game_engine.load_book(file_path):
            return jsonify({"error": "Failed to load book"}), 500
        
        if not game_engine.extract_knowledge_graphs():
            return jsonify({"error": "Failed to extract knowledge"}), 500
        
        return jsonify({
            "status": "success",
            "book_title": game_engine.book_title,
            "characters": list(game_engine.characters.keys()),
            "total_events": len(game_engine.events_timeline)
        })
        
    except Exception as e:
        logger.error(f"Error loading book: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/setup_game", methods=["POST"])
def setup_game():
    """Setup game with user preferences."""
    try:
        data = request.json
        settings = GameSettings(
            book_title=data.get("book_title", game_engine.book_title),
            selected_character=data.get("selected_character"),
            starting_point=data.get("starting_point", 0),
            custom_setting=data.get("custom_setting"),
            language=data.get("language", "English"),
            difficulty=data.get("difficulty", "normal")
        )
        
        if not game_engine.setup_game(settings):
            return jsonify({"error": "Failed to setup game"}), 500
        
        return jsonify({"status": "game_setup_complete"})
        
    except Exception as e:
        logger.error(f"Error setting up game: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/start_game", methods=["POST"])
def start_game():
    """Start the interactive game."""
    try:
        result = game_engine.start_game()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/make_choice", methods=["POST"])
def make_choice():
    """Process player choice and continue story."""
    try:
        data = request.json
        choice_index = data.get("choice_index")
        custom_action = data.get("custom_action")
        
        result = game_engine.process_player_choice(choice_index, custom_action)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing choice: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_game_state", methods=["GET"])
def get_game_state():
    """Get current game state."""
    try:
        return jsonify({
            "game_state": game_engine.game_state.value,
            "world_state": game_engine._get_world_state_summary() if game_engine.world_state else None,
            "available_characters": list(game_engine.characters.keys()) if game_engine.characters else []
        })
        
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001) 