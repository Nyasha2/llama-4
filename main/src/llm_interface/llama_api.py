import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("Llama_API_KEY")
API_ENDPOINT = os.getenv("Llama_API_ENDPOINT")

def call_llama_api(prompt: str, context: dict) -> str:
    """
    Sends a request to the Meta Llama API and returns the generated text.

    Args:
        prompt: The main instruction or question for the model.
        context: A dictionary containing the world knowledge and game state.

    Returns:
        The text content of the model's response, or an error message.
    """
    if not API_KEY or not API_ENDPOINT:
        # Return mock response for testing if API key or endpoint is not set
        print("--- Warning: API key or endpoint not set. Running in mock response mode. ---")
        return get_mock_response(prompt)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    # Meta Llama API official format
    payload = {
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": [
            {
                "role": "user",
                "content": f"You are a master storyteller and game master. Use the provided knowledge graph and game state to continue the story. Here is the context: {json.dumps(context)}\n\n{prompt}",
            }
        ],
        "max_completion_tokens": 1024,
        "temperature": 0.7,
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for 4xx or 5xx status codes
        
        data = response.json()
        
        # Handle the new response format with completion_message and metrics
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
        print(f"Error calling Llama API: {e}")
        return f"Error: Could not connect to the Llama API. Details: {e}"
    except (KeyError, IndexError) as e:
        print(f"Error parsing API response: {e}")
        return f"Error: Unexpected response format from the API. Details: {e}"

def get_mock_response(prompt: str) -> str:
    """Returns a mock response for testing purposes."""
    prompt_lower = prompt.lower()
    
    if "walk over" in prompt_lower or "approach" in prompt_lower:
        return "As you approach the mysterious figure, they slowly raise their hood to reveal weathered features and piercing blue eyes. 'I've been waiting for you,' they whisper in a gravelly voice. 'The time has come to begin your quest.' They reach into their cloak and produce an ancient map. What would you like to do next?"
    
    elif "talk" in prompt_lower or "speak" in prompt_lower:
        return "The figure nods approvingly at your choice to engage in conversation. 'I am Gandalf the Grey,' they introduce themselves. 'I have been watching your journey from afar. You possess a rare gift that could change the fate of Middle-earth.' They gesture toward the map. 'Will you accept this quest?'"
    
    elif "accept" in prompt_lower or "yes" in prompt_lower:
        return "A warm smile spreads across Gandalf's face. 'Excellent! Your courage does you credit.' He hands you the map and a small silver ring. 'This ring will guide you when all other lights go out. Your journey begins at dawn. Rest well tonight, for tomorrow you face the unknown.'"
    
    elif "refuse" in prompt_lower or "no" in prompt_lower:
        return "Gandalf's expression darkens with concern. 'I understand your hesitation, but the choice is not mine to make. The forces of darkness are already moving. Whether you accept or not, the shadow will find you.' He places the map on the table. 'The choice remains yours.'"
    
    elif "ask" in prompt_lower or "question" in prompt_lower:
        return "Gandalf leans forward, his eyes twinkling with ancient wisdom. 'Ask what you will, young one. I have traveled far and seen much. Perhaps I can provide the answers you seek before you make your decision.'"
    
    else:
        return "The mysterious figure watches you carefully, waiting for your next move. The dim light of the inn flickers, casting dancing shadows across their weathered face. What would you like to do?" 