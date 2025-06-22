import json
import logging
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from flask import Flask, jsonify, request
from flask_cors import CORS

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
    character_states: Dict
    location_states: Dict
    plot_elements: Dict
    relationships: Dict
    modified_events: List[Dict]

class SimpleStoryEngine:
    def __init__(self):
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
        logger.info("Simple Story Engine initialized")

    def load_book(self, file_path: str) -> bool:
        """Load book from TXT file."""
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
            if line and len(line) < 100:
                return line
        return "Unknown Title"

    def extract_knowledge_graphs(self) -> bool:
        """Enhanced knowledge extraction from book content."""
        try:
            logger.info("Starting enhanced knowledge extraction...")
            
            # Extract actual character names from the text
            self._extract_character_names()
            
            # Build character profiles
            self._build_character_profiles()
            
            # Extract story events
            self._extract_story_events()
            
            # Build relationships
            self._build_relationships()
            
            self._save_knowledge_base()
            self.game_state = GameState.KNOWLEDGE_EXTRACTED
            logger.info("Enhanced knowledge extraction completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during knowledge extraction: {e}")
            return False

    def _extract_character_names(self):
        """Extract actual character names from the book text."""
        import re
        from collections import Counter
        
        # Find potential character names using patterns
        # Look for capitalized words that appear frequently and in dialogue contexts
        
        # Pattern 1: Names in dialogue (words before "said", "asked", etc.)
        dialogue_pattern = r'([A-Z][a-z]+)\s+(?:said|asked|replied|whispered|shouted|exclaimed|muttered|cried)'
        dialogue_names = re.findall(dialogue_pattern, self.book_content)
        
        # Pattern 2: Possessive forms (Alex's, Mary's, etc.)
        possessive_pattern = r"([A-Z][a-z]+)'s"
        possessive_names = re.findall(possessive_pattern, self.book_content)
        
        # Pattern 3: Direct address ("Hello, John", "Come here, Sarah")
        address_pattern = r'[,\s]([A-Z][a-z]+)[,\s]*[!?.]'
        address_names = re.findall(address_pattern, self.book_content)
        
        # Pattern 4: Common name patterns with titles
        title_pattern = r'(?:Mr\.|Mrs\.|Miss|Ms\.|Dr\.|Professor)\s+([A-Z][a-z]+)'
        title_names = re.findall(title_pattern, self.book_content)
        
        # Combine all potential names
        all_names = dialogue_names + possessive_names + address_names + title_names
        
        # Count occurrences and filter
        name_counts = Counter(all_names)
        
        # Filter out common false positives
        false_positives = {
            'The', 'And', 'But', 'When', 'Where', 'What', 'How', 'Why', 'This', 'That',
            'Chapter', 'Book', 'Part', 'Then', 'Now', 'Here', 'There', 'They', 'She', 'He'
        }
        
        # Keep names that appear at least 3 times and aren't false positives
        self.character_names = []
        for name, count in name_counts.items():
            if count >= 3 and name not in false_positives and len(name) > 1:
                self.character_names.append(name)
        
        # If we don't find enough names, add some from the text
        if len(self.character_names) < 2:
            # Look for any capitalized words that might be names
            all_caps = re.findall(r'\b[A-Z][a-z]+\b', self.book_content)
            caps_counter = Counter(all_caps)
            for name, count in caps_counter.most_common(10):
                if name not in false_positives and name not in self.character_names:
                    self.character_names.append(name)
                if len(self.character_names) >= 5:
                    break
        
        logger.info(f"Found character names: {self.character_names}")

    def _build_character_profiles(self):
        """Build detailed profiles for each character."""
        self.characters = {}
        
        for name in self.character_names:
            # Find contexts where this character appears
            contexts = self._find_character_contexts(name)
            
            # Determine character role
            role = self._determine_character_role(name, contexts)
            
            # Extract traits
            traits = self._extract_character_traits(name, contexts)
            
            # Create backstory
            backstory = self._create_character_backstory(name, contexts)
            
            self.characters[name] = {
                "id": f"char_{len(self.characters)}",
                "name": name,
                "role": role,
                "traits": traits,
                "backstory": backstory,
                "contexts": contexts[:3],  # Keep first 3 contexts
                "importance": len(contexts)
            }

    def _find_character_contexts(self, name):
        """Find sentences/paragraphs where character appears."""
        import re
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', self.book_content)
        contexts = []
        
        for sentence in sentences:
            if name in sentence and len(sentence.strip()) > 20:
                contexts.append(sentence.strip())
        
        return contexts

    def _determine_character_role(self, name, contexts):
        """Determine character's role based on context."""
        all_text = ' '.join(contexts).lower()
        
        # Count role indicators
        protagonist_words = ['hero', 'main', 'journey', 'adventure', 'quest', 'destiny', 'chosen']
        antagonist_words = ['villain', 'enemy', 'evil', 'dark', 'against', 'oppose', 'kill']
        supporting_words = ['friend', 'ally', 'help', 'support', 'companion', 'guide']
        
        p_score = sum(1 for word in protagonist_words if word in all_text)
        a_score = sum(1 for word in antagonist_words if word in all_text)
        s_score = sum(1 for word in supporting_words if word in all_text)
        
        if p_score > a_score and p_score > s_score:
            return "protagonist"
        elif a_score > s_score:
            return "antagonist"
        elif s_score > 0:
            return "supporting"
        else:
            return "character"

    def _extract_character_traits(self, name, contexts):
        """Extract personality traits from contexts."""
        all_text = ' '.join(contexts).lower()
        
        trait_keywords = {
            'brave': ['brave', 'courageous', 'fearless', 'bold', 'heroic'],
            'kind': ['kind', 'gentle', 'compassionate', 'caring', 'loving'],
            'intelligent': ['smart', 'clever', 'wise', 'brilliant', 'genius'],
            'mysterious': ['mysterious', 'secretive', 'enigmatic', 'hidden'],
            'determined': ['determined', 'persistent', 'stubborn', 'resolved'],
            'funny': ['funny', 'humorous', 'witty', 'jokes', 'laughed']
        }
        
        traits = []
        for trait, keywords in trait_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                traits.append(trait)
        
        return traits[:3] if traits else ['mysterious']

    def _create_character_backstory(self, name, contexts):
        """Create character backstory from contexts."""
        if not contexts:
            return f"{name} is a character in {self.book_title}."
        
        # Take the most descriptive context
        best_context = max(contexts, key=len)
        
        # Clean and format
        backstory = f"{name} appears in the story: {best_context[:200]}..."
        return backstory

    def _extract_story_events(self):
        """Extract story events from the text."""
        import re
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in self.book_content.split('\n\n') if len(p.strip()) > 50]
        
        self.events_timeline = []
        for i, paragraph in enumerate(paragraphs[:20]):  # First 20 paragraphs
            # Find characters in this paragraph
            chars_involved = [name for name in self.character_names if name in paragraph]
            
            # Determine event type
            event_type = self._classify_paragraph_type(paragraph)
            
            # Extract location hints
            location = self._extract_location_hints(paragraph)
            
            event = {
                "id": f"evt_{i+1:03d}",
                "sequence": i,
                "type": event_type,
                "primary_characters": chars_involved,
                "location": location,
                "description": paragraph[:150] + "..." if len(paragraph) > 150 else paragraph,
                "full_text": paragraph,
                "interactive_potential": self._generate_interaction_potential(paragraph, chars_involved)
            }
            
            self.events_timeline.append(event)

    def _classify_paragraph_type(self, paragraph):
        """Classify the type of story event."""
        text = paragraph.lower()
        
        if any(word in text for word in ['said', 'asked', 'replied', 'spoke']):
            return 'dialogue'
        elif any(word in text for word in ['fight', 'battle', 'attack', 'struck']):
            return 'conflict'
        elif any(word in text for word in ['went', 'walked', 'traveled', 'moved']):
            return 'journey'
        elif any(word in text for word in ['felt', 'thought', 'remembered', 'realized']):
            return 'reflection'
        else:
            return 'narrative'

    def _extract_location_hints(self, paragraph):
        """Extract location information from paragraph."""
        import re
        
        # Look for location patterns
        location_patterns = [
            r'in the ([A-Z][a-z]+ ?[A-Z]?[a-z]*)',
            r'at the ([A-Z][a-z]+ ?[A-Z]?[a-z]*)',
            r'through the ([A-Z][a-z]+ ?[A-Z]?[a-z]*)',
            r'near the ([A-Z][a-z]+ ?[A-Z]?[a-z]*)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, paragraph)
            if match:
                return match.group(1)
        
        # Default locations based on common words
        text = paragraph.lower()
        if 'forest' in text:
            return 'Forest'
        elif 'castle' in text:
            return 'Castle'
        elif 'village' in text:
            return 'Village'
        elif 'home' in text:
            return 'Home'
        else:
            return 'Unknown location'

    def _generate_interaction_potential(self, paragraph, characters):
        """Generate potential player interactions for this event."""
        if not characters:
            return "Observe and decide how to proceed"
        
        main_char = characters[0]
        text = paragraph.lower()
        
        if 'said' in text or 'asked' in text:
            return f"Choose how {main_char} responds in this conversation"
        elif 'fight' in text or 'danger' in text:
            return f"Decide {main_char}'s strategy for handling this threat"
        elif 'door' in text or 'path' in text:
            return f"Choose which direction {main_char} should go"
        else:
            return f"Determine {main_char}'s next action in this situation"

    def _build_relationships(self):
        """Build relationship graph between characters."""
        self.relationships = {
            "title": self.book_title,
            "summary": f"Character relationships extracted from {self.book_title}",
            "nodes": [
                {
                    "id": char["id"],
                    "name": char["name"],
                    "role": char["role"],
                    "traits": char["traits"]
                }
                for char in self.characters.values()
            ],
            "links": []
        }
        
        # Find relationships by checking co-occurrences
        for char1_name, char1_data in self.characters.items():
            for char2_name, char2_data in self.characters.items():
                if char1_name != char2_name:
                    relationship = self._find_relationship(char1_name, char2_name)
                    if relationship:
                        self.relationships["links"].append({
                            "source": char1_data["id"],
                            "target": char2_data["id"],
                            "label": relationship
                        })

    def _find_relationship(self, char1, char2):
        """Find relationship between two characters."""
        # Look for sentences containing both characters
        import re
        sentences = re.split(r'[.!?]+', self.book_content)
        
        for sentence in sentences:
            if char1 in sentence and char2 in sentence:
                sentence_lower = sentence.lower()
                
                # Check for relationship indicators
                if any(word in sentence_lower for word in ['friend', 'ally', 'together']):
                    return 'friend'
                elif any(word in sentence_lower for word in ['enemy', 'rival', 'against']):
                    return 'enemy'
                elif any(word in sentence_lower for word in ['father', 'mother', 'brother', 'sister']):
                    return 'family'
                elif any(word in sentence_lower for word in ['love', 'beloved']):
                    return 'romantic'
                else:
                    return 'knows'
        
        return None

    def setup_game(self, settings: GameSettings) -> bool:
        """Setup game with user preferences."""
        try:
            self.game_settings = settings
            
            self.world_state = WorldState(
                current_event_index=settings.starting_point,
                character_states={},
                location_states={},
                plot_elements={},
                relationships=self.relationships,
                modified_events=[]
            )
            
            self.game_state = GameState.GAME_SETUP
            logger.info(f"Game setup completed. Starting at event {settings.starting_point}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up game: {e}")
            return False

    def start_game(self) -> Dict:
        """Start the interactive game with comprehensive backstory."""
        if self.game_state != GameState.GAME_SETUP:
            raise ValueError("Game not properly set up")
        
        if not self.game_settings or not self.world_state:
            raise ValueError("Game settings or world state not initialized")
        
        self.game_state = GameState.PLAYING
        
        # Get selected character details
        selected_char = self.characters.get(self.game_settings.selected_character, {})
        
        # Generate comprehensive backstory up to starting point
        backstory = self._generate_backstory_summary()
        
        # Get current situation
        current_event = self.events_timeline[self.world_state.current_event_index] if self.world_state.current_event_index < len(self.events_timeline) else None
        
        # Create comprehensive summary
        summary = f"""
🎭 Welcome to "{self.book_title}"!

🎯 You are playing as: {self.game_settings.selected_character}
📍 Setting: {self.game_settings.custom_setting or 'Original story setting'}
🗣️ Language: {self.game_settings.language}

👤 About {self.game_settings.selected_character}:
Role: {selected_char.get('role', 'Character').title()}
Traits: {', '.join(selected_char.get('traits', ['Determined']))}
{selected_char.get('backstory', f'{self.game_settings.selected_character} is ready for adventure.')}

📖 Story So Far:
{backstory}

🎬 Current Situation:
{current_event['description'] if current_event else 'You stand at the beginning of your adventure, ready to make choices that will shape your destiny.'}
📍 Location: {current_event['location'] if current_event else 'Starting point'}

What do you choose to do?
        """
        
        choices = self._generate_contextual_choices(current_event)
        
        return {
            "status": "game_started",
            "summary": summary,
            "current_character": self.game_settings.selected_character,
            "current_location": current_event.get('location', 'Starting point') if current_event else 'Starting point',
            "character_details": selected_char,
            "backstory": backstory,
            "choices": choices
        }

    def _generate_backstory_summary(self):
        """Generate summary of what happened before the starting point."""
        if not self.world_state or not self.game_settings:
            return "Your story is about to begin."
            
        if self.world_state.current_event_index == 0:
            return f"You are {self.game_settings.selected_character}, and your story is about to begin."
        
        # Get events up to starting point that involve the character
        relevant_events = []
        for i in range(min(self.world_state.current_event_index, len(self.events_timeline))):
            event = self.events_timeline[i]
            if self.game_settings.selected_character in event.get('primary_characters', []):
                relevant_events.append(event)
        
        if not relevant_events:
            return f"As {self.game_settings.selected_character}, you have been part of this story, and now you're ready to take control of your destiny."
        
        # Create narrative from relevant events
        backstory_parts = []
        for event in relevant_events[-5:]:  # Last 5 relevant events
            backstory_parts.append(f"• {event['description']}")
        
        backstory = f"Here's what {self.game_settings.selected_character} has experienced so far:\n\n"
        backstory += "\n".join(backstory_parts)
        backstory += f"\n\nNow, as {self.game_settings.selected_character}, you have the power to shape what happens next."
        
        return backstory

    def _generate_contextual_choices(self, current_event):
        """Generate choices based on current event context."""
        if not current_event:
            return self._generate_default_choices()
        
        event_type = current_event.get('type', 'narrative')
        characters = current_event.get('primary_characters', [])
        char_name = self.game_settings.selected_character
        
        if event_type == 'dialogue':
            return [
                {
                    "title": "Engage Actively",
                    "action": f"Participate fully in the conversation as {char_name}",
                    "risk_level": "Medium",
                    "outcome": "Influence the direction of the conversation and build relationships"
                },
                {
                    "title": "Listen Carefully",
                    "action": f"Pay close attention to what others are saying",
                    "risk_level": "Low",
                    "outcome": "Gather valuable information without revealing your intentions"
                },
                {
                    "title": "Ask Probing Questions",
                    "action": f"Challenge others with pointed questions",
                    "risk_level": "High",
                    "outcome": "Uncover hidden truths but potentially create tension"
                }
            ]
        elif event_type == 'conflict':
            return [
                {
                    "title": "Face the Challenge Head-On",
                    "action": f"Confront the conflict directly with courage",
                    "risk_level": "High",
                    "outcome": "Potentially resolve the conflict but face significant danger"
                },
                {
                    "title": "Seek a Peaceful Solution",
                    "action": f"Try to find a diplomatic resolution",
                    "risk_level": "Medium",
                    "outcome": "Avoid violence but may need to make compromises"
                },
                {
                    "title": "Use Strategy and Cunning",
                    "action": f"Outmaneuver opponents through clever tactics",
                    "risk_level": "Medium",
                    "outcome": "Gain advantage through intelligence rather than force"
                }
            ]
        elif event_type == 'journey':
            return [
                {
                    "title": "Lead the Way",
                    "action": f"Take charge and guide others forward",
                    "risk_level": "Medium",
                    "outcome": "Shape the direction of the journey and earn respect"
                },
                {
                    "title": "Scout Ahead",
                    "action": f"Explore the path ahead for dangers and opportunities",
                    "risk_level": "High",
                    "outcome": "Discover important information but face unknown risks"
                },
                {
                    "title": "Stay Alert and Ready",
                    "action": f"Remain vigilant while traveling",
                    "risk_level": "Low",
                    "outcome": "Be prepared for whatever comes next"
                }
            ]
        else:
            return [
                {
                    "title": "Take Initiative",
                    "action": f"Be proactive and shape the situation",
                    "risk_level": "Medium",
                    "outcome": "Influence events but take responsibility for the consequences"
                },
                {
                    "title": "Observe and Learn",
                    "action": f"Watch carefully and gather information",
                    "risk_level": "Low",
                    "outcome": "Understand the situation better before acting"
                },
                {
                    "title": "Follow Your Instincts",
                    "action": f"Trust your gut feeling about what to do",
                    "risk_level": "Medium",
                    "outcome": "Make authentic choices that reflect your character"
                }
            ]

    def _generate_default_choices(self):
        """Generate default choices when no specific event context."""
        char_name = self.game_settings.selected_character
        
        return [
            {
                "title": "Explore Your World",
                "action": f"Look around and discover what's available to {char_name}",
                "risk_level": "Low",
                "outcome": "Learn about your environment and find new opportunities"
            },
            {
                "title": "Seek Out Allies",
                "action": f"Look for friends and companions to join your journey",
                "risk_level": "Medium",
                "outcome": "Build relationships but reveal your intentions to others"
            },
            {
                "title": "Plan Your Adventure",
                "action": f"Take time to think about your goals and strategy",
                "risk_level": "Low",
                "outcome": "Make more informed decisions going forward"
            }
        ]

    def _generate_mock_choices(self, event: Dict) -> List[Dict]:
        """Generate mock choices based on event type."""
        base_choices = [
            {
                "title": "Cautious Approach",
                "action": "Proceed carefully and observe the situation",
                "risk_level": "Low",
                "outcome": "Gather more information safely"
            },
            {
                "title": "Bold Action", 
                "action": "Take decisive action immediately",
                "risk_level": "High",
                "outcome": "Quick resolution but potential consequences"
            },
            {
                "title": "Diplomatic Solution",
                "action": "Try to negotiate or find peaceful resolution",
                "risk_level": "Medium",
                "outcome": "Attempt to resolve without conflict"
            }
        ]
        
        # Add event-specific choice
        if event['type'] == 'conflict':
            base_choices.append({
                "title": "Strategic Retreat",
                "action": "Fall back and regroup",
                "risk_level": "Low",
                "outcome": "Live to fight another day"
            })
        
        return base_choices

    def process_player_choice(self, choice_index: int, custom_action: str = None) -> Dict:
        """Process player's choice and continue story."""
        try:
            current_event = self.events_timeline[self.world_state.current_event_index]
            choices = self._generate_mock_choices(current_event)
            
            if choice_index >= len(choices):
                raise ValueError("Invalid choice index")
            
            selected_choice = choices[choice_index]
            action = custom_action or selected_choice.get('action', '')
            
            # Mock story continuation
            story_continuation = f"""
            You chose: {selected_choice['title']}
            Action taken: {action}
            
            Result: {selected_choice['outcome']}
            
            The story continues as your choice ripples through the narrative...
            """
            
            # Update world state
            self.world_state.current_event_index = min(
                self.world_state.current_event_index + 1,
                len(self.events_timeline) - 1
            )
            
            # Record modification
            modification = {
                "event_index": self.world_state.current_event_index - 1,
                "player_action": action,
                "choice_made": selected_choice['title'],
                "result": selected_choice['outcome']
            }
            self.world_state.modified_events.append(modification)
            
            # Generate next choices if not at end
            if self.world_state.current_event_index < len(self.events_timeline):
                next_event = self.events_timeline[self.world_state.current_event_index]
                next_choices = self._generate_mock_choices(next_event)
            else:
                next_choices = [{"title": "End of Story", "action": "The adventure concludes", "risk_level": "None", "outcome": "Story complete"}]
            
            return {
                "status": "choice_processed",
                "action_taken": action,
                "story_continuation": story_continuation,
                "next_choices": next_choices,
                "world_state": self._get_world_state_summary()
            }
            
        except Exception as e:
            logger.error(f"Error processing player choice: {e}")
            return {"status": "error", "message": str(e)}

    def _get_world_state_summary(self) -> Dict:
        """Get a summary of the current world state."""
        return {
            "current_event": self.world_state.current_event_index,
            "total_events": len(self.events_timeline),
            "modifications_made": len(self.world_state.modified_events),
            "current_location": self.events_timeline[self.world_state.current_event_index].get('location', 'Unknown') if self.world_state.current_event_index < len(self.events_timeline) else 'Story Complete'
        }

    def _save_knowledge_base(self):
        """Save extracted knowledge to files."""
        with open(os.path.join(self.knowledge_base_path, "world_knowledge_graph.json"), 'w') as f:
            json.dump(self.relationships, f, indent=2)
        
        with open(os.path.join(self.knowledge_base_path, "events_timeline.json"), 'w') as f:
            json.dump(self.events_timeline, f, indent=2)
        
        game_state_data = {
            "book_title": self.book_title,
            "total_characters": len(self.characters),
            "total_events": len(self.events_timeline),
            "extraction_complete": True
        }
        
        with open(os.path.join(self.knowledge_base_path, "game_state.json"), 'w') as f:
            json.dump(game_state_data, f, indent=2)

# Initialize game engine
game_engine = SimpleStoryEngine()

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
            "characters": [char["name"] for char in game_engine.characters.values()],
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
            selected_character=data.get("selected_character", "Protagonist"),
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
        choice_index = data.get("choice_index", 0)
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
            "available_characters": [char["name"] for char in game_engine.characters.values()] if game_engine.characters else []
        })
        
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    """Home endpoint."""
    return jsonify({
        "message": "Interactive Story Game Engine API",
        "status": "running",
        "endpoints": [
            "/load_book - POST - Upload and process a book",
            "/setup_game - POST - Configure game settings", 
            "/start_game - POST - Begin interactive gameplay",
            "/make_choice - POST - Process player choices",
            "/get_game_state - GET - Get current game status"
        ]
    })

if __name__ == "__main__":
    print("🎮 Starting Interactive Story Game Engine...")
    print("📚 Upload a book file to begin your adventure!")
    print("🌐 API running on http://localhost:5001")
    app.run(debug=True, port=5001) 