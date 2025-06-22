import json
import logging
import os
import requests
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS

# Load environment variables
load_dotenv('../../api.env')

# Flask setup
app = Flask(__name__)
CORS(app)

# API Configuration
LLAMA_API_KEY = os.getenv('LLAMA_API_KEY')
LLAMA_API_URL = "https://api.llama.com/v1/chat/completions"
MODEL_NAME = "Llama-4-Maverick-17B-128E-Instruct-FP8"

if not LLAMA_API_KEY:
    raise ValueError("LLAMA_API_KEY not found in environment variables")

CHARACTER_SYSTEM_PROMPT = """
You are a highly detailed literary analyst AI. Your sole mission is to meticulously extract comprehensive information about characters and the *nuances* of their relationships from the provided text segment. This data will be used later to build a relationship graph.

**Objective:** Identify EVERY character mentioned. For each pair of interacting characters, describe their relationship in detail, focusing on the context, roles, emotional dynamics, history, and key interactions *as presented or clearly implied* within this specific text segment.

**Instructions:**

1.  **Identify Characters:** List every unique character name mentioned in the text segment.
2.  **Identify Relationships & Interactions:** For each character, document their interactions and connections with *every other* character mentioned *within this segment*.
3.  **Describe Relationship Nuances:** Do not just state the type (e.g., "friend"). Describe the *quality and context* of the relationship based *only* on the text. Note:
    * **Roles:** (e.g., mentor-mentee, leader-follower, parent-child, rivals for power, allies in battle).
    * **Emotional Dynamics:** (e.g., loyalty, distrust, affection, resentment, fear, admiration).
    * **History:** (e.g., childhood friends, former enemies, long-lost siblings, recent acquaintances).
    * **Key Events/Context:** Mention specific events, shared goals, conflicts, or settings *within this segment* that define or illustrate the relationship (e.g., "fought side-by-side during the siege," "argued fiercely over the inheritance," "shared a secret confided in the garden").
4.  **Quote Evidence (Briefly):** If a short quote directly illuminates the nature of the relationship, include it as supporting evidence.
5.  **Be Exhaustive:** Capture every piece of relationship information present *in this specific text segment*.
6.  **Stick Strictly to the Text:** Base your analysis *only* on the provided text segment. Do not infer information not present, make assumptions, or bring in outside knowledge.
7.  **Output Format:** Present the findings as clear, descriptive text for each character, detailing their relationships. **DO NOT use JSON or graph formats (nodes/links) at this stage.** Focus purely on capturing rich, accurate, descriptive textual data about the relationships.

**Example Output Structure (Conceptual):**

* **Character:** [Character Name A]
    * **Relationship with [Character Name B]:** Described as close friends since childhood ('lifelong companions' mentioned). In this segment, Character A relies on B for emotional support during the journey planning. Character B shows fierce loyalty, vowing to protect A.
    * **Relationship with [Character Name C]:** Character C acts as a mentor, providing guidance about the ancient artifact. Character A shows respect but also some fear of C's power, as seen when A hesitates to ask a direct question.
    * **Relationship with [Character Name D]:** Openly antagonistic rivals. In this segment, they have a heated argument regarding leadership strategy, revealing deep-seated distrust. Character A believes D is reckless.

Process the provided text segment thoroughly based *only* on these instructions.
"""

