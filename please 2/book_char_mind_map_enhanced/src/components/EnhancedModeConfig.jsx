import React, { useState } from 'react';
import axios from 'axios';

const EnhancedModeConfig = ({ 
  onConfigApply, 
  bookContent, 
  isLoading, 
  setIsLoading 
}) => {
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [settingType, setSettingType] = useState('original');
  const [timePeriod, setTimePeriod] = useState('');
  const [location, setLocation] = useState('');
  const [customSetting, setCustomSetting] = useState('');
  const [showConfig, setShowConfig] = useState(true);

  // Popular languages supported by Llama 4
  const languages = [
    'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 
    'Russian', 'Chinese (Simplified)', 'Chinese (Traditional)', 'Japanese', 
    'Korean', 'Arabic', 'Hindi', 'Bengali', 'Dutch', 'Swedish', 'Norwegian', 
    'Danish', 'Polish', 'Czech', 'Hungarian', 'Romanian', 'Bulgarian', 
    'Greek', 'Turkish', 'Hebrew', 'Thai', 'Vietnamese', 'Indonesian', 
    'Malay', 'Filipino', 'Swahili', 'Yoruba', 'Amharic'
  ];

  const timePeriods = [
    'Ancient Times (Before 500 AD)',
    'Medieval Period (500-1500)',
    'Renaissance (1400-1600)',
    'Age of Exploration (1500-1700)',
    'Industrial Revolution (1760-1840)',
    'Victorian Era (1837-1901)',
    '1900s-1910s',
    '1920s (Roaring Twenties)',
    '1930s (Great Depression)',
    '1940s (World War II Era)',
    '1950s (Post-War Boom)',
    '1960s (Cultural Revolution)',
    '1970s (Disco Era)',
    '1980s (Digital Age Beginning)',
    '1990s (Internet Age)',
    '2000s (New Millennium)',
    '2010s (Social Media Era)',
    '2020s (Modern Times)',
    'Near Future (2030s-2040s)',
    'Distant Future (Beyond 2050)'
  ];

  const locations = [
    'New York City, USA',
    'London, England',
    'Paris, France',
    'Tokyo, Japan',
    'Rome, Italy',
    'Berlin, Germany',
    'Moscow, Russia',
    'Beijing, China',
    'Mumbai, India',
    'Cairo, Egypt',
    'Lagos, Nigeria',
    'São Paulo, Brazil',
    'Sydney, Australia',
    'Medieval European Castle',
    'Ancient Greek City-State',
    'Wild West American Frontier',
    'Victorian London',
    '1920s Chicago',
    'Space Station',
    'Underwater City',
    'Post-Apocalyptic Wasteland',
    'Magical Fantasy Realm',
    'Cyberpunk Megacity'
  ];

  const handleApplyConfig = async () => {
    setIsLoading(true);
    
    try {
      let transformedContent = bookContent;
      let configDescription = [];
      
      // Apply setting transformation first
      if (settingType !== 'original') {
        console.log('Applying setting transformation...');
        const settingData = {
          book_content: bookContent,
          setting_type: settingType,
          time_period: timePeriod,
          location: location,
          custom_setting: customSetting
        };
        
        const settingResponse = await axios.post('http://localhost:5002/transform_setting', settingData);
        transformedContent = settingResponse.data.transformed_content;
        configDescription.push(settingResponse.data.setting_description);
      }
      
      // Apply language translation
      if (selectedLanguage !== 'English') {
        console.log(`Translating to ${selectedLanguage}...`);
        const translationData = {
          book_content: transformedContent,
          target_language: selectedLanguage
        };
        
        const translationResponse = await axios.post('http://localhost:5002/translate_book', translationData);
        transformedContent = translationResponse.data.translated_content;
        configDescription.push(`Translated to ${selectedLanguage}`);
      }
      
      // Apply the configuration
      const enhancedConfig = {
        transformedContent,
        language: selectedLanguage,
        settingContext: settingType !== 'original' ? 
          `${settingType === 'time' ? timePeriod : settingType === 'place' ? location : settingType === 'time_and_place' ? `${timePeriod} in ${location}` : customSetting}` : '',
        configDescription: configDescription.join(' + ')
      };
      
             onConfigApply(enhancedConfig);
       
     } catch (error) {
      console.error('Error applying enhanced configuration:', error);
      alert('Error applying configuration. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mb-6 p-6 bg-gradient-to-r from-purple-100 to-blue-100 rounded-lg border-2 border-purple-200">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-purple-800 text-center">🚀 Enhanced Mode Configuration</h3>
        <p className="text-center text-purple-600 mt-2">Transform your story with different languages and settings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Language Selection */}
        <div className="space-y-3">
          <h4 className="font-semibold text-purple-700">🌍 Language Translation</h4>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="w-full p-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500"
          >
            {languages.map(lang => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>
          <p className="text-xs text-purple-600">
            Translate the entire story into your chosen language
          </p>
        </div>

        {/* Setting Transformation */}
        <div className="space-y-3">
          <h4 className="font-semibold text-purple-700">🏛️ Setting Transformation</h4>
          <select
            value={settingType}
            onChange={(e) => setSettingType(e.target.value)}
            className="w-full p-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500"
          >
            <option value="original">Keep Original Setting</option>
            <option value="time">Change Time Period</option>
            <option value="place">Change Location</option>
            <option value="time_and_place">Change Time & Place</option>
            <option value="custom">Custom Setting</option>
          </select>

          {/* Time Period Selection */}
          {(settingType === 'time' || settingType === 'time_and_place') && (
            <select
              value={timePeriod}
              onChange={(e) => setTimePeriod(e.target.value)}
              className="w-full p-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Select Time Period</option>
              {timePeriods.map(period => (
                <option key={period} value={period}>{period}</option>
              ))}
            </select>
          )}

          {/* Location Selection */}
          {(settingType === 'place' || settingType === 'time_and_place') && (
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full p-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Select Location</option>
              {locations.map(loc => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          )}

          {/* Custom Setting Input */}
          {settingType === 'custom' && (
            <textarea
              value={customSetting}
              onChange={(e) => setCustomSetting(e.target.value)}
              placeholder="Describe your custom setting (e.g., 'Cyberpunk Tokyo in 2087 with flying cars and neon-lit streets')"
              className="w-full p-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 h-20 resize-none"
            />
          )}
        </div>
      </div>

      <div className="mt-6 flex justify-center">
        <button
          onClick={handleApplyConfig}
          disabled={isLoading}
          className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 font-semibold"
        >
          {isLoading ? 'Applying Configuration...' : 'Apply Enhanced Configuration'}
        </button>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-xs text-blue-700">
          <strong>Note:</strong> This process may take several minutes depending on book length. 
          The AI will transform your story while preserving characters, plot, and relationships.
        </p>
      </div>
    </div>
  );
};

export default EnhancedModeConfig; 