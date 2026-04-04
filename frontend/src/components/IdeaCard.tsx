import { useState } from 'react';

interface IdeaCardProps {
  idea: {
    id: string;
    title: string;
    description: string;
    estimated_cost: number;
    duration_minutes: number;
    location: string;
    activity_types: string[];
  };
}

export default function IdeaCard({ idea }: IdeaCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
      <div className="flex justify-between items-start mb-3">
        <h2 className="text-2xl font-bold text-gray-800">{idea.title}</h2>
        <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-semibold">
          ${idea.estimated_cost}
        </span>
      </div>

      <p className="text-gray-600 mb-4">{idea.description}</p>

      <div className="flex gap-3 mb-4 flex-wrap">
        {idea.activity_types.map(activity => (
          <span
            key={activity}
            className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
          >
            {activity}
          </span>
        ))}
      </div>

      <div className="flex justify-between items-center text-gray-600 text-sm mb-4">
        <span>⏱️ {idea.duration_minutes} minutes</span>
        <span>📍 {idea.location}</span>
      </div>

      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-purple-500 hover:text-purple-700 font-semibold"
      >
        {showDetails ? 'Hide Details' : 'View Details'}
      </button>

      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button className="w-full bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-2 rounded-lg hover:shadow-lg transition">
            Save This Idea
          </button>
        </div>
      )}
    </div>
  );
}
