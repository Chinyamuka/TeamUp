/**
 * Login Component
 * 
 * Handles user authentication with the backend API.
 * Supports both login and registration.
 */

import React, { useState } from 'react';
import { auth, setToken, setRefreshToken } from '../../api/client';

export const Login = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        // Registration
        const data = await auth.register(email, password, fullName);
        if (data.user) {
          // After registration, log in automatically
          const loginData = await auth.login(email, password);
          handleLoginSuccess(loginData);
        }
      } else {
        // Login
        const data = await auth.login(email, password);
        handleLoginSuccess(data);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (data) => {
    if (data.tokens) {
      setToken(data.tokens.access_token);
      setRefreshToken(data.tokens.refresh_token);
    }
    if (data.user) {
      onLogin(data.user, data.tokens);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl border border-border shadow-lg p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-terminal-indigo text-white mb-3">
            <span className="material-symbols-outlined text-3xl">grid_view</span>
          </div>
          <h1 className="text-3xl font-bold text-terminal-indigo">TeamUp</h1>
          <p className="text-text-secondary mt-1">
            {isRegister ? 'Create your account' : 'Sign in to your workspace'}
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-error-light border border-error text-on-error-container px-4 py-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-sm font-semibold text-text-primary mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                required={isRegister}
                className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-text-primary mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-text-primary mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={8}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-logic-blue text-white font-semibold rounded-lg hover:bg-logic-blue-dark transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        {/* Toggle */}
        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            className="text-sm text-logic-blue hover:underline"
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
        </div>

        {/* Demo Credentials */}
        {!isRegister && (
          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-text-muted text-center mb-3">Demo Credentials</p>
            <button
              onClick={() => {
                setEmail('d@gmail.com');
                setPassword('TestPass123');
              }}
              className="w-full py-1.5 text-sm text-logic-blue hover:bg-logic-blue/5 rounded-lg transition"
            >
              Use Demo Account
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