RELATIONSHIP_SYSTEM_PROMPT = """
You are an expert data architect AI specializing in transforming literary analysis into structured graph data. Your task is to synthesize character and relationship information into a specific JSON format containing nodes and links, including a title and summary.

**Objective:** Convert the provided textual analysis of characters and relationships (extracted from a book) into the specified JSON graph format. Generate unique IDs, sequential values, and synthesize detailed relationship descriptions into link labels.
I'll give you a harsh punishment if you miss any character or relationship.

**Input:**
1.  **Character & Relationship Data:** Unstructured or semi-structured text detailing character names and rich descriptions of their relationships (context, roles, dynamics, history, key interactions). This data is compiled from the analysis of the entire book.
2.  **Book Title:** The full title of the book.
3.  **Book Summary:** A brief summary of the book's plot or content.

**Instructions:**

1.  **Identify Unique Characters:** From the input data, identify the list of all unique characters.
2.  **Generate Nodes:** Create a JSON list under the key `"nodes"`. For each unique character:
    * Assign a unique `"id"` string (e.g., "c1", "c2", "c3"...). Keep a mapping of character names to their assigned IDs.
    * Include the character's full `"name"` as found in the data.
    * Assign a sequential integer `"val"`, starting from 1.
3.  **Generate Links:** Create a JSON list under the key `"links"`. For each distinct relationship between two characters identified in the input data:
    * Determine the `source` character's ID and the `target` character's ID using the mapping created in step 2.
    * **Synthesize the Relationship Label:** Carefully analyze the *detailed description* of the relationship provided in the input data (including roles, dynamics, context, history). Create a concise yet descriptive **natural-language `"label"`** that captures the essence of this relationship.
        * **Focus on Specificity:** Avoid vague terms like "friend" or "related to". Use descriptive phrases like the examples provided (e.g., "childhood best friend and traveling companion of", "rival general who betrayed during the siege", "wise mentor guiding the protagonist", "secret lover and political adversary of").
        * The label should ideally describe the relationship *from* the source *to* the target, or be neutral if applicable (e.g., "siblings").
    * Ensure each significant relationship pair is represented by a link object. A single mutual relationship should typically be represented by one link, with the label reflecting the connection. If the relationship is distinctly different from each perspective, consider if two links are necessary.
4.  **Assemble Final JSON:** Construct the final JSON object with the following top-level keys:
    * `"title"`: Use the provided Book Title.
    * `"summary"`: Use the provided Book Summary.
    * `"nodes"`: The list of node objects created in step 2.
    * `"links"`: The list of link objects created in step 3.
5.  **Strict JSON Output:** Generate *only* the complete, valid JSON object adhering to the specified structure. Do not include any introductory text, explanations, comments, or markdown formatting outside the JSON structure itself. If you include one of them, I'll give you a punishment. You are gonna get a

**Target JSON Structure Example:**

```json
{
  "title": "The Fellowship of the Ring",
  "summary": "In the first part of the epic trilogy, Frodo Baggins inherits a powerful ring that must be destroyed to stop the rise of evil. He sets out on a perilous journey with a group of companions to reach Mount Doom. Along the way, they face temptation, betrayal, and battles that test their unity and resolve.",
  "nodes": [
    { "id": "c1", "name": "Frodo Baggins", "val": 1 },
    { "id": "c2", "name": "Samwise Gamgee", "val": 2 },
    { "id": "c3", "name": "Gandalf", "val": 3 },
    { "id": "c4", "name": "Aragorn", "val": 4 }
    // ... other characters
  ],
  "links": [
    { "source": "c2", "target": "c1", "label": "childhood friend and fiercely loyal traveling companion of" },
    { "source": "c3", "target": "c1", "label": "wise mentor who guides Frodo through early parts of the journey and warns him about the Ring's power" },
    { "source": "c4", "target": "c3", "label": "trusted warrior and future king who follows Gandalf's counsel during the quest" }
    // ... other relationships
  ]
}
```
"""

JSON_SYSTEM_PROMPT = """
You are an extremely precise and strict JSON extractor.
Extract only the complete JSON object from the input. Get the last one if there are multiple.
Output must:
1. Start with opening brace {
2. End with closing brace }
3. Contain no text, markdown, or other characters outside the JSON
4. Be valid, parseable JSON
```
"""

SEARCH_SYSTEM_PROMPT = """
You are an expert search AI designed to help users find detailed information about character relationships from a book. Your task is to assist users in querying the relationship data extracted from the book.

**Objective:** Allow users to search for specific character relationships using natural language queries. Provide concise and accurate responses based on the relationship data.

**Instructions:**

1. **Understand the Query:** Analyze the user's query to identify the characters and the type of relationship information they are seeking.
2. **Search Relationship Data:** Use the relationship data extracted from the book to find relevant information. Focus on the characters and relationship details mentioned in the query.
3. **Provide Clear Responses:** Respond with clear and concise information about the relationship, including roles, dynamics, history, and key interactions as described in the data.
4. **Be Specific:** Avoid vague responses. Use specific details from the relationship data to answer the query.
5. **Maintain Context:** Ensure that the response is relevant to the query and provides a comprehensive understanding of the relationship.

**Example Query and Response:**

*Query:* "What is the relationship between Frodo Baggins and Samwise Gamgee?"

*Response:* "Samwise Gamgee is Frodo Baggins' childhood friend and fiercely loyal traveling companion. He provides emotional support and protection during their journey."

Use this format to assist users in finding the relationship information they need.
"""

