import json
import logging
import os
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import Counter, defaultdict
import spacy
from spacy import displacy

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
class Character:
    name: str
    full_name: str
    aliases: List[str]
    role: str  # protagonist, antagonist, supporting, minor
    description: str
    relationships: Dict[str, str]
    first_appearance: int  # chapter/section number
    personality_traits: List[str]
    backstory: str
    current_status: str
    importance_score: float

@dataclass
class Event:
    id: str
    chapter: int
    sequence: int
    event_type: str  # dialogue, action, description, conflict, resolution
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

class EnhancedStoryEngine:
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
        self.nlp = None
        
        # Knowledge base storage
        self.knowledge_base_path = "knowledge_base/"
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        
        # Initialize NLP model
        self._initialize_nlp()
        logger.info("Enhanced Story Engine initialized")

    def _initialize_nlp(self):
        """Initialize spaCy NLP model for text processing."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.warning("SpaCy model not found. Using basic text processing.")
            self.nlp = None

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
        """Extract comprehensive knowledge graphs from the book."""
        try:
            logger.info("Starting comprehensive knowledge extraction...")
            
            # Step 1: Extract characters with detailed information
            self._extract_characters()
            
            # Step 2: Extract events and plot structure
            self._extract_events()
            
            # Step 3: Extract locations
            self._extract_locations()
            
            # Step 4: Build relationship graph
            self._build_relationship_graph()
            
            # Step 5: Analyze character importance and roles
            self._analyze_character_importance()
            
            # Step 6: Save knowledge base
            self._save_knowledge_base()
            
            self.game_state = GameState.KNOWLEDGE_EXTRACTED
            logger.info("Knowledge extraction completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during knowledge extraction: {e}")
            return False

    def _extract_characters(self):
        """Extract character names and information using NLP."""
        logger.info("Extracting characters...")
        
        # Find potential character names using NLP
        character_mentions = defaultdict(int)
        character_contexts = defaultdict(list)
        
        if self.nlp:
            # Use spaCy for named entity recognition
            doc = self.nlp(self.book_content[:50000])  # Process first 50k chars
            
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    if self._is_valid_character_name(name):
                        character_mentions[name] += 1
                        # Get context around the mention
                        start = max(0, ent.start_char - 100)
                        end = min(len(self.book_content), ent.end_char + 100)
                        context = self.book_content[start:end]
                        character_contexts[name].append(context)
        else:
            # Fallback: Use regex patterns for common name patterns
            name_patterns = [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last
                r'\b[A-Z][a-z]+\b(?=\s+(?:said|asked|replied|thought|felt|went|came|looked|smiled|laughed|cried|whispered|shouted))',
                r'(?:Mr\.|Mrs\.|Ms\.|Dr\.|Professor)\s+[A-Z][a-z]+',
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, self.book_content)
                for match in matches:
                    if self._is_valid_character_name(match):
                        character_mentions[match] += 1

        # Filter and create character objects
        min_mentions = 3  # Minimum mentions to be considered a character
        for name, count in character_mentions.items():
            if count >= min_mentions:
                character = self._create_character_profile(name, character_contexts[name])
                self.characters[name] = character
        
        logger.info(f"Extracted {len(self.characters)} characters")

    def _is_valid_character_name(self, name: str) -> bool:
        """Check if a name is likely a valid character name."""
        # Filter out common false positives
        invalid_names = {
            'Chapter', 'Book', 'Part', 'Section', 'The', 'And', 'But', 'When', 'Where',
            'What', 'How', 'Why', 'This', 'That', 'There', 'Here', 'Now', 'Then'
        }
        
        if name in invalid_names:
            return False
        
        # Must be 2-30 characters, contain at least one letter
        if not (2 <= len(name) <= 30 and re.search(r'[a-zA-Z]', name)):
            return False
        
        return True

    def _create_character_profile(self, name: str, contexts: List[str]) -> Character:
        """Create detailed character profile from contexts."""
        # Analyze contexts to determine character traits
        all_context = ' '.join(contexts)
        
        # Determine role based on mention frequency and context
        role = self._determine_character_role(name, all_context)
        
        # Extract personality traits
        traits = self._extract_personality_traits(all_context)
        
        # Create backstory from contexts
        backstory = self._generate_character_backstory(name, all_context)
        
        # Find relationships
        relationships = self._find_character_relationships(name, all_context)
        
        return Character(
            name=name,
            full_name=name,
            aliases=[],
            role=role,
            description=f"Character from {self.book_title}",
            relationships=relationships,
            first_appearance=1,
            personality_traits=traits,
            backstory=backstory,
            current_status="active",
            importance_score=0.0
        )

    def _determine_character_role(self, name: str, context: str) -> str:
        """Determine character's role in the story."""
        context_lower = context.lower()
        
        # Keywords that suggest different roles
        protagonist_keywords = ['hero', 'main', 'journey', 'quest', 'adventure', 'destiny']
        antagonist_keywords = ['villain', 'enemy', 'evil', 'dark', 'against', 'oppose']
        supporting_keywords = ['friend', 'ally', 'help', 'support', 'companion']
        
        protagonist_score = sum(1 for word in protagonist_keywords if word in context_lower)
        antagonist_score = sum(1 for word in antagonist_keywords if word in context_lower)
        supporting_score = sum(1 for word in supporting_keywords if word in context_lower)
        
        if protagonist_score > antagonist_score and protagonist_score > supporting_score:
            return "protagonist"
        elif antagonist_score > supporting_score:
            return "antagonist"
        elif supporting_score > 0:
            return "supporting"
        else:
            return "minor"

    def _extract_personality_traits(self, context: str) -> List[str]:
        """Extract personality traits from context."""
        trait_keywords = {
            'brave': ['brave', 'courageous', 'fearless', 'bold'],
            'kind': ['kind', 'gentle', 'compassionate', 'caring'],
            'intelligent': ['smart', 'clever', 'wise', 'brilliant'],
            'mysterious': ['mysterious', 'secretive', 'enigmatic'],
            'determined': ['determined', 'persistent', 'stubborn'],
            'humorous': ['funny', 'witty', 'humorous', 'jokes']
        }
        
        traits = []
        context_lower = context.lower()
        
        for trait, keywords in trait_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                traits.append(trait)
        
        return traits[:3]  # Return top 3 traits

    def _generate_character_backstory(self, name: str, context: str) -> str:
        """Generate character backstory from context."""
        # Find sentences that mention the character
        sentences = re.split(r'[.!?]+', context)
        character_sentences = [s.strip() for s in sentences if name in s and len(s) > 20]
        
        if character_sentences:
            # Take the most descriptive sentences
            backstory_parts = character_sentences[:3]
            return f"{name} appears in the story with the following background: " + " ".join(backstory_parts)
        else:
            return f"{name} is a character in {self.book_title} whose background unfolds throughout the story."

    def _find_character_relationships(self, name: str, context: str) -> Dict[str, str]:
        """Find relationships between characters."""
        relationships = {}
        
        # Look for other character names in this character's context
        for other_name in self.characters.keys():
            if other_name != name and other_name in context:
                # Determine relationship type based on context
                relationship_type = self._determine_relationship_type(name, other_name, context)
                if relationship_type:
                    relationships[other_name] = relationship_type
        
        return relationships

    def _determine_relationship_type(self, char1: str, char2: str, context: str) -> str:
        """Determine the type of relationship between two characters."""
        context_lower = context.lower()
        
        relationship_keywords = {
            'friend': ['friend', 'ally', 'companion', 'together'],
            'enemy': ['enemy', 'rival', 'against', 'fight', 'battle'],
            'family': ['father', 'mother', 'brother', 'sister', 'son', 'daughter'],
            'mentor': ['teacher', 'mentor', 'guide', 'master'],
            'romantic': ['love', 'beloved', 'romance', 'marry', 'kiss']
        }
        
        for rel_type, keywords in relationship_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                return rel_type
        
        return 'acquaintance'

    def _extract_events(self):
        """Extract story events and plot structure."""
        logger.info("Extracting story events...")
        
        # Split content into chapters or sections
        chapters = self._split_into_chapters()
        
        event_id = 1
        for chapter_num, chapter_content in enumerate(chapters):
            chapter_events = self._extract_chapter_events(chapter_num + 1, chapter_content)
            for event in chapter_events:
                event.id = f"evt_{event_id:03d}"
                event_id += 1
                self.events.append(event)
        
        logger.info(f"Extracted {len(self.events)} events")

    def _split_into_chapters(self) -> List[str]:
        """Split book content into chapters."""
        # Look for chapter markers
        chapter_patterns = [
            r'Chapter \d+',
            r'CHAPTER \d+',
            r'Chapter [IVXLC]+',
            r'\d+\.',
            r'Part \d+'
        ]
        
        for pattern in chapter_patterns:
            matches = list(re.finditer(pattern, self.book_content))
            if len(matches) > 1:  # Found multiple chapters
                chapters = []
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(self.book_content)
                    chapters.append(self.book_content[start:end])
                return chapters
        
        # If no chapter markers found, split into equal parts
        content_length = len(self.book_content)
        chunk_size = content_length // 10  # 10 sections
        chapters = []
        for i in range(0, content_length, chunk_size):
            chapters.append(self.book_content[i:i + chunk_size])
        
        return chapters

    def _extract_chapter_events(self, chapter_num: int, content: str) -> List[Event]:
        """Extract events from a chapter."""
        events = []
        
        # Split chapter into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for seq, paragraph in enumerate(paragraphs):
            if len(paragraph) > 50:  # Only process substantial paragraphs
                event = self._create_event_from_paragraph(chapter_num, seq, paragraph)
                if event:
                    events.append(event)
        
        return events

    def _create_event_from_paragraph(self, chapter: int, sequence: int, text: str) -> Optional[Event]:
        """Create an event from a paragraph of text."""
        # Determine event type
        event_type = self._classify_event_type(text)
        
        # Find characters involved
        characters_involved = []
        for char_name in self.characters.keys():
            if char_name in text:
                characters_involved.append(char_name)
        
        # Extract location if mentioned
        location = self._extract_location_from_text(text)
        
        # Determine emotional tone
        emotional_tone = self._analyze_emotional_tone(text)
        
        # Create description
        description = text[:200] + "..." if len(text) > 200 else text
        
        # Generate player choice potential
        choice_potential = self._generate_choice_potential(text, characters_involved)
        
        return Event(
            id="",  # Will be set later
            chapter=chapter,
            sequence=sequence,
            event_type=event_type,
            characters_involved=characters_involved,
            location=location,
            description=description,
            consequences=[],
            emotional_tone=emotional_tone,
            plot_significance="medium",
            player_choice_potential=choice_potential,
            original_text=text
        )

    def _classify_event_type(self, text: str) -> str:
        """Classify the type of event based on text content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['said', 'asked', 'replied', 'whispered', 'shouted']):
            return 'dialogue'
        elif any(word in text_lower for word in ['fight', 'battle', 'attack', 'conflict']):
            return 'conflict'
        elif any(word in text_lower for word in ['went', 'walked', 'ran', 'moved', 'traveled']):
            return 'action'
        elif any(word in text_lower for word in ['felt', 'thought', 'remembered', 'wondered']):
            return 'internal'
        else:
            return 'description'

    def _extract_location_from_text(self, text: str) -> str:
        """Extract location information from text."""
        # Look for location indicators
        location_patterns = [
            r'in the ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'at the ([A-Z][a-z]+)',
            r'in ([A-Z][a-z]+)',
            r'at ([A-Z][a-z]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group(1)
                self.locations.add(location)
                return location
        
        return "Unknown location"

    def _analyze_emotional_tone(self, text: str) -> str:
        """Analyze the emotional tone of the text."""
        text_lower = text.lower()
        
        positive_words = ['happy', 'joy', 'smile', 'laugh', 'love', 'hope', 'excited']
        negative_words = ['sad', 'angry', 'fear', 'worried', 'dark', 'death', 'pain']
        neutral_words = ['said', 'went', 'looked', 'thought', 'found']
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"

    def _generate_choice_potential(self, text: str, characters: List[str]) -> str:
        """Generate potential player choices for this event."""
        if not characters:
            return "Observe the unfolding events"
        
        main_character = characters[0] if characters else "protagonist"
        
        # Generate context-appropriate choices
        text_lower = text.lower()
        
        if 'said' in text_lower or 'asked' in text_lower:
            return f"Choose how {main_character} responds to the conversation"
        elif 'fight' in text_lower or 'battle' in text_lower:
            return f"Decide {main_character}'s strategy in the conflict"
        elif 'went' in text_lower or 'moved' in text_lower:
            return f"Choose where {main_character} goes next"
        else:
            return f"Determine {main_character}'s next action"

    def _extract_locations(self):
        """Extract and catalog all locations mentioned in the story."""
        logger.info("Extracting locations...")
        # Locations are already extracted during event processing
        logger.info(f"Found {len(self.locations)} unique locations")

    def _build_relationship_graph(self):
        """Build comprehensive relationship graph."""
        logger.info("Building relationship graph...")
        
        self.relationships_graph = {
            "title": self.book_title,
            "summary": f"Character relationships in {self.book_title}",
            "characters": {},
            "relationships": []
        }
        
        # Add character nodes
        for name, character in self.characters.items():
            self.relationships_graph["characters"][name] = {
                "name": character.name,
                "role": character.role,
                "importance": character.importance_score,
                "traits": character.personality_traits,
                "backstory": character.backstory
            }
        
        # Add relationship edges
        for char_name, character in self.characters.items():
            for other_char, relationship_type in character.relationships.items():
                self.relationships_graph["relationships"].append({
                    "source": char_name,
                    "target": other_char,
                    "type": relationship_type,
                    "strength": 1.0
                })

    def _analyze_character_importance(self):
        """Analyze and score character importance."""
        logger.info("Analyzing character importance...")
        
        for character in self.characters.values():
            # Calculate importance based on various factors
            mention_count = sum(1 for event in self.events if character.name in event.characters_involved)
            relationship_count = len(character.relationships)
            
            # Role-based scoring
            role_scores = {
                "protagonist": 10.0,
                "antagonist": 8.0,
                "supporting": 5.0,
                "minor": 2.0
            }
            
            role_score = role_scores.get(character.role, 1.0)
            
            # Calculate final importance score
            character.importance_score = (
                mention_count * 0.4 +
                relationship_count * 0.3 +
                role_score * 0.3
            )

    def setup_game(self, settings: GameSettings) -> bool:
        """Setup game with comprehensive world state."""
        try:
            self.game_settings = settings
            
            # Initialize comprehensive world state
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

    def start_game(self) -> Dict:
        """Start the interactive game with comprehensive backstory."""
        if self.game_state != GameState.GAME_SETUP:
            raise ValueError("Game not properly set up")
        
        self.game_state = GameState.PLAYING
        
        # Get selected character
        selected_character = self.characters.get(self.game_settings.selected_character)
        if not selected_character:
            raise ValueError(f"Character '{self.game_settings.selected_character}' not found")
        
        # Generate comprehensive backstory and current situation
        backstory = self._generate_comprehensive_backstory(selected_character)
        current_situation = self._generate_current_situation()
        choices = self._generate_contextual_choices()
        
        summary = f"""
