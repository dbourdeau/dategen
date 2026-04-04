import React, { useState } from 'react';
import PreferencesPage from './pages/Preferences';
import GenerateIdeasPage from './pages/GenerateIdeas';
import './App.css';

type Page = 'preferences' | 'ideas' | 'reviews';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('ideas');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600">
            DateGen ❤️
          </h1>
          <div className="flex gap-4">
            <button
              onClick={() => setCurrentPage('ideas')}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                currentPage === 'ideas'
                  ? 'bg-purple-500 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              ✨ Ideas
            </button>
            <button
              onClick={() => setCurrentPage('preferences')}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                currentPage === 'preferences'
                  ? 'bg-purple-500 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              ⚙️ Settings
            </button>
            <button
              onClick={() => setCurrentPage('reviews')}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                currentPage === 'reviews'
                  ? 'bg-purple-500 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              ⭐ Reviews
            </button>
            <button className="px-4 py-2 rounded-lg font-semibold text-gray-700 hover:bg-gray-100 transition">
              👤 Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main>
        {currentPage === 'ideas' && <GenerateIdeasPage />}
        {currentPage === 'preferences' && <PreferencesPage />}
        {currentPage === 'reviews' && (
          <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8">
            <div className="max-w-4xl mx-auto">
              <h1 className="text-4xl font-bold text-gray-800 mb-8">Past Dates</h1>
              <div className="bg-white rounded-lg shadow-lg p-8 text-center">
                <p className="text-gray-600 text-lg">Reviews and analytics coming soon!</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
