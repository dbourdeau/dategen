import { useState } from 'react';
import IdeaCard from '../components/IdeaCard';
import { ideasAPI } from '../api';

interface DateIdea {
  id: string;
  title: string;
  description: string;
  estimated_cost: number;
  duration_minutes: number;
  location: string;
  activity_types: string[];
  reasoning: string;
  confidence: number;
}

export function GenerateIdeasPage() {
  const [ideas, setIdeas] = useState<DateIdea[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerateIdeas = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await ideasAPI.generate();
      setIdeas(response.data);
    } catch (err) {
      setError('Failed to generate real ideas. Check preferences, auth, and API keys.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">Generate Date Ideas</h1>

        <button
          onClick={handleGenerateIdeas}
          disabled={loading}
          className="mb-8 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-3 px-8 rounded-lg hover:shadow-lg transition disabled:opacity-50"
        >
          {loading ? 'Generating...' : '✨ Get Date Ideas'}
        </button>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="grid gap-6">
          {ideas.length === 0 ? (
            <div className="bg-white rounded-lg shadow-lg p-12 text-center">
              <p className="text-gray-600 text-lg">Click "Get Date Ideas" to start planning!</p>
            </div>
          ) : (
            ideas.map(idea => <IdeaCard key={idea.id} idea={idea} />)
          )}
        </div>
      </div>
    </div>
  );
}

export default GenerateIdeasPage;
