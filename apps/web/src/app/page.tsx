'use client';

import Link from "next/link";
import { useEffect, useState } from "react";
import { getEnvironmentInfo } from "@/utils/environment";

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { agentDomain } = getEnvironmentInfo();

  useEffect(() => {
    // Check if user is authenticated (check both localStorage and cookies)
    const localToken = localStorage.getItem('bearerToken');
    const cookieToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('bearerToken='))
      ?.split('=')[1];
    
    setIsAuthenticated(!!(localToken || cookieToken));
    setIsLoading(false);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 md:p-8">
        <div className="text-center">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            Agent Dashboard
          </h1>
          <p className="text-gray-600 mb-8">
            AI-powered task creation and management
          </p>
          
          <div className="space-y-4">
            <Link
              href={isAuthenticated ? "/chat" : "/login"}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition-colors block"
            >
              {isAuthenticated ? "Open Chat Interface" : "Login to Continue"}
            </Link>
            
            <div className="text-sm text-gray-500">
              Create tasks with natural language and AI assistance
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-200">
            <div className="text-xs text-gray-400">
              Connected to agent.evanm.xyz
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
