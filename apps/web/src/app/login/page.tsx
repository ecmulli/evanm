'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Lock, Loader } from 'lucide-react';
import { getEnvironmentInfo } from '@/utils/environment';

function LoginForm() {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { agentDomain } = getEnvironmentInfo();

  const validateToken = async (tokenToValidate: string) => {
    try {
      // Test token using the auth validation endpoint
      const response = await fetch('/api/v1/auth/validate', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${tokenToValidate}`,
        },
      });
      
      return response.ok;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token.trim()) {
      setError('Please enter a bearer token');
      return;
    }

    const trimmedToken = token.trim();
    
    // Basic format validation (should be a long hex string)
    if (trimmedToken.length < 32 || !/^[a-fA-F0-9]+$/.test(trimmedToken)) {
      setError('Invalid token format. Token should be a hexadecimal string.');
      return;
    }

    setIsValidating(true);
    setError('');

    try {
      console.log('🔐 Validating token:', trimmedToken.substring(0, 10) + '...');
      
      const isValid = await validateToken(trimmedToken);
      
      if (!isValid) {
        setError('Invalid authentication credentials. Please check your bearer token.');
        setIsValidating(false);
        return;
      }

      console.log('✅ Token validated successfully');
      
      // Store token in both localStorage and cookies for middleware
      localStorage.setItem('bearerToken', trimmedToken);
      
      // Set cookie for middleware
      document.cookie = `bearerToken=${trimmedToken}; path=/; max-age=${60 * 60 * 24 * 7}`; // 7 days
      
      // Redirect to the original page (or /dashboard as default)
      const redirect = searchParams.get('redirect') || '/dashboard';
      router.push(redirect);
    } catch (err) {
      setError('Failed to validate token. Please check your connection and try again.');
      console.error('Login error:', err);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Authentication Required
          </h1>
          <p className="text-gray-600">
            Please enter your bearer token to access the chat interface
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="token" className="block text-sm font-medium text-gray-700 mb-2">
              Bearer Token
            </label>
            <input
              type="password"
              id="token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Enter your bearer token"
              disabled={isValidating}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <div className="text-xs text-gray-500 mt-1">
              Enter the hexadecimal bearer token configured in your backend
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isValidating}
            className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center"
          >
            {isValidating ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Validating...
              </>
            ) : (
              'Login'
            )}
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-gray-200 text-center">
          <div className="text-xs text-gray-400">
            {agentDomain}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}