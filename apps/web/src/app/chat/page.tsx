'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Upload, AlertCircle, Clock, User, Bot, LogOut, Menu, X } from 'lucide-react';
import { getEnvironmentInfo } from '@/utils/environment';

interface Message {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'system';
  timestamp: Date;
  taskInfo?: {
    taskName: string;
    workspace: string;
    priority: string;
    estimatedHours: number;
    status: string;
    notionUrl?: string;
  };
}

interface ConfirmationDialog {
  isOpen: boolean;
  taskData: {
    task_name: string;
    workspace: string;
    priority: string;
    estimated_hours: number;
    due_date?: string;
    description: string;
    acceptance_criteria?: string;
    labels?: string[];
    status: string;
    team: string;
  } | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hi! I can help you create tasks. Just describe what you need to do and I\'ll help you create a structured task with all the details.',
      type: 'assistant',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { agentDomain } = getEnvironmentInfo();
  const [confirmation, setConfirmation] = useState<ConfirmationDialog>({
    isOpen: false,
    taskData: null,
    onConfirm: () => {},
    onCancel: () => {}
  });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && selectedFiles.length === 0) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      type: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // First, do a dry run to get task preview
      const dryRunResponse = await createTask(input, selectedFiles, true);
      
      if (dryRunResponse.success) {
        // Show confirmation dialog
        setConfirmation({
          isOpen: true,
          taskData: dryRunResponse.parsed_data,
          onConfirm: async () => {
            setConfirmation(prev => ({ ...prev, isOpen: false }));
            
            // Create actual task
            const actualResponse = await createTask(input, selectedFiles, false);
            
            const assistantMessage: Message = {
              id: (Date.now() + 1).toString(),
              content: actualResponse.message,
              type: 'assistant',
              timestamp: new Date(),
              taskInfo: actualResponse.success ? {
                taskName: actualResponse.parsed_data.task_name,
                workspace: actualResponse.parsed_data.workspace,
                priority: actualResponse.parsed_data.priority,
                estimatedHours: actualResponse.parsed_data.estimated_hours,
                status: actualResponse.parsed_data.status,
                notionUrl: actualResponse.task_url,
              } : undefined,
            };
            
            setMessages(prev => [...prev, assistantMessage]);
          },
          onCancel: () => {
            setConfirmation(prev => ({ ...prev, isOpen: false }));
            const cancelMessage: Message = {
              id: (Date.now() + 1).toString(),
              content: 'Task creation cancelled. Feel free to modify your request or try again.',
              type: 'system',
              timestamp: new Date(),
            };
            setMessages(prev => [...prev, cancelMessage]);
          }
        });
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `Error: ${dryRunResponse.message || 'Failed to process request'}`,
          type: 'system',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Failed to connect to the server. Please try again.',
        type: 'system',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setSelectedFiles([]);
    }
  };

  const createTask = async (textInput: string, files: File[], dryRun: boolean) => {
    // Get token from localStorage
    const token = localStorage.getItem('bearerToken') || process.env.NEXT_PUBLIC_BEARER_TOKEN || '';
    
    console.log('🔑 Token being used:', token ? `${token.substring(0, 10)}...` : 'No token found');
    
    // Add files for OCR if any
    const imageUrls: string[] = [];
    if (files.length > 0) {
      for (const file of files) {
        // In a real implementation, you'd upload to cloud storage first
        // For now, we'll convert to base64 for demo purposes
        const base64 = await fileToBase64(file);
        imageUrls.push(base64);
      }
    }

    const requestBody = {
      text_inputs: [textInput],
      image_urls: imageUrls.length > 0 ? imageUrls : undefined,
      dry_run: dryRun,
    };

    console.log('📤 API Request:', {
      url: '/api/v1/task_creator',
      headers: {
        'Authorization': `Bearer ${token ? `${token.substring(0, 10)}...` : 'No token'}`,
        'Content-Type': 'application/json',
      },
      body: requestBody
    });

    const response = await fetch('/api/v1/task_creator', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    console.log('📥 API Response:', response.status, response.statusText);
    
    const result = await response.json();
    console.log('📋 Response data:', result);
    
    return result;
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleLogout = () => {
    // Clear both localStorage and cookies
    localStorage.removeItem('bearerToken');
    document.cookie = 'bearerToken=; path=/; max-age=0';
    
    // Redirect to login
    window.location.href = '/login';
  };

  return (
    <div className="flex h-screen bg-gray-50 relative">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsSidebarOpen(true)}
        className="md:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-white border border-gray-200 shadow-lg"
      >
        <Menu size={20} className="text-gray-600" />
      </button>

      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed md:static inset-y-0 left-0 z-50 w-80 bg-white border-r border-gray-200 flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Task Creator</h1>
            <p className="text-sm text-gray-600">Create tasks with AI assistance</p>
          </div>
          {/* Close button for mobile */}
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="md:hidden p-1 rounded-lg hover:bg-gray-100"
          >
            <X size={20} className="text-gray-600" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-sm font-medium text-gray-900 mb-3">Recent Conversations</h2>
          <div className="space-y-2">
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 cursor-pointer">
              <div className="text-sm font-medium text-blue-900">Current Session</div>
              <div className="text-xs text-blue-600 mt-1">{messages.length} messages</div>
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={16} />
            <span>Logout</span>
          </button>
          <div className="text-xs text-gray-500 mt-2 text-center">
            Connected to {agentDomain}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col md:ml-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 pt-16 md:pt-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-full md:max-w-3xl ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 ${message.type === 'user' ? 'ml-3' : 'mr-3'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : message.type === 'assistant'
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-500 text-white'
                  }`}>
                    {message.type === 'user' ? <User size={16} /> : message.type === 'assistant' ? <Bot size={16} /> : <AlertCircle size={16} />}
                  </div>
                </div>
                
                <div className={`rounded-2xl px-4 py-2 ${
                  message.type === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : message.type === 'assistant'
                    ? 'bg-white border border-gray-200 text-gray-900'
                    : 'bg-yellow-50 border border-yellow-200 text-yellow-800'
                }`}>
                  <div className="text-sm">{message.content}</div>
                  
                  {message.taskInfo && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <h4 className="font-medium text-gray-900 mb-2">Task Created:</h4>
                      <div className="space-y-1 text-xs text-gray-600">
                        <div><strong>Name:</strong> {message.taskInfo.taskName}</div>
                        <div><strong>Workspace:</strong> {message.taskInfo.workspace}</div>
                        <div><strong>Priority:</strong> {message.taskInfo.priority}</div>
                        <div><strong>Estimated Hours:</strong> {message.taskInfo.estimatedHours}</div>
                        <div><strong>Status:</strong> {message.taskInfo.status}</div>
                        {message.taskInfo.notionUrl && (
                          <div>
                            <strong>Notion URL:</strong>{' '}
                            <a 
                              href={message.taskInfo.notionUrl} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 underline"
                            >
                              Open in Notion →
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <div className="text-xs opacity-70 mt-2">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex mr-3">
                <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center">
                  <Bot size={16} />
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-2">
                <div className="flex items-center space-x-2">
                  <Clock size={16} className="animate-spin text-gray-400" />
                  <span className="text-sm text-gray-600">Processing your request...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white p-4 pb-safe">
          {selectedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {selectedFiles.map((file, index) => (
                <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-1 text-sm text-blue-800">
                  {file.name}
                  <button
                    onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="flex items-end space-x-2 md:space-x-3">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Describe the task you want to create..."
                className="w-full resize-none rounded-lg border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
            </div>
            
            <div className="flex space-x-1 md:space-x-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept="image/*"
                multiple
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                <Upload size={18} className="text-gray-600 md:w-5 md:h-5" />
              </button>
              
              <button
                type="submit"
                disabled={(!input.trim() && selectedFiles.length === 0) || isLoading}
                className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send size={18} className="md:w-5 md:h-5" />
              </button>
            </div>
          </form>
          
          <div className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {confirmation.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 md:p-4">
          <div className="bg-white rounded-lg max-w-full md:max-w-4xl w-full max-h-[95vh] md:max-h-[90vh] flex flex-col m-2 md:m-0">
            <div className="p-4 md:p-6 border-b border-gray-200">
              <h3 className="text-lg md:text-xl font-semibold text-gray-900">📋 Confirm Task Creation</h3>
            </div>
            
            {confirmation.taskData && (
              <div className="flex-1 overflow-y-auto p-4 md:p-6">
                <div className="space-y-4 md:space-y-6">
                  {/* Task Header */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-900 mb-3">
                      {confirmation.taskData.task_name}
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 text-sm">
                      <div>
                        <span className="text-blue-700 font-medium">🏢 Workspace:</span>
                        <div className="text-blue-900">{confirmation.taskData.workspace}</div>
                      </div>
                      <div>
                        <span className="text-blue-700 font-medium">⚡ Priority:</span>
                        <div className="text-blue-900">{confirmation.taskData.priority}</div>
                      </div>
                      <div>
                        <span className="text-blue-700 font-medium">⏱️ Duration:</span>
                        <div className="text-blue-900">{confirmation.taskData.estimated_hours} hours</div>
                      </div>
                      <div>
                        <span className="text-blue-700 font-medium">📅 Due Date:</span>
                        <div className="text-blue-900">{confirmation.taskData.due_date || 'Not set'}</div>
                      </div>
                    </div>
                    {confirmation.taskData.labels && confirmation.taskData.labels.length > 0 && (
                      <div className="mt-3">
                        <span className="text-blue-700 font-medium text-sm">🏷️ Labels:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {confirmation.taskData.labels.map((label: string, idx: number) => (
                            <span key={idx} className="bg-blue-200 text-blue-800 text-xs px-2 py-1 rounded">
                              {label}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  <div>
                    <h5 className="font-semibold text-gray-900 mb-3">📝 Description</h5>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {confirmation.taskData.description}
                      </div>
                    </div>
                  </div>

                  {/* Acceptance Criteria */}
                  {confirmation.taskData.acceptance_criteria && (
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-3">✅ Acceptance Criteria</h5>
                      <div className="bg-green-50 rounded-lg p-4">
                        <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                          {confirmation.taskData.acceptance_criteria.split('\n').map((line: string, idx: number) => {
                            if (line.trim().startsWith('- [ ]')) {
                              return (
                                <div key={idx} className="flex items-start space-x-2 mb-2">
                                  <input type="checkbox" className="mt-1 rounded" disabled />
                                  <span className="text-gray-700">{line.replace('- [ ]', '').trim()}</span>
                                </div>
                              );
                            } else if (line.trim()) {
                              return (
                                <div key={idx} className="text-gray-700 mb-1">{line}</div>
                              );
                            }
                            return <div key={idx} className="mb-1"></div>;
                          })}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Additional Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="font-medium text-gray-700">✅ Status:</span>
                      <span className="ml-2 text-gray-900">{confirmation.taskData.status}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">👥 Team:</span>
                      <span className="ml-2 text-gray-900">{confirmation.taskData.team}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div className="p-4 md:p-6 border-t border-gray-200 flex flex-col sm:flex-row justify-end gap-3 sm:space-x-3">
              <button
                onClick={confirmation.onCancel}
                className="px-4 md:px-6 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors order-2 sm:order-1"
              >
                Cancel
              </button>
              <button
                onClick={confirmation.onConfirm}
                className="px-4 md:px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium order-1 sm:order-2"
              >
                ✅ Create Task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}