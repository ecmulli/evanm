'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, XCircle, Loader, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function EnphaseCallbackPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Processing authorization...');
  const [tokens, setTokens] = useState<{ access_token?: string; refresh_token?: string } | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      setStatus('error');
      setMessage(`Authorization failed: ${error}`);
      return;
    }

    if (!code) {
      setStatus('error');
      setMessage('No authorization code received');
      return;
    }

    // Verify state matches what we stored
    const storedState = sessionStorage.getItem('enphase_oauth_state');
    if (state && storedState && state !== storedState) {
      setStatus('error');
      setMessage('State mismatch - possible CSRF attack');
      return;
    }

    // Exchange code for tokens
    exchangeCodeForTokens(code, state || '');
  }, [searchParams]);

  const exchangeCodeForTokens = async (code: string, state: string) => {
    try {
      const token = localStorage.getItem('bearerToken') || '';
      
      const response = await fetch('/api/v1/enphase/oauth/callback', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, state }),
      });

      const data = await response.json();

      if (data.success) {
        setStatus('success');
        setMessage('Successfully connected to Enphase!');
        setTokens({
          access_token: data.access_token,
          refresh_token: data.refresh_token,
        });
        // Clear stored state
        sessionStorage.removeItem('enphase_oauth_state');
      } else {
        setStatus('error');
        setMessage(data.message || 'Failed to exchange authorization code');
      }
    } catch (err) {
      setStatus('error');
      setMessage('Failed to connect to server');
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl border border-gray-200 p-8 max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <Loader className="w-12 h-12 text-amber-500 animate-spin mx-auto mb-4" />
            <h1 className="text-xl font-semibold text-gray-900 mb-2">Connecting to Enphase</h1>
            <p className="text-gray-600">{message}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-green-500" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">Connected!</h1>
            <p className="text-gray-600 mb-6">{message}</p>
            
            {tokens && (
              <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
                <p className="text-xs text-gray-500 mb-2">Tokens have been saved. You can now query your solar data.</p>
                <div className="text-xs font-mono text-gray-600 break-all">
                  <div className="mb-1">
                    <span className="text-gray-400">Access:</span> {tokens.access_token}
                  </div>
                  <div>
                    <span className="text-gray-400">Refresh:</span> {tokens.refresh_token}
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3">
              <Link
                href="/chat"
                className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Go to Chat
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/settings"
                className="block text-sm text-gray-600 hover:text-gray-900"
              >
                Back to Settings
              </Link>
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-10 h-10 text-red-500" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">Connection Failed</h1>
            <p className="text-gray-600 mb-6">{message}</p>
            
            <div className="space-y-3">
              <Link
                href="/settings"
                className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Back to Settings
              </Link>
              <button
                onClick={() => window.location.href = '/settings'}
                className="block w-full text-sm text-blue-600 hover:text-blue-700"
              >
                Try Again
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
