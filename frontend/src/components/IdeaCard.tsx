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
    maps_link?: string;
    verification?: {
      status?: string;
      avg_source_reliability?: number;
      avg_freshness?: number;
      provider_verified_count?: number;
    };
    stops?: Array<{
      name: string;
      url: string;
      source_domain?: string;
      reliability?: number;
      freshness?: number;
      neighborhood?: string;
    }>;
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
          {idea.verification && (
            <div className="mb-4 text-sm text-gray-700 space-y-1">
              <p>
                Verification: {idea.verification.status || 'unknown'} | Source reliability:{' '}
                {idea.verification.avg_source_reliability ?? 'n/a'} | Freshness:{' '}
                {idea.verification.avg_freshness ?? 'n/a'}
              </p>
            </div>
          )}

          {idea.stops && idea.stops.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-semibold text-gray-700 mb-2">Stops and sources</p>
              <ul className="text-sm text-gray-600 space-y-1">
                {idea.stops.map((stop) => (
                  <li key={`${idea.id}-${stop.name}`}>
                    {stop.url ? (
                      <a
                        href={stop.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {stop.name}
                      </a>
                    ) : (
                      <span>{stop.name}</span>
                    )}
                    {stop.source_domain ? ` (${stop.source_domain})` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {idea.maps_link && (
            <a
              href={idea.maps_link}
              target="_blank"
              rel="noreferrer"
              className="block mb-4 text-sm text-blue-600 hover:underline"
            >
              Primary source link
            </a>
          )}

          <button className="w-full bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-2 rounded-lg hover:shadow-lg transition">
            Save This Idea
          </button>
        </div>
      )}
    </div>
  );
}
