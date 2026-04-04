import React, { useState } from 'react';

interface ReviewFormProps {
  ideaId: string;
  onSubmit: (review: any) => void;
}

export default function ReviewForm({ ideaId, onSubmit }: ReviewFormProps) {
  const [rating, setRating] = useState(5);
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ date_idea_id: ideaId, rating, went_well: feedback });
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6 space-y-4">
      <h2 className="text-2xl font-bold text-gray-800">How was the date?</h2>

      <div>
        <label className="block font-semibold text-gray-700 mb-2">Rating</label>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map(r => (
            <button
              key={r}
              type="button"
              onClick={() => setRating(r)}
              className={`w-12 h-12 rounded-lg font-bold text-lg transition ${
                rating === r
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {r}⭐
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block font-semibold text-gray-700 mb-2">What went well?</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          placeholder="Tell us what you enjoyed about this date..."
          rows={4}
        />
      </div>

      <button
        type="submit"
        className="w-full bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-2 rounded-lg hover:shadow-lg transition"
      >
        Submit Review
      </button>

      {submitted && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          Thanks for the feedback! We'll use it to improve future suggestions.
        </div>
      )}
    </form>
  );
}