🎭 Welcome to "{self.book_title}"!

🎯 You are playing as: {selected_character.name}
📍 Setting: {self.game_settings.custom_setting or 'Original story setting'}
🗣️ Language: {self.game_settings.language}

👤 About {selected_character.name}:
{selected_character.backstory}

🧠 Character Traits: {', '.join(selected_character.personality_traits)}
🤝 Key Relationships: {', '.join([f"{name} ({rel})" for name, rel in selected_character.relationships.items()])}

📖 Story So Far:
{backstory}

🎬 Current Situation:
{current_situation}

What do you choose to do?
        """
        
        return {
            "status": "game_started",
            "summary": summary,
            "current_character": selected_character.name,
            "current_location": self._get_current_location(),
            "character_backstory": backstory,
            "choices": choices,
            "world_state": self._get_world_state_summary()
        }

    def _generate_comprehensive_backstory(self, character: Character) -> str:
        """Generate comprehensive backstory up to the starting point."""
        backstory_events = []
        
        # Get events up to starting point that involve this character
        for i in range(min(self.game_settings.starting_point, len(self.events))):
            event = self.events[i]
            if character.name in event.characters_involved:
                backstory_events.append(event)
        
        if not backstory_events:
            return f"{character.name} begins their journey in {self.book_title}."
        
        # Create narrative from events
        backstory_parts = []
        for event in backstory_events[-5:]:  # Last 5 relevant events
            backstory_parts.append(f"• {event.description}")
        
        return f"Here's what {character.name} has experienced so far:\n\n" + "\n".join(backstory_parts)

    def _generate_current_situation(self) -> str:
        """Generate current situation description."""
        if self.game_settings.starting_point < len(self.events):
            current_event = self.events[self.game_settings.starting_point]
            return f"You find yourself {current_event.location}. {current_event.description}"
        else:
            return "You are at a pivotal moment in your story, ready to make choices that will shape your destiny."

    def _generate_contextual_choices(self) -> List[Dict]:
        """Generate contextual choices based on current situation."""
        if self.game_settings.starting_point < len(self.events):
            current_event = self.events[self.game_settings.starting_point]
            return self._create_choices_for_event(current_event)
        else:
            return self._create_default_choices()

    def _create_choices_for_event(self, event: Event) -> List[Dict]:
        """Create specific choices for an event."""
        character_name = self.game_settings.selected_character
        
        choices = []
        
        if event.event_type == 'dialogue':
            choices = [
                {
                    "title": "Engage in Conversation",
                    "action": f"Participate actively in the dialogue",
                    "risk_level": "Low",
                    "outcome": "Learn more about other characters and advance relationships"
                },
                {
                    "title": "Listen Carefully",
                    "action": f"Observe and listen without speaking",
                    "risk_level": "Low",
                    "outcome": "Gain information while remaining neutral"
                },
                {
                    "title": "Challenge the Speaker",
                    "action": f"Question or confront what's being said",
                    "risk_level": "Medium",
                    "outcome": "Potentially create conflict but assert your position"
                }
            ]
        elif event.event_type == 'conflict':
            choices = [
                {
                    "title": "Face the Challenge",
                    "action": f"Confront the conflict directly",
                    "risk_level": "High",
                    "outcome": "Potentially resolve the conflict but risk consequences"
                },
                {
                    "title": "Seek Peaceful Resolution",
                    "action": f"Try to find a diplomatic solution",
                    "risk_level": "Medium",
                    "outcome": "Avoid violence but may compromise your position"
                },
                {
                    "title": "Retreat and Regroup",
                    "action": f"Step back to reassess the situation",
                    "risk_level": "Low",
                    "outcome": "Avoid immediate danger but may lose opportunities"
                }
            ]
        else:
            choices = [
                {
                    "title": "Take Initiative",
                    "action": f"Lead the way forward",
                    "risk_level": "Medium",
                    "outcome": "Shape the direction of events"
                },
                {
                    "title": "Follow Others",
                    "action": f"Let others take the lead",
                    "risk_level": "Low",
                    "outcome": "Avoid responsibility but limit your influence"
                },
                {
                    "title": "Explore Alternatives",
                    "action": f"Look for different approaches",
                    "risk_level": "Medium",
                    "outcome": "Discover new possibilities but take time"
                }
            ]
        
        return choices

    def _create_default_choices(self) -> List[Dict]:
        """Create default choices when no specific event context."""
        return [
            {
                "title": "Explore Your Surroundings",
                "action": "Look around and investigate your environment",
                "risk_level": "Low",
                "outcome": "Discover new information about your world"
            },
            {
                "title": "Seek Out Allies",
                "action": "Look for friends or companions to help you",
                "risk_level": "Medium",
                "outcome": "Build relationships but reveal your intentions"
            },
            {
                "title": "Plan Your Next Move",
                "action": "Take time to think and strategize",
                "risk_level": "Low",
                "outcome": "Make more informed decisions going forward"
            }
        ]

    def process_player_choice(self, choice_index: int, custom_action: str = None) -> Dict:
        """Process player choice and generate story continuation."""
        try:
            # Record the choice
            choice_made = {
                "event_index": self.world_state.current_event_index,
                "choice_index": choice_index,
                "custom_action": custom_action,
                "timestamp": self.world_state.current_event_index
            }
            self.world_state.player_choices_made.append(choice_made)
            
            # Generate story continuation based on choice
            story_continuation = self._generate_story_continuation(choice_made)
            
            # Update world state
            self._update_world_state(choice_made)
            
            # Generate next choices
            next_choices = self._generate_next_choices()
            
            # Advance story
            self.world_state.current_event_index += 1
            
            return {
                "status": "choice_processed",
                "story_continuation": story_continuation,
                "next_choices": next_choices,
                "world_state": self._get_world_state_summary(),
                "character_status": self._get_character_status()
            }
            
        except Exception as e:
            logger.error(f"Error processing choice: {e}")
            return {"status": "error", "message": str(e)}

    def _generate_story_continuation(self, choice_made: Dict) -> str:
        """Generate detailed story continuation based on player choice."""
        character_name = self.game_settings.selected_character
        
        if choice_made["custom_action"]:
            # Handle custom action
            action = choice_made["custom_action"]
            continuation = f"""
