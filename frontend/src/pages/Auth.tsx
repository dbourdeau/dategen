import { useState } from 'react';
import axios from 'axios';
import { authAPI } from '../api';

interface AuthPageProps {
  onAuthenticated: () => void;
}

export default function AuthPage({ onAuthenticated }: AuthPageProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = mode === 'login'
        ? await authAPI.login(email, password)
        : await authAPI.register(email, password);

      const token = response.data?.access_token;
      if (!token) {
        throw new Error('No access token returned from server');
      }

      localStorage.setItem('access_token', token);
      onAuthenticated();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Authentication failed');
      } else {
        setError('Authentication failed');
      }
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8 flex items-center justify-center">
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">DateGen</h1>
        <p className="text-gray-600 mb-6">Sign in to generate real date ideas with LLM + web search.</p>

        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setMode('login')}
            className={`flex-1 py-2 rounded-lg font-semibold ${
              mode === 'login' ? 'bg-purple-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            className={`flex-1 py-2 rounded-lg font-semibold ${
              mode === 'register' ? 'bg-purple-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-2 rounded-lg disabled:opacity-50"
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>

        {error && (
          <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