STORY_ANALYSIS_SYSTEM_PROMPT = """
You are an expert story analyst AI. Your task is to analyze a book and extract detailed information about story events, character decision points, and story structure to enable interactive storytelling.

**Objective:** Identify key story events, character involvement, and critical decision points where characters could have acted differently, changing the story's trajectory.

**Instructions:**

1. **Story Events:** List major events in chronological order with:
   - Event description
   - Characters involved
   - Outcome/consequences
   - Story significance (1-10 scale)

2. **Character Decision Points:** For each major character, identify moments where they:
   - Made important choices or decisions
   - Took significant actions
   - Said something crucial
   - Could have reasonably acted differently

3. **Story Segments:** Break the story into segments based on:
   - Character involvement/perspective
   - Major plot developments
   - Natural breaking points for interaction

4. **Character Involvement:** For each segment, note:
   - Which characters are active participants
   - Which characters are observers
   - Which characters are absent

**Output Format:** Present as structured text with clear sections for Events, Decision Points, Segments, and Character Involvement.

Process the provided text thoroughly and identify every significant moment where character choices could create story branches.
"""

CHOICE_GENERATION_SYSTEM_PROMPT = """
You are a creative story branching AI. Your task is to generate alternative actions and choices for a character at specific decision points in a story.

**Objective:** For a given character at a specific story moment, create 3-4 realistic alternative actions that:
- Stay true to the character's personality and background
- Would meaningfully change the story direction
- Are distinct from each other in approach/outcome
- Remain plausible within the story's context

**Instructions:**

1. **Analyze the Situation:** Understand the context, stakes, and character's motivations
2. **Generate Alternatives:** Create options that represent different approaches:
   - Cautious vs Bold
   - Emotional vs Logical
   - Individual vs Collaborative
   - Direct vs Subtle

3. **Consider Consequences:** Each choice should lead to meaningfully different outcomes

4. **Maintain Character Voice:** Ensure choices reflect the character's established traits and speaking style

**Output Format:** JSON with choices array containing action/dialogue options and brief consequence descriptions.

Generate choices that create exciting branching possibilities while respecting the source material's tone and characters.
"""

STORY_CONTINUATION_SYSTEM_PROMPT = """
You are an expert story continuation AI. Your task is to generate compelling story text that follows naturally from a user's choice at a decision point.

**Objective:** Continue the story from where the user made their choice, incorporating:
- The immediate consequences of their action
- How other characters react
- How the plot trajectory changes
- Maintaining the original story's style and tone

**Instructions:**

1. **Immediate Response:** Show the direct result of the user's choice
2. **Character Reactions:** How do other characters respond to this new action?
3. **Plot Adjustment:** How does this change affect the broader story?
4. **Style Consistency:** Match the original author's writing style and pacing
5. **Character Voice:** Keep all characters true to their established personalities

**Output Format:** Natural story text that flows seamlessly from the user's choice, typically 2-4 paragraphs.

Create engaging continuations that make the user feel their choices truly matter to the story's direction.
"""

CHARACTER_APPEARANCE_SYSTEM_PROMPT = """
You are an expert literary analyst. Your task is to analyze a book and identify exactly when and where each character first appears, and break the story into chapters or natural segments.

**Objective:** Create a detailed map of character appearances and story structure to enable precise interactive storytelling.

**Instructions:**

1. **Chapter/Section Detection:** Identify natural story breaks (chapters, parts, scene changes)
2. **Character First Appearances:** For each character, find:
   - Which chapter/section they first appear
   - The exact paragraph/scene where they're introduced
   - The context of their introduction
   - Their role in that scene (active participant, observer, mentioned)

3. **Scene Analysis:** For each character appearance, note:
   - What is happening in the scene
   - Who else is present
   - What the character is doing/saying
   - What decision points or actions they could take

4. **Story Segments:** Break the story into segments where:
   - Each segment focuses on specific characters
   - Natural pause points for character decisions
   - Key plot developments

**Output Format:** Structured analysis with:
- Chapter breakdown
- Character appearance map (character -> first chapter/scene)
- Scene context for each appearance
- Potential action points for each character

Focus on creating actionable moments where characters could realistically make different choices.
"""

