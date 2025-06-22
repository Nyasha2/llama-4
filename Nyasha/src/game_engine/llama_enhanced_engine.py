import json
import logging
import os
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import Counter, defaultdict
import requests
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
CORS(app)

class GameState(Enum):
    INITIALIZING = "initializing"
    BOOK_LOADED = "book_loaded"
    KNOWLEDGE_EXTRACTED = "knowledge_extracted"
    GAME_SETUP = "game_setup"
    PLAYING = "playing"

@dataclass
class Character:
    name: str
    full_name: str
    aliases: List[str]
    role: str  # protagonist, antagonist, supporting, minor
    description: str
    relationships: Dict[str, str]
    first_appearance: int
    personality_traits: List[str]
    backstory: str
    current_status: str
    importance_score: float

@dataclass
class Event:
    id: str
    chapter: int
    sequence: int
    event_type: str
    characters_involved: List[str]
    location: str
    description: str
    consequences: List[str]
    emotional_tone: str
    plot_significance: str
    player_choice_potential: str
    original_text: str

@dataclass
class GameSettings:
    book_title: str
    selected_character: str
    starting_point: int
    custom_setting: Optional[str] = None
    language: str = "English"
    difficulty: str = "normal"

@dataclass
class WorldState:
    current_event_index: int
    current_chapter: int
    character_states: Dict[str, Dict]
    location_states: Dict[str, Dict]
    plot_elements: Dict[str, any]
    relationships: Dict[str, Dict]
    modified_events: List[Dict]
    story_arc_position: str
    player_choices_made: List[Dict]
    narrative_momentum: str

