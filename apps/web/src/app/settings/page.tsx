'use client';

import { useState, useEffect } from 'react';
import { Sun, CheckCircle, XCircle, Loader, ArrowLeft, ExternalLink, RefreshCw } from 'lucide-react';
import Link from 'next/link';

interface EnphaseStatus {
  configured: boolean;
  has_tokens: boolean;
  system_id: string | null;
  service_initialized: boolean;
}

export default function SettingsPage() {
  const [enphaseStatus, setEnphaseStatus] = useState<EnphaseStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEnphaseStatus();
  }, []);

  const fetchEnphaseStatus = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('bearerToken') || '';
      const response = await fetch('/api/v1/enphase/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setEnphaseStatus(data);
      } else {
        setError('Failed to fetch Enphase status');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const initiateOAuth = async () => {
    setIsConnecting(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('bearerToken') || '';
      const response = await fetch('/api/v1/enphase/oauth/init', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        // Store state for verification
        sessionStorage.setItem('enphase_oauth_state', data.state);
        // Redirect to Enphase authorization
        window.location.href = data.auth_url;
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to initiate OAuth');
      }
    } catch (err) {
      setError('Failed to start OAuth flow');
      console.error(err);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link 
              href="/chat" 
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-600" />
            </Link>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
              <p className="text-sm text-gray-600">Manage your integrations</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Enphase Integration Card */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-amber-100 rounded-lg">
                <Sun className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Enphase Solar</h2>
                <p className="text-sm text-gray-600">Connect your solar system to query production and consumption data</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {isLoading ? (
              <div className="flex items-center gap-3 text-gray-600">
                <Loader className="w-5 h-5 animate-spin" />
                <span>Checking connection status...</span>
              </div>
            ) : error ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-red-600">
                  <XCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
                <button
                  onClick={fetchEnphaseStatus}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  <RefreshCw size={16} />
                  Retry
                </button>
              </div>
            ) : enphaseStatus ? (
              <div className="space-y-6">
                {/* Status Indicators */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    {enphaseStatus.configured ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-400" />
                    )}
                    <div>
                      <div className="text-sm font-medium text-gray-900">API Credentials</div>
                      <div className="text-xs text-gray-500">
                        {enphaseStatus.configured ? 'Configured' : 'Not configured'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    {enphaseStatus.has_tokens ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-400" />
                    )}
                    <div>
                      <div className="text-sm font-medium text-gray-900">OAuth Tokens</div>
                      <div className="text-xs text-gray-500">
                        {enphaseStatus.has_tokens ? 'Connected' : 'Not connected'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    {enphaseStatus.system_id ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-400" />
                    )}
                    <div>
                      <div className="text-sm font-medium text-gray-900">System ID</div>
                      <div className="text-xs text-gray-500">
                        {enphaseStatus.system_id || 'Not configured'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    {enphaseStatus.service_initialized ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-400" />
                    )}
                    <div>
                      <div className="text-sm font-medium text-gray-900">Service Status</div>
                      <div className="text-xs text-gray-500">
                        {enphaseStatus.service_initialized ? 'Active' : 'Not initialized'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Button */}
                {enphaseStatus.configured && !enphaseStatus.has_tokens && (
                  <div className="pt-4 border-t border-gray-100">
                    <p className="text-sm text-gray-600 mb-4">
                      Your API credentials are configured. Connect your Enphase account to authorize access to your solar data.
                    </p>
                    <button
                      onClick={initiateOAuth}
                      disabled={isConnecting}
                      className="flex items-center gap-2 px-6 py-3 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isConnecting ? (
                        <>
                          <Loader className="w-5 h-5 animate-spin" />
                          Connecting...
                        </>
                      ) : (
                        <>
                          <ExternalLink className="w-5 h-5" />
                          Connect Enphase Account
                        </>
                      )}
                    </button>
                  </div>
                )}

                {enphaseStatus.has_tokens && (
                  <div className="pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-2 text-green-600 mb-4">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-medium">Enphase is connected!</span>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      You can now ask the assistant about your solar production, consumption, and net energy usage.
                    </p>
                    <Link
                      href="/chat"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Go to Chat
                      <ArrowLeft className="w-4 h-4 rotate-180" />
                    </Link>
                  </div>
                )}

                {!enphaseStatus.configured && (
                  <div className="pt-4 border-t border-gray-100">
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                      <h3 className="font-medium text-amber-900 mb-2">Configuration Required</h3>
                      <p className="text-sm text-amber-800 mb-3">
                        To connect Enphase, the following environment variables need to be set in Railway:
                      </p>
                      <ul className="text-sm text-amber-800 space-y-1 font-mono">
                        <li>• ENPHASE_CLIENT_ID</li>
                        <li>• ENPHASE_CLIENT_SECRET</li>
                        <li>• ENPHASE_API_KEY</li>
                        <li>• ENPHASE_SYSTEM_ID</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">How to Connect Enphase</h3>
          <ol className="space-y-3 text-sm text-gray-600">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">1</span>
              <span>Register at <a href="https://developer.enphase.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">developer.enphase.com</a> and create an application</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">2</span>
              <span>Add the Client ID, Client Secret, and API Key to your Railway environment variables</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">3</span>
              <span>Find your System ID in the Enphase Enlighten portal and add it to Railway</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">4</span>
              <span>Click &quot;Connect Enphase Account&quot; above to authorize access</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}
