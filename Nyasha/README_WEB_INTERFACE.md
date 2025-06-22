# 🎮 Interactive Story Game Engine - Web Interface

A beautiful, modern web interface for transforming any book into an interactive adventure where you control the story!

## 🚀 Quick Start

### 1. Start the Servers

**Terminal 1 - Start the Game Engine API:**
```bash
cd src/game_engine
python simple_game_demo.py
```

**Terminal 2 - Start the Web Interface:**
```bash
cd app
python app.py
```

### 2. Open Your Browser

Navigate to: **http://localhost:3000**

## 🎯 How to Use

### Step 1: Upload Your Book 📚
- **Drag & Drop**: Simply drag a TXT or PDF file onto the upload area
- **Browse**: Click "Choose File" to select from your files
- **Supported formats**: `.txt` and `.pdf` files
- **Example**: Use the included `test_story.txt` for a quick demo

### Step 2: Configure Your Adventure ⚙️
- **Choose Character**: Select which character you want to play as
- **Starting Point**: Choose which event to start from (0 = beginning)
- **Custom Setting**: Optionally change the story setting (e.g., "Modern New York City")
- **Language**: Select from 10+ supported languages

### Step 3: Play Your Interactive Story 🎭
- **Read**: The story unfolds based on your choices
- **Choose**: Select from pre-generated choice cards with risk levels
- **Custom Actions**: Write your own actions in the text area
- **Stats**: Track your progress with live game statistics

## ✨ Features

### 🎨 Beautiful Modern UI
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Gradient Backgrounds**: Eye-catching visual design
- **Smooth Animations**: Hover effects and transitions
- **Interactive Cards**: Choice cards with risk indicators

### 🎮 Rich Gameplay
- **Dynamic Storytelling**: AI-powered story adaptation
- **Multiple Choice Types**: Pre-generated options + custom actions
- **Risk Assessment**: Low, Medium, High risk indicators
- **World State Tracking**: Consistent story world management

### 📊 Game Statistics
- **Current Event**: Track story progression
- **Total Events**: See how much content is available
- **Choices Made**: Count your decisions
- **Current Location**: Track where you are in the story

### 🌍 Multi-Language Support
- English, Spanish, French, German, Italian
- Portuguese, Russian, Japanese, Chinese, Korean
- Easy to add more languages

## 🛠️ Technical Details

### Architecture
- **Frontend**: Pure HTML5/CSS3/JavaScript (no frameworks)
- **Backend**: Flask API with CORS support
- **Communication**: RESTful API calls
- **File Processing**: PDF and TXT support

### API Endpoints
- `POST /load_book` - Upload and process books
- `POST /setup_game` - Configure game settings
- `POST /start_game` - Begin interactive gameplay
- `POST /make_choice` - Process player choices
- `GET /get_game_state` - Get current game status

### Port Configuration
- **Web Interface**: http://localhost:3000
- **Game Engine API**: http://localhost:5001

## 🎯 Example Workflow

1. **Upload** `test_story.txt`
2. **Select** "Alex" as your character
3. **Set** custom setting to "Modern New York City"
4. **Start** the adventure
5. **Make choices** to guide the story
6. **Watch** as the AI adapts the narrative to your decisions

## 🐛 Troubleshooting

### Common Issues

**"Connection refused" errors:**
- Make sure both servers are running
- Check ports 3000 and 5001 are available
- Verify virtual environment is activated

**File upload fails:**
- Check file format (TXT or PDF)
- Ensure file is not corrupted
- Try with the included `test_story.txt`

**No characters appear:**
- Wait for book processing to complete
- Check browser console for errors
- Verify the book contains character names

### Browser Compatibility
- **Chrome**: Fully supported ✅
- **Firefox**: Fully supported ✅
- **Safari**: Fully supported ✅
- **Edge**: Fully supported ✅

## 🔧 Development

### Adding New Features
- **Frontend**: Edit `app/templates/index.html`
- **Backend**: Modify `src/game_engine/simple_game_demo.py`
- **Styling**: CSS is embedded in the HTML file

### Custom Styling
The interface uses CSS Grid and Flexbox for responsive design. Key classes:
- `.game-panel`: Main content containers
- `.choice-card`: Interactive choice elements
- `.stat-card`: Game statistics display
- `.action-btn`: Primary action buttons

## 🎉 Enjoy Your Interactive Adventure!

Transform any book into a personalized gaming experience where every choice matters and the story adapts to your decisions! 