class LlamaAPI:
    """Interface for Llama 4 API calls using the exact format from the reference code."""
    
    def __init__(self):
        self.api_key = os.getenv("Llama_API_KEY")
        self.api_endpoint = os.getenv("Llama_API_ENDPOINT")
        
        if not self.api_key or not self.api_endpoint:
            logger.warning("Llama_API_KEY or Llama_API_ENDPOINT not found in environment variables. Using fallback mode.")
    
    def call_llama_api(self, prompt: str, context: dict, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """
        Sends a request to the Meta Llama API and returns the generated text.
        Uses the exact same format as the reference code.
        
        Args:
            prompt: The main instruction or question for the model.
            context: A dictionary containing the world knowledge and game state.
            max_tokens: Maximum tokens to generate
            temperature: Creativity vs coherence (0.0 to 1.0)
        
        Returns:
            The text content of the model's response, or an error message.
        """
        if not self.api_key or not self.api_endpoint:
            logger.warning("API key or endpoint not set. Running in mock response mode.")
            return self._get_mock_response(prompt)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Meta Llama API official format (matching reference code exactly)
        payload = {
            "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
            "messages": [
                {
                    "role": "user",
                    "content": f"You are a master storyteller and game master. Use the provided knowledge graph and game state to continue the story. Here is the context: {json.dumps(context)}\n\n{prompt}",
                }
            ],
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle the new response format with completion_message and metrics (from reference code)
            if 'completion_message' in data and 'content' in data['completion_message']:
                content = data['completion_message']['content']
                
                # Handle content that can be either a string or an object with 'text' field
                if isinstance(content, dict) and 'text' in content:
                    return content['text'].strip()
                elif isinstance(content, str):
                    return content.strip()
                else:
                    return f"Error: Unexpected content format in completion_message: {content}"
            
            # Fallback to the old format for backward compatibility
            elif 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            
            else:
                return f"Error: Unexpected response format. Response: {data}"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Llama API: {e}")
            return self._get_mock_response(prompt)
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing API response: {e}")
            return self._get_mock_response(prompt)
    
    def _get_mock_response(self, prompt: str) -> str:
        """Returns a mock response for testing purposes (from reference code)."""
        prompt_lower = prompt.lower()
        
        if "character" in prompt_lower or "backstory" in prompt_lower:
            return """You are Alex the Explorer, a curious and intelligent adventurer with a thirst for discovery. Your journey began in the quiet village where you grew up, always dreaming of the mysteries that lay beyond the familiar hills.

Recently, you've discovered ancient maps and cryptic messages that hint at a great treasure hidden in the mystical realm beyond the forest. Your courage and determination have brought you to this pivotal moment where your choices will shape not just your destiny, but the fate of all who depend on you.

The path ahead is uncertain, but your spirit remains unbroken. What will you choose to do next?"""
        
        elif "choice" in prompt_lower or "decision" in prompt_lower:
            return """Your decision creates ripples through the fabric of the story. The consequences of your choice begin to unfold:

As you move forward with your chosen path, you notice the world around you responding to your actions. Characters react differently, new opportunities emerge, and the very nature of your quest begins to evolve.

The story continues to adapt to your choices, creating a unique narrative experience tailored to your decisions."""
        
        elif "story" in prompt_lower or "continue" in prompt_lower:
            return """The narrative unfolds before you like an ancient scroll being unrolled for the first time. Your choices have set in motion a chain of events that will reshape the very fabric of this tale.

New challenges emerge on the horizon, and unexpected allies may reveal themselves. The path you've chosen leads to uncharted territories where your courage and wisdom will be tested in ways you never imagined.

What happens next depends entirely on the choices you make."""
        
        else:
            return "The story continues to evolve based on your choices. Each decision you make opens new possibilities and shapes the narrative in unique ways. What would you like to do next?"

class LlamaEnhancedStoryEngine:
    def __init__(self):
        self.game_state = GameState.INITIALIZING
        self.book_content = ""
        self.book_title = ""
        self.characters: Dict[str, Character] = {}
        self.events: List[Event] = []
        self.locations: Set[str] = set()
        self.relationships_graph = {}
        self.world_state = None
        self.game_settings = None
        self.llama_api = LlamaAPI()
        
        # Knowledge base storage
        self.knowledge_base_path = "knowledge_base/"
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        
        logger.info("Llama Enhanced Story Engine initialized")

    def load_book(self, file_path: str) -> bool:
        """Load and parse book content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.book_content = f.read()
            
            self.book_title = self._extract_book_title()
            self.game_state = GameState.BOOK_LOADED
            logger.info(f"Book loaded successfully: {self.book_title}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading book: {e}")
            return False

    def _extract_book_title(self) -> str:
        """Extract book title from content."""
        lines = self.book_content.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) < 100 and not line.startswith('Chapter'):
                return line
        return "Unknown Title"

    def extract_knowledge_graphs(self) -> bool:
        """Extract comprehensive knowledge graphs using Llama 4 for enhanced analysis."""
        try:
            logger.info("Starting Llama-enhanced knowledge extraction...")
            
            # Step 1: Use Llama 4 to analyze the book and extract characters
            self._llama_extract_characters()
            
            # Step 2: Use Llama 4 to extract and analyze events
            self._llama_extract_events()
            
            # Step 3: Extract locations
            self._extract_locations()
            
            # Step 4: Use Llama 4 to build relationship graph
            self._llama_build_relationships()
            
            # Step 5: Save knowledge base
            self._save_knowledge_base()
            
            self.game_state = GameState.KNOWLEDGE_EXTRACTED
            logger.info("Llama-enhanced knowledge extraction completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during knowledge extraction: {e}")
            return False

    def _llama_extract_characters(self):
        """Use Llama 4 to extract and analyze characters."""
        # First, use basic pattern matching to find potential characters
        self._extract_character_names()
        
        # Then use Llama 4 to enhance character analysis
        for name in self.character_names[:10]:  # Limit to top 10 characters for API efficiency
            context = {
                "book_title": self.book_title,
                "character_name": name,
                "book_excerpt": self.book_content[:2000]  # First 2000 chars for context
            }
            
            prompt = f"""
            Analyze the character '{name}' from the book "{self.book_title}".
            
            Based on the text provided, determine:
            1. Character role (protagonist, antagonist, supporting, minor)
            2. 3 key personality traits
            3. Brief backstory (2-3 sentences)
            4. Character's importance to the story (scale 1-10)
            
            Respond in JSON format:
            {{
                "role": "protagonist/antagonist/supporting/minor",
                "traits": ["trait1", "trait2", "trait3"],
                "backstory": "Character background...",
                "importance": 8
            }}
            """
            
            response = self.llama_api.call_llama_api(prompt, context, max_tokens=300, temperature=0.3)
            
            try:
                # Try to parse JSON response
                char_data = json.loads(response)
                
                self.characters[name] = Character(
                    name=name,
                    full_name=name,
                    aliases=[],
                    role=char_data.get('role', 'character'),
                    description=f"Character from {self.book_title}",
                    relationships={},
                    first_appearance=1,
                    personality_traits=char_data.get('traits', ['mysterious']),
                    backstory=char_data.get('backstory', f"{name} is a character in {self.book_title}."),
                    current_status="active",
                    importance_score=float(char_data.get('importance', 5))
                )
            except (json.JSONDecodeError, KeyError):
                # Fallback to basic analysis if JSON parsing fails
                self.characters[name] = self._create_basic_character_profile(name)
        
        logger.info(f"Llama-enhanced analysis completed for {len(self.characters)} characters")

    def _llama_extract_events(self):
        """Use Llama 4 to extract and analyze story events."""
        # Split content into manageable chunks
        chunks = self._split_into_chunks(self.book_content, 1500)
        
        self.events = []
        for i, chunk in enumerate(chunks[:10]):  # Limit for API efficiency
            context = {
                "book_title": self.book_title,
                "chunk_number": i + 1,
                "characters": list(self.characters.keys()),
                "text_chunk": chunk
            }
            
            prompt = f"""
            Analyze this text chunk from "{self.book_title}" and extract the main story event.
            
            Characters in the story: {', '.join(list(self.characters.keys())[:5])}
            
            For the main event in this text, provide:
            1. Event type (dialogue, conflict, journey, reflection, narrative)
            2. Characters involved (from the list above)
            3. Location where it takes place
            4. Brief description (1-2 sentences)
            5. Emotional tone (positive, negative, neutral, tense, mysterious)
            
            Respond in JSON format:
            {{
                "event_type": "dialogue",
                "characters_involved": ["character1", "character2"],
                "location": "location name",
                "description": "Brief event description...",
                "emotional_tone": "positive"
            }}
            """
            
            response = self.llama_api.call_llama_api(prompt, context, max_tokens=250, temperature=0.4)
            
            try:
                event_data = json.loads(response)
                
                event = Event(
                    id=f"evt_{i+1:03d}",
                    chapter=1,
                    sequence=i,
                    event_type=event_data.get('event_type', 'narrative'),
                    characters_involved=event_data.get('characters_involved', []),
                    location=event_data.get('location', 'Unknown location'),
                    description=event_data.get('description', chunk[:100] + "..."),
                    consequences=[],
                    emotional_tone=event_data.get('emotional_tone', 'neutral'),
                    plot_significance="medium",
                    player_choice_potential=self._generate_choice_potential(event_data),
                    original_text=chunk
                )
                
                self.events.append(event)
                
            except (json.JSONDecodeError, KeyError):
                # Fallback to basic event creation
                event = self._create_basic_event(i, chunk)
                self.events.append(event)
        
        logger.info(f"Llama-enhanced analysis completed for {len(self.events)} events")

    def _llama_build_relationships(self):
        """Use Llama 4 to analyze character relationships."""
        if len(self.characters) < 2:
            self.relationships_graph = {"characters": {}, "relationships": []}
            return
        
        characters_list = list(self.characters.keys())[:5]  # Limit for API efficiency
        
        context = {
            "book_title": self.book_title,
            "characters": characters_list,
            "book_excerpt": self.book_content[:3000]
        }
        
        prompt = f"""
        Analyze the relationships between characters in "{self.book_title}".
        
        Characters: {', '.join(characters_list)}
        
        For each pair of characters that interact, determine their relationship type:
        - friend (allies, companions)
        - enemy (rivals, opponents)
        - family (relatives)
        - romantic (love interests)
        - mentor (teacher-student)
        - neutral (acquaintances)
        
        Respond in JSON format with an array of relationships:
        {{
            "relationships": [
                {{"character1": "Name1", "character2": "Name2", "type": "friend"}},
                {{"character1": "Name3", "character2": "Name4", "type": "enemy"}}
            ]
        }}
        """
        
        response = self.llama_api.call_llama_api(prompt, context, max_tokens=400, temperature=0.3)
        
        try:
            rel_data = json.loads(response)
            
            # Build relationships graph
            self.relationships_graph = {
                "title": self.book_title,
                "summary": f"Character relationships in {self.book_title}",
                "characters": {name: asdict(char) for name, char in self.characters.items()},
                "relationships": []
            }
            
            for rel in rel_data.get('relationships', []):
                char1 = rel.get('character1')
                char2 = rel.get('character2')
                rel_type = rel.get('type', 'neutral')
                
                if char1 in self.characters and char2 in self.characters:
                    self.relationships_graph["relationships"].append({
                        "source": char1,
                        "target": char2,
                        "type": rel_type,
                        "strength": 1.0
                    })
                    
                    # Update character relationships
                    self.characters[char1].relationships[char2] = rel_type
                    self.characters[char2].relationships[char1] = rel_type
                    
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse Llama relationship analysis, using fallback")
            self._build_basic_relationships()

    def start_game(self) -> Dict:
        """Start the interactive game with Llama-enhanced backstory."""
        if self.game_state != GameState.GAME_SETUP:
            raise ValueError("Game not properly set up")
        
        if not self.game_settings or not self.world_state:
            raise ValueError("Game settings or world state not initialized")
        
        self.game_state = GameState.PLAYING
        
        # Get selected character details
        selected_char = self.characters.get(self.game_settings.selected_character, {})
        
        # Use Llama 4 to generate comprehensive backstory
        backstory = self._llama_generate_backstory()
        
        # Get current situation
        current_event = self.events[self.world_state.current_event_index] if self.world_state.current_event_index < len(self.events) else None
        
        # Use Llama 4 to generate enhanced summary
        summary = self._llama_generate_game_summary(selected_char, backstory, current_event)
        
        # Generate contextual choices using Llama 4
        choices = self._llama_generate_choices(current_event)
        
        return {
            "status": "game_started",
            "summary": summary,
            "current_character": self.game_settings.selected_character,
            "current_location": current_event.location if current_event else 'Starting point',
            "character_details": asdict(selected_char) if isinstance(selected_char, Character) else selected_char,
            "backstory": backstory,
            "choices": choices
        }

    def _llama_generate_backstory(self) -> str:
        """Use Llama 4 to generate character backstory."""
        if not self.world_state or not self.game_settings:
            return "Your story is about to begin."
        
        context = {
            "book_title": self.book_title,
            "character": self.game_settings.selected_character,
            "starting_point": self.world_state.current_event_index,
            "character_details": asdict(self.characters.get(self.game_settings.selected_character, {})),
            "events_so_far": [asdict(event) for event in self.events[:self.world_state.current_event_index]]
        }
        
        prompt = f"""
        Generate a compelling backstory for {self.game_settings.selected_character} in "{self.book_title}".
        
        The player is starting at event {self.world_state.current_event_index} of the story.
        
        Create a 2-3 paragraph backstory that:
        1. Summarizes what {self.game_settings.selected_character} has experienced so far
        2. Establishes their current situation and mindset
        3. Sets up their motivations and goals
        4. Makes the player feel connected to the character
        
        Write in second person ("You are {self.game_settings.selected_character}...") to immerse the player.
        """
        
        response = self.llama_api.call_llama_api(prompt, context, max_tokens=400, temperature=0.6)
        return response

    def _llama_generate_game_summary(self, character, backstory, current_event) -> str:
        """Use Llama 4 to generate enhanced game summary."""
        context = {
            "book_title": self.book_title,
            "character": character,
            "backstory": backstory,
            "current_event": asdict(current_event) if current_event else None,
            "custom_setting": self.game_settings.custom_setting,
            "language": self.game_settings.language
        }
        
        prompt = f"""
        Create an engaging game start summary for an interactive story experience.
        
        Include:
        1. Welcome message with book title
        2. Character introduction with role and traits
        3. Setting information (including custom setting if provided)
        4. Current situation description
        5. An exciting call to action
        
        Use emojis and formatting to make it visually appealing.
        Keep it concise but immersive.
        """
        
        response = self.llama_api.call_llama_api(prompt, context, max_tokens=300, temperature=0.7)
        return response

    def _llama_generate_choices(self, current_event) -> List[Dict]:
        """Use Llama 4 to generate contextual choices."""
        if not current_event:
            return self._generate_default_choices()
        
        context = {
            "character": self.game_settings.selected_character,
            "current_event": asdict(current_event),
            "character_traits": self.characters.get(self.game_settings.selected_character, {}).personality_traits,
            "relationships": self.characters.get(self.game_settings.selected_character, {}).relationships
        }
        
        prompt = f"""
        Generate 3 meaningful choice options for {self.game_settings.selected_character} in this situation:
        
        Event: {current_event.description}
        Location: {current_event.location}
        Event Type: {current_event.event_type}
        
        Each choice should:
        1. Be appropriate for the character and situation
        2. Have different risk levels (Low/Medium/High)
        3. Lead to different potential outcomes
        4. Reflect the character's personality and relationships
        
        Respond in JSON format:
        {{
            "choices": [
                {{
                    "title": "Choice Title",
                    "action": "Detailed action description",
                    "risk_level": "Low/Medium/High",
                    "outcome": "Potential consequence"
                }}
            ]
        }}
        """
        
        response = self.llama_api.call_llama_api(prompt, context, max_tokens=400, temperature=0.8)
        
        try:
            choices_data = json.loads(response)
            return choices_data.get('choices', self._generate_default_choices())
        except (json.JSONDecodeError, KeyError):
            return self._generate_default_choices()

    def process_player_choice(self, choice_index: int, custom_action: str = None) -> Dict:
        """Process player choice using Llama 4 for dynamic story continuation."""
        try:
            # Record the choice
            choice_made = {
                "event_index": self.world_state.current_event_index,
                "choice_index": choice_index,
                "custom_action": custom_action,
                "timestamp": self.world_state.current_event_index
            }
            self.world_state.player_choices_made.append(choice_made)
            
            # Use Llama 4 to generate story continuation
            story_continuation = self._llama_generate_story_continuation(choice_made)
            
            # Use Llama 4 to generate next choices
            next_choices = self._llama_generate_next_choices(choice_made)
            
            # Update world state
            self._update_world_state(choice_made)
            
            # Advance story
            self.world_state.current_event_index += 1
            
            return {
                "status": "choice_processed",
                "story_continuation": story_continuation,
                "action_taken": custom_action or f"Choice {choice_index + 1}",
                "next_choices": next_choices,
                "world_state": self._get_world_state_summary()
            }
            
        except Exception as e:
            logger.error(f"Error processing choice: {e}")
            return {"status": "error", "message": str(e)}

    def _llama_generate_story_continuation(self, choice_made: Dict) -> str:
        """Use Llama 4 to generate dynamic story continuation."""
        context = {
            "character": self.game_settings.selected_character,
            "choice_made": choice_made,
            "world_state": asdict(self.world_state),
            "character_details": asdict(self.characters.get(self.game_settings.selected_character, {})),
            "recent_events": [asdict(event) for event in self.events[max(0, self.world_state.current_event_index-2):self.world_state.current_event_index+1]],
            "custom_setting": self.game_settings.custom_setting
        }
        
        action_description = choice_made.get('custom_action', f"made choice {choice_made.get('choice_index', 0) + 1}")
        
        prompt = f"""
        Continue the interactive story for {self.game_settings.selected_character}.
        
        {self.game_settings.selected_character} just {action_description}.
        
        Generate a compelling 2-3 paragraph continuation that:
        1. Shows the immediate consequences of the choice
        2. Advances the plot meaningfully
        3. Maintains character consistency
        4. Creates new opportunities for player engagement
        5. Incorporates the custom setting if provided: {self.game_settings.custom_setting or 'original setting'}
        
        Write in an engaging, immersive style that makes the player feel their choice mattered.
        """
        
        response = self.llama_api.call_llama_api(prompt, context, max_tokens=500, temperature=0.7)
        return response

    def _llama_generate_next_choices(self, choice_made: Dict) -> List[Dict]:
        """Use Llama 4 to generate next set of choices based on the story continuation."""
        context = {
            "character": self.game_settings.selected_character,
            "previous_choice": choice_made,
            "story_progress": len(self.world_state.player_choices_made),
            "character_relationships": self.characters.get(self.game_settings.selected_character, {}).relationships
        }
        
        prompt = f"""
        Generate 3 new choice options for {self.game_settings.selected_character} after their recent action.
        
        The story has progressed, and new opportunities have emerged.
        
        Create choices that:
        1. Build on the consequences of the previous action
        2. Offer different strategic approaches
        3. Vary in risk and potential reward
        4. Allow for character growth and relationship development
        
        Respond in JSON format:
        {{
            "choices": [
                {{
                    "title": "Choice Title",
                    "action": "What the character will do",
                    "risk_level": "Low/Medium/High",
                    "outcome": "Potential result"
                }}
            ]
        }}
        """
        
        response = self.llama_api.call_llama_api(prompt, context, max_tokens=400, temperature=0.8)
        
        try:
            choices_data = json.loads(response)
            return choices_data.get('choices', self._generate_default_choices())
        except (json.JSONDecodeError, KeyError):
            return self._generate_default_choices()

    # Include all the helper methods from the previous implementation
    def _extract_character_names(self):
        """Extract character names using pattern matching (fallback method)."""
        import re
        from collections import Counter
        
        # Pattern matching for character names
        dialogue_pattern = r'([A-Z][a-z]+)\s+(?:said|asked|replied|whispered|shouted|exclaimed|muttered|cried)'
        possessive_pattern = r"([A-Z][a-z]+)'s"
        address_pattern = r'[,\s]([A-Z][a-z]+)[,\s]*[!?.]'
        title_pattern = r'(?:Mr\.|Mrs\.|Miss|Ms\.|Dr\.|Professor)\s+([A-Z][a-z]+)'
        
        all_names = []
        for pattern in [dialogue_pattern, possessive_pattern, address_pattern, title_pattern]:
            all_names.extend(re.findall(pattern, self.book_content))
        
        name_counts = Counter(all_names)
        false_positives = {
            'The', 'And', 'But', 'When', 'Where', 'What', 'How', 'Why', 'This', 'That',
            'Chapter', 'Book', 'Part', 'Then', 'Now', 'Here', 'There', 'They', 'She', 'He'
        }
        
        self.character_names = []
        for name, count in name_counts.items():
            if count >= 3 and name not in false_positives and len(name) > 1:
                self.character_names.append(name)
        
        # Ensure we have at least a few characters
        if len(self.character_names) < 2:
            all_caps = re.findall(r'\b[A-Z][a-z]+\b', self.book_content)
            caps_counter = Counter(all_caps)
            for name, count in caps_counter.most_common(10):
                if name not in false_positives and name not in self.character_names:
                    self.character_names.append(name)
                if len(self.character_names) >= 5:
                    break

    def _create_basic_character_profile(self, name: str) -> Character:
        """Create basic character profile as fallback."""
        return Character(
            name=name,
            full_name=name,
            aliases=[],
            role="character",
            description=f"Character from {self.book_title}",
            relationships={},
            first_appearance=1,
            personality_traits=["mysterious"],
            backstory=f"{name} is a character in {self.book_title}.",
            current_status="active",
            importance_score=5.0
        )

    def _split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into manageable chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def _create_basic_event(self, index: int, text: str) -> Event:
        """Create basic event as fallback."""
        return Event(
            id=f"evt_{index+1:03d}",
            chapter=1,
            sequence=index,
            event_type="narrative",
            characters_involved=[],
            location="Unknown location",
            description=text[:150] + "..." if len(text) > 150 else text,
            consequences=[],
            emotional_tone="neutral",
            plot_significance="medium",
            player_choice_potential="Determine your next action",
            original_text=text
        )

    def _generate_choice_potential(self, event_data: Dict) -> str:
        """Generate choice potential from event data."""
        event_type = event_data.get('event_type', 'narrative')
        characters = event_data.get('characters_involved', [])
        
        if characters:
            main_char = characters[0]
            if event_type == 'dialogue':
                return f"Choose how {main_char} responds in this conversation"
            elif event_type == 'conflict':
                return f"Decide {main_char}'s strategy for this challenge"
            else:
                return f"Determine {main_char}'s next action"
        return "Decide how to proceed"

    def _build_basic_relationships(self):
        """Build basic relationships as fallback."""
        self.relationships_graph = {
            "title": self.book_title,
            "summary": f"Character relationships in {self.book_title}",
            "characters": {name: asdict(char) for name, char in self.characters.items()},
            "relationships": []
        }

    def _extract_locations(self):
        """Extract locations from events."""
        for event in self.events:
            if event.location != "Unknown location":
                self.locations.add(event.location)

    def _generate_default_choices(self) -> List[Dict]:
        """Generate default choices when Llama API fails."""
        char_name = self.game_settings.selected_character if self.game_settings else "the character"
        
        return [
            {
                "title": "Explore and Investigate",
                "action": f"Look around carefully and gather information",
                "risk_level": "Low",
                "outcome": "Discover new details about your surroundings"
            },
            {
                "title": "Take Bold Action",
                "action": f"Act decisively and take charge of the situation",
                "risk_level": "High",
                "outcome": "Create significant change but face potential consequences"
            },
            {
                "title": "Proceed Cautiously",
                "action": f"Move forward carefully, considering all options",
                "risk_level": "Medium",
                "outcome": "Make steady progress while minimizing risks"
            }
        ]

    def setup_game(self, settings: GameSettings) -> bool:
        """Setup game with user preferences."""
        try:
            self.game_settings = settings
            
            self.world_state = WorldState(
                current_event_index=settings.starting_point,
                current_chapter=1,
                character_states={},
                location_states={},
                plot_elements={},
                relationships=self.relationships_graph,
                modified_events=[],
                story_arc_position="beginning",
                player_choices_made=[],
                narrative_momentum="building"
            )
            
            # Initialize character states
            for char_name, character in self.characters.items():
                self.world_state.character_states[char_name] = {
                    "status": "active",
                    "location": "unknown",
                    "emotional_state": "neutral",
                    "relationships": character.relationships.copy(),
                    "knowledge": [],
                    "goals": []
                }
            
            self.game_state = GameState.GAME_SETUP
            logger.info(f"Game setup completed for character: {settings.selected_character}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up game: {e}")
            return False

    def _update_world_state(self, choice_made: Dict):
        """Update world state based on player choice."""
        # Update narrative momentum
        if len(self.world_state.player_choices_made) < 3:
            self.world_state.narrative_momentum = "building"
        elif len(self.world_state.player_choices_made) < 7:
            self.world_state.narrative_momentum = "accelerating"
        else:
            self.world_state.narrative_momentum = "climactic"
        
        # Update story arc position
        total_events = len(self.events)
        progress = self.world_state.current_event_index / max(total_events, 1)
        
        if progress < 0.3:
            self.world_state.story_arc_position = "beginning"
        elif progress < 0.7:
            self.world_state.story_arc_position = "middle"
        else:
            self.world_state.story_arc_position = "climax"

    def _get_world_state_summary(self) -> Dict:
        """Get comprehensive world state summary."""
        return {
            "current_event": self.world_state.current_event_index,
            "total_events": len(self.events),
            "current_chapter": self.world_state.current_chapter,
            "story_arc_position": self.world_state.story_arc_position,
            "narrative_momentum": self.world_state.narrative_momentum,
            "modifications_made": len(self.world_state.player_choices_made),
            "current_location": self.events[min(self.world_state.current_event_index, len(self.events)-1)].location if self.events else "Unknown"
        }

    def _save_knowledge_base(self):
        """Save extracted knowledge to files."""
        try:
            # Save characters
            characters_data = {name: asdict(char) for name, char in self.characters.items()}
            with open(os.path.join(self.knowledge_base_path, "characters.json"), 'w') as f:
                json.dump(characters_data, f, indent=2)
            
            # Save events
            events_data = [asdict(event) for event in self.events]
            with open(os.path.join(self.knowledge_base_path, "events.json"), 'w') as f:
                json.dump(events_data, f, indent=2)
            
            # Save relationships
            with open(os.path.join(self.knowledge_base_path, "relationships.json"), 'w') as f:
                json.dump(self.relationships_graph, f, indent=2)
            
            logger.info("Knowledge base saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")

# Initialize the Llama-enhanced engine
engine = LlamaEnhancedStoryEngine()

# API Routes (same as before but using the enhanced engine)
@app.route("/load_book", methods=["POST"])
def load_book():
    """Load and process a book file with Llama enhancement."""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "error": "No file uploaded"})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "error": "No file selected"})
        
        # Save uploaded file
        filename = file.filename
        filepath = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(filepath)
        
        # Load book
        if engine.load_book(filepath):
            # Extract knowledge graphs with Llama enhancement
            if engine.extract_knowledge_graphs():
                return jsonify({
                    "status": "success",
                    "book_title": engine.book_title,
                    "characters": list(engine.characters.keys()),
                    "character_details": {name: {
                        "role": char.role,
                        "traits": char.personality_traits,
                        "importance": char.importance_score,
                        "backstory": char.backstory[:100] + "..." if len(char.backstory) > 100 else char.backstory
                    } for name, char in engine.characters.items()},
                    "total_events": len(engine.events),
                    "locations": list(engine.locations),
                    "message": "Book processed successfully with Llama 4 enhanced analysis"
                })
            else:
                return jsonify({"status": "error", "error": "Failed to extract knowledge from book"})
        else:
            return jsonify({"status": "error", "error": "Failed to load book"})
    
    except Exception as e:
        logger.error(f"Error in load_book: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route("/setup_game", methods=["POST"])
def setup_game():
    """Setup game with user preferences."""
    try:
        data = request.get_json()
        
        settings = GameSettings(
            book_title=engine.book_title,
            selected_character=data.get('selected_character'),
            starting_point=data.get('starting_point', 0),
            custom_setting=data.get('custom_setting'),
            language=data.get('language', 'English'),
            difficulty=data.get('difficulty', 'normal')
        )
        
        if engine.setup_game(settings):
            return jsonify({
                "status": "game_setup_complete",
                "character": settings.selected_character,
                "character_details": asdict(engine.characters[settings.selected_character]) if settings.selected_character in engine.characters else {},
                "starting_point": settings.starting_point,
                "custom_setting": settings.custom_setting,
                "world_state": engine._get_world_state_summary()
            })
        else:
            return jsonify({"status": "error", "error": "Failed to setup game"})
    
    except Exception as e:
        logger.error(f"Error in setup_game: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route("/start_game", methods=["POST"])
def start_game():
    """Start the interactive game with Llama enhancement."""
    try:
        result = engine.start_game()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in start_game: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route("/make_choice", methods=["POST"])
def make_choice():
    """Process player choice with Llama enhancement."""
    try:
        data = request.get_json()
        choice_index = data.get('choice_index', 0)
        custom_action = data.get('custom_action')
        
        result = engine.process_player_choice(choice_index, custom_action)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in make_choice: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route("/get_game_state", methods=["GET"])
def get_game_state():
    """Get current game state."""
    try:
        return jsonify({
            "status": "success",
            "game_state": engine.game_state.value,
            "world_state": engine._get_world_state_summary() if engine.world_state else None,
            "character_details": asdict(engine.characters[engine.game_settings.selected_character]) if engine.game_settings and engine.game_settings.selected_character in engine.characters else None
        })
    
    except Exception as e:
        logger.error(f"Error in get_game_state: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route("/", methods=["GET"])
def home():
    """API home endpoint."""
    return jsonify({
        "message": "Llama 4 Enhanced Interactive Story Game Engine API",
        "status": "running",
        "llama_api_status": "configured" if engine.llama_api.api_key else "fallback_mode",
        "features": [
            "🤖 Llama 4 powered character analysis and story generation",
            "📚 Real character extraction with AI-enhanced profiling",
            "🎭 Dynamic story continuation based on player choices",
            "🧠 Intelligent relationship mapping and world building",
            "⚡ Contextual choice generation with consequence prediction",
            "🌍 Custom setting integration and multi-language support"
        ],
        "endpoints": [
            "/load_book - POST - Upload and AI-analyze books",
            "/setup_game - POST - Configure enhanced gameplay",
            "/start_game - POST - Begin AI-powered interactive story",
            "/make_choice - POST - Process choices with dynamic consequences",
            "/get_game_state - GET - Get comprehensive game status"
        ]
    })

if __name__ == '__main__':
    print("🤖 Starting Llama 4 Enhanced Interactive Story Game Engine...")
    print("📚 Upload a book file to begin AI-powered story analysis!")
    print("🔑 Make sure to set your LLAMA_API_KEY environment variable")
    print("🌐 API running on http://localhost:5002")
    app.run(debug=True, port=5002, host='0.0.0.0') 