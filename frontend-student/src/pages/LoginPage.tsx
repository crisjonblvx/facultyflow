import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, loading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch {
      // Error is already set in the store
    }
  };

  return (
    <div className="min-h-screen bg-light-gray flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <img src="/logo.png" alt="ReadySetClass Student Edition" className="h-20 mx-auto" />
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-text-primary mb-1">Welcome back</h2>
          <p className="text-dark-gray text-sm mb-6">Sign in to your account</p>

          {error && (
            <div className="bg-error/10 border border-error/20 text-error rounded-lg px-4 py-3 mb-4 text-sm">
              {error}
              <button onClick={clearError} className="float-right font-bold">x</button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@university.edu"
                className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Your password"
                className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-navy-primary text-white py-3 rounded-lg font-semibold text-base hover:bg-navy-hover transition disabled:opacity-50 disabled:cursor-not-allowed min-h-[48px]"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-dark-gray">
              Don't have an account?{' '}
              <Link to="/register" className="text-student-blue font-semibold hover:underline">
                Sign up free
              </Link>
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-dark-gray mt-6">
          Canvas, made simple.
        </p>
      </div>
    </div>
  );
}