🎭 {character_name}'s Action: {action}

📖 Story Continuation:
{character_name} decided to {action.lower()}. This choice set in motion a series of events that would have lasting consequences.

As {character_name} took this path, the world around them began to shift. Other characters noticed this decision, and the ripple effects started to spread through the story.

The consequences of this choice would become clear as the adventure continued...
            """
        else:
            # Handle predefined choice
            if self.world_state.current_event_index < len(self.events):
                current_event = self.events[self.world_state.current_event_index]
                continuation = f"""
🎭 {character_name} has made their choice...

📖 Story Continuation:
{self._generate_consequence_narrative(current_event, choice_made)}

The story unfolds as {character_name} faces the results of their decision. Each choice shapes not only their own destiny but also the fate of everyone around them.

New challenges and opportunities emerge as the tale continues...
                """
            else:
                continuation = f"""
🎭 {character_name} continues their journey...

📖 Story Continuation:
Your choices have led to new and unexpected developments. The story branches in directions that weren't part of the original tale, creating a unique narrative shaped by your decisions.

{character_name} must now navigate this changed world, where every action has consequences and every decision matters.
                """
        
        return continuation.strip()

    def _generate_consequence_narrative(self, event: Event, choice_made: Dict) -> str:
        """Generate narrative consequences for the choice."""
        character_name = self.game_settings.selected_character
        
        # Create consequences based on event type and choice
        if event.event_type == 'dialogue':
            return f"{character_name} engaged with the conversation, and their words carried weight. The other characters' reactions would influence future interactions."
        elif event.event_type == 'conflict':
            return f"{character_name} faced the conflict with determination. Their approach to this challenge revealed their true character and affected their relationships with others."
        else:
            return f"{character_name} took action in this situation, and the consequences began to unfold. The world responded to their choice in ways both expected and surprising."

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

    def _generate_next_choices(self) -> List[Dict]:
        """Generate next set of choices based on current state."""
        # Check if we have a next event
        if self.world_state.current_event_index + 1 < len(self.events):
            next_event = self.events[self.world_state.current_event_index + 1]
            return self._create_choices_for_event(next_event)
        else:
            # Generate dynamic choices based on story state
            return self._create_dynamic_choices()

    def _create_dynamic_choices(self) -> List[Dict]:
        """Create dynamic choices when beyond original story events."""
        character_name = self.game_settings.selected_character
        
        choices = [
            {
                "title": "Forge a New Path",
                "action": f"Create your own destiny beyond the original story",
                "risk_level": "High",
                "outcome": "Shape the story in completely new directions"
            },
            {
                "title": "Seek Resolution",
                "action": f"Work towards resolving ongoing conflicts",
                "risk_level": "Medium", 
                "outcome": "Bring closure to story elements"
            },
            {
                "title": "Explore Consequences",
                "action": f"Investigate the results of your previous choices",
                "risk_level": "Low",
                "outcome": "Understand the impact of your decisions"
            }
        ]
        
        return choices

    def _get_current_location(self) -> str:
        """Get current location in the story."""
        if self.world_state.current_event_index < len(self.events):
            return self.events[self.world_state.current_event_index].location
        return "Unknown location"

    def _get_character_status(self) -> Dict:
        """Get current character status."""
        character_name = self.game_settings.selected_character
        if character_name in self.world_state.character_states:
            return self.world_state.character_states[character_name]
        return {}

    def _get_world_state_summary(self) -> Dict:
        """Get comprehensive world state summary."""
        return {
            "current_event": self.world_state.current_event_index,
            "total_events": len(self.events),
            "current_chapter": self.world_state.current_chapter,
            "story_arc_position": self.world_state.story_arc_position,
            "narrative_momentum": self.world_state.narrative_momentum,
            "choices_made": len(self.world_state.player_choices_made),
            "current_location": self._get_current_location(),
            "available_characters": list(self.characters.keys())
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
            
            # Save world state
            if self.world_state:
                with open(os.path.join(self.knowledge_base_path, "world_state.json"), 'w') as f:
                    json.dump(asdict(self.world_state), f, indent=2)
            
            logger.info("Knowledge base saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")

# Initialize the enhanced engine
engine = EnhancedStoryEngine()

# API Routes
@app.route("/load_book", methods=["POST"])
def load_book():
    """Load and process a book file."""
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
            # Extract knowledge graphs
            if engine.extract_knowledge_graphs():
                return jsonify({
                    "status": "success",
                    "book_title": engine.book_title,
                    "characters": list(engine.characters.keys()),
                    "character_details": {name: {
                        "role": char.role,
                        "traits": char.personality_traits,
                        "importance": char.importance_score
                    } for name, char in engine.characters.items()},
                    "total_events": len(engine.events),
                    "locations": list(engine.locations),
                    "message": "Book processed successfully with comprehensive knowledge extraction"
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
                "character_details": asdict(engine.characters[settings.selected_character]),
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
    """Start the interactive game."""
    try:
        result = engine.start_game()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in start_game: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route("/make_choice", methods=["POST"])
def make_choice():
    """Process player choice."""
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
            "character_details": asdict(engine.characters[engine.game_settings.selected_character]) if engine.game_settings else None
        })
    
    except Exception as e:
        logger.error(f"Error in get_game_state: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route("/", methods=["GET"])
def home():
    """API home endpoint."""
    return jsonify({
        "message": "Enhanced Interactive Story Game Engine API",
        "status": "running",
        "features": [
            "Comprehensive character extraction with roles and traits",
            "Detailed story event analysis",
            "Dynamic relationship mapping",
            "Contextual choice generation",
            "Consequential story continuation",
            "Character backstory generation",
            "Multi-language support"
        ],
        "endpoints": [
            "/load_book - POST - Upload and comprehensively process a book",
            "/setup_game - POST - Configure game with detailed character selection",
            "/start_game - POST - Begin interactive gameplay with full backstory",
            "/make_choice - POST - Process player choices with consequences",
            "/get_game_state - GET - Get comprehensive game status"
        ]
    })

if __name__ == '__main__':
    print("🎮 Starting Enhanced Interactive Story Game Engine...")
    print("📚 Upload a book file to begin comprehensive story analysis!")
    print("🌐 API running on http://localhost:5001")
    app.run(debug=True, port=5001, host='0.0.0.0') 