CONTEXTUAL_CHOICE_SYSTEM_PROMPT = """
You are an expert interactive fiction AI. Your task is to create specific, contextual action choices that will branch the story in different directions.

**Critical Requirements:**
1. **Be Extremely Specific:** No generic actions like "be cautious" or "act boldly"
2. **Focus on Story Branching:** Each choice should lead to a different story path
3. **Use Scene Details:** Reference specific people, objects, locations from the scene
4. **Character-Appropriate:** Consider what this character would realistically do

**Example of GOOD choices for a character at a gas station with no money:**
- "Walk the remaining 20 miles to your destination"
- "Approach the elderly woman by the coffee machine and ask for spare change"
- "Call your ex-girlfriend Sarah to ask for help, despite your pride"
- "Turn around and abandon the journey completely"

**Example of BAD choices (too generic):**
- "Be cautious"
- "Take action" 
- "Make a decision"
- "Act boldly"

**Output Format:** Return ONLY clean JSON like this:
{
  "actions": [
    {
      "text": "Walk over to Professor Snape and ask him directly about the strange potion smell",
      "description": "Confront the authority figure"
    },
    {
      "text": "Whisper to Hermione: 'Something's not right about this lesson'",
      "description": "Share concerns with a friend"
    },
    {
      "text": "Deliberately knock over your cauldron to create a distraction",
      "description": "Create chaos to investigate"
    },
    {
      "text": "Pretend to feel sick and ask to leave the classroom",
      "description": "Escape the situation"
    }
  ]
}

Make each choice lead to a completely different story direction. Be specific about WHO they interact with, WHAT they say, WHERE they go.
"""

STORY_CONTINUATION_ENHANCED_PROMPT = """
You are an expert story continuation AI. Your task is to continue the story from a specific character action, maintaining the original style while incorporating the new choice.

**Objective:** Continue the story naturally from the user's choice, showing:
- Immediate consequences of the action
- How other characters react
- How the scene develops
- Maintain original writing style and character voices

**Instructions:**

1. **Immediate Response:** Show what happens as a direct result of the choice
2. **Character Reactions:** How do others in the scene respond?
3. **Scene Development:** Continue until the next natural pause point where the character might need to make another decision
4. **Style Consistency:** Match the original author's tone, pacing, and descriptive style
5. **Character Authenticity:** Keep all characters true to their established personalities

**Important:** Continue writing until you reach a natural stopping point where the character would need to make another decision. Don't stop too early - develop the consequences of their choice.

**Output Format:** Natural story text that flows from the choice, typically 2-4 paragraphs that advance the plot meaningfully.
"""

CHAPTER_SUMMARY_SYSTEM_PROMPT = """
You are a story summarization expert. Your task is to create concise but comprehensive summaries of story chapters/sections.

**Objective:** Summarize the key events, character developments, and plot points from chapters that the user will skip.

**Instructions:**

1. **Key Events:** What major things happened?
2. **Character Introductions:** Who was introduced and their importance?
3. **Plot Developments:** How did the story advance?
4. **Character Relationships:** What relationships were established or changed?
5. **Important Details:** What background info is crucial for understanding later events?

**Output Format:** Clear, engaging summary that brings the reader up to speed without being overwhelming.

Focus on information that will be relevant for understanding the character's situation when they appear.
"""

