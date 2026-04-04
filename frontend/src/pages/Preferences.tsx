import { useEffect, useState, type ChangeEvent } from 'react';
import { preferencesAPI } from '../api';

interface Preferences {
  budget_min: number;
  budget_max: number;
  city: string;
  activity_types: string[];
  her_interests: string[];
  dietary_restrictions: string[];
  available_duration_min: number;
  available_duration_max: number;
}

export function PreferencesPage() {
  const [preferences, setPreferences] = useState<Preferences>({
    budget_min: 20,
    budget_max: 150,
    city: 'Chicago',
    activity_types: [],
    her_interests: [],
    dietary_restrictions: [],
    available_duration_min: 1,
    available_duration_max: 3,
  });

  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await preferencesAPI.get();
        setPreferences(response.data);
      } catch {
        // No saved preferences yet is expected for first-time users.
      }
    };

    loadPreferences();
  }, []);


  const activityOptions = [
    'outdoor',
    'dining',
    'cultural',
    'adventure',
    'relaxation',
    'nightlife',
    'sports',
  ];

  const handleToggleActivity = (activity: string) => {
    setPreferences(prev => ({
      ...prev,
      activity_types: prev.activity_types.includes(activity)
        ? prev.activity_types.filter(a => a !== activity)
        : [...prev.activity_types, activity],
    }));
  };

  const handleInterestChange = (e: ChangeEvent<HTMLInputElement>) => {
    setPreferences(prev => ({
      ...prev,
      her_interests: e.target.value.split(',').map(i => i.trim()),
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    setError('');
    try {
      await preferencesAPI.create(preferences);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Error saving preferences:', err);
      setError('Failed to save preferences. Make sure you are logged in.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">Your Date Preferences</h1>

        <div className="bg-white rounded-lg shadow-lg p-8 space-y-6">
          {/* Budget */}
          <div>
            <label className="block text-lg font-semibold text-gray-700 mb-2">
              Budget Range: ${preferences.budget_min} - ${preferences.budget_max}
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="10"
                max="500"
                value={preferences.budget_max}
                onChange={(e) =>
                  setPreferences(prev => ({
                    ...prev,
                    budget_max: parseInt(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>
          </div>

          {/* City */}
          <div>
            <label className="block text-lg font-semibold text-gray-700 mb-2">
              City
            </label>
            <input
              type="text"
              value={preferences.city}
              onChange={(e) =>
                setPreferences(prev => ({ ...prev, city: e.target.value }))
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Chicago"
            />
          </div>

          {/* Activity Types */}
          <div>
            <label className="block text-lg font-semibold text-gray-700 mb-4">
              Activity Types (Select multiple)
            </label>
            <div className="grid grid-cols-2 gap-3">
              {activityOptions.map(activity => (
                <button
                  key={activity}
                  onClick={() => handleToggleActivity(activity)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    preferences.activity_types.includes(activity)
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {activity}
                </button>
              ))}
            </div>
          </div>

          {/* Her Interests */}
          <div>
            <label className="block text-lg font-semibold text-gray-700 mb-2">
              Her Interests (comma separated)
            </label>
            <input
              type="text"
              value={preferences.her_interests.join(', ')}
              onChange={handleInterestChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="hiking, museums, live music, cooking"
            />
          </div>

          {/* Duration */}
          <div>
            <label className="block text-lg font-semibold text-gray-700 mb-2">
              Available Duration: {preferences.available_duration_min}-
              {preferences.available_duration_max} hours
            </label>
            <div className="flex gap-4">
              <input
                type="range"
                min="1"
                max="8"
                value={preferences.available_duration_max}
                onChange={(e) =>
                  setPreferences(prev => ({
                    ...prev,
                    available_duration_max: parseInt(e.target.value),
                  }))
                }
                className="flex-1"
              />
            </div>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-3 rounded-lg hover:shadow-lg transition disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Preferences'}
          </button>

          {saved && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              Preferences saved successfully!
            </div>
          )}

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PreferencesPage;
