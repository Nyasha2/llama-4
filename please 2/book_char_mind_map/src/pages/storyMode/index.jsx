import React, { useState } from 'react';
import axios from 'axios';
import { FaBook, FaUser, FaPlay, FaHome, FaFastForward } from 'react-icons/fa';
import { Link } from "react-router-dom";

export default function StoryMode() {
  const [step, setStep] = useState(1); // 1: upload, 2: character select, 3: story play
  const [fileObject, setFileObject] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [bookContent, setBookContent] = useState("");
  const [characters, setCharacters] = useState([]);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [appearanceAnalysis, setAppearanceAnalysis] = useState(null);

  const [currentScene, setCurrentScene] = useState("");
  const [storyHistory, setStoryHistory] = useState([]);
  const [choices, setChoices] = useState([]);
  const [chapterSummary, setChapterSummary] = useState("");
  const [isFirstAppearance, setIsFirstAppearance] = useState(true);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!fileObject) return;

    setIsLoading(true);
    try {
      // First, get character analysis like before
      const formData = new FormData();
      formData.append('file', fileObject);

      const response = await axios.post("http://localhost:5001/inference", formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.graph_data && response.data.graph_data.nodes) {
        setCharacters(response.data.graph_data.nodes);
        
        // Read file content
        const text = await fileObject.text();
        setBookContent(text);
        
        // Analyze character appearances
        const appearanceResponse = await axios.post("http://localhost:5001/analyze_character_appearances", {
          book_content: text,
          characters: response.data.graph_data.nodes
        });
        
        setAppearanceAnalysis(appearanceResponse.data.appearance_analysis);
        setStep(2); // Move to character selection
      }
    } catch (error) {
      console.error("Error processing book:", error);
      alert("Failed to process the book. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const selectCharacter = async (character) => {
    setSelectedCharacter(character);
    setIsLoading(true);
    
    try {
      // Get the story segment for this character
      const segmentResponse = await axios.post("http://localhost:5001/get_story_segment", {
        character: character.name,
        book_content: bookContent,
        appearance_info: appearanceAnalysis
      });
      
      const storySegment = segmentResponse.data.story_segment;
      
      // Check if we need a summary (character appears later)
      if (storySegment.includes("SUMMARY:") || storySegment.includes("summary")) {
        const summaryResponse = await axios.post("http://localhost:5001/get_chapter_summary", {
          book_content: bookContent,
          character: character.name,
          skip_to_chapter: "Character's first appearance"
        });
        setChapterSummary(summaryResponse.data.summary);
        setIsFirstAppearance(false);
      }
      
      setCurrentScene(storySegment);
      setStoryHistory([{ text: storySegment, isChoice: false }]);
      setStep(3);
      
    } catch (error) {
      console.error("Error getting story segment:", error);
      alert("Failed to get story segment. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const generateContextualChoices = async () => {
    try {
      setIsLoading(true);
      
      // Get the most recent story context for choice generation
      const recentText = currentScene.split('\n').filter(line => line.trim().length > 0).slice(-3).join('\n');
      const sceneContext = recentText || currentScene.substring(Math.max(0, currentScene.length - 500));
      
      const response = await axios.post("http://localhost:5001/generate_contextual_choices", {
        character: selectedCharacter.name,
        scene_context: sceneContext,
        character_background: `Character from the story: ${selectedCharacter.name}`,
        other_characters: "Characters present in the scene"
      });
      
      // Use the choices directly from the API response
      if (response.data.choices && Array.isArray(response.data.choices)) {
        setChoices(response.data.choices);
      } else {
        // Fallback choices
        setChoices([
          { id: 1, text: "Take a cautious approach", description: "Proceed carefully" },
          { id: 2, text: "Act boldly", description: "Make a decisive move" },
          { id: 3, text: "Observe the situation", description: "Gather more information" }
        ]);
      }
    } catch (error) {
      console.error("Error generating choices:", error);
      setChoices([
        { id: 1, text: "Continue with the story", description: "Move forward" },
        { id: 2, text: "Take a different approach", description: "Try something new" }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const makeChoice = async (choice) => {
    try {
      setIsLoading(true);
      const response = await axios.post("http://localhost:5001/continue_story_enhanced", {
        user_choice: choice.text,
        scene_context: currentScene,
        character: selectedCharacter.name,
        original_style: bookContent.substring(0, 1000), // Sample for style
        other_characters: "Characters in the scene"
      });
      
      const continuation = response.data.continuation;
      
      // Add the choice and continuation to history
      const choiceScene = {
        text: `**Your choice:** ${choice.text}`,
        isChoice: true,
        userChoice: choice.text
      };
      
      const continuationScene = {
        text: continuation,
        isChoice: false,
        userChoice: choice.text
      };
      
      setStoryHistory([...storyHistory, choiceScene, continuationScene]);
      setCurrentScene(continuation);
      setChoices([]);
    } catch (error) {
      console.error("Error continuing story:", error);
      alert("Failed to continue story. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <Link to="/" className="flex items-center text-blue-600 hover:text-blue-800">
            <FaHome className="mr-2" />
            Home
          </Link>
          <h1 className="text-3xl font-bold text-gray-800">
            📚 Interactive Story Mode
          </h1>
          <div className="text-sm text-gray-600">
            Step {step}/3
          </div>
        </div>

        {/* Step 1: File Upload */}
        {step === 1 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6 text-center">Upload Your Story</h2>
            <form onSubmit={handleFileUpload} className="space-y-6">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <input
                  type="file"
                  accept=".txt,.pdf,.doc,.docx"
                  onChange={(e) => setFileObject(e.target.files?.[0])}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <FaBook className="mx-auto text-4xl text-gray-400 mb-4" />
                  <p className="text-gray-600">
                    {fileObject ? fileObject.name : "Click to upload a book file"}
                  </p>
                </label>
              </div>
              <button
                type="submit"
                disabled={!fileObject || isLoading}
                className="w-full bg-purple-600 text-white py-3 rounded-lg font-semibold disabled:opacity-50"
              >
                {isLoading ? "Analyzing story structure..." : "Analyze Story"}
              </button>
            </form>
          </div>
        )}

        {/* Step 2: Character Selection */}
        {step === 2 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6 text-center">Choose Your Character</h2>
            <p className="text-center text-gray-600 mb-6">
              Select which character you want to play as. The story will start from their first appearance.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {characters.map((character) => (
                <div
                  key={character.id}
                  className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-400 cursor-pointer transition-colors"
                  onClick={() => selectCharacter(character)}
                >
                  <div className="flex items-center mb-2">
                    <FaUser className="text-purple-600 mr-2" />
                    <h3 className="font-semibold">{character.name}</h3>
                  </div>
                  <p className="text-sm text-gray-600">Step into their shoes and make their choices</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Story Play */}
        {step === 3 && (
          <div className="space-y-6">
            {/* Character Info */}
            <div className="bg-white rounded-lg shadow p-4 flex items-center">
              <FaUser className="text-purple-600 mr-3" />
              <div>
                <h3 className="font-semibold">Playing as: {selectedCharacter?.name}</h3>
                <p className="text-sm text-gray-600">Your choices will reshape the story</p>
              </div>
            </div>

            {/* Chapter Summary (if character appears later) */}
            {!isFirstAppearance && chapterSummary && (
              <div className="bg-amber-50 rounded-lg shadow p-6 border-l-4 border-amber-400">
                <div className="flex items-center mb-3">
                  <FaFastForward className="text-amber-600 mr-2" />
                  <h4 className="font-semibold text-amber-700">Story So Far</h4>
                </div>
                <p className="text-amber-800 leading-relaxed">{chapterSummary}</p>
              </div>
            )}

            {/* Story Display */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="prose max-w-none">
                {storyHistory.map((scene, index) => (
                  <div key={index} className="mb-6">
                    {scene.isChoice ? (
                      <div className="p-4 bg-purple-50 rounded border-l-4 border-purple-400">
                        <span className="text-sm font-semibold text-purple-700">Your choice: </span>
                        <span className="text-purple-600">{scene.userChoice}</span>
                      </div>
                    ) : (
                      <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                        {scene.text}
                      </p>
                    )}
                  </div>
                ))}

                {/* Choice Buttons */}
                {choices.length > 0 && (
                  <div className="mt-8">
                    <h4 className="font-semibold mb-4 text-purple-700">What do you do?</h4>
                    <div className="space-y-3">
                      {choices.map((choice) => (
                        <button
                          key={choice.id}
                          onClick={() => makeChoice(choice)}
                          className="w-full text-left p-4 border-2 border-gray-200 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors"
                          disabled={isLoading}
                        >
                          <div className="font-medium">{choice.text}</div>
                          {choice.description && (
                            <div className="text-sm text-gray-600 mt-1">{choice.description}</div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Continue Button */}
                {choices.length === 0 && !isLoading && storyHistory.length > 0 && (
                  <div className="mt-8 text-center">
                    <button
                      onClick={generateContextualChoices}
                      className="bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 flex items-center mx-auto"
                    >
                      <FaPlay className="mr-2" />
                      What's Next?
                    </button>
                  </div>
                )}

                {isLoading && (
                  <div className="mt-8 text-center">
                    <div className="text-purple-600">
                      {choices.length === 0 ? "Generating choices..." : "Continuing story..."}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Story Progress */}
            {storyHistory.length > 1 && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold mb-2">Your Story Journey</h4>
                <div className="text-sm text-gray-600">
                  {storyHistory.filter(scene => scene.isChoice).length} choices made • 
                  {storyHistory.length} scenes experienced
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 