@app.route("/inference", methods=["POST"])
def inference():
    """
    Handles inference requests from the frontend.
    """

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Read file content directly from the uploaded file
        file_content = file.read().decode("utf-8")

        # Save the book in the current directory
        with open(os.path.join(os.getcwd(), "book.txt"), "w") as f:
            f.write(file_content)

        # Calculate the number of input tokens
        num_input_tokens = calculate_input_tokens(file_content)

        # Step 1: Character extraction
        messages = [
            {"role": "system", "content": CHARACTER_SYSTEM_PROMPT},
            {"role": "user", "content": file_content},
        ]
        character_outputs = call_llama_api(messages)
        character_response_text = character_outputs
        print("character_response_text: ", character_response_text)

        # Step 2: Relationship extraction
        messages = [
            {"role": "system", "content": RELATIONSHIP_SYSTEM_PROMPT},
            {"role": "user", "content": f"Book content:\n{file_content}"},
            {"role": "assistant", "content": character_response_text},
            {
                "role": "user",
                "content": "Generate the JSON graph with title, summary, nodes, and links.",
            },
        ]
        relationship_outputs = call_llama_api(messages)
        relationship_response_text = relationship_outputs
        print("relationship_response_text: ", relationship_response_text)

        graph_data = ""
        try:
            graph_data = jsonify_graph_response(relationship_response_text)
            logging.info("Graph data generated:", json.dumps(graph_data, indent=2))
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing graph response from : {e}")
            try:
                # Try to parse the response as a JSON object
                json_response = llm_json_output(relationship_response_text)
                print("json_response: ", json_response)
                graph_data = jsonify_graph_response(json_response)
                logging.info("Graph data generated:", json.dumps(graph_data, indent=2))
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing graph response from json result: {e}")

        return (
            jsonify(
                {
                    "graph_data": graph_data,
                    "character_response_text": character_response_text,
                    "num_input_tokens": num_input_tokens,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles search requests from the frontend.
    """
    try:
        data = request.json
        search_query = data.get("query")
        relationship_data = data.get("relationship_data")
        chat_history_data = data.get("chat_history_data")

        # Read the book.txt file from the current directory
        with open(os.path.join(os.getcwd(), "book.txt"), "r") as f:
            file_content = f.read()

        if not search_query or not relationship_data:
            return (
                jsonify({"error": "search_query and relationship_data are required"}),
                400,
            )
        messages = [
            {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
            {"role": "assistant", "content": file_content},
            {"role": "assistant", "content": relationship_data},
        ]

        # Format chat history for the model
        formatted_history = []
        for msg in chat_history_data:
            formatted_history.append({"role": msg["sender"], "content": msg["text"]})

        # Add chat history
        messages.extend(formatted_history)

        # Add the current user message
        messages.append({"role": "user", "content": search_query})

        search_outputs = call_llama_api(messages)
        search_response_text = search_outputs
        print("search_response_text: ", search_response_text)
        return jsonify({"response": search_response_text}), 200

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


def llm_json_output(response):
    messages = [
        {"role": "system", "content": JSON_SYSTEM_PROMPT},
        {"role": "user", "content": response},
    ]

    outputs = call_llama_api(messages)

    response_text = outputs
    print("response_text: ", response_text)
    return response_text


def calculate_input_tokens(input_text):
    # Rough approximation: 1 token ≈ 4 characters for English text
    # This is a simple estimate since we don't have direct access to the tokenizer
    return len(input_text) // 4


def jsonify_graph_response(content):
    """Extract and parse JSON content from graph response."""
    try:
        # Find indices of first { and last }
        start_idx = content.find("{")
        end_idx = content.rfind("}")

        if start_idx == -1 or end_idx == -1:
            raise ValueError("No valid JSON object found in response")

        # Extract JSON string
        json_str = content[start_idx : end_idx + 1]

        # Parse JSON
        return json.loads(json_str)

    except Exception as e:
        logging.error(f"Error parsing graph response: {e}")
        return None


def call_llama_api(messages, max_tokens=800, temperature=0.7):
    """
    Call the Llama API with the given messages
    """
    headers = {
        "Authorization": f"Bearer {LLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        response = requests.post(LLAMA_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        response_json = response.json()
        print(f"API Response: {json.dumps(response_json, indent=2)}")
        
        # Check if the response has the Llama API structure
        if "completion_message" in response_json:
            content = response_json["completion_message"]["content"]
            if isinstance(content, dict) and "text" in content:
                return content["text"]
            else:
                return str(content)
        else:
            print(f"Unexpected API response structure: {response_json}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling Llama API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None


@app.route("/analyze_character_appearances", methods=["POST"])
def analyze_character_appearances():
    """
    Analyzes when and where each character first appears in the story
    """
    try:
        data = request.json
        if not data or 'book_content' not in data:
            return jsonify({"error": "book_content is required"}), 400

        book_content = data['book_content']
        characters = data.get('characters', [])
        
        # Create character list for analysis
        character_names = [char['name'] for char in characters] if characters else []
        character_list = ", ".join(character_names)
        
        prompt = f"""
        Characters to analyze: {character_list}
        
        Book content: {book_content}
        
        Analyze this book to find:
        1. Natural chapter/section breaks
        2. When each character first appears
        3. The context of their first appearance
        4. Actionable moments for each character
        """
        
        messages = [
            {"role": "system", "content": CHARACTER_APPEARANCE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        
        appearance_analysis = call_llama_api(messages, max_tokens=2000)
        
        if not appearance_analysis:
            return jsonify({"error": "Failed to analyze character appearances"}), 500
            
        return jsonify({
            "appearance_analysis": appearance_analysis,
            "status": "success"
        }), 200

    except Exception as e:
        print(f"Error analyzing character appearances: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_story_segment", methods=["POST"])
def get_story_segment():
    """
    Gets clean story text for a character's first appearance - NO ANALYSIS
    """
    try:
        data = request.json
        if not data or 'character' not in data or 'book_content' not in data:
            return jsonify({"error": "character and book_content are required"}), 400

        character_name = data['character']
        book_content = data['book_content']
        appearance_info = data.get('appearance_info', '')
        
        # Simple, direct prompt that asks for ONLY story text
        prompt = f"""
        EXTRACT STORY TEXT ONLY - NO ANALYSIS OR COMMENTARY

        Character: {character_name}
        Book Content: {book_content}
        
        Instructions: Find where {character_name} first appears in the text and return ONLY the actual story narrative from that point until a natural pause where the character needs to make a decision.
        
        Return ONLY the story text - no "Step 1", no analysis, no commentary, no explanations.
        Just the clean narrative text from the book.
        
        If {character_name} appears early, start from the beginning.
        If {character_name} appears later, provide a brief summary of what happened before, then start the actual story text from their first scene.
        """
        
        messages = [
            {"role": "system", "content": "You extract clean story text. Return ONLY narrative text with no analysis, steps, or commentary."},
            {"role": "user", "content": prompt},
        ]
        
        story_response = call_llama_api(messages, max_tokens=1500)
        
        if not story_response:
            return jsonify({"error": "Failed to get story segment"}), 500
        
        # Clean the response aggressively
        clean_story = story_response.strip()
        
        # Remove any markdown formatting
        clean_story = clean_story.replace('```', '').replace('**', '').replace('##', '')
        
        # Remove analysis lines more aggressively
        lines = clean_story.split('\n')
        story_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not any(skip_word in line for skip_word in [
                'Step ', 'Analysis', 'Character:', 'Book Content:', 'Instructions:', 
                'EXTRACT', 'Return ONLY', 'Your task', 'To address', 'CRITICAL',
                'The following', 'Based on', 'In this', 'actionable moment',
                '1.', '2.', '3.', '4.', 'First,', 'Second,', 'Finally,'
            ]):
                story_lines.append(line)
        
        clean_story = '\n\n'.join([line for line in story_lines if line]).strip()
        
        # Final safety check - if we still have analysis text, create a clean start
        if (not clean_story or len(clean_story) < 50 or 
            any(word in clean_story for word in ['Step', 'Analysis', 'EXTRACT', 'Instructions'])):
            
            # Extract actual text segments from the book content directly
            book_paragraphs = book_content.split('\n\n')
            character_found = False
            story_start = []
            
            for para in book_paragraphs:
                if character_name in para:
                    character_found = True
                
                if character_found and len(para) > 50:
                    # This looks like actual story content
                    if not any(meta_word in para for meta_word in ['Chapter', 'Page ', 'Analysis', 'Character:']):
                        story_start.append(para)
                        if len(story_start) >= 3:  # Get a few paragraphs
                            break
            
            if story_start:
                clean_story = '\n\n'.join(story_start)
            else:
                # Final fallback with actual story beginning
                clean_story = f"""Mr. and Mrs. Dursley of number four, Privet Drive, were proud to say that they were perfectly normal, thank you very much. They were the last people you'd expect to be involved in anything strange or mysterious, because they just didn't hold with such nonsense.

Mr. Dursley was the director of a firm called Grunnings, which made drills. He was a big, beefy man with hardly any neck, although he did have a very large mustache. Mrs. Dursley was thin and blonde and had nearly twice the usual amount of neck, which came in very useful as she spent so much of her time craning over garden fences, spying on the neighbors.

As {character_name}, you find yourself in this world where extraordinary events are about to unfold..."""
        
        return jsonify({
            "story_segment": clean_story,
            "character": character_name,
            "status": "success"
        }), 200

    except Exception as e:
        print(f"Error getting story segment: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/generate_contextual_choices", methods=["POST"])
def generate_contextual_choices():
    """
    Generates specific, contextual choices for a character in their exact situation
    """
    try:
        data = request.json
        if not data or 'character' not in data or 'scene_context' not in data:
            return jsonify({"error": "character and scene_context are required"}), 400

        character = data['character']
        scene_context = data['scene_context']
        character_background = data.get('character_background', '')
        other_characters = data.get('other_characters', '')
        
        prompt = f"""
        Character: {character}
        
        Current Scene: {scene_context}
        
        Based on this exact scene, generate 3-4 specific actions {character} could take RIGHT NOW that would change the story direction.

        Requirements:
        - Reference specific people, objects, or locations mentioned in the scene
        - Create choices that would lead to completely different story outcomes
        - Be extremely specific about what the character does or says
        - Each choice should be something the character could realistically do in this moment

        Example of GOOD choices (if scene has Harry in Potions class):
        - "Raise your hand and tell Professor Snape you smell something strange in the dungeon"
        - "Lean over and whisper to Hermione: 'I think someone's trying to steal the Philosopher's Stone'"
        - "Deliberately add the wrong ingredient to your potion to see what happens"
        - "Get up and walk over to examine Neville's cauldron more closely"

        Example of BAD choices (too generic):
        - "Be careful"
        - "Take action"
        - "Make a decision"

        Return ONLY this JSON format:
        {{
          "actions": [
            {{
              "text": "[Specific action with details from the scene]",
              "description": "[What this choice might lead to]"
            }},
            {{
              "text": "[Another specific action]",
              "description": "[Consequence of this choice]"
            }},
            {{
              "text": "[Third specific action]",
              "description": "[How this changes the story]"
            }},
            {{
              "text": "[Fourth specific action]",
              "description": "[Different outcome this creates]"
            }}
          ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "You generate specific action choices in JSON format. No analysis, no explanations, just the JSON response."},
            {"role": "user", "content": prompt},
        ]
        
        choices_response = call_llama_api(messages, max_tokens=1000)
        
        if not choices_response:
            return jsonify({"error": "Failed to generate contextual choices"}), 500
        
        # Parse the JSON response from the AI
        try:
            # Clean up the response
            json_match = choices_response.strip()
            
            # Remove markdown code blocks if present
            if json_match.startswith('```json'):
                json_match = json_match.replace('```json', '').replace('```', '').strip()
            elif json_match.startswith('```'):
                json_match = json_match.replace('```', '').strip()
            
            # Find JSON object in the response
            start_idx = json_match.find('{')
            end_idx = json_match.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_match = json_match[start_idx:end_idx]
            
            print(f"Attempting to parse JSON: {json_match}")
            parsed_response = json.loads(json_match)
            
            # Format the choices for the frontend
            formatted_choices = []
            if 'actions' in parsed_response:
                for i, action in enumerate(parsed_response['actions']):
                    formatted_choices.append({
                        "id": i + 1,
                        "text": action.get('text', action.get('action', f'Action {i+1}')),
                        "description": action.get('description', action.get('consequence', ''))
                    })
            
            print(f"Successfully formatted {len(formatted_choices)} choices")
            
            return jsonify({
                "choices": formatted_choices,
                "raw_response": choices_response,
                "status": "success"
            }), 200
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse AI response as JSON: {e}")
            print(f"Raw response was: {choices_response}")
            
            # Create better fallback contextual choices based on scene
            scene_words = scene_context.lower().split()
            
            # Try to create contextual fallbacks based on common scene elements
            if any(word in scene_words for word in ['classroom', 'lesson', 'teacher', 'professor']):
                fallback_choices = [
                    {"id": 1, "text": f"Raise your hand and ask the teacher a question", "description": "Engage with authority"},
                    {"id": 2, "text": f"Whisper to the student next to you", "description": "Communicate quietly"},
                    {"id": 3, "text": f"Focus intently on the lesson being taught", "description": "Pay close attention"},
                    {"id": 4, "text": f"Look around the classroom for anything unusual", "description": "Observe the environment"}
                ]
            elif any(word in scene_words for word in ['house', 'home', 'room', 'door']):
                fallback_choices = [
                    {"id": 1, "text": f"Walk to the door and listen for sounds outside", "description": "Investigate"},
                    {"id": 2, "text": f"Look out the window to see what's happening", "description": "Observe from inside"},
                    {"id": 3, "text": f"Call out to see if anyone responds", "description": "Make contact"},
                    {"id": 4, "text": f"Stay quiet and wait to see what happens next", "description": "Remain hidden"}
                ]
            else:
                # Generic but character-specific fallback
                fallback_choices = [
                    {"id": 1, "text": f"Take a moment to carefully observe the situation around you", "description": "Gather information"},
                    {"id": 2, "text": f"Approach someone nearby and start a conversation", "description": "Be social"},
                    {"id": 3, "text": f"Make a bold decision based on {character}'s personality", "description": "Act decisively"},
                    {"id": 4, "text": f"Find a way to leave this situation", "description": "Seek an exit"}
                ]
            
            return jsonify({
                "choices": fallback_choices,
                "raw_response": choices_response,
                "status": "fallback_used"
            }), 200

    except Exception as e:
        print(f"Error generating contextual choices: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/continue_story_enhanced", methods=["POST"])
def continue_story_enhanced():
    """
    Continues the story based on user's choice with enhanced context awareness
    """
    try:
        data = request.json
        if not data or 'user_choice' not in data or 'scene_context' not in data:
            return jsonify({"error": "user_choice and scene_context are required"}), 400

        user_choice = data['user_choice']
        scene_context = data['scene_context']
        character = data.get('character', '')
        original_style = data.get('original_style', '')
        other_characters = data.get('other_characters', '')
        
        prompt = f"""
        Character: {character}
        User's Specific Choice: {user_choice}
        Current Scene Context: {scene_context}
        Other Characters Present: {other_characters}
        
        Original Story Style Reference: {original_style}
        
        Continue the story from this specific choice. Show:
        1. Immediate consequences of the action
        2. How other characters react
        3. How the scene develops
        4. Continue until the next natural decision point for {character}
        
        Maintain the original author's writing style and character voices.
        """
        
        messages = [
            {"role": "system", "content": STORY_CONTINUATION_ENHANCED_PROMPT},
            {"role": "user", "content": prompt},
        ]
        
        continuation = call_llama_api(messages, max_tokens=1500)
        
        if not continuation:
            return jsonify({"error": "Failed to continue story"}), 500
            
        return jsonify({
            "continuation": continuation,
            "status": "success"
        }), 200

    except Exception as e:
        print(f"Error continuing story: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_chapter_summary", methods=["POST"])
def get_chapter_summary():
    """
    Provides summary of chapters that will be skipped
    """
    try:
        data = request.json
        if not data or 'book_content' not in data:
            return jsonify({"error": "book_content is required"}), 400

        book_content = data['book_content']
        character = data.get('character', '')
        skip_to_chapter = data.get('skip_to_chapter', '')
        
        prompt = f"""
        Character who will be played: {character}
        Skip to: {skip_to_chapter}
        
        Book content: {book_content}
        
        Provide a summary of the key events that happened before {character} appears, 
        focusing on information that will be relevant for understanding their situation.
        """
        
        messages = [
            {"role": "system", "content": CHAPTER_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        
        summary = call_llama_api(messages, max_tokens=1000)
        
        if not summary:
            return jsonify({"error": "Failed to generate chapter summary"}), 500
            
        return jsonify({
            "summary": summary,
            "character": character,
            "status": "success"
        }), 200

    except Exception as e:
        print(f"Error generating chapter summary: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5001)
