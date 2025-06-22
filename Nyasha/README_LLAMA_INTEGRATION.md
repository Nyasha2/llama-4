# 🤖 Llama 4 Enhanced Interactive Story Game Engine

This enhanced version of the Interactive Story Game Engine integrates with **Llama 4** to provide AI-powered dynamic storytelling, character analysis, and intelligent story adaptation.

## 🚀 Quick Start

### 1. Setup Environment

Run the automated setup script:

```bash
python setup_llama_engine.py
```

This will:
- Install all required dependencies
- Create necessary directories
- Set up your `.env` file
- Test the installation

### 2. Add Your Llama API Key

**IMPORTANT**: Edit the `.env` file and add your hackathon API key:

```bash
# Edit .env file
nano .env

# Replace this line:
Llama_API_KEY=your_hackathon_api_key_here

# With your actual key:
Llama_API_KEY=your_actual_hackathon_key_here
```

### 3. Run the Enhanced Engine

Start the Llama-enhanced API server:

```bash
python src/game_engine/llama_enhanced_engine.py
```

The API will be available at: `http://localhost:5002`

### 4. Run the Web Interface

In a separate terminal, start the web interface:

```bash
python app/app.py
```

Open your browser to: `http://localhost:3000`

## 🤖 Llama 4 Integration Features

### ✨ AI-Powered Character Analysis
- **Real Character Extraction**: Uses Llama 4 to identify and analyze actual character names from books
- **Personality Profiling**: AI determines character roles, traits, and importance scores
- **Relationship Mapping**: Intelligent analysis of character relationships and dynamics
- **Character Backstories**: Generated comprehensive backstories based on text analysis

### 🎭 Dynamic Story Generation
- **Contextual Choices**: Llama 4 generates meaningful choices based on current story context
- **Consequence Prediction**: AI predicts and generates realistic outcomes for player decisions
- **Story Continuation**: Dynamic story progression that adapts to player choices
- **Custom Setting Integration**: Seamlessly incorporates user-defined story settings

### 🧠 Intelligent Game Management
- **World State Tracking**: AI maintains consistency across story modifications
- **Narrative Momentum**: Adjusts story pacing based on player engagement
- **Event Classification**: Automatically categorizes story events for better interaction
- **Multi-language Support**: Generate stories in different languages

## 🔧 API Configuration

The engine uses the exact same API format as the reference code:

```python
# API Configuration (in .env file)
Llama_API_KEY=your_hackathon_key
Llama_API_ENDPOINT=https://api.llama-api.com/chat/completions

# Model Configuration
Model: Llama-4-Maverick-17B-128E-Instruct-FP8
Max Tokens: 1024
Temperature: 0.7
```

## 📊 API Endpoints

### Enhanced Story Engine API (Port 5002)

- `POST /load_book` - Upload and AI-analyze books
- `POST /setup_game` - Configure game with AI-enhanced character selection
- `POST /start_game` - Begin AI-powered interactive story
- `POST /make_choice` - Process choices with dynamic AI consequences
- `GET /get_game_state` - Get comprehensive AI-managed game status

### Web Interface (Port 3000)

- Beautiful, modern interface for story interaction
- Real-time AI-generated character profiles
- Dynamic choice presentation with risk indicators
- Story progression tracking

## 🎮 How It Works

### 1. Book Analysis Phase
```
📚 Upload Book → 🤖 Llama 4 Analysis → 👥 Character Extraction → 🕸️ Relationship Mapping
```

### 2. Game Setup Phase
```
🎯 Character Selection → ⚙️ Custom Settings → 🌍 World State Initialization
```

### 3. Interactive Gameplay
```
📖 Story Context → 🤖 AI Choice Generation → 👤 Player Decision → 🔄 Dynamic Continuation
```

## 🔄 Fallback Mode

If the Llama API is not available, the engine automatically switches to **Mock Response Mode**:
- Provides intelligent fallback responses
- Maintains game functionality
- Allows testing without API access

## 🎯 Example Usage

### Character Analysis Output
```json
{
  "characters": {
    "Alex": {
      "role": "protagonist",
      "traits": ["intelligent", "brave", "curious"],
      "backstory": "Alex grew up in a small village, always dreaming of adventure...",
      "importance": 9.2
    }
  }
}
```

### AI-Generated Story Continuation
```
Your decision creates ripples through the fabric of the story. As you choose to approach the mysterious figure, they slowly turn to face you, their eyes gleaming with ancient wisdom. "I've been waiting for someone like you," they whisper...
```

## 🔍 Troubleshooting

### Common Issues

**1. API Key Not Working**
```bash
# Check your .env file
cat .env

# Make sure the key is correctly formatted
Llama_API_KEY=your_actual_key_without_quotes
```

**2. Dependencies Missing**
```bash
# Run setup again
python setup_llama_engine.py

# Or install manually
pip install flask flask-cors requests python-dotenv spacy PyPDF2
python -m spacy download en_core_web_sm
```

**3. Port Already in Use**
```bash
# Kill processes on ports
lsof -ti:5002 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

## 🎨 Customization

### Modify AI Prompts
Edit the prompt templates in `main/src/game_engine/prompts.py` to customize AI behavior.

### Adjust API Parameters
Modify the `call_llama_api` method in `llama_enhanced_engine.py`:
```python
# Increase creativity
temperature=0.9

# Generate longer responses  
max_tokens=2048
```

## 📈 Performance Tips

1. **Batch API Calls**: The engine batches character analysis for efficiency
2. **Smart Caching**: Responses are cached to reduce API usage
3. **Fallback Mode**: Automatic fallback ensures uninterrupted gameplay
4. **Optimized Prompts**: Carefully crafted prompts minimize token usage

## 🎪 Demo Mode

To test without an API key:
```bash
# Leave API key empty in .env
Llama_API_KEY=

# Engine will automatically use mock responses
python src/game_engine/llama_enhanced_engine.py
```

## 🤝 Integration with Existing Code

The enhanced engine is fully compatible with your existing web interface and maintains all original functionality while adding AI capabilities.

## 🔮 Advanced Features

- **Multi-book Support**: Analyze multiple books simultaneously
- **Character Relationship Graphs**: Visual relationship mapping
- **Story Branching**: AI-generated alternative storylines
- **Sentiment Analysis**: Emotional tone tracking
- **Language Translation**: Multi-language story generation

---

## 🎉 Ready to Play!

Your Llama 4 Enhanced Interactive Story Game Engine is ready! Upload a book, select a character, and let AI create a personalized adventure experience.

**Happy Storytelling! 📚✨** 