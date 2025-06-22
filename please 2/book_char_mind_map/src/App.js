import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/homePage/index";
import BookPage from "./pages/bookPage/index";
import StoryMode from "./pages/storyMode/index";

function App() {
  return (
    <Router>
      <Routes>
        {/* Define routes for Home, BookPage, and StoryMode */}
        <Route path="/" element={<Home />} />
        <Route path="/book" element={<BookPage />} />
        <Route path="/story" element={<StoryMode />} />
      </Routes>
    </Router>
  );
}

export default